//! Utilitas numerik bersama untuk Applied Math Lab.

pub mod cfrac;
pub mod poly;
pub mod quad;
pub mod rational;
pub mod roots;
pub mod stats;

/// Membandingkan dua `f64` dengan toleransi relatif dan absolut.
///
/// Semantik sama dengan `math.isclose` Python (simetris terhadap a dan b):
/// `|a - b| <= max(rel_tol * max(|a|, |b|), abs_tol)`.
///
/// # Examples
/// ```
/// use lab_numerics::approx_eq;
/// assert!(approx_eq(0.1 + 0.2, 0.3, 1e-12, 0.0));
/// assert!(!approx_eq(1.0, 1.1, 1e-12, 0.0));
/// ```
#[must_use]
pub fn approx_eq(a: f64, b: f64, rel_tol: f64, abs_tol: f64) -> bool {
    if a == b {
        return true; // termasuk inf == inf
    }
    if !a.is_finite() || !b.is_finite() {
        return false; // NaN, atau inf vs bilangan lain
    }
    let diff = (a - b).abs();
    diff <= (rel_tol * a.abs().max(b.abs())).max(abs_tol)
}

#[cfg(test)]
mod tests {
    use super::approx_eq;

    #[test]
    fn exact_and_infinite() {
        assert!(approx_eq(1.0, 1.0, 0.0, 0.0));
        assert!(approx_eq(f64::INFINITY, f64::INFINITY, 0.0, 0.0));
        assert!(!approx_eq(f64::INFINITY, f64::NEG_INFINITY, 1.0, 1.0));
    }

    #[test]
    fn nan_is_never_close() {
        assert!(!approx_eq(f64::NAN, f64::NAN, 1.0, 1.0));
    }

    #[test]
    fn relative_tolerance_fails_near_zero() {
        assert!(!approx_eq(1e-20, 0.0, 1e-9, 0.0));
        assert!(approx_eq(1e-20, 0.0, 1e-9, 1e-12));
    }
}
