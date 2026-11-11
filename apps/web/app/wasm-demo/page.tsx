"use client";

import { useEffect, useMemo, useState } from "react";

import {
  convergents,
  loadLabNumerics,
  meanVariance,
  meanVarianceJs,
  type MeanVariance,
} from "@/src/lib/lab-numerics";

type Status = "loading" | "ready" | "error";

interface Bench {
  wasmMs: number;
  jsMs: number;
  wasm: MeanVariance | null;
  js: MeanVariance | null;
}

const BENCH_SIZE = 1_000_000;

export default function WasmDemoPage() {
  const [status, setStatus] = useState<Status>("loading");
  const [message, setMessage] = useState("");
  const [count, setCount] = useState(10);
  const [bench, setBench] = useState<Bench | null>(null);

  // Unduh dan inisialisasi modul WASM sekali saat halaman dibuka.
  useEffect(() => {
    let active = true;
    loadLabNumerics().then(
      () => {
        if (active) setStatus("ready");
      },
      (err: unknown) => {
        if (!active) return;
        setMessage(err instanceof Error ? err.message : String(err));
        setStatus("error");
      },
    );
    return () => {
      active = false;
    };
  }, []);

  // Dihitung ulang oleh Rust di browser setiap slider digeser.
  const rows = useMemo(
    () => (status === "ready" ? convergents(count) : []),
    [status, count],
  );

  const runBench = () => {
    const xs = Float64Array.from({ length: BENCH_SIZE }, () => Math.random());
    const t0 = performance.now();
    const wasm = meanVariance(xs, 1);
    const t1 = performance.now();
    const js = meanVarianceJs(xs, 1);
    const t2 = performance.now();
    setBench({ wasmMs: t1 - t0, jsMs: t2 - t1, wasm, js });
  };

  if (status === "loading") return <p>Memuat modul WASM…</p>;
  if (status === "error") return <p>Gagal memuat modul WASM: {message}</p>;

  return (
    <main>
      <h1>Demo Rust → WASM</h1>
      <p>
        Semua angka di halaman ini dihitung crate <code>lab-numerics</code> yang
        berjalan di browser, tanpa permintaan ke server.
      </p>

      <h2>Konvergen pecahan berlanjut √2</h2>
      <label>
        Jumlah konvergen: {count}{" "}
        <input
          type="range"
          min={1}
          max={50}
          value={count}
          onChange={(e) => setCount(Number(e.target.value))}
        />
      </label>
      <table>
        <thead>
          <tr>
            <th>n</th>
            <th>p</th>
            <th>q</th>
            <th>|p/q − √2|</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.n}>
              <td>{r.n}</td>
              <td>{r.p.toString()}</td>
              <td>{r.q.toString()}</td>
              <td>{r.error.toExponential(3)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>
        Mean dan variansi {BENCH_SIZE.toLocaleString("id-ID")} bilangan acak
      </h2>
      <button onClick={runBench}>Jalankan</button>
      {bench && (
        <ul>
          <li>
            WASM: {bench.wasmMs.toFixed(1)} ms (mean {bench.wasm?.mean},
            variansi {bench.wasm?.variance})
          </li>
          <li>
            JS: {bench.jsMs.toFixed(1)} ms (mean {bench.js?.mean}, variansi{" "}
            {bench.js?.variance})
          </li>
        </ul>
      )}
    </main>
  );
}
