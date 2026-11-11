//! Binding WebAssembly untuk `lab-numerics`. Hanya konversi tipe; tanpa matematika.

use wasm_bindgen::prelude::*;

/// `n` konvergen pertama √2, diratakan menjadi [p0, q0, p1, q1, ...].
///
/// Di JavaScript hasilnya `BigInt64Array`: p dan q bisa melampaui 2^53,
/// batas bilangan bulat yang masih eksak di tipe `number`.
/// Barisan berhenti sendiri di 50 konvergen (batas i64).
#[wasm_bindgen(js_name = sqrt2Convergents)]
pub fn sqrt2_convergents(n: usize) -> Vec<i64> {
    lab_numerics::cfrac::sqrt2_convergents()
        .take(n)
        .flat_map(|(p, q)| [p, q])
        .collect()
}

/// Mean dan variansi (pembagi n − ddof) dengan algoritma Welford.
///
/// Mengembalikan [mean, variansi], atau `undefined` bila panjang data <= ddof.
/// `Float64Array` dari JS disalin sekali ke memori WASM sebelum dihitung.
#[wasm_bindgen(js_name = meanVariance)]
pub fn mean_variance(xs: &[f64], ddof: u32) -> Option<Vec<f64>> {
    lab_numerics::stats::mean_variance(xs, u64::from(ddof)).map(|(mean, var)| vec![mean, var])
}
