// Kontrak hello-api, ditulis tangan. OpenAPI + openapi-typescript menyusul
// di API domain pertama; bentuk ini harus sama dengan jobView di Go.

export type JobStatus =
  "queued" | "running" | "succeeded" | "failed" | "cancelled";

/** Error dari hello-api; membawa status HTTP agar UI bisa membedakan penyebabnya. */
export class HelloApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "HelloApiError";
    this.status = status;
  }
}

export interface Job {
  id: string;
  kind: string;
  status: JobStatus;
  attempts: number;
  max_attempts: number;
  progress: unknown;
  result: unknown;
  error: unknown;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
}

const TERMINAL: ReadonlySet<JobStatus> = new Set([
  "succeeded",
  "failed",
  "cancelled",
]);

/** Job terminal tidak akan berubah lagi; stream SSE ditutup server. */
export function isTerminal(status: JobStatus): boolean {
  return TERMINAL.has(status);
}

/** Mengambil tahap dari progress hello; null bila bentuknya tidak dikenal. */
export function progressStage(progress: unknown): string | null {
  if (
    typeof progress === "object" &&
    progress !== null &&
    "tahap" in progress
  ) {
    const { tahap } = progress as { tahap: unknown };
    return typeof tahap === "string" ? tahap : null;
  }
  return null;
}

export function renderResult(result: unknown): string | null {
  if (
    typeof result === "object" &&
    result !== null &&
    "mean" in result &&
    "variance" in result
  ) {
    const { mean, variance } = result as { mean: unknown; variance: unknown };
    return typeof mean === "number" && typeof variance === "number"
      ? `Mean: ${mean}, Variance: ${variance}`
      : "";
  }
  return null;
}

/** Mengajukan job lab.stats.summary; payload divalidasi skema di Go (422 bila melanggar). */
export async function createHelloJob(
  payload: unknown,
): Promise<{ id: string }> {
  const res = await fetch("/api/hello/jobs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  // Body belum tentu JSON: saat Go mati, proxy Next.js membalas 502 berupa teks.
  // Membaca teks dulu mencegah res.json() melempar SyntaxError yang menyesatkan.
  const text = await res.text();
  let body: unknown = null;
  try {
    body = JSON.parse(text);
  } catch {
    // bukan JSON; pesan cadangan dipakai di bawah
  }

  if (!res.ok) {
    const msg =
      typeof body === "object" &&
      body !== null &&
      "error" in body &&
      typeof body.error === "string"
        ? body.error
        : `HTTP ${res.status}`;
    throw new HelloApiError(res.status, msg);
  }
  return body as { id: string };
}
