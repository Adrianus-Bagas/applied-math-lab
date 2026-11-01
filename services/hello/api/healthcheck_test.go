package main

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestHealthcheckMain(t *testing.T) {
	tests := []struct {
		name   string
		status int
		want   int
	}{
		{"sehat", http.StatusOK, 0},
		{"tidak sehat", http.StatusServiceUnavailable, 1},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				if r.URL.Path != "/healthz" {
					http.NotFound(w, r)
					return
				}
				w.WriteHeader(tt.status)
			}))
			defer srv.Close()

			// srv.URL berbentuk http://127.0.0.1:PORT; ambil host:port saja.
			addr := strings.TrimPrefix(srv.URL, "http://")
			getenv := func(k string) string {
				if k == "HELLO_API_ADDR" {
					return addr
				}
				return ""
			}
			if got := healthcheckMain(getenv); got != tt.want {
				t.Fatalf("healthcheckMain() = %d, ingin %d", got, tt.want)
			}
		})
	}
}
