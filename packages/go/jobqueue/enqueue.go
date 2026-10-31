package jobqueue

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgconn"
)

// NotifyChannel adalah kanal LISTEN/NOTIFY yang ditunggu worker; payload-nya kind job.
// Notifikasi hanya petunjuk untuk membangunkan worker: tabel lab_jobs adalah sumber kebenaran.
const NotifyChannel = "lab_jobs"

const (
	defaultMaxAttempts = 3
	defaultTimeoutS    = 600
)

// Job mendeskripsikan job yang akan dimasukkan. MaxAttempts atau TimeoutS bernilai nol berarti default.
type Job struct {
	Kind          string
	SchemaVersion int
	Payload       json.RawMessage
	Priority      int16
	MaxAttempts   int32
	TimeoutS      int32
}

// DBTX dipenuhi oleh *pgxpool.Pool, *pgx.Conn, dan pgx.Tx, sehingga pemanggil bisa
// melakukan enqueue di dalam transaksinya sendiri bersama penulisan data domain.
type DBTX interface {
	Exec(ctx context.Context, sql string, args ...any) (pgconn.CommandTag, error)
	QueryRow(ctx context.Context, sql string, args ...any) pgx.Row
}

// Enqueue memvalidasi payload, menyimpan job berstatus queued, dan mengirim
// notifikasi. Bila db adalah pgx.Tx, baris dan notifikasinya baru terlihat
// jika transaksi di-commit.
func Enqueue(ctx context.Context, db DBTX, reg *Registry, job Job) (string, error) {
	if err := reg.Validate(job.Kind, job.SchemaVersion, job.Payload); err != nil {
		return "", err
	}
	maxAttempts := job.MaxAttempts
	if maxAttempts == 0 {
		maxAttempts = defaultMaxAttempts
	}
	timeoutS := job.TimeoutS
	if timeoutS == 0 {
		timeoutS = defaultTimeoutS
	}

	var id string
	err := db.QueryRow(ctx, `
		INSERT INTO lab_jobs (kind, schema_version, payload, priority, max_attempts, timeout_s)
		VALUES ($1, $2, $3, $4, $5, $6)
		RETURNING id::text`,
		job.Kind, job.SchemaVersion, job.Payload, job.Priority, maxAttempts, timeoutS,
	).Scan(&id)
	if err != nil {
		return "", fmt.Errorf("jobqueue: insert job: %w", err)
	}

	if _, err := db.Exec(ctx, `SELECT pg_notify($1, $2)`, NotifyChannel, job.Kind); err != nil {
		return "", fmt.Errorf("jobqueue: notify: %w", err)
	}
	return id, nil
}
