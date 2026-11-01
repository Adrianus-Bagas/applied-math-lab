package main

import (
	"context"
	"fmt"
	"net"
	"net/http"
	"os"
	"time"
)

// healthcheckMain dijalankan saat binary dipanggil sebagai `hello-api healthcheck`.
// Image distroless tidak punya shell maupun curl, jadi binary memeriksa
// endpoint /healthz miliknya sendiri. Nilai kembali adalah exit code:
// 0 = sehat, 1 = tidak sehat (konvensi HEALTHCHECK Docker).
func healthcheckMain(getenv func(string) string) int {
	addr := getenv("HELLO_API_ADDR")
	if addr == "" {
		addr = "127.0.0.1:8080" // samakan dengan default di run()
	}
	host, port, err := net.SplitHostPort(addr)
	if err != nil {
		fmt.Fprintln(os.Stderr, "healthcheck: alamat tidak valid:", err)
		return 1
	}
	// Server yang mendengarkan di semua antarmuka dihubungi lewat loopback.
	if host == "" || host == "0.0.0.0" || host == "::" {
		host = "127.0.0.1"
	}

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	url := "http://" + net.JoinHostPort(host, port) + "/healthz"
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		fmt.Fprintln(os.Stderr, "healthcheck:", err)
		return 1
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		fmt.Fprintln(os.Stderr, "healthcheck:", err)
		return 1
	}
	defer func() { _ = resp.Body.Close() }()
	if resp.StatusCode != http.StatusOK {
		fmt.Fprintln(os.Stderr, "healthcheck: status", resp.StatusCode)
		return 1
	}
	return 0
}
