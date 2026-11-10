//! Polinomial berkoefisien `f64`, disimpan urut naik:
//! `coeffs[i]` adalah koefisien xⁱ, jadi `[1.0, -3.0, 2.0]` berarti 1 − 3x + 2x².
//! Slice kosong melambangkan polinomial nol.

/// Mengevaluasi p(x) dengan skema Horner: b ← b·x + aᵢ dari derajat tertinggi.
pub fn eval(coeffs: &[f64], x: f64) -> f64 {
    let mut result = 0.0;

    for &coeff in coeffs.iter().rev() {
        result = x * result + coeff;
    }

    result
}

/// Turunan p' sebagai polinomial baru yang dimiliki pemanggil.
/// Turunan polinomial konstan atau nol adalah polinomial nol (vektor kosong).
pub fn derivative(coeffs: &[f64]) -> Vec<f64> {
    coeffs
        .iter()
        .enumerate()
        .skip(1)
        .map(|(index, &value)| value * (index as f64))
        .collect()
}

/// Mengembalikan (p(x), p'(x)) dalam satu lintasan Horner.
/// Nilai p(x) harus identik bit dengan [`eval`], jadi pakai rekurensi yang sama persis.
pub fn eval_with_derivative(coeffs: &[f64], x: f64) -> (f64, f64) {
    let (mut b, mut d) = (0.0, 0.0);
    for &coeff in coeffs.iter().rev() {
        d = d * x + b;
        b = b * x + coeff;
    }
    (b, d)
}

/// Membuang koefisien nol di ujung (derajat tertinggi) secara in-place.
/// Nol di awal atau di tengah tidak disentuh.
pub fn trim(coeffs: &mut Vec<f64>) {
    while coeffs.last() == Some(&0.0) {
        coeffs.pop();
    }
}

/// Derajat polinomial tanpa mengubah input; `None` untuk polinomial nol.
pub fn degree(coeffs: &[f64]) -> Option<usize> {
    coeffs.iter().rposition(|&a| a != 0.0)
}

#[cfg(test)]
mod tests {
    use super::*;

    // p(x) = 1 − 3x + 2x² = (2x − 1)(x − 1); semua nilai uji eksak di f64.
    const P: [f64; 3] = [1.0, -3.0, 2.0];

    #[test]
    fn eval_hitung_tangan() {
        assert_eq!(eval(&P, 2.0), 3.0);
        assert_eq!(eval(&P, 0.5), 0.0);
        assert_eq!(eval(&P, 1.0), 0.0);
        assert_eq!(eval(&P, 0.0), 1.0);
    }

    #[test]
    fn eval_polinomial_nol_dan_konstan() {
        assert_eq!(eval(&[], 7.0), 0.0);
        assert_eq!(eval(&[4.0], 7.0), 4.0);
    }

    #[test]
    fn horner_tidak_menghitung_pangkat_x_terpisah() {
        // Cara naif: x² = 1e600 → inf, lalu 0·inf = NaN. Horner: tetap 1.
        assert_eq!(eval(&[1.0, 0.0, 0.0], 1e300), 1.0);
        assert_eq!(eval_with_derivative(&[1.0, 0.0, 0.0], 1e300), (1.0, 0.0));
    }

    #[test]
    fn turunan_hitung_tangan() {
        assert_eq!(derivative(&P), vec![-3.0, 4.0]);
        assert!(derivative(&[5.0]).is_empty());
        assert!(derivative(&[]).is_empty());
    }

    #[test]
    fn nilai_dan_turunan_sekaligus() {
        assert_eq!(eval_with_derivative(&P, 2.0), (3.0, 5.0));
        assert_eq!(eval_with_derivative(&[], 2.0), (0.0, 0.0));
        assert_eq!(eval_with_derivative(&[4.0], 2.0), (4.0, 0.0));
    }

    #[test]
    fn satu_lintasan_konsisten_dengan_fungsi_terpisah() {
        let q = [0.1, -0.7, 0.3, 1.9, -2.2];
        let dq = derivative(&q);
        for &x in &[-1.3, 0.0, 0.37, 2.5] {
            let (p, dp) = eval_with_derivative(&q, x);
            // Rekurensi sama → identik bit.
            assert_eq!(p, eval(&q, x));
            // Urutan operasi berbeda → cukup dekat (toleransi rinci di L0.10).
            assert!((dp - eval(&dq, x)).abs() <= 1e-12 * (1.0 + dp.abs()));
        }
    }

    #[test]
    fn trim_membuang_nol_di_ujung_saja() {
        let mut a = vec![1.0, 2.0, 0.0, 0.0];
        trim(&mut a);
        assert_eq!(a, vec![1.0, 2.0]);

        let mut nol = vec![0.0, 0.0];
        trim(&mut nol);
        assert!(nol.is_empty());

        let mut b = vec![0.0, 1.0, 0.0];
        trim(&mut b);
        assert_eq!(b, vec![0.0, 1.0]);
    }

    #[test]
    fn derajat() {
        assert_eq!(degree(&P), Some(2));
        assert_eq!(degree(&[1.0, 2.0, 0.0]), Some(1));
        assert_eq!(degree(&[3.0]), Some(0));
        assert_eq!(degree(&[0.0, 0.0]), None);
        assert_eq!(degree(&[]), None);
    }
}
