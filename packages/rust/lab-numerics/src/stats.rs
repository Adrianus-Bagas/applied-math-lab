//! Statistik deskriptif yang stabil secara numerik.

/// Ringkasan satu kali lintas data dengan algoritma Welford.
///
/// Invarian: setelah `k` pemanggilan `push`, `mean` adalah rata-rata `k` data
/// dan `m2` = Σ (x_i − mean)².
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Moments {
    pub count: u64,
    pub mean: f64,
    pub m2: f64,
}

impl Moments {
    #[must_use]
    pub fn new() -> Self {
        Self {
            count: 0,
            mean: 0.0,
            m2: 0.0,
        }
    }

    /// Tambahkan satu observasi.
    pub fn push(&mut self, x: f64) {
        self.count += 1;
        let delta = x - self.mean;
        self.mean += delta / self.count as f64;
        // Memakai mean yang SUDAH diperbarui: δ · (x − m_k).
        self.m2 += delta * (x - self.mean);
    }

    /// Variansi dengan pembagi `n − ddof` (ddof = 0: populasi, 1: sampel).
    /// `None` bila `n ≤ ddof`, karena variansinya tidak terdefinisi.
    #[must_use]
    pub fn variance(&self, ddof: u64) -> Option<f64> {
        (self.count > ddof).then(|| self.m2 / (self.count - ddof) as f64)
    }
}

impl Default for Moments {
    fn default() -> Self {
        Self::new()
    }
}

impl FromIterator<f64> for Moments {
    fn from_iter<I: IntoIterator<Item = f64>>(iter: I) -> Self {
        let mut m = Self::new();
        for x in iter {
            m.push(x);
        }
        m
    }
}

/// Mean dan variansi dari sebuah slice. `None` bila `xs.len() ≤ ddof`.
/// NaN di input menular ke output (sama seperti NumPy).
#[must_use]
pub fn mean_variance(xs: &[f64], ddof: u64) -> Option<(f64, f64)> {
    let m: Moments = xs.iter().copied().collect();
    Some((m.mean, m.variance(ddof)?))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn assert_close(actual: f64, expected: f64, rtol: f64) {
        let tol = rtol * expected.abs().max(1.0);
        assert!(
            (actual - expected).abs() <= tol,
            "actual = {actual}, expected = {expected}, tol = {tol}"
        );
    }

    /// Rumus naif Σx²/n − x̄², dikoreksi ke variansi sampel. Hanya untuk pembanding.
    fn naive_sample_variance(xs: &[f64]) -> f64 {
        let n = xs.len() as f64;
        let mean = xs.iter().sum::<f64>() / n;
        let mean_sq = xs.iter().map(|x| x * x).sum::<f64>() / n;
        (mean_sq - mean * mean) * n / (n - 1.0)
    }

    #[test]
    fn hitung_tangan() {
        // Mean 5; Σ(x − 5)² = 32 → populasi 32/8 = 4, sampel 32/7.
        let xs = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0];
        let (mean, var_pop) = mean_variance(&xs, 0).unwrap();
        assert_close(mean, 5.0, 1e-15);
        assert_close(var_pop, 4.0, 1e-15);
        let (_, var_sample) = mean_variance(&xs, 1).unwrap();
        assert_close(var_sample, 32.0 / 7.0, 1e-15);
    }

    #[test]
    fn stabil_saat_offset_besar() {
        let xs = [4.0, 7.0, 13.0, 16.0].map(|d| 1e12 + d);
        let (_, var) = mean_variance(&xs, 1).unwrap();
        assert_close(var, 30.0, 1e-12);
        // Dokumentasi masalahnya: rumus naif meleset jauh.
        assert!((naive_sample_variance(&xs) - 30.0).abs() > 1.0);
    }

    #[test]
    fn kasus_tepi() {
        assert_eq!(mean_variance(&[], 0), None);
        assert_eq!(mean_variance(&[3.0], 1), None);
        assert_eq!(mean_variance(&[3.0], 0), Some((3.0, 0.0)));
    }
}
