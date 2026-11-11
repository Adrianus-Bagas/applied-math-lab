// Pembungkus modul WASM lab-numerics: memuat sekali, lalu memberi fungsi bertipe rapi.
import init, {
  meanVariance as wasmMeanVariance,
  sqrt2Convergents,
  type InitInput,
} from "../wasm/lab-numerics/lab_numerics";

/** Lokasi biner di folder public (ditaruh di sana oleh `just wasm`). */
const WASM_URL = "/wasm/lab_numerics_bg.wasm";

let ready: Promise<void> | null = null;

/**
 * Memuat dan menginisialisasi modul WASM. Aman dipanggil berkali-kali:
 * unduhan dan kompilasi hanya terjadi sekali per tab.
 * `source` bisa diganti dengan byte file (dipakai test di Node).
 */
export function loadLabNumerics(source: InitInput = WASM_URL): Promise<void> {
  ready ??= init({ module_or_path: source }).then(
    () => undefined,
    (err: unknown) => {
      ready = null; // gagal (mis. jaringan putus): izinkan percobaan ulang
      throw err;
    },
  );
  return ready;
}

export interface Convergent {
  /** Indeks konvergen, mulai dari 0. */
  n: number;
  p: bigint;
  q: bigint;
  /** |p/q − √2| dalam aritmetika float64. */
  error: number;
}

/** `count` konvergen pertama √2 (maksimum 50, batas i64 di Rust). */
export function convergents(count: number): Convergent[] {
  // Rust mengembalikan array rata [p0, q0, p1, q1, ...].
  const flat = sqrt2Convergents(count);
  const rows: Convergent[] = [];
  for (let i = 0; i < flat.length; i += 2) {
    const p = flat[i];
    const q = flat[i + 1];
    rows.push({
      n: i / 2,
      p,
      q,
      error: Math.abs(Number(p) / Number(q) - Math.SQRT2),
    });
  }
  return rows;
}

export interface MeanVariance {
  mean: number;
  variance: number;
}

/** Mean dan variansi (pembagi n − ddof) lewat Rust/WASM. */
export function meanVariance(xs: Float64Array, ddof = 0): MeanVariance | null {
  const out = wasmMeanVariance(xs, ddof);
  return out ? { mean: out[0], variance: out[1] } : null;
}

/** Algoritma Welford yang sama, ditulis di JS sebagai pembanding. */
export function meanVarianceJs(
  xs: Float64Array,
  ddof = 0,
): MeanVariance | null {
  const n = xs.length;
  if (n <= ddof) return null;
  let mean = 0;
  let m2 = 0;
  for (let i = 0; i < n; i++) {
    const delta = xs[i] - mean;
    mean += delta / (i + 1);
    m2 += delta * (xs[i] - mean);
  }
  return { mean, variance: m2 / (n - ddof) };
}
