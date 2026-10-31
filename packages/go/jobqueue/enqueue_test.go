package jobqueue_test

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"log"
	"os"
	"testing"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	_ "github.com/jackc/pgx/v5/stdlib"
	"github.com/testcontainers/testcontainers-go"
	"github.com/testcontainers/testcontainers-go/modules/postgres"

	"github.com/Adrianus-Bagas/applied-math-lab/contracts"
	"github.com/Adrianus-Bagas/applied-math-lab/packages/go/jobqueue"
)

const summaryKind = "lab.stats.summary"

var (
	pool *pgxpool.Pool
	reg  *jobqueue.Registry
)

func TestMain(m *testing.M) { os.Exit(runTests(m)) }

// runTests ada agar pembersihan ter-defer berjalan sebelum os.Exit.
func runTests(m *testing.M) int {
	ctx := context.Background()

	ctr, err := postgres.Run(ctx, "postgres:18",
		postgres.WithDatabase("test"),
		postgres.WithUsername("test"),
		postgres.WithPassword("test"),
		postgres.BasicWaitStrategies(),
	)
	if err != nil {
		log.Printf("start postgres: %v", err)
		return 1
	}
	defer func() {
		if err := testcontainers.TerminateContainer(ctr); err != nil {
			log.Printf("terminate postgres: %v", err)
		}
	}()

	dsn, err := ctr.ConnectionString(ctx, "sslmode=disable")
	if err != nil {
		log.Printf("dsn: %v", err)
		return 1
	}

	db, err := sql.Open("pgx", dsn)
	if err != nil {
		log.Printf("open: %v", err)
		return 1
	}
	if _, err := jobqueue.Migrate(ctx, db); err != nil {
		log.Printf("migrate: %v", err)
		return 1
	}
	_ = db.Close()

	pool, err = pgxpool.New(ctx, dsn)
	if err != nil {
		log.Printf("pool: %v", err)
		return 1
	}
	defer pool.Close()

	reg, err = jobqueue.NewRegistry(contracts.Jobs, "jobs")
	if err != nil {
		log.Printf("registry: %v", err)
		return 1
	}
	return m.Run()
}

func reset(t *testing.T) {
	t.Helper()
	if _, err := pool.Exec(context.Background(), "TRUNCATE lab_jobs"); err != nil {
		t.Fatalf("truncate: %v", err)
	}
}

func countJobs(t *testing.T) int {
	t.Helper()
	var n int
	if err := pool.QueryRow(context.Background(), "SELECT count(*) FROM lab_jobs").Scan(&n); err != nil {
		t.Fatalf("count: %v", err)
	}
	return n
}

func summaryJob(payload string) jobqueue.Job {
	return jobqueue.Job{Kind: summaryKind, SchemaVersion: 1, Payload: json.RawMessage(payload)}
}

func TestEnqueueStoresQueuedJobWithDefaults(t *testing.T) {
	reset(t)
	ctx := context.Background()

	id, err := jobqueue.Enqueue(ctx, pool, reg, summaryJob(`{"n": 1000, "seed": 9007199254740991}`))
	if err != nil {
		t.Fatalf("enqueue: %v", err)
	}

	var (
		status           string
		attempts, maxAtt int32
		timeoutS         int32
		seed             int64
	)
	err = pool.QueryRow(ctx, `
		SELECT status, attempts, max_attempts, timeout_s, (payload->>'seed')::bigint
		FROM lab_jobs WHERE id = $1`, id,
	).Scan(&status, &attempts, &maxAtt, &timeoutS, &seed)
	if err != nil {
		t.Fatalf("select: %v", err)
	}
	if status != "queued" || attempts != 0 || maxAtt != 3 || timeoutS != 600 {
		t.Errorf("got status=%s attempts=%d max=%d timeout=%d", status, attempts, maxAtt, timeoutS)
	}
	if seed != 9007199254740991 { // 2^53 - 1 harus selamat tanpa pembulatan
		t.Errorf("seed = %d, want 9007199254740991", seed)
	}
}

func TestEnqueueRejectsInvalidPayload(t *testing.T) {
	cases := map[string]string{
		"missing seed":    `{"n": 10}`,
		"n zero":          `{"n": 0, "seed": 1}`,
		"n not integer":   `{"n": 10.5, "seed": 1}`,
		"unknown field":   `{"n": 10, "seed": 1, "sead": 2}`,
		"seed above 2^53": `{"n": 10, "seed": 9007199254740992}`,
		"negative seed":   `{"n": 10, "seed": -1}`,
		"not json":        `{"n": 10,`,
	}
	for name, payload := range cases {
		t.Run(name, func(t *testing.T) {
			reset(t)
			_, err := jobqueue.Enqueue(context.Background(), pool, reg, summaryJob(payload))
			if !errors.Is(err, jobqueue.ErrInvalidPayload) {
				t.Fatalf("err = %v, want ErrInvalidPayload", err)
			}
			if n := countJobs(t); n != 0 {
				t.Fatalf("%d rows inserted, want 0", n)
			}
		})
	}
}

func TestEnqueueRejectsUnknownKindOrVersion(t *testing.T) {
	reset(t)
	ctx := context.Background()
	for _, job := range []jobqueue.Job{
		{Kind: "lab.nope", SchemaVersion: 1, Payload: json.RawMessage(`{}`)},
		{Kind: summaryKind, SchemaVersion: 2, Payload: json.RawMessage(`{"n": 1, "seed": 1}`)},
	} {
		if _, err := jobqueue.Enqueue(ctx, pool, reg, job); !errors.Is(err, jobqueue.ErrUnknownKind) {
			t.Errorf("%s v%d: err = %v, want ErrUnknownKind", job.Kind, job.SchemaVersion, err)
		}
	}
}

func TestEnqueueNotifiesListeners(t *testing.T) {
	reset(t)
	ctx := context.Background()

	conn, err := pool.Acquire(ctx)
	if err != nil {
		t.Fatalf("acquire: %v", err)
	}
	defer conn.Release()
	if _, err := conn.Exec(ctx, "LISTEN "+jobqueue.NotifyChannel); err != nil {
		t.Fatalf("listen: %v", err)
	}
	// Koneksi kembali ke pool; jangan biarkan masih LISTEN.
	defer func() { _, _ = conn.Exec(ctx, "UNLISTEN *") }()

	if _, err := jobqueue.Enqueue(ctx, pool, reg, summaryJob(`{"n": 1, "seed": 1}`)); err != nil {
		t.Fatalf("enqueue: %v", err)
	}

	wctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()
	n, err := conn.Conn().WaitForNotification(wctx)
	if err != nil {
		t.Fatalf("wait: %v", err)
	}
	if n.Channel != jobqueue.NotifyChannel || n.Payload != summaryKind {
		t.Errorf("got channel=%q payload=%q", n.Channel, n.Payload)
	}
}

func TestEnqueueRollbackLeavesNoTrace(t *testing.T) {
	reset(t)
	ctx := context.Background()

	conn, err := pool.Acquire(ctx)
	if err != nil {
		t.Fatalf("acquire: %v", err)
	}
	defer conn.Release()
	if _, err := conn.Exec(ctx, "LISTEN "+jobqueue.NotifyChannel); err != nil {
		t.Fatalf("listen: %v", err)
	}
	// Koneksi kembali ke pool; jangan biarkan masih LISTEN.
	defer func() { _, _ = conn.Exec(ctx, "UNLISTEN *") }()

	tx, err := pool.Begin(ctx)
	if err != nil {
		t.Fatalf("begin: %v", err)
	}
	// Pengaman: bila test berhenti di tengah, koneksi tx tetap kembali ke pool.
	// Rollback kedua setelah rollback eksplisit hanya mengembalikan ErrTxClosed.
	defer func() { _ = tx.Rollback(ctx) }()

	if _, err := jobqueue.Enqueue(ctx, tx, reg, summaryJob(`{"n": 1, "seed": 1}`)); err != nil {
		t.Fatalf("enqueue: %v", err)
	}

	// Di dalam tx baris sudah terlihat: insert benar-benar terjadi.
	var inTx int
	if err := tx.QueryRow(ctx, "SELECT count(*) FROM lab_jobs").Scan(&inTx); err != nil {
		t.Fatalf("count in tx: %v", err)
	}
	if inTx != 1 {
		t.Fatalf("rows inside tx = %d, want 1", inTx)
	}

	if err := tx.Rollback(ctx); err != nil {
		t.Fatalf("rollback: %v", err)
	}

	// Dari koneksi lain, setelah rollback: tidak ada baris.
	if n := countJobs(t); n != 0 {
		t.Fatalf("rows after rollback = %d, want 0", n)
	}

	// Tidak ada notifikasi: NOTIFY hanya terkirim saat commit.
	wctx, cancel := context.WithTimeout(ctx, 500*time.Millisecond)
	defer cancel()
	_, err = conn.Conn().WaitForNotification(wctx)
	if !errors.Is(err, context.DeadlineExceeded) {
		t.Fatalf("err = %v, want DeadlineExceeded (no notification after rollback)", err)
	}
}
