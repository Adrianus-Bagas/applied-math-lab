//! Pecahan berlanjut (continued fraction) dan konvergennya.
//!
//! Pecahan berlanjut sederhana [a0; a1, a2, ...] berarti
//! a0 + 1/(a1 + 1/(a2 + ...)). Konvergen ke-n adalah p_n/q_n = [a0; a1, ..., an].

use std::{f64::consts::SQRT_2, iter::FusedIterator};

/// Iterator konvergen (p_n, q_n) dari barisan hasil bagi parsial a0, a1, ...
///
/// Rekurensi: p_n = a_n·p_{n−1} + p_{n−2} dan q_n = a_n·q_{n−1} + q_{n−2},
/// dengan nilai awal p_{−2} = 0, p_{−1} = 1, q_{−2} = 1, q_{−1} = 0.
/// Iterasi berhenti (`None`) saat barisan input habis atau saat hasil
/// melampaui `i64`; sesudah itu selalu `None` (lihat `FusedIterator`).
#[derive(Debug, Clone)]
pub struct Convergents<I> {
    quotients: I,
    /// (p_{n−2}, p_{n−1})
    p: (i64, i64),
    /// (q_{n−2}, q_{n−1})
    q: (i64, i64),
    selesai: bool,
}

impl<I> Convergents<I>
where
    I: Iterator<Item = i64>,
{
    /// Membuat iterator konvergen dari barisan hasil bagi parsial.
    pub fn new(quotients: I) -> Self {
        Self {
            quotients,
            p: (0, 1),
            q: (1, 0),
            selesai: false,
        }
    }
}

impl<I> Iterator for Convergents<I>
where
    I: Iterator<Item = i64>,
{
    type Item = (i64, i64);

    fn next(&mut self) -> Option<Self::Item> {
        // Langkah 1: bila sudah pernah berhenti, tetap berhenti.
        if self.selesai {
            return None;
        }

        // Langkah 2: ambil a_n berikutnya; bila input habis, tandai selesai.
        let Some(a) = self.quotients.next() else {
            self.selesai = true;
            return None;
        };

        // Langkah 3: hitung p_n dan q_n lewat `langkah` (keduanya Option).
        //   Catatan: jangan memakai `?` langsung di fungsi ini. `?` akan
        //   me-return None TANPA men-set `selesai`, sehingga janji
        //   FusedIterator dilanggar. Gabungkan dua Option dengan `match`
        //   atau `zip`.
        //   let pasangan = /* TODO: Option<(i64, i64)> berisi (p_n, q_n) */;
        let p_n = langkah(a, self.p.0, self.p.1);
        let q_n = langkah(a, self.q.0, self.q.1);
        let Some((p_n, q_n)) = p_n.zip(q_n) else {
            self.selesai = true;
            return None;
        };
        // Langkah 4: bila pasangan None (overflow), set `selesai` lalu return None.
        // Langkah 5: geser jendela:
        //   (p_{n−2}, p_{n−1}) ← (p_{n−1}, p_n), begitu juga untuk q.
        self.p = (self.p.1, p_n);
        self.q = (self.q.1, q_n);
        // Langkah 6: kembalikan Some((p_n, q_n)).
        Some((p_n, q_n))
    }
}

// Janji: sesudah None, selalu None. Ditepati oleh field `selesai`.
impl<I: Iterator<Item = i64>> FusedIterator for Convergents<I> {}

/// Satu langkah rekurensi: a·sekarang + sebelumnya, atau None bila overflow i64.
fn langkah(a: i64, sebelumnya: i64, sekarang: i64) -> Option<i64> {
    // TODO: satu baris dengan checked_mul lalu checked_add.
    //   Di sini `?` BOLEH dipakai: fungsi ini memang mengembalikan Option.
    a.checked_mul(sekarang)?.checked_add(sebelumnya)
}

/// Hasil bagi parsial √2 = [1; 2, 2, 2, ...] (tak hingga).
pub fn sqrt2_quotients() -> impl Iterator<Item = i64> {
    std::iter::once(1).chain(std::iter::repeat(2))
}

/// Konvergen √2: 1/1, 3/2, 7/5, 17/12, ... sampai batas i64.
pub fn sqrt2_convergents() -> Convergents<impl Iterator<Item = i64>> {
    Convergents::new(sqrt2_quotients())
}

/// Konvergen √2 pertama p/q dengan |p/q − √2| < tol, atau None bila
/// toleransi itu tidak tercapai sebelum overflow i64.
pub fn sqrt2_approx(tol: f64) -> Option<(i64, i64)> {
    // Langkah 1: mulai dari sqrt2_convergents().
    let approx = sqrt2_convergents().find(|&(p, q)| ((p as f64 / q as f64) - SQRT_2).abs() < tol);
    // Langkah 2: pakai .find(|&(p, q)| ...) dengan syarat galat < tol.
    //   Konversi: p as f64 / q as f64; konstanta std::f64::consts::SQRT_2.
    // Langkah 3: hasil find sudah berupa Option, langsung dikembalikan.
    approx
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::rational::gcd;

    #[test]
    fn enam_konvergen_pertama_sqrt2() {
        let v: Vec<_> = sqrt2_convergents().take(6).collect();
        assert_eq!(v, [(1, 1), (3, 2), (7, 5), (17, 12), (41, 29), (99, 70)]);
    }

    #[test]
    fn pecahan_berhingga_415_per_93() {
        // 415/93 = [4; 2, 6, 7]; iterator berhenti sendiri saat input habis.
        let v: Vec<_> = Convergents::new([4, 2, 6, 7].into_iter()).collect();
        println!("{:?}", v);
        assert_eq!(v, [(4, 1), (9, 2), (58, 13), (415, 93)]);
    }

    #[test]
    fn rasio_emas_memberi_fibonacci() {
        // φ = [1; 1, 1, ...] → rasio bilangan Fibonacci berurutan.
        let v: Vec<_> = Convergents::new(std::iter::repeat(1)).take(5).collect();
        assert_eq!(v, [(1, 1), (2, 1), (3, 2), (5, 3), (8, 5)]);
    }

    #[test]
    fn identitas_pell_berselang_tanda() {
        // p_n² − 2 q_n² = (−1)^{n+1}; dihitung di i128 agar kuadratnya muat.
        // Loop ini juga menguji bahwa iterator berhenti sendiri saat overflow.
        for (n, (p, q)) in sqrt2_convergents().enumerate() {
            let (p, q) = (i128::from(p), i128::from(q));
            let harapan = if n % 2 == 0 { -1 } else { 1 };
            assert_eq!(p * p - 2 * q * q, harapan, "n = {n}");
        }
    }

    #[test]
    fn konvergen_dalam_bentuk_paling_sederhana() {
        assert!(sqrt2_convergents().all(|(p, q)| gcd(p as u128, q as u128) == 1));
    }

    #[test]
    fn berhenti_saat_overflow_dan_tetap_berhenti() {
        let mut it = sqrt2_convergents();
        // by_ref: pinjam iterator untuk dihabiskan, tanpa memindahkan miliknya.
        let banyak = it.by_ref().count();
        assert!((40..60).contains(&banyak), "banyak = {banyak}");
        assert_eq!(it.next(), None);
        assert_eq!(it.next(), None);
    }

    #[test]
    fn galat_lebih_kecil_dari_satu_per_q_kuadrat() {
        for (p, q) in sqrt2_convergents().take(15) {
            let galat = (p as f64 / q as f64 - std::f64::consts::SQRT_2).abs();
            assert!(galat < 1.0 / (q as f64).powi(2), "{p}/{q}");
        }
    }

    #[test]
    fn aproksimasi_dengan_toleransi() {
        // 7/5 meleset 0,0142; 17/12 meleset 0,0025.
        assert_eq!(sqrt2_approx(1e-2), Some((17, 12)));
        // Toleransi 0 tidak pernah tercapai: find berhenti karena iterator habis.
        assert_eq!(sqrt2_approx(0.0), None);
    }
}
