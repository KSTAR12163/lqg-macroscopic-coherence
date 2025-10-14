#!/usr/bin/env python3
"""
Numerical Guardrails for LQG Macroscopic Coherence Framework

Prevents floating-point artifacts by enforcing minimum thresholds for
physically meaningful coupling constants and matrix elements.

LESSON FROM PHASE B: g₀ ~ 10⁻¹²¹ J is below float precision → artifact!
"""

import numpy as np
import warnings
from typing import Tuple, Optional
from dataclasses import dataclass

# ============================================================================
# FUNDAMENTAL THRESHOLDS
# ============================================================================

# Absolute minimum for numerical stability (IEEE 754 double precision)
MACHINE_EPSILON = np.finfo(float).eps  # ~2.2e-16

# Physical thresholds (conservative estimates)
G_EFF_THRESHOLD = 1e-50  # J - Minimum coupling for meaningful physics
ENERGY_THRESHOLD = 1e-60  # J - Minimum energy scale
MATRIX_ELEMENT_THRESHOLD = 1e-50  # Minimum Hamiltonian off-diagonal

# Warning thresholds (yellow flags before hard errors)
G_EFF_WARNING = 1e-40  # J - Warn if coupling is very weak
PERTURBATIVE_THRESHOLD = 0.1  # |H_int|/|H_0| must be < this


@dataclass
class NumericalValidation:
    """Result of numerical validation check."""
    is_valid: bool
    is_warning: bool
    coupling_value: float
    threshold: float
    message: str


# ============================================================================
# CORE VALIDATION FUNCTIONS
# ============================================================================

def validate_coupling(g_eff: float, 
                      name: str = "g_eff",
                      threshold: float = G_EFF_THRESHOLD,
                      warn_threshold: float = G_EFF_WARNING) -> NumericalValidation:
    """
    Validate that effective coupling is numerically meaningful.
    
    Args:
        g_eff: Effective coupling constant (Joules)
        name: Name of the coupling for error messages
        threshold: Hard threshold for validity
        warn_threshold: Soft threshold for warnings
        
    Returns:
        NumericalValidation object with status and message
        
    Example:
        >>> g0 = 1e-121  # From LQG calculation
        >>> result = validate_coupling(g0, name="g₀")
        >>> if not result.is_valid:
        ...     raise ValueError(result.message)
    """
    abs_g = abs(g_eff)
    
    # Hard failure: below numerical stability threshold
    if abs_g < threshold:
        return NumericalValidation(
            is_valid=False,
            is_warning=False,
            coupling_value=abs_g,
            threshold=threshold,
            message=f"NUMERICAL INSTABILITY: {name} = {abs_g:.3e} J is below "
                   f"threshold {threshold:.1e} J. Results are not physically meaningful. "
                   f"Matrix elements will be indistinguishable from zero."
        )
    
    # Warning: between threshold and warning level
    if abs_g < warn_threshold:
        return NumericalValidation(
            is_valid=True,
            is_warning=True,
            coupling_value=abs_g,
            threshold=warn_threshold,
            message=f"WARNING: {name} = {abs_g:.3e} J is very weak (below {warn_threshold:.1e} J). "
                   f"Results may have large numerical uncertainties. Verify with higher precision."
        )
    
    # All good
    return NumericalValidation(
        is_valid=True,
        is_warning=False,
        coupling_value=abs_g,
        threshold=threshold,
        message=f"OK: {name} = {abs_g:.3e} J is numerically stable."
    )


def validate_hamiltonian(H: np.ndarray,
                        H_int: Optional[np.ndarray] = None,
                        check_hermitian: bool = True) -> NumericalValidation:
    """
    Validate Hamiltonian matrix for numerical stability.
    
    Args:
        H: Total Hamiltonian matrix
        H_int: Interaction Hamiltonian (optional, for perturbative check)
        check_hermitian: Whether to verify Hermiticity
        
    Returns:
        NumericalValidation object
        
    Checks:
        1. Off-diagonal elements above threshold (actual coupling)
        2. Perturbative regime if H_int provided
        3. Hermiticity (for Hermitian systems)
    """
    # Check off-diagonal elements
    if H.shape[0] < 2:
        return NumericalValidation(
            is_valid=False,
            is_warning=False,
            coupling_value=0.0,
            threshold=MATRIX_ELEMENT_THRESHOLD,
            message="Hamiltonian must be at least 2×2 for coupling analysis."
        )
    
    # Extract off-diagonal (coupling strength)
    off_diag = np.abs(H[0, 1])
    diag_scale = np.max(np.abs(np.diag(H)))
    
    # Check if off-diagonal is numerically zero
    if off_diag < MATRIX_ELEMENT_THRESHOLD:
        return NumericalValidation(
            is_valid=False,
            is_warning=False,
            coupling_value=off_diag,
            threshold=MATRIX_ELEMENT_THRESHOLD,
            message=f"COUPLING TOO WEAK: Off-diagonal H[0,1] = {off_diag:.3e} J is below "
                   f"threshold {MATRIX_ELEMENT_THRESHOLD:.1e} J. System is effectively diagonal. "
                   f"No actual coupling between states!"
        )
    
    # Check perturbative regime (if interaction provided)
    if H_int is not None:
        int_scale = np.max(np.abs(H_int))
        ratio = int_scale / diag_scale if diag_scale > 0 else np.inf
        
        if ratio > PERTURBATIVE_THRESHOLD:
            return NumericalValidation(
                is_valid=False,
                is_warning=True,
                coupling_value=ratio,
                threshold=PERTURBATIVE_THRESHOLD,
                message=f"PERTURBATIVE VIOLATION: |H_int|/|H_0| = {ratio:.3e} > {PERTURBATIVE_THRESHOLD}. "
                       f"System is in strong-coupling regime. Perturbation theory invalid."
            )
    
    # Check Hermiticity (for closed systems)
    if check_hermitian:
        hermiticity_error = np.max(np.abs(H - H.conj().T))
        if hermiticity_error > 1e-10 * diag_scale:
            return NumericalValidation(
                is_valid=False,
                is_warning=True,
                coupling_value=hermiticity_error,
                threshold=1e-10,
                message=f"NON-HERMITIAN: max|H - H†| = {hermiticity_error:.3e}. "
                       f"For closed systems, Hamiltonian should be Hermitian. "
                       f"If using gain/loss, set check_hermitian=False."
            )
    
    return NumericalValidation(
        is_valid=True,
        is_warning=False,
        coupling_value=off_diag,
        threshold=MATRIX_ELEMENT_THRESHOLD,
        message=f"OK: Hamiltonian numerically stable with coupling {off_diag:.3e} J."
    )


def validate_purcell_scan(F_p: float, g0: float) -> NumericalValidation:
    """
    Validate that Purcell enhancement produces meaningful coupling.
    
    Args:
        F_p: Purcell factor (dimensionless)
        g0: Bare coupling (Joules)
        
    Returns:
        NumericalValidation for effective coupling g_eff = √F_p × g0
    """
    g_eff = np.sqrt(F_p) * abs(g0)
    
    result = validate_coupling(g_eff, name=f"g_eff (F_p={F_p:.1e})")
    
    if not result.is_valid:
        # Add Purcell-specific guidance
        min_Fp = (G_EFF_THRESHOLD / abs(g0))**2
        result.message += f"\n\nRequired minimum: F_p > {min_Fp:.2e} for numerical stability."
        
        if min_Fp > 1e12:
            result.message += "\n⚠️  This Purcell factor is BEYOND current technology limits!"
    
    return result


def check_growth_rate_independence(results: list, 
                                   param_name: str,
                                   tolerance: float = 1e-6) -> Tuple[bool, str]:
    """
    Check if growth rate is artificially independent of a parameter.
    
    This detects artifacts like Phase B where growth rate was identical
    for all drive frequencies because coupling was numerically zero.
    
    Args:
        results: List of (parameter_value, growth_rate) tuples
        param_name: Name of parameter being varied
        tolerance: Relative tolerance for "identical"
        
    Returns:
        (is_suspicious, message)
        
    Example:
        >>> # Phase B artifact: all multi-tone results identical
        >>> results = [(1, 6.29e-11), (2, 6.29e-11), (3, 6.29e-11)]
        >>> is_bad, msg = check_growth_rate_independence(results, "num_tones")
        >>> print(msg)  # "WARNING: Growth rate is suspiciously constant..."
    """
    if len(results) < 3:
        return False, "Not enough data points to check independence."
    
    growth_rates = [r[1] for r in results]
    mean_rate = np.mean(growth_rates)
    
    if mean_rate == 0:
        return True, f"ARTIFACT DETECTED: All growth rates are exactly zero. No physics!"
    
    # Check if all values are within tolerance of mean
    rel_std = np.std(growth_rates) / mean_rate if mean_rate != 0 else 0
    
    if rel_std < tolerance:
        return True, (
            f"ARTIFACT SUSPECTED: Growth rate is suspiciously constant across {param_name}.\n"
            f"  All values within {rel_std:.2e} relative std of mean {mean_rate:.3e}.\n"
            f"  This suggests parameter has no effect (likely because coupling is numerically zero).\n"
            f"  Check that coupling constants are above {G_EFF_THRESHOLD:.1e} J!"
        )
    
    return False, f"OK: Growth rate varies with {param_name} (rel_std = {rel_std:.3e})."


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def enforce_coupling_threshold(g_eff: float, 
                              name: str = "g_eff",
                              raise_on_fail: bool = True) -> float:
    """
    Enforce coupling threshold, raising exception or returning corrected value.
    
    Args:
        g_eff: Effective coupling
        name: Parameter name
        raise_on_fail: Whether to raise exception (True) or return corrected (False)
        
    Returns:
        Validated coupling (same or corrected)
        
    Raises:
        ValueError: If coupling below threshold and raise_on_fail=True
    """
    result = validate_coupling(g_eff, name)
    
    if not result.is_valid:
        if raise_on_fail:
            raise ValueError(result.message)
        else:
            warnings.warn(result.message + f"\nSetting {name} = {G_EFF_THRESHOLD:.1e} J")
            return G_EFF_THRESHOLD
    
    if result.is_warning:
        warnings.warn(result.message)
    
    return g_eff


def safe_divide(numerator: float, denominator: float, 
                default: float = np.inf) -> float:
    """
    Safe division with default for zero denominator.
    
    Useful for computing timescales: t = target / rate
    where rate might be zero.
    """
    if abs(denominator) < MACHINE_EPSILON:
        return default
    return numerator / denominator


def format_validation_report(validation: NumericalValidation) -> str:
    """
    Format validation result as colored terminal output.
    """
    if not validation.is_valid:
        marker = "❌ FAIL"
        color = "\033[91m"  # Red
    elif validation.is_warning:
        marker = "⚠️  WARN"
        color = "\033[93m"  # Yellow
    else:
        marker = "✅ PASS"
        color = "\033[92m"  # Green
    
    reset = "\033[0m"
    
    return f"{color}{marker}{reset}: {validation.message}"


# ============================================================================
# UNIT TESTS (Run with: python -m pytest numerical_guardrails.py)
# ============================================================================

def test_validate_coupling_below_threshold():
    """Test that very weak coupling is flagged."""
    g0_lqg = 3.96e-121  # Phase B value
    result = validate_coupling(g0_lqg, "g₀_LQG")
    assert not result.is_valid
    assert "NUMERICAL INSTABILITY" in result.message


def test_validate_coupling_warning_zone():
    """Test that weak-but-stable coupling triggers warning."""
    g0 = 1e-45  # Between threshold (1e-50) and warning (1e-40)
    result = validate_coupling(g0)
    assert result.is_valid
    assert result.is_warning


def test_validate_coupling_ok():
    """Test that strong coupling passes."""
    g0 = 1e-20
    result = validate_coupling(g0)
    assert result.is_valid
    assert not result.is_warning


def test_validate_hamiltonian_diagonal():
    """Test that effectively diagonal Hamiltonian is flagged."""
    # Diagonal Hamiltonian (no coupling)
    H = np.array([[1e-16, 1e-121],  # Off-diagonal below threshold
                  [1e-121, -1e-16]])
    result = validate_hamiltonian(H)
    assert not result.is_valid
    assert "COUPLING TOO WEAK" in result.message


def test_purcell_enhancement():
    """Test Purcell factor validation."""
    g0_lqg = 3.96e-121
    
    # With realistic F_p = 1e6 (cavity QED)
    result_realistic = validate_purcell_scan(1e6, g0_lqg)
    assert not result_realistic.is_valid  # Still too weak!
    
    # Need F_p ~ 10^141 for stability
    result_extreme = validate_purcell_scan(1e141, g0_lqg)
    assert result_extreme.is_valid


def test_growth_rate_independence():
    """Test detection of suspicious parameter independence."""
    # Phase B artifact: all multi-tone results identical
    results = [
        ("single", 6.291382e-11),
        ("dual", 6.291382e-11),
        ("tri", 6.291382e-11),
        ("chirp", 6.291382e-11),
    ]
    
    is_bad, msg = check_growth_rate_independence(results, "drive_type")
    assert is_bad
    assert "ARTIFACT SUSPECTED" in msg


if __name__ == "__main__":
    print("=" * 80)
    print("NUMERICAL GUARDRAILS - UNIT TESTS")
    print("=" * 80)
    
    # Run all tests
    test_validate_coupling_below_threshold()
    print("✅ Test 1: Weak coupling detection")
    
    test_validate_coupling_warning_zone()
    print("✅ Test 2: Warning zone detection")
    
    test_validate_coupling_ok()
    print("✅ Test 3: Strong coupling passes")
    
    test_validate_hamiltonian_diagonal()
    print("✅ Test 4: Diagonal Hamiltonian detection")
    
    test_purcell_enhancement()
    print("✅ Test 5: Purcell enhancement validation")
    
    test_growth_rate_independence()
    print("✅ Test 6: Growth rate independence detection")
    
    print("\n" + "=" * 80)
    print("ALL TESTS PASSED - GUARDRAILS ACTIVE ✅")
    print("=" * 80)
