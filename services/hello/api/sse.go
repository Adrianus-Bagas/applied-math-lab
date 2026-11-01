package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"time"

	"github.com/jackc/pgx/v5"
)

const (
	sseHeartbeat    = 15 * time.Second // ping + polling cadangan
	sseWriteTimeout = 10 * time.Second // tenggat per event
)

// terminal melaporkan apakah job sudah tidak akan berubah lagi.
func (j jobView) terminal() bool {
	switch j.Status {
	case "succeeded", "failed", "cancelled":
		return true
	}
	return false
}

// sseStream membungkus satu koneksi SSE.
type sseStream struct {
	w    http.ResponseWriter
	rc   *http.ResponseController
	last []byte // snapshot terakhir yang terkirim, untuk menghindari duplikat
}

// write menulis potongan mentah lalu flush. Tenggat tulis dipasang ulang per
// event agar klien yang macet tidak menahan goroutine ini selamanya.
func (st *sseStream) write(chunk string) error {
	if err := st.rc.SetWriteDeadline(time.Now().Add(sseWriteTimeout)); err != nil {
		return err
	}
	if _, err := io.WriteString(st.w, chunk); err != nil {
		return err
	}
	return st.rc.Flush()
}

// sendJob mengirim snapshot job bila berbeda dari yang terakhir; sent=false
// berarti tidak ada perubahan. json.Marshal tidak pernah menghasilkan newline
// mentah, jadi satu baris "data:" selalu cukup.
func (st *sseStream) sendJob(j jobView) (sent bool, err error) {
	data, err := json.Marshal(j)
	if err != nil {
		return false, err
	}
	if bytes.Equal(data, st.last) {
		return false, nil
	}
	st.last = data
	return true, st.write("event: job\ndata: " + string(data) + "\n\n")
}

// handleJobEvents mengalirkan snapshot job lewat Server-Sent Events sampai
// job mencapai status terminal, klien pergi, atau server dimatikan.
func (s *server) handleJobEvents(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	id := r.PathValue("id")
	if !validJobID(id) {
		s.writeError(w, http.StatusBadRequest, "id job bukan UUID")
		return
	}

	// Berlangganan SEBELUM membaca snapshot awal: urutan sebaliknya membuka
	// celah di mana perubahan di antara keduanya terlewat.
	updates, unsubscribe := s.hub.subscribe(id)
	defer unsubscribe()

	j, err := getJob(ctx, s.pool, id)
	switch {
	case errors.Is(err, pgx.ErrNoRows):
		s.writeError(w, http.StatusNotFound, "job tidak ditemukan")
		return
	case err != nil:
		s.logger.ErrorContext(ctx, "membaca job gagal", "err", err, "id", id)
		s.writeError(w, http.StatusInternalServerError, "gagal membaca job")
		return
	}

	rc := http.NewResponseController(w)
	// Stream bisa hidup lebih lama dari ReadTimeout server; tanpa ini koneksi
	// dapat diputus di tengah jalan.
	if err := rc.SetReadDeadline(time.Time{}); err != nil {
		s.logger.ErrorContext(ctx, "tidak bisa menghapus deadline baca", "err", err)
		s.writeError(w, http.StatusInternalServerError, "streaming tidak didukung")
		return
	}
	hdr := w.Header()
	hdr.Set("Content-Type", "text/event-stream")
	hdr.Set("Cache-Control", "no-cache")
	hdr.Set("X-Accel-Buffering", "no") // minta proxy tidak mem-buffer stream
	w.WriteHeader(http.StatusOK)

	st := &sseStream{w: w, rc: rc}
	// retry: jeda reconnect EventSource (ms) bila koneksi putus.
	if err := st.write("retry: 3000\n\n"); err != nil {
		return
	}
	if _, err := st.sendJob(j); err != nil || j.terminal() {
		return
	}

	ticker := time.NewTicker(sseHeartbeat)
	defer ticker.Stop()
	for {
		tick := false
		select {
		case <-ctx.Done(): // klien menutup koneksi
			return
		case <-s.hub.Done(): // server dimatikan
			return
		case <-updates:
		case <-ticker.C:
			tick = true // polling cadangan bila NOTIFY terlewat
		}

		j, err := getJob(ctx, s.pool, id)
		if err != nil {
			if ctx.Err() == nil {
				s.logger.WarnContext(ctx, "SSE: membaca ulang job gagal", "err", err, "id", id)
			}
			return // klien akan reconnect dan mendapat snapshot baru
		}
		sent, err := st.sendJob(j)
		if err == nil && !sent && tick {
			// Komentar SSE diabaikan EventSource; menjaga koneksi diam tetap hidup.
			err = st.write(": ping\n\n")
		}
		if err != nil || j.terminal() {
			return
		}
	}
}
