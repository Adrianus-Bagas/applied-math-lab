package main

import (
	"encoding/json"
	"io"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/jackc/pgx/v5/stdlib"
	"github.com/testcontainers/testcontainers-go"
	"github.com/testcontainers/testcontainers-go/modules/postgres"

	"github.com/Adrianus-Bagas/applied-math-lab/contracts"
	"github.com/Adrianus-Bagas/applied-math-lab/packages/go/jobqueue"
)

// validPayload harus lolos contracts/jobs/lab.stats.summary.v1.schema.json.
const validPayload = "{\"n\": 1000000, \"seed\": 42}"

// respon adalah hasil request yang body-nya sudah dibaca habis dan ditutup.
type respon struct {
	status int
	header http.Header
	body   []byte
}

// doReq mengirim request dan langsung membaca serta menutup body-nya.
func doReq(t *testing.T, method, url, body string) respon {
	t.Helper()
	req, err := http.NewRequestWithContext(t.Context(), method, url, strings.NewReader(body))
	if err != nil {
		t.Fatal(err)
	}
	req.Header.Set("Content-Type", "application/json")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatal(err)
	}
	defer func() { _ = resp.Body.Close() }()
	b, err := io.ReadAll(resp.Body)
	if err != nil {
		t.Fatal(err)
	}
	return respon{status: resp.StatusCode, header: resp.Header, body: b}
}

// newTestServer menyalakan Postgres sekali pakai, menerapkan migrasi antrean,
// dan mengembalikan hello-api yang tersambung ke sana.
func newTestServer(t *testing.T) (*httptest.Server, *pgxpool.Pool) {
	t.Helper()
	ctx := t.Context()

	ctr, err := postgres.Run(ctx, "postgres:18",
		postgres.WithDatabase("test"),
		postgres.WithUsername("test"),
		postgres.WithPassword("test"),
		postgres.BasicWaitStrategies(),
	)
	testcontainers.CleanupContainer(t, ctr) // didaftarkan pertama → dibersihkan terakhir
	if err != nil {
		t.Fatalf("menyalakan postgres: %v", err)
	}
	dsn, err := ctr.ConnectionString(ctx, "sslmode=disable")
	if err != nil {
		t.Fatal(err)
	}
	pool, err := pgxpool.New(ctx, dsn)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(pool.Close)

	// Migrate butuh *sql.DB; stdlib membungkus pool pgx sebagai database/sql.
	db := stdlib.OpenDBFromPool(pool)
	t.Cleanup(func() { _ = db.Close() })
	if _, err := jobqueue.Migrate(ctx, db); err != nil {
		t.Fatalf("migrasi: %v", err)
	}

	reg, err := jobqueue.NewRegistry(contracts.Jobs, "jobs") // sesuaikan dengan main.go
	if err != nil {
		t.Fatal(err)
	}
	h := newHub(pool, slog.New(slog.DiscardHandler))
	go h.run(ctx)
	select { // tunggu LISTEN aktif agar UPDATE di test tidak mendahuluinya
	case <-h.ready:
	case <-time.After(10 * time.Second):
		t.Fatal("hub tidak siap")
	}
	ts := httptest.NewServer(newServer(slog.New(slog.DiscardHandler), pool, reg, h))
	t.Cleanup(ts.Close)
	return ts, pool
}

func TestJobsAPI(t *testing.T) {
	ts, _ := newTestServer(t)
	jobsURL := ts.URL + "/api/hello/jobs"

	t.Run("POST menolak input buruk", func(t *testing.T) {
		tests := []struct {
			name string
			body string
			want int
		}{
			{"bukan JSON", "{bukan json", http.StatusBadRequest},
			{"melanggar skema", "[]", http.StatusUnprocessableEntity},
			{"terlalu besar", `"` + strings.Repeat("x", maxPayloadBytes) + `"`, http.StatusRequestEntityTooLarge},
		}
		for _, tc := range tests {
			t.Run(tc.name, func(t *testing.T) {
				if got := doReq(t, http.MethodPost, jobsURL, tc.body).status; got != tc.want {
					t.Fatalf("status = %d, mau %d", got, tc.want)
				}
			})
		}
	})

	t.Run("POST lalu GET", func(t *testing.T) {
		resp := doReq(t, http.MethodPost, jobsURL, validPayload)
		if resp.status != http.StatusAccepted {
			t.Fatalf("status = %d, mau 202", resp.status)
		}
		loc := resp.header.Get("Location")
		if loc == "" {
			t.Fatal("header Location kosong")
		}

		got := doReq(t, http.MethodGet, ts.URL+loc, validPayload)
		if got.status != http.StatusOK {
			t.Fatalf("GET status = %d, mau 200", got.status)
		}
		var j jobView
		if err := json.Unmarshal(got.body, &j); err != nil {
			t.Fatal(err)
		}
		if j.Status != "queued" || j.Kind != helloKind || j.Attempts != 0 {
			t.Fatalf("job tidak sesuai: %+v", j)
		}
	})

	t.Run("GET id tidak valid atau tidak ada", func(t *testing.T) {
		if got := doReq(t, http.MethodGet, jobsURL+"/bukan-uuid", validPayload).status; got != http.StatusBadRequest {
			t.Fatalf("status = %d, mau 400", got)
		}
		if got := doReq(t, http.MethodGet, jobsURL+"/00000000-0000-0000-0000-000000000000", validPayload).status; got != http.StatusNotFound {
			t.Fatalf("status = %d, mau 404", got)
		}
	})
}
