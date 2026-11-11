import { readFile } from "node:fs/promises";

import { beforeAll, describe, expect, it } from "vitest";

import {
  convergents,
  loadLabNumerics,
  meanVariance,
  meanVarianceJs,
} from "./lab-numerics";

beforeAll(async () => {
  const file = new URL(
    "../../public/wasm/lab_numerics_bg.wasm",
    import.meta.url,
  );
  await loadLabNumerics(new Uint8Array(await readFile(file)));
});

describe("convergents", () => {
  it("memberi konvergen √2 pertama", () => {
    const rows = convergents(5);
    expect(rows.map((r) => `${r.p}/${r.q}`)).toEqual([
      "1/1",
      "3/2",
      "7/5",
      "17/12",
      "41/29",
    ]);
  });

  it("berhenti di 50 konvergen (batas i64)", () => {
    expect(convergents(1000)).toHaveLength(50);
  });

  it("memenuhi identitas Pell p² − 2q² = ±1 secara eksak", () => {
    for (const { n, p, q } of convergents(50)) {
      const sisa = p * p - BigInt(2) * q * q;
      expect(sisa).toBe(BigInt(n % 2 === 0 ? -1 : 1));
    }
  });
});

describe("meanVariance", () => {
  it("cocok dengan hitung tangan", () => {
    const xs = new Float64Array([1, 2, 3, 4]);
    expect(meanVariance(xs, 0)).toEqual({ mean: 2.5, variance: 1.25 });
  });

  it("mengembalikan null bila data tidak cukup", () => {
    expect(meanVariance(new Float64Array([]), 0)).toBeNull();
    expect(meanVariance(new Float64Array([1]), 1)).toBeNull();
  });

  it("sepakat dengan versi JS dalam toleransi pembulatan", () => {
    // 1000 nilai deterministik di [0, 1).
    const xs = Float64Array.from(
      { length: 1000 },
      (_, i) => ((i * 37) % 101) / 101,
    );
    const wasm = meanVariance(xs, 1);
    const js = meanVarianceJs(xs, 1);
    // Bound galat Welford ~ c·n·u = c·1000·1,1e-16 ≈ 1e-13 untuk data di [0, 1);
    // 1e-12 memberi ruang satu orde.
    const tol = 1e-12;
    expect(Math.abs(wasm!.mean - js!.mean)).toBeLessThanOrEqual(tol);
    expect(Math.abs(wasm!.variance - js!.variance)).toBeLessThanOrEqual(tol);
  });
});
