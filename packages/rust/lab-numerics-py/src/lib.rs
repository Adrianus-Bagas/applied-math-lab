//! Binding PyO3 untuk `lab-numerics`. Hanya konversi tipe dan GIL; tanpa matematika.

use std::borrow::Cow;

use numpy::PyArrayLike1;
use pyo3::prelude::*;

/// Mean dan variansi (pembagi n − ddof) dengan algoritma Welford.
/// Mengembalikan None bila len(xs) <= ddof.
///
/// Array float64 contiguous dibaca tanpa salin dan GIL dilepas selama
/// perhitungan: array tidak boleh diubah thread lain selama panggilan.
#[pyfunction]
#[pyo3(signature = (xs, ddof = 0))]
fn mean_variance<'py>(
    py: Python<'py>,
    xs: PyArrayLike1<'py, f64>,
    ddof: u64,
) -> Option<(f64, f64)> {
    let data: Cow<'_, [f64]> = match xs.as_slice() {
        Ok(slice) => Cow::Borrowed(slice),
        // View berstride (mis. arr[::2]) bukan slice: salin sekali.
        Err(_) => Cow::Owned(xs.as_array().iter().copied().collect()),
    };
    py.detach(|| lab_numerics::stats::mean_variance(&data, ddof))
}

#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(mean_variance, m)?)?;
    Ok(())
}
