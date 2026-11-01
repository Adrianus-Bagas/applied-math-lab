package main

import (
	"context"
	"encoding/json"
	"log/slog"
	"net/http"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"

	"github.com/Adrianus-Bagas/applied-math-lab/packages/go/jobqueue"
)

// server menampung dependensi yang dipakai bersama oleh semua handler.
type server struct {
	logger *slog.Logger
	pool   *pgxpool.Pool
	reg    *jobqueue.Registry
	mux    *http.ServeMux
	hub    *hub
}

// newServer membangun handler HTTP hello-api beserta seluruh rutenya.
func newServer(logger *slog.Logger, pool *pgxpool.Pool, reg *jobqueue.Registry, hub *hub) http.Handler {
	s := &server{logger: logger, pool: pool, reg: reg, mux: http.NewServeMux(), hub: hub}
	s.routes()
	return s.mux
}

func (s *server) routes() {
	s.mux.HandleFunc("GET /healthz", s.handleHealthz)
	s.mux.HandleFunc("GET /readyz", s.handleReadyz)
	s.mux.HandleFunc("POST /api/hello/jobs", s.handleCreateJob)
	s.mux.HandleFunc("GET /api/hello/jobs/{id}", s.handleGetJob)
	s.mux.HandleFunc("GET /api/hello/jobs/{id}/events", s.handleJobEvents)
}

// writeError menulis error dengan bentuk seragam {"error": "..."}.
func (s *server) writeError(w http.ResponseWriter, status int, msg string) {
	s.writeJSON(w, status, map[string]string{"error": msg})
}

// handleHealthz adalah liveness: hanya menyatakan proses hidup, tanpa
// menyentuh database, agar gangguan DB tidak memicu restart berantai.
func (s *server) handleHealthz(w http.ResponseWriter, _ *http.Request) {
	s.writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

// handleReadyz adalah readiness: siap melayani hanya bila database terjangkau.
func (s *server) handleReadyz(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 2*time.Second)
	defer cancel()
	if err := s.pool.Ping(ctx); err != nil {
		s.logger.WarnContext(ctx, "readyz: database tidak siap", "err", err)
		s.writeJSON(w, http.StatusServiceUnavailable, map[string]string{"status": "unavailable"})
		return
	}
	s.writeJSON(w, http.StatusOK, map[string]string{"status": "ready"})
}

// writeJSON menulis v sebagai JSON. Status dan header sudah terkirim sebelum
// body, jadi kegagalan encode hanya bisa dicatat, tidak bisa diubah jadi 500.
func (s *server) writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(v); err != nil {
		s.logger.Error("gagal menulis respons JSON", "err", err)
	}
}
