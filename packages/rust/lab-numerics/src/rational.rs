//! Bilangan rasional eksak p/q dalam bentuk kanonik.

use std::fmt;
use std::ops::{Add, Div, Mul, Neg, Sub};

/// FPB dengan algoritma Euclid: FPB(a, b) = FPB(b, a mod b), FPB(a, 0) = a.
#[must_use]
pub fn gcd(a: u128, b: u128) -> u128 {
    let mut a = a;
    let mut b = b;
    while b != 0 {
        (a, b) = (b, a % b);
    }
    a
}

/// Bilangan rasional dalam bentuk kanonik.
///
/// Invarian: `den > 0` dan FPB(|num|, den) = 1; nol disimpan sebagai 0/1.
/// Karena representasinya tunggal, kesamaan cukup membandingkan field (`derive`).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Rational {
    num: i64,
    den: i64,
}

impl Rational {
    pub const ZERO: Self = Self { num: 0, den: 1 };
    pub const ONE: Self = Self { num: 1, den: 1 };

    /// Membentuk num/den dalam bentuk kanonik; `None` bila `den == 0`.
    #[must_use]
    pub fn new(num: i64, den: i64) -> Option<Self> {
        if den == 0 {
            None
        } else {
            Some(Self::from_i128(i128::from(num), i128::from(den)))
        }
    }

    /// Normalisasi hasil antara di i128 ke bentuk kanonik i64.
    ///
    /// # Panics
    /// Bila `den == 0`, atau hasil yang sudah disederhanakan tidak muat di i64.
    fn from_i128(num: i128, den: i128) -> Self {
        assert!(den != 0, "penyebut nol");

        // 1. Penyebut positif. `if` adalah ekspresi, jadi hasilnya bisa langsung
        //    dibongkar ke (num, den) baru yang menutupi parameter lama.
        let (num, den) = if den < 0 { (-num, -den) } else { (num, den) };

        // 2. g = FPB(|num|, den), masih di i128.
        //    - num.unsigned_abs() → |num| bertipe u128
        //    - den sudah positif, jadi den.unsigned_abs() sama dengan den
        //    - hasil gcd bertipe u128; ubah kembali dengan `as i128`
        let g = gcd(num.unsigned_abs(), den.unsigned_abs()) as i128;

        // 3. Bagi dengan g, baru konversi ke i64.
        Self {
            num: i64::try_from(num / g).expect("overflow: pembilang tidak muat di i64"),
            den: i64::try_from(den / g).expect("overflow: penyebut tidak muat di i64"),
        }
    }

    #[must_use]
    pub fn numer(&self) -> i64 {
        self.num
    }

    #[must_use]
    pub fn denom(&self) -> i64 {
        self.den
    }

    /// Hampiran floating-point (bisa membulatkan).
    #[must_use]
    pub fn to_f64(&self) -> f64 {
        self.num as f64 / self.den as f64
    }
}

impl Add for Rational {
    type Output = Self;

    fn add(self, rhs: Self) -> Self {
        let (a, b) = (i128::from(self.num), i128::from(self.den));
        let (c, d) = (i128::from(rhs.num), i128::from(rhs.den));
        Self::from_i128(a * d + c * b, b * d)
    }
}

impl Neg for Rational {
    type Output = Self;

    fn neg(self) -> Self {
        let (num, den) = (i128::from(self.num), i128::from(self.den));
        Self::from_i128(-num, den)
    }
}

impl Sub for Rational {
    type Output = Self;

    fn sub(self, rhs: Self) -> Self {
        let (a, b) = (i128::from(self.num), i128::from(self.den));
        let (c, d) = (i128::from(rhs.num), i128::from(rhs.den));
        Self::from_i128(a * d - c * b, b * d)
    }
}

impl Mul for Rational {
    type Output = Self;

    fn mul(self, rhs: Self) -> Self {
        let (a, b) = (i128::from(self.num), i128::from(self.den));
        let (c, d) = (i128::from(rhs.num), i128::from(rhs.den));
        Self::from_i128(a * c, b * d)
    }
}

impl Div for Rational {
    type Output = Self;

    /// # Panics
    /// Bila `rhs` nol (sama seperti pembagian bilangan bulat dengan nol).
    fn div(self, rhs: Self) -> Self {
        assert!(rhs.num != 0, "pembagian dengan nol");
        let (a, b) = (i128::from(self.num), i128::from(self.den));
        let (c, d) = (i128::from(rhs.num), i128::from(rhs.den));
        Self::from_i128(a * d, b * c)
    }
}

impl fmt::Display for Rational {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        if self.den == 1 {
            write!(f, "{}", self.num)
        } else {
            write!(f, "{}/{}", self.num, self.den)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn r(num: i64, den: i64) -> Rational {
        Rational::new(num, den).unwrap()
    }

    #[test]
    fn fpb_euclid() {
        assert_eq!(gcd(48, 18), 6);
        assert_eq!(gcd(18, 48), 6);
        assert_eq!(gcd(17, 5), 1);
        assert_eq!(gcd(0, 5), 5);
        assert_eq!(gcd(0, 0), 0);
    }

    #[test]
    fn bentuk_kanonik() {
        assert_eq!(r(2, 4), r(1, 2));
        assert_eq!(r(-3, -6), r(1, 2));
        let negatif = r(1, -2);
        assert_eq!((negatif.numer(), negatif.denom()), (-1, 2));
        assert_eq!(r(0, -5), Rational::ZERO);
        assert_eq!(Rational::new(1, 0), None);
    }

    #[test]
    fn aritmetika_hitung_tangan() {
        assert_eq!(r(1, 2) + r(1, 3), r(5, 6));
        assert_eq!(r(1, 2) - r(1, 2), Rational::ZERO);
        assert_eq!(r(2, 3) * r(9, 4), r(3, 2));
        assert_eq!(r(1, 2) / r(1, 4), r(2, 1));
        assert_eq!(-r(1, 2), r(-1, 2));
        assert_eq!(r(-1, 3) / r(-2, 3), r(1, 2));
    }

    #[test]
    fn deret_harmonik_eksak() {
        // 1 + 1/2 + … + 1/10 = 7381/2520, tanpa galat pembulatan.
        let h = (1..=10)
            .map(|k| r(1, k))
            .fold(Rational::ZERO, |acc, x| acc + x);
        assert_eq!(h, r(7381, 2520));
        assert_eq!(h.to_string(), "7381/2520");
    }

    #[test]
    fn tampilan() {
        assert_eq!(r(5, 6).to_string(), "5/6");
        assert_eq!(r(-1, 2).to_string(), "-1/2");
        assert_eq!(r(4, 2).to_string(), "2");
    }

    #[test]
    #[should_panic(expected = "overflow")]
    fn overflow_terdeteksi() {
        let _ = r(i64::MAX, 1) + Rational::ONE;
    }

    #[test]
    #[should_panic(expected = "nol")]
    fn bagi_nol_panik() {
        let _ = Rational::ONE / Rational::ZERO;
    }
}
