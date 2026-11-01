import { afterEach, describe, expect, it, vi } from "vitest";

import {
  createHelloJob,
  HelloApiError,
  isTerminal,
  progressStage,
} from "./hello-api";

describe("createHelloJob", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("melempar HelloApiError berisi pesan server untuk 422", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(
            JSON.stringify({ error: "jobqueue: invalid payload: n wajib" }),
            { status: 422 },
          ),
      ),
    );
    const err: unknown = await createHelloJob([]).catch((e: unknown) => e);
    expect(err).toBeInstanceOf(HelloApiError);
    expect(err).toMatchObject({
      status: 422,
      message: "jobqueue: invalid payload: n wajib",
    });
  });

  it("memberi pesan cadangan saat body bukan JSON (502 dari proxy)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("Bad Gateway", { status: 502 })),
    );
    await expect(createHelloJob({})).rejects.toMatchObject({
      status: 502,
      message: "HTTP 502",
    });
  });
});

describe("createHelloJob", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("melempar HelloApiError berisi pesan server untuk 422", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(
            JSON.stringify({ error: "jobqueue: invalid payload: n wajib" }),
            { status: 422 },
          ),
      ),
    );
    const err: unknown = await createHelloJob([]).catch((e: unknown) => e);
    expect(err).toBeInstanceOf(HelloApiError);
    expect(err).toMatchObject({
      status: 422,
      message: "jobqueue: invalid payload: n wajib",
    });
  });

  it("memberi pesan cadangan saat body bukan JSON (502 dari proxy)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("Bad Gateway", { status: 502 })),
    );
    await expect(createHelloJob({})).rejects.toMatchObject({
      status: 502,
      message: "HTTP 502",
    });
  });
});

describe("progressStage", () => {
  it.each([
    { input: { tahap: "hitung" }, want: "hitung" },
    { input: { tahap: "bangkitkan", n: 1000000 }, want: "bangkitkan" },
  ])("mengambil tahap dari $input", ({ input, want }) => {
    expect(progressStage(input)).toBe(want);
  });

  it.each([
    { name: "null (progres belum ada)", input: null },
    { name: "objek tanpa tahap", input: { n: 5 } },
    { name: "tahap bukan string", input: { tahap: 3 } },
    { name: "bukan objek", input: "hitung" },
    { name: "array", input: ["tahap"] },
  ])("null untuk $name", ({ input }) => {
    expect(progressStage(input)).toBeNull();
  });
});

describe("isTerminal", () => {
  it.each(["succeeded", "failed", "cancelled"] as const)("%s terminal", (s) => {
    expect(isTerminal(s)).toBe(true);
  });
  it.each(["queued", "running"] as const)("%s belum terminal", (s) => {
    expect(isTerminal(s)).toBe(false);
  });
});
