// Command hello-api adalah Go API walking skeleton lab: menerima pengajuan job
// lab.stats.summary, menyimpannya ke antrean PostgreSQL, dan melaporkan
// progresnya ke browser lewat Server-Sent Events.
package main

import (
	"context"
	"errors"
	"fmt"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"

	"github.com/Adrianus-Bagas/applied-math-lab/contracts"
	"github.com/Adrianus-Bagas/applied-math-lab/packages/go/jobqueue"
)

func main() {
	// ctx dibatalkan saat proses menerima Ctrl-C (SIGINT) atau SIGTERM dari Docker.
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	err := run(ctx, os.Getenv)
	// stop dipanggil eksplisit, bukan lewat defer: os.Exit melewati semua defer.
	stop()
	if err != nil {
		fmt.Fprintf(os.Stderr, "hello-api: %v\n", err)
		os.Exit(1)
	}
}

// run merakit dependensi, menjalankan server HTTP, dan mematikannya dengan rapi
// saat ctx dibatalkan. getenv disuntikkan agar konfigurasi mudah diganti di test.
func run(ctx context.Context, getenv func(string) string) error {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))

	dbURL := getenv("DATABASE_URL")
	if dbURL == "" {
		return errors.New("DATABASE_URL wajib diisi")
	}
	addr := getenv("HELLO_API_ADDR")
	if addr == "" {
		addr = "127.0.0.1:8080"
	}

	// pgxpool.New belum membuka koneksi; koneksi dibuat saat pertama dipakai.
	pool, err := pgxpool.New(ctx, dbURL)
	if err != nil {
		return fmt.Errorf("membuat pool database: %w", err)
	}
	defer pool.Close()

	reg, err := jobqueue.NewRegistry(contracts.Jobs, "jobs")
	if err != nil {
		return fmt.Errorf("memuat skema job: %w", err)
	}

	// Hub hidup selama ctx. Saat sinyal datang, hub berhenti dan semua stream SSE
	// ikut selesai, sehingga srv.Shutdown tidak tertahan sampai timeout.
	h := newHub(pool, logger)
	go h.run(ctx)

	srv := &http.Server{
		Addr:              addr,
		Handler:           newServer(logger, pool, reg, h),
		ReadHeaderTimeout: 5 * time.Second, // lindungi dari klien lambat (slowloris)
		ReadTimeout:       10 * time.Second,
		WriteTimeout:      15 * time.Second, // handler SSE memperpanjangnya sendiri (langkah 3)
		IdleTimeout:       60 * time.Second,
	}

	// ListenAndServe memblokir, jadi dijalankan di goroutine. Error dikirim
	// lewat channel ber-buffer 1 supaya goroutine tidak macet bila tak dibaca.
	errCh := make(chan error, 1)
	go func() {
		logger.Info("hello-api mendengarkan", "addr", addr)
		if err := srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			errCh <- err
		}
	}()

	select {
	case err := <-errCh:
		return fmt.Errorf("server berhenti: %w", err)
	case <-ctx.Done():
	}

	logger.Info("sinyal diterima, mematikan server")
	// ctx sudah batal, jadi tenggat shutdown memakai context baru.
	shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	if err := srv.Shutdown(shutdownCtx); err != nil {
		return fmt.Errorf("shutdown: %w", err)
	}
	return nil
}
