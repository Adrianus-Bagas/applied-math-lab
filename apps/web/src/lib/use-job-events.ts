"use client";

import { useEffect, useState } from "react";

import { isTerminal, type Job } from "./hello-api";

export type Connection = "connecting" | "open" | "reconnecting" | "closed";

/**
 * Berlangganan snapshot job lewat SSE. Pasang komponen pemakainya dengan
 * `key={id}` agar state ter-reset saat id berganti.
 *
 * Setiap event berisi status lengkap (snapshot), jadi reconnect otomatis
 * EventSource langsung mendapat status terkini tanpa replay.
 */
export function useJobEvents(id: string): {
  job: Job | null;
  connection: Connection;
} {
  const [job, setJob] = useState<Job | null>(null);
  const [connection, setConnection] = useState<Connection>("connecting");

  useEffect(() => {
    const es = new EventSource(
      `/api/hello/jobs/${encodeURIComponent(id)}/events`,
    );
    es.onopen = () => setConnection("open");
    es.addEventListener("job", (e: MessageEvent<string>) => {
      const next = JSON.parse(e.data) as Job;
      setJob(next);
      // Wajib: server menutup stream setelah status terminal. Tanpa close(),
      // EventSource akan reconnect tanpa henti setiap 3 detik (retry dari server).
      if (isTerminal(next.status)) {
        es.close();
        setConnection("closed");
      }
    });
    // readyState CLOSED = gagal permanen (mis. 404/400); selain itu browser sedang reconnect.
    es.onerror = () =>
      setConnection(
        es.readyState === EventSource.CLOSED ? "closed" : "reconnecting",
      );
    return () => es.close();
  }, [id]);

  return { job, connection };
}
