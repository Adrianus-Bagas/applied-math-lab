//! Kuadratur numerik: menghampiri ∫ₐᵇ f(x) dx.

/// Aturan kuadratur komposit dengan galat ≈ C·hᴼᴿᴰᴱᴿ.
pub trait Quadrature {
    /// Orde galat: memperkecil h dua kali lipat membagi galat dengan 2^ORDER.
    const ORDER: u32;

    /// Menghampiri ∫ₐᵇ f dengan `n` subinterval selebar h = (b − a)/n.
    fn integrate<F: Fn(f64) -> f64>(&self, f: F, a: f64, b: f64, n: usize) -> f64;

    /// Ekstrapolasi Richardson dari n dan 2n subinterval:
    /// menghapus suku galat hᴼᴿᴰᴱᴿ sehingga orde naik.
    fn richardson<F: Fn(f64) -> f64>(&self, f: F, a: f64, b: f64, n: usize) -> f64 {
        let kasar = self.integrate(&f, a, b, n);
        let halus = self.integrate(&f, a, b, 2 * n);
        halus + (halus - kasar) / (f64::from(2_u32.pow(Self::ORDER) - 1))
    }
}

/// Aturan trapesium: f dihampiri garis lurus per subinterval (orde 2).
#[derive(Debug, Clone, Copy, Default)]
pub struct Trapezoid;

/// Aturan Simpson: f dihampiri parabola per dua subinterval (orde 4).
#[derive(Debug, Clone, Copy, Default)]
pub struct Simpson;

impl Quadrature for Trapezoid {
    const ORDER: u32 = 2;

    /// # Panics
    /// Bila `n == 0`.
    fn integrate<F: Fn(f64) -> f64>(&self, f: F, a: f64, b: f64, n: usize) -> f64 {
        assert!(n > 0, "trapesium butuh n > 0");
        let h = (b - a) / n as f64;
        // 1. Jumlahkan f di titik dalam x₁ … xₙ₋₁ (bobot 1).
        let middle_sum = (1..n).map(|i| f(a + i as f64 * h)).sum::<f64>();
        // 2. Tambahkan setengah dari f(a) dan f(b).
        let result = h * (f(a) / 2.0 + middle_sum + f(b) / 2.0);
        // 3. Kalikan dengan h.
        result
    }
}

impl Quadrature for Simpson {
    const ORDER: u32 = 4;

    /// # Panics
    /// Bila `n` nol atau ganjil.
    fn integrate<F: Fn(f64) -> f64>(&self, f: F, a: f64, b: f64, n: usize) -> f64 {
        assert!(n > 0 && n.is_multiple_of(2), "simpson butuh n genap");
        let h = (b - a) / n as f64;
        let mut result: f64;
        let middle_sum = (1..n)
            .map(|i| {
                let bobot = if !i.is_multiple_of(2) { 4.0 } else { 2.0 };
                bobot * f(a + i as f64 * h)
            })
            .sum::<f64>();
        result = f(a) + middle_sum + f(b);
        result *= h / 3.0;
        result
    }
}

/// Orde konvergensi empiris dari integral dengan n, 2n, dan 4n subinterval:
/// p ≈ log₂(|Iₙ − I₂ₙ| / |I₂ₙ − I₄ₙ|). Tidak membutuhkan nilai eksak.
pub fn empirical_order<Q: Quadrature>(
    rule: &Q,
    f: impl Fn(f64) -> f64,
    a: f64,
    b: f64,
    n: usize,
) -> f64 {
    let i_n = rule.integrate(&f, a, b, n);
    let i_2n = rule.integrate(&f, a, b, 2 * n);
    let i_4n = rule.integrate(&f, a, b, 4 * n);
    ((i_n - i_2n).abs() / (i_2n - i_4n).abs()).log2()
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::f64::consts::E;

    #[test]
    fn trapesium_eksak_untuk_fungsi_linear() {
        // ∫₀¹ (3x + 1) dx = 2.5; f″ = 0 sehingga galat nol bahkan dengan n = 1.
        assert_eq!(Trapezoid.integrate(|x| 3.0 * x + 1.0, 0.0, 1.0, 1), 2.5);
    }

    #[test]
    fn simpson_eksak_untuk_kubik() {
        // ∫₀² x³ dx = 4; dengan h = 1: (1/3)(0 + 4·1 + 8) = 4.
        assert_eq!(Simpson.integrate(|x| x * x * x, 0.0, 2.0, 2), 4.0);
    }

    #[test]
    fn trapesium_di_dalam_batas_galat_teori() {
        // |galat| ≤ (b − a)·h²/12 · max|f″|, dengan f = exp di [0, 1]: max f″ = e.
        let n = 100;
        let h = 1.0 / n as f64;
        let galat = (Trapezoid.integrate(f64::exp, 0.0, 1.0, n) - (E - 1.0)).abs();
        assert!(galat <= h * h / 12.0 * E, "galat = {galat}");
    }

    #[test]
    fn simpson_di_dalam_batas_galat_teori() {
        // |galat| ≤ (b − a)·h⁴/180 · max|f⁽⁴⁾|; untuk exp, f⁽⁴⁾ = exp ≤ e.
        let n = 10;
        let h = 1.0 / n as f64;
        let galat = (Simpson.integrate(f64::exp, 0.0, 1.0, n) - (E - 1.0)).abs();
        assert!(galat <= h.powi(4) / 180.0 * E, "galat = {galat}");
    }

    #[test]
    fn simpson_jauh_lebih_akurat_dengan_titik_yang_sama() {
        let eksak = E - 1.0;
        let t = (Trapezoid.integrate(f64::exp, 0.0, 1.0, 10) - eksak).abs();
        let s = (Simpson.integrate(f64::exp, 0.0, 1.0, 10) - eksak).abs();
        assert!(s < t / 100.0, "trapesium {t}, Simpson {s}");
    }

    #[test]
    fn interval_terbalik_mengubah_tanda() {
        let maju = Simpson.integrate(f64::sin, 0.0, 1.0, 20);
        let mundur = Simpson.integrate(f64::sin, 1.0, 0.0, 20);
        assert!((maju + mundur).abs() <= 1e-15);
    }

    #[test]
    #[should_panic(expected = "genap")]
    fn simpson_menolak_n_ganjil() {
        let _ = Simpson.integrate(f64::exp, 0.0, 1.0, 3);
    }

    #[test]
    fn richardson_trapesium_adalah_simpson() {
        for n in [1, 2, 5, 10] {
            let r = Trapezoid.richardson(f64::exp, 0.0, 1.0, n);
            let s = Simpson.integrate(f64::exp, 0.0, 1.0, 2 * n);
            assert!((r - s).abs() <= 1e-14 * s.abs(), "n = {n}: {r} vs {s}");
        }
    }

    #[test]
    fn richardson_simpson_menghapus_suku_h4() {
        let eksak = E - 1.0;
        let simpson = (Simpson.integrate(f64::exp, 0.0, 1.0, 16) - eksak).abs();
        let richardson = (Simpson.richardson(f64::exp, 0.0, 1.0, 8) - eksak).abs();
        assert!(
            richardson < simpson / 100.0,
            "Simpson {simpson}, Richardson {richardson}"
        );
    }

    #[test]
    fn orde_empiris_sesuai_teori() {
        let p_trap = empirical_order(&Trapezoid, f64::exp, 0.0, 1.0, 8);
        let p_simp = empirical_order(&Simpson, f64::exp, 0.0, 1.0, 8);
        assert!((p_trap - 2.0).abs() < 0.05, "trapesium p = {p_trap}");
        assert!((p_simp - 4.0).abs() < 0.05, "Simpson p = {p_simp}");
    }

    #[test]
    fn orde_turun_bila_fungsi_tidak_mulus() {
        // √x: turunannya tak hingga di 0, asumsi Taylor runtuh → orde 1,5, bukan 2.
        let p = empirical_order(&Trapezoid, f64::sqrt, 0.0, 1.0, 256);
        assert!((p - 1.5).abs() < 0.05, "p = {p}");
    }
}
