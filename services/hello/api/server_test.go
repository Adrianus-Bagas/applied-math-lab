package main

import (
	"log/slog"
	"net/http"
	"net/http/httptest"
	"testing"
)

// TestHealthz memeriksa liveness tanpa database (pool nil sengaja dipakai:
// healthz tidak boleh menyentuh DB).
func TestHealthz(t *testing.T) {
	h := newServer(slog.New(slog.DiscardHandler), nil, nil, nil)

	tests := []struct {
		name   string
		method string
		want   int
	}{
		{"GET berhasil", http.MethodGet, http.StatusOK},
		{"POST ditolak", http.MethodPost, http.StatusMethodNotAllowed},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			rec := httptest.NewRecorder()
			h.ServeHTTP(rec, httptest.NewRequest(tc.method, "/healthz", nil))
			if rec.Code != tc.want {
				t.Fatalf("status = %d, mau %d", rec.Code, tc.want)
			}
		})
	}
}
