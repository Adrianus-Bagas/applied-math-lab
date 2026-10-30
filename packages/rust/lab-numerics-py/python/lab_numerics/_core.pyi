from collections.abc import Sequence

import numpy as np
import numpy.typing as npt

def mean_variance(
    xs: Sequence[float] | npt.NDArray[np.float64], ddof: int = 0
) -> tuple[float, float] | None:
    """Mean dan variansi (pembagi n - ddof) dengan algoritma Welford.

    Array float64 contiguous dibaca tanpa salin dan GIL dilepas selama perhitungan:
    array tidak boleh diubah thread lain selama panggilan.
    """
