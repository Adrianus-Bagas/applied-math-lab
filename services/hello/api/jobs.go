package main

import (
	"context"
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgtype"

	"github.com/Adrianus-Bagas/applied-math-lab/packages/go/jobqueue"
)

const (
	helloKind          = "lab.stats.summary"
	helloSchemaVersion = 1
	maxPayloadBytes    = 64 << 10 // 64 KiB: jauh di atas payload hello yang wajar
)

// jobView adalah representasi job yang dikirim ke klien. Kolom internal antrean
// (worker_id, heartbeat_at, run_after) sengaja tidak diekspos.
type jobView struct {
	ID          string          `json:"id"`
	Kind        string          `json:"kind"`
	Status      string          `json:"status"`
	Attempts    int32           `json:"attempts"`
	MaxAttempts int32           `json:"max_attempts"`
	Progress    json.RawMessage `json:"progress"` // NULL di DB → null di JSON
	Result      json.RawMessage `json:"result"`
	Error       json.RawMessage `json:"error"`
	CreatedAt   time.Time       `json:"created_at"`
	StartedAt   *time.Time      `json:"started_at"`
	FinishedAt  *time.Time      `json:"finished_at"`
}

const selectJobSQL = `
SELECT id::text, kind, status, attempts, max_attempts, progress, result, error,
       created_at, started_at, finished_at
FROM lab_jobs
WHERE id = $1 AND kind = $2`

// getJob membaca satu job hello dari tabel, sumber kebenaran antrean.
// Mengembalikan pgx.ErrNoRows bila tidak ada. Dipakai ulang oleh SSE (langkah 3).
func getJob(ctx context.Context, db jobqueue.DBTX, id string) (jobView, error) {
	var j jobView
	err := db.QueryRow(ctx, selectJobSQL, id, helloKind).Scan(
		&j.ID, &j.Kind, &j.Status, &j.Attempts, &j.MaxAttempts,
		&j.Progress, &j.Result, &j.Error,
		&j.CreatedAt, &j.StartedAt, &j.FinishedAt,
	)
	return j, err
}

// validJobID memeriksa format UUID di Go agar input sampah tidak sampai ke DB.
func validJobID(s string) bool {
	var u pgtype.UUID
	return u.Scan(s) == nil
}

// handleCreateJob menerima payload lab.stats.summary dan memasukkannya ke antrean.
func (s *server) handleCreateJob(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	body, err := io.ReadAll(http.MaxBytesReader(w, r.Body, maxPayloadBytes))
	if err != nil {
		var tooLarge *http.MaxBytesError
		if errors.As(err, &tooLarge) {
			s.writeError(w, http.StatusRequestEntityTooLarge, "payload melebihi 64 KiB")
			return
		}
		s.writeError(w, http.StatusBadRequest, "gagal membaca body")
		return
	}
	if !json.Valid(body) {
		s.writeError(w, http.StatusBadRequest, "body bukan JSON yang valid")
		return
	}

	job := jobqueue.Job{Kind: helloKind, SchemaVersion: helloSchemaVersion, Payload: body}
	var id string
	// BeginFunc: commit bila closure mengembalikan nil, rollback bila error.
	// Baris dan NOTIFY dari Enqueue baru terlihat oleh worker setelah commit.
	err = pgx.BeginFunc(ctx, s.pool, func(tx pgx.Tx) error {
		newID, enqErr := jobqueue.Enqueue(ctx, tx, s.reg, job)
		id = newID
		return enqErr
	})
	switch {
	case errors.Is(err, jobqueue.ErrInvalidPayload):
		s.writeError(w, http.StatusUnprocessableEntity, err.Error())
		return
	case err != nil:
		s.logger.ErrorContext(ctx, "enqueue gagal", "err", err)
		s.writeError(w, http.StatusInternalServerError, "gagal memasukkan job")
		return
	}

	w.Header().Set("Location", "/api/hello/jobs/"+id)
	s.writeJSON(w, http.StatusAccepted, map[string]string{"id": id, "status": "queued"})
}

// handleGetJob mengembalikan status terkini satu job.
func (s *server) handleGetJob(w http.ResponseWriter, r *http.Request) {
	id := r.PathValue("id")
	if !validJobID(id) {
		s.writeError(w, http.StatusBadRequest, "id job bukan UUID")
		return
	}
	j, err := getJob(r.Context(), s.pool, id)
	switch {
	case errors.Is(err, pgx.ErrNoRows):
		s.writeError(w, http.StatusNotFound, "job tidak ditemukan")
		return
	case err != nil:
		s.logger.ErrorContext(r.Context(), "membaca job gagal", "err", err, "id", id)
		s.writeError(w, http.StatusInternalServerError, "gagal membaca job")
		return
	}
	s.writeJSON(w, http.StatusOK, j)
}
