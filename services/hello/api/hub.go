package main

import (
	"context"
	"fmt"
	"log/slog"
	"sync"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"

	"github.com/Adrianus-Bagas/applied-math-lab/packages/go/jobqueue"
)

// hub mendengarkan kanal progres lewat SATU koneksi khusus (di luar pool) dan
// meneruskan sinyal "ada perubahan" ke handler SSE yang berlangganan id job.
// Satu koneksi untuk semua klien menjaga pemakaian max_connections tetap kecil.
type hub struct {
	connConfig *pgx.ConnConfig
	logger     *slog.Logger
	ready      chan struct{} // ditutup setelah LISTEN pertama berhasil
	readyOnce  sync.Once
	done       chan struct{} // ditutup saat run berakhir (server dimatikan)

	mu   sync.Mutex
	subs map[string]map[chan struct{}]struct{} // id job → himpunan channel pelanggan
}

func newHub(pool *pgxpool.Pool, logger *slog.Logger) *hub {
	return &hub{
		connConfig: pool.Config().ConnConfig.Copy(),
		logger:     logger,
		ready:      make(chan struct{}),
		done:       make(chan struct{}),
		subs:       make(map[string]map[chan struct{}]struct{}),
	}
}

// Done ditutup saat hub berhenti; handler SSE memakainya untuk ikut selesai.
func (h *hub) Done() <-chan struct{} { return h.done }

// run menjaga listener tetap hidup sampai ctx dibatalkan, menyambung ulang bila putus.
func (h *hub) run(ctx context.Context) {
	defer close(h.done)
	for {
		err := h.listen(ctx)
		if ctx.Err() != nil {
			return
		}
		h.logger.WarnContext(ctx, "listener SSE putus, menyambung ulang", "err", err)
		select {
		case <-ctx.Done():
			return
		case <-time.After(time.Second):
		}
	}
}

func (h *hub) listen(ctx context.Context) error {
	conn, err := pgx.ConnectConfig(ctx, h.connConfig)
	if err != nil {
		return fmt.Errorf("koneksi listener: %w", err)
	}
	defer func() { _ = conn.Close(context.Background()) }()

	listenSQL := "LISTEN " + pgx.Identifier{jobqueue.ProgressChannel}.Sanitize()
	if _, err := conn.Exec(ctx, listenSQL); err != nil {
		return fmt.Errorf("LISTEN: %w", err)
	}
	h.readyOnce.Do(func() { close(h.ready) })

	// Notifikasi selama listener mati (atau sebelum LISTEN pertama) hilang,
	// jadi semua pelanggan diminta membaca ulang tabel. NOTIFY petunjuk, tabel kebenaran.
	h.publishAll()

	for {
		n, err := conn.WaitForNotification(ctx)
		if err != nil {
			return err
		}
		h.publish(n.Payload)
	}
}

// subscribe mendaftarkan pelanggan untuk satu id job. Fungsi yang dikembalikan
// wajib dipanggil (biasanya lewat defer) untuk berhenti berlangganan.
func (h *hub) subscribe(id string) (<-chan struct{}, func()) {
	ch := make(chan struct{}, 1)
	h.mu.Lock()
	if h.subs[id] == nil {
		h.subs[id] = make(map[chan struct{}]struct{})
	}
	h.subs[id][ch] = struct{}{}
	h.mu.Unlock()

	return ch, func() {
		h.mu.Lock()
		delete(h.subs[id], ch)
		if len(h.subs[id]) == 0 {
			delete(h.subs, id)
		}
		h.mu.Unlock()
	}
}

func (h *hub) publish(id string) {
	h.mu.Lock()
	defer h.mu.Unlock()
	for ch := range h.subs[id] {
		poke(ch)
	}
}

func (h *hub) publishAll() {
	h.mu.Lock()
	defer h.mu.Unlock()
	for _, set := range h.subs {
		for ch := range set {
			poke(ch)
		}
	}
}

// poke mengirim tanpa memblokir. Bila buffer (kapasitas 1) sudah terisi,
// pelanggan memang belum membaca ulang; sinyal baru boleh dibuang karena
// pembacaan berikutnya akan mendapat snapshot terbaru.
func poke(ch chan struct{}) {
	select {
	case ch <- struct{}{}:
	default:
	}
}
