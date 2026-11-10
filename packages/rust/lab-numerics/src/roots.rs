//! Pencarian akar persamaan f(x) = 0.

/// Akar yang ditemukan beserta jumlah iterasi yang dipakai.
/// Wadah hasil tanpa invarian, jadi field-nya boleh publik.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Root {
    pub x: f64,
    pub iterations: u32,
}

/// Alasan pencarian akar gagal.
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum RootError {
    /// Interval tidak sah: bukan a < b, atau ada ujung yang tidak hingga.
    InvalidInterval { a: f64, b: f64 },
    /// f(a) dan f(b) bertanda sama, jadi teorema nilai antara tidak menjamin akar.
    NoSignChange { fa: f64, fb: f64 },
    /// f menghasilkan NaN atau tak hingga di titik `x`.
    NonFinite { x: f64 },
    /// Batas iterasi habis sebelum toleransi tercapai.
    NotConverged { last: f64, iterations: u32 },
    /// f'(x) = 0: garis singgung mendatar, langkah Newton tidak terdefinisi.
    ZeroDerivative { x: f64 },
}

impl std::fmt::Display for RootError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::InvalidInterval { a, b } => write!(
                f,
                "interval [{a}, {b}] tidak sah: butuh a < b dan keduanya hingga"
            ),
            Self::NoSignChange { fa, fb } => write!(f, "f(a) = {fa} dan f(b) = {fb} bertanda sama"),
            Self::NonFinite { x } => write!(f, "f menghasilkan NaN atau tak hingga di titik {x}"),
            Self::NotConverged { last, iterations } => write!(
                f,
                "belum konvergen setelah {iterations} iterasi (tebakan terakhir {last})"
            ),
            Self::ZeroDerivative { x } => write!(
                f,
                "garis singgung di {x} mendatar sehingga langkah Newton tidak terdefinisi"
            ),
        }
    }
}

// Tanpa method tambahan: Error cukup mensyaratkan Debug + Display.
impl std::error::Error for RootError {}

/// Memastikan f(a) dan f(b) berbeda tanda (atau salah satunya nol).
fn check_bracket(fa: f64, fb: f64) -> Result<(), RootError> {
    if (fa > 0.0 && fb > 0.0) || (fa < 0.0 && fb < 0.0) {
        return Err(RootError::NoSignChange { fa, fb });
    }
    Ok(())
}

/// Mencari akar f di [a, b] dengan metode bisection.
///
/// Di iterasi ke-i: hitung titik tengah m dan f(m). Kembalikan m bila f(m) = 0
/// atau setengah lebar interval saat ini ≤ `tol`; jika tidak, buang separuh
/// interval yang tidak memuat perubahan tanda.
pub fn bisection(
    f: impl Fn(f64) -> f64,
    a: f64,
    b: f64,
    tol: f64,
    max_iter: u32,
) -> Result<Root, RootError> {
    // Langkah A: validasi interval → Err(RootError::InvalidInterval { a, b }).
    if !(a.is_finite() && b.is_finite() && a < b) {
        return Err(RootError::InvalidInterval { a, b });
    }
    let fa = f(a);
    let fb = f(b);
    // Langkah B: hitung fa dan fb. Bila salah satu tidak hingga → Err(NonFinite { x }).
    if !fa.is_finite() {
        return Err(RootError::NonFinite { x: a });
    }
    if !fb.is_finite() {
        return Err(RootError::NonFinite { x: b });
    }
    // Langkah C: bila fa == 0 atau fb == 0, ujung itu adalah akar (iterations: 0).
    if fa == 0.0 {
        return Ok(Root {
            x: a,
            iterations: 0,
        });
    }
    if fb == 0.0 {
        return Ok(Root {
            x: b,
            iterations: 0,
        });
    }
    // Langkah D: check_bracket(fa, fb)?;
    check_bracket(fa, fb)?;
    // Langkah E: salin a dan b ke variabel `mut`, lalu loop i in 1..=max_iter.

    let mut a = a;
    let mut b = b;
    let mut fa = fa;

    let mut m = a;
    for i in 1..=max_iter {
        m = a + (b - a) / 2.0;
        let fm = f(m);

        if !fm.is_finite() {
            return Err(RootError::NonFinite { x: m });
        }

        if fm == 0.0 || (b - a) / 2.0 <= tol {
            return Ok(Root {
                x: m,
                iterations: i,
            });
        }

        if (fa < 0.0) == (fm < 0.0) {
            a = m;
            fa = fm;
        } else {
            b = m;
        }
    }
    // Langkah F: setelah loop → Err(NotConverged { last: titik tengah terakhir, iterations: max_iter }).
    Err(RootError::NotConverged {
        last: m,
        iterations: max_iter,
    })
}

/// Mencari akar f mulai dari `x0` dengan metode Newton.
/// `f_df(x)` mengembalikan pasangan (f(x), f'(x)).
///
/// Berhenti dengan sukses bila f(x) = 0 tepat, atau bila |langkah| ≤ `tol`
/// (yang dikembalikan adalah x setelah langkah itu).
pub fn newton(
    f_df: impl Fn(f64) -> (f64, f64),
    x0: f64,
    tol: f64,
    max_iter: u32,
) -> Result<Root, RootError> {
    let mut x = x0;
    for i in 1..=max_iter {
        let (fx, dfx) = f_df(x); // membongkar pasangan (tuple) jadi dua variabel

        // 1. fx atau dfx tidak hingga → Err(NonFinite { x }).
        if !(fx.is_finite() && dfx.is_finite()) {
            return Err(RootError::NonFinite { x });
        }
        // 2. fx == 0 → x sudah akar, belum ada langkah di iterasi ini:
        //    Ok(Root { x, iterations: i - 1 }).
        if fx == 0.0 {
            return Ok(Root {
                x,
                iterations: i - 1,
            });
        }
        // 3. dfx == 0 → Err(ZeroDerivative { x }).
        if dfx == 0.0 {
            return Err(RootError::ZeroDerivative { x });
        }
        // 4. Hitung langkah = fx / dfx, lalu perbarui x.
        let langkah = fx / dfx;
        let x_baru = x - langkah;
        // 5. x baru tidak hingga → Err(NonFinite { x }).
        if !x_baru.is_finite() {
            return Err(RootError::NonFinite { x });
        }
        x = x_baru;
        // 6. |langkah| ≤ tol → Ok(Root { x, iterations: i }).
        if langkah.abs() <= tol {
            return Ok(Root { x, iterations: i });
        }
    }
    Err(RootError::NotConverged {
        last: x,
        iterations: max_iter,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn akar_dua_dengan_jumlah_iterasi_sesuai_teori() {
        let r = bisection(|x| x * x - 2.0, 0.0, 2.0, 1e-12, 100).unwrap();
        assert!((r.x - 2.0_f64.sqrt()).abs() <= 1e-12);
        assert_eq!(r.iterations, 41); // cocokkan dengan jawaban soal ⭐ nomor 2
    }

    #[test]
    fn titik_tengah_tepat_di_akar() {
        // [0, 1] → m = 0.5 (f > 0) → [0, 0.5] → m = 0.25, f(m) = 0 tepat.
        let r = bisection(|x| x - 0.25, 0.0, 1.0, 1e-12, 100).unwrap();
        print!("{:?}", r);
        assert_eq!(
            r,
            Root {
                x: 0.25,
                iterations: 2
            }
        );
    }

    #[test]
    fn ujung_interval_adalah_akar() {
        assert_eq!(
            bisection(|x| x, 0.0, 1.0, 1e-12, 100),
            Ok(Root {
                x: 0.0,
                iterations: 0
            })
        );
    }

    #[test]
    fn tanpa_perubahan_tanda() {
        assert_eq!(
            bisection(|x| x * x + 1.0, -1.0, 1.0, 1e-12, 100),
            Err(RootError::NoSignChange { fa: 2.0, fb: 2.0 })
        );
    }

    #[test]
    fn interval_tidak_sah() {
        assert_eq!(
            bisection(|x| x, 1.0, 0.0, 1e-12, 100),
            Err(RootError::InvalidInterval { a: 1.0, b: 0.0 })
        );
        assert!(matches!(
            bisection(|x| x, f64::NAN, 1.0, 1e-12, 100),
            Err(RootError::InvalidInterval { .. })
        ));
    }

    #[test]
    fn fungsi_tidak_hingga_di_ujung() {
        // ln(−1) = NaN.
        assert_eq!(
            bisection(f64::ln, -1.0, 2.0, 1e-12, 100),
            Err(RootError::NonFinite { x: -1.0 })
        );
    }

    #[test]
    fn batas_iterasi_habis() {
        let r = bisection(|x| x * x - 2.0, 0.0, 2.0, 0.0, 10);
        assert!(matches!(
            r,
            Err(RootError::NotConverged { iterations: 10, .. })
        ));
    }

    #[test]
    fn max_iter_tepat_cukup() {
        // Menurut teori butuh tepat 41 iterasi; dengan max_iter = 41 harus berhasil.
        let r = bisection(|x| x * x - 2.0, 0.0, 2.0, 1e-12, 41).unwrap();
        assert_eq!(r.iterations, 41);
    }

    #[test]
    fn pesan_error_dapat_dibaca() {
        let e = RootError::NoSignChange { fa: 2.0, fb: 2.0 };
        assert_eq!(e.to_string(), "f(a) = 2 dan f(b) = 2 bertanda sama");
        // Bisa dikemas sebagai error umum karena impl std::error::Error.
        let _umum: Box<dyn std::error::Error> = Box::new(e);
    }

    use crate::poly;

    #[test]
    fn newton_akar_dua_jauh_lebih_cepat_dari_bisection() {
        let r = newton(|x| (x * x - 2.0, 2.0 * x), 1.0, 1e-12, 50).unwrap();
        assert!((r.x - 2.0_f64.sqrt()).abs() <= 1e-15);
        assert!(r.iterations <= 6, "iterasi = {}", r.iterations); // bisection: 41
    }

    #[test]
    fn newton_memakai_horner_dari_sesi_1() {
        // p(x) = 1 − 3x + 2x², akar 0.5 dan 1.
        let p = [1.0, -3.0, 2.0];
        let r = newton(|x| poly::eval_with_derivative(&p, x), 0.0, 1e-14, 50).unwrap();
        assert!((r.x - 0.5).abs() <= 1e-14);
    }

    #[test]
    fn newton_tebakan_awal_sudah_akar() {
        assert_eq!(
            newton(|x| (x - 3.0, 1.0), 3.0, 1e-12, 50),
            Ok(Root {
                x: 3.0,
                iterations: 0
            })
        );
    }

    #[test]
    fn newton_akar_ganda_hanya_linear() {
        // f = (x − 1)², f'(1) = 0. Semua iterasi eksak di f64: xₖ = 1 + 2⁻ᵏ.
        let r = newton(
            |x| ((x - 1.0) * (x - 1.0), 2.0 * (x - 1.0)),
            2.0,
            1e-12,
            100,
        )
        .unwrap();
        assert_eq!(r.iterations, 40); // jelaskan lewat soal ⭐ nomor 5
    }

    #[test]
    fn newton_garis_singgung_mendatar() {
        assert_eq!(
            newton(|x| (x * x - 1.0, 2.0 * x), 0.0, 1e-12, 50),
            Err(RootError::ZeroDerivative { x: 0.0 })
        );
    }

    #[test]
    fn newton_berputar_tidak_konvergen() {
        // x³ − 2x + 2 dari 0: 0 → 1 → 0 → 1 → …
        let r = newton(
            |x| (x * x * x - 2.0 * x + 2.0, 3.0 * x * x - 2.0),
            0.0,
            1e-12,
            20,
        );
        assert!(matches!(
            r,
            Err(RootError::NotConverged { iterations: 20, .. })
        ));
    }

    #[test]
    fn newton_keluar_domain() {
        // ln tidak terdefinisi untuk x < 0.
        assert_eq!(
            newton(|x: f64| (x.ln(), 1.0 / x), -1.0, 1e-12, 50),
            Err(RootError::NonFinite { x: -1.0 })
        );
    }
}
