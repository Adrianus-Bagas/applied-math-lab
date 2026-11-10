//! Statistik deskriptif yang stabil secara numerik.

/// Ringkasan satu kali lintas data dengan algoritma Welford.
///
/// Invarian: setelah `k` pemanggilan `push`, `mean` adalah rata-rata `k` data
/// dan `m2` = Σ (x_i − mean)².
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Moments {
    count: u64,
    mean: f64,
    m2: f64,
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

    /// Banyak observasi.
    #[must_use]
    pub fn count(&self) -> u64 {
        self.count
    }

    /// Rata-rata; `None` bila kosong.
    pub fn mean(&self) -> Option<f64> {
        (self.count > 0).then_some(self.mean)
    }

    pub fn m2(&self) -> f64 {
        self.m2
    }

    /// Varians populasi M₂/n; `None` bila n = 0.
    pub fn variance_population(&self) -> Option<f64> {
        (self.count > 0).then(|| self.m2 / self.count as f64)
    }

    /// Varians sampel M₂/(n − 1); `None` bila n < 2.
    pub fn variance_sample(&self) -> Option<f64> {
        (self.count >= 2).then(|| self.m2 / (self.count - 1) as f64)
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

    /// Menggabungkan statistik `other` ke `self` (rumus Chan, Golub, LeVeque).
    /// Gabungan dengan ringkasan kosong tidak boleh menghasilkan NaN.
    pub fn merge(&mut self, other: &Self) {
        // (kasus tepi: lihat Langkah 4, tambahkan nanti)
        if other.count == 0 {
            return;
        }

        if self.count == 0 {
            *self = *other;
            return;
        }

        // 1. Besaran pembantu, semuanya f64.
        let n_a = self.count as f64;
        let n_b = other.count as f64;
        let n = n_a + n_b;
        let delta = other.mean - self.mean;

        // 2. Nilai baru, masih di variabel lokal.
        let mean_baru = self.mean + delta * n_b / n;
        let m2_baru = self.m2 + other.m2 + delta * delta * n_a * n_b / n;

        // 3. Baru sekarang tulis ke field.
        self.count += other.count;
        self.mean = mean_baru;
        self.m2 = m2_baru;
    }

    /// Versi yang mengembalikan nilai baru; cocok untuk `Iterator::reduce`.
    #[must_use]
    pub fn merged(mut self, other: Self) -> Self {
        // 1. Gabungkan `other` ke salinan `self` dengan memanggil merge.
        // 2. Kembalikan `self`.
        self.merge(&other);
        self
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
        assert_eq!(mean_variance(&[], 1), None);
    }

    const DATA: [f64; 8] = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0];

    fn dari(xs: &[f64]) -> Moments {
        xs.iter().copied().collect()
    }

    #[test]
    fn merge_di_setiap_titik_potong_sama_dengan_satu_lintasan() {
        let utuh = dari(&DATA);
        for k in 0..=DATA.len() {
            let (kiri, kanan) = DATA.split_at(k);
            let mut a = dari(kiri);
            a.merge(&dari(kanan));
            assert_eq!(a.count, utuh.count, "k = {k}");
            assert_close(a.mean, utuh.mean, 1e-14);
            assert_close(a.m2, utuh.m2, 1e-14);
        }
    }

    #[test]
    fn merge_dengan_kosong_tidak_mengubah_apa_pun() {
        let s = dari(&DATA);

        let mut a = s;
        a.merge(&Moments::new());
        assert_eq!(a, s);

        let mut b = Moments::new();
        b.merge(&s);
        assert_eq!(b, s);

        assert_eq!(Moments::new().merged(Moments::new()), Moments::new());
    }

    #[test]
    fn merge_hampir_asosiatif() {
        let (a, b, c) = (dari(&DATA[..3]), dari(&DATA[3..5]), dari(&DATA[5..]));
        let kiri = a.merged(b).merged(c);
        let kanan = a.merged(b.merged(c));
        assert_close(kiri.m2, kanan.m2, 1e-14);
    }

    #[test]
    fn reduce_per_potongan_seperti_rayon() {
        let xs: Vec<f64> = (1..=1000).map(|i| f64::from(i).sqrt()).collect();
        let utuh = dari(&xs);
        let gabungan = xs.chunks(37).map(dari).reduce(Moments::merged).unwrap();
        assert_eq!(gabungan.count, utuh.count);
        assert_close(gabungan.mean, utuh.mean, 1e-13);
        assert_close(gabungan.m2, utuh.m2, 1e-12);
    }

    #[test]
    fn merge_offset_besar() {
        // Rata-rata berjalan DATA (3.333…, 4.428…) tidak representable di sekitar 1e12
        // (jarak antar-f64 ≈ 1.2e-4), jadi galat relatif varians bisa ~1e-4.
        let xs = DATA.map(|v| 1e12 + v);
        let s = dari(&xs[..5]).merged(dari(&xs[5..]));
        assert_close(s.variance(0).unwrap(), 4.0, 1e-3);
    }
}
