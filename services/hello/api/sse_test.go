package main

import (
	"bufio"
	"encoding/json"
	"io"
	"net/http"
	"strings"
	"testing"
	"time"
)

// readEvents mengurai baris "data:" dari stream SSE; channel ditutup saat stream berakhir.
func readEvents(body io.Reader, out chan<- jobView) {
	defer close(out)
	sc := bufio.NewScanner(body)
	for sc.Scan() {
		data, ok := strings.CutPrefix(sc.Text(), "data: ")
		if !ok {
			continue
		}
		var j jobView
		if json.Unmarshal([]byte(data), &j) == nil {
			out <- j
		}
	}
}

func TestJobEventsSSE(t *testing.T) {
	ts, pool := newTestServer(t)
	ctx := t.Context()

	created := doReq(t, http.MethodPost, ts.URL+"/api/hello/jobs", validPayload)
	var c struct{ ID string }
	if err := json.Unmarshal(created.body, &c); err != nil {
		t.Fatal(err)
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, ts.URL+"/api/hello/jobs/"+c.ID+"/events", nil)
	if err != nil {
		t.Fatal(err)
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatal(err)
	}
	defer func() { _ = resp.Body.Close() }()
	if ct := resp.Header.Get("Content-Type"); ct != "text/event-stream" {
		t.Fatalf("Content-Type = %q", ct)
	}

	events := make(chan jobView, 16)
	go readEvents(resp.Body, events)
	next := func() (jobView, bool) {
		t.Helper()
		select {
		case j, ok := <-events:
			return j, ok
		case <-time.After(5 * time.Second): // jauh di bawah heartbeat 15 s: harus dari NOTIFY
			t.Fatal("event tidak datang")
			return jobView{}, false
		}
	}
	exec := func(sql string) {
		t.Helper()
		if _, err := pool.Exec(ctx, sql, c.ID); err != nil {
			t.Fatal(err)
		}
	}

	if j, _ := next(); j.Status != "queued" {
		t.Fatalf("snapshot awal = %q, mau queued", j.Status)
	}
	// Setiap UPDATE ditunggu event-nya dulu agar coalescing tidak menggabungkannya.
	exec(`UPDATE lab_jobs SET status='running', attempts=1, worker_id='test', heartbeat_at=now() WHERE id=$1`)
	if j, _ := next(); j.Status != "running" {
		t.Fatalf("status = %q, mau running", j.Status)
	}
	exec(`UPDATE lab_jobs SET progress='{"tahap":"hitung"}' WHERE id=$1`)
	if j, _ := next(); !strings.Contains(string(j.Progress), "hitung") {
		t.Fatalf("progress = %s", j.Progress)
	}
	exec(`UPDATE lab_jobs SET heartbeat_at=now() WHERE id=$1`) // tidak boleh memicu event
	exec(`UPDATE lab_jobs SET status='succeeded', result='{}', finished_at=now() WHERE id=$1`)
	if j, _ := next(); j.Status != "succeeded" {
		t.Fatalf("status = %q, mau succeeded (heartbeat tidak boleh menghasilkan event)", j.Status)
	}
	if _, ok := next(); ok {
		t.Fatal("stream seharusnya ditutup setelah status terminal")
	}
}
