"""Handler job contoh lab (walking skeleton L0.4 sampai L0.8)."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

import numpy as np
from lab_numerics import mean_variance
from lab_worker.worker import Handler, JobContext, PermanentError

KIND_STATS_SUMMARY = "lab.stats.summary"


def stats_summary(ctx: JobContext) -> Mapping[str, Any]:
    """Bangkitkan n sampel N(0,1) dari seed, lalu hitung mean dan variansi sampel di Rust."""
    # JSON Schema "integer" juga menerima 1000.0 (bagian pecahan nol), dan JSONB
    # mengembalikannya sebagai float; paksa ke int sebelum dipakai NumPy.
    n = int(ctx.payload["n"])
    seed = int(ctx.payload["seed"])

    ctx.progress({"tahap": "bangkitkan", "n": n})
    xs = np.random.default_rng(seed).standard_normal(n)

    ctx.progress({"tahap": "hitung"})
    stats = mean_variance(xs, ddof=1)
    if stats is None:
        raise PermanentError(f"variansi sampel tidak terdefinisi untuk n={n} (butuh n >= 2)")
    mean, variance = stats

    # JSON tidak punya NaN/Infinity: json.dumps Python menulis "NaN" yang ditolak Postgres.
    if not (math.isfinite(mean) and math.isfinite(variance)):
        raise PermanentError("hasil tidak hingga")
    return {"n": n, "seed": seed, "ddof": 1, "mean": mean, "variance": variance}


HANDLERS: Mapping[str, Handler] = {KIND_STATS_SUMMARY: stats_summary}
