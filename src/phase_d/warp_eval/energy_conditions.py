"""
Warp Bubble Energy Conditions

Evaluate energy conditions (NEC, WEC, ANEC, QI, QNEC) for warp bubble candidates.
"""

from typing import Dict, Tuple
import numpy as np


def check_null_energy_condition(
    T_00: float,  # Energy density
    T_ii: float,  # Pressure (assume isotropic for now)
    location: str = "unknown"
) -> Tuple[bool, Dict]:
    """
    Check Null Energy Condition: T_μν k^μ k^ν ≥ 0 for null vectors k.
    
    For perfect fluid: NEC ⇔ ρ + p ≥ 0
    
    Args:
        T_00: Energy density component (J/m³)
        T_ii: Pressure component (Pa = J/m³)
        location: Description of where in spacetime
        
    Returns:
        (passed, diagnostics)
    """
    rho_plus_p = T_00 + T_ii
    
    passed = rho_plus_p >= 0
    violation = abs(rho_plus_p) if not passed else 0.0
    
    return passed, {
        'condition': 'NEC',
        'formula': 'ρ + p ≥ 0',
        'rho': T_00,
        'p': T_ii,
        'rho_plus_p': rho_plus_p,
        'passed': passed,
        'violation_magnitude': violation,
        'location': location
    }


def check_weak_energy_condition(
    T_00: float,
    T_ii: float,
    location: str = "unknown"
) -> Tuple[bool, Dict]:
    """
    Check Weak Energy Condition: ρ ≥ 0 and ρ + p ≥ 0.
    
    Args:
        T_00: Energy density (J/m³)
        T_ii: Pressure (Pa)
        location: Description
        
    Returns:
        (passed, diagnostics)
    """
    rho_positive = T_00 >= 0
    rho_plus_p = T_00 + T_ii
    rho_plus_p_positive = rho_plus_p >= 0
    
    passed = rho_positive and rho_plus_p_positive
    
    violations = []
    if not rho_positive:
        violations.append(f"ρ = {T_00:.4e} < 0")
    if not rho_plus_p_positive:
        violations.append(f"ρ + p = {rho_plus_p:.4e} < 0")
    
    return passed, {
        'condition': 'WEC',
        'formula': 'ρ ≥ 0 AND ρ + p ≥ 0',
        'rho': T_00,
        'p': T_ii,
        'rho_positive': rho_positive,
        'rho_plus_p': rho_plus_p,
        'rho_plus_p_positive': rho_plus_p_positive,
        'passed': passed,
        'violations': violations,
        'location': location
    }


def check_averaged_null_energy_condition(
    T_profile: np.ndarray,  # Stress-energy along null geodesic
    geodesic_affine: np.ndarray,  # Affine parameter values
    location: str = "unknown"
) -> Tuple[bool, Dict]:
    """
    Check Averaged Null Energy Condition: ∫ T_μν k^μ k^ν dλ ≥ 0.
    
    ANEC is critical for traversable wormholes and warp drives.
    
    Args:
        T_profile: T_μν k^μ k^ν along geodesic
        geodesic_affine: Affine parameter λ values
        location: Description
        
    Returns:
        (passed, diagnostics)
    """
    # Integrate using trapezoidal rule
    integral = np.trapz(T_profile, geodesic_affine)
    
    passed = integral >= 0
    violation = abs(integral) if not passed else 0.0
    
    return passed, {
        'condition': 'ANEC',
        'formula': '∫ T_μν k^μ k^ν dλ ≥ 0',
        'integral': integral,
        'passed': passed,
        'violation_magnitude': violation,
        'geodesic_length': len(T_profile),
        'location': location
    }


def check_quantum_inequality(
    T_expectation: float,  # <T_μν> quantum expectation value
    tau: float,  # Sampling timescale
    hbar: float = 1.054571817e-34,  # J·s
    location: str = "unknown"
) -> Tuple[bool, Dict]:
    """
    Check Quantum Inequality: <T_μν> ≥ -ℏ/(cτ)⁴ (schematic bound).
    
    Quantum effects allow temporary negative energy but constrained.
    
    Args:
        T_expectation: Quantum expectation value of stress-energy
        tau: Sampling timescale (s)
        hbar: Reduced Planck constant
        location: Description
        
    Returns:
        (passed, diagnostics)
    """
    c = 2.99792458e8  # m/s
    
    # Quantum bound (schematic, exact bound geometry-dependent)
    quantum_bound = -hbar / (c * tau)**4
    
    passed = T_expectation >= quantum_bound
    violation = abs(T_expectation - quantum_bound) if not passed else 0.0
    
    return passed, {
        'condition': 'QI',
        'formula': '<T_μν> ≥ -ℏ/(cτ)⁴',
        'T_expectation': T_expectation,
        'tau': tau,
        'quantum_bound': quantum_bound,
        'passed': passed,
        'violation_magnitude': violation,
        'location': location
    }


def check_quantum_null_energy_condition(
    T_expectation: float,
    second_derivative_metric: float,  # R_μν k^μ k^ν contribution
    location: str = "unknown"
) -> Tuple[bool, Dict]:
    """
    Check Quantum Null Energy Condition: <T_μν> k^μ k^ν ≥ -(1/4π) □R_μν k^μ k^ν.
    
    QNEC is a quantum-corrected version of NEC.
    
    Args:
        T_expectation: <T_μν k^μ k^ν>
        second_derivative_metric: Curvature term
        location: Description
        
    Returns:
        (passed, diagnostics)
    """
    bound = -(1.0 / (4 * np.pi)) * second_derivative_metric
    
    passed = T_expectation >= bound
    violation = abs(T_expectation - bound) if not passed else 0.0
    
    return passed, {
        'condition': 'QNEC',
        'formula': '<T_μν> k^μ k^ν ≥ -(1/4π) □R_μν k^μ k^ν',
        'T_expectation': T_expectation,
        'curvature_term': second_derivative_metric,
        'bound': bound,
        'passed': passed,
        'violation_magnitude': violation,
        'location': location
    }


def evaluate_all_energy_conditions(
    candidate: Dict,
    portal_boost: float = 1.0
) -> Dict:
    """
    Evaluate all energy conditions for a warp bubble candidate.
    
    Args:
        candidate: Bubble specification (metric, shape, velocity)
        portal_boost: Multiplicative factor from portal coupling (1 + η_portal)
        
    Returns:
        Dictionary with all condition results
    """
    # TODO: Extract stress-energy from candidate metric
    # For now, use placeholder values
    
    # Placeholder: Alcubierre-style exotic energy
    T_00_exotic = -1e10  # J/m³ (negative energy density)
    T_ii_exotic = 1e10  # Pa (positive pressure)
    
    # Apply portal boost (QUESTION: does this help or hurt?)
    T_00_modified = T_00_exotic / portal_boost
    T_ii_modified = T_ii_exotic / portal_boost
    
    results = {}
    
    # Classical conditions
    nec_passed, nec_diag = check_null_energy_condition(T_00_modified, T_ii_modified, "bubble_wall")
    results['NEC'] = nec_diag
    
    wec_passed, wec_diag = check_weak_energy_condition(T_00_modified, T_ii_modified, "bubble_wall")
    results['WEC'] = wec_diag
    
    # ANEC (needs geodesic integration - placeholder)
    geodesic_affine = np.linspace(0, 10, 100)
    T_profile = T_00_modified * np.exp(-(geodesic_affine - 5)**2 / 2)  # Gaussian profile
    anec_passed, anec_diag = check_averaged_null_energy_condition(T_profile, geodesic_affine, "null_geodesic")
    results['ANEC'] = anec_diag
    
    # Quantum conditions (placeholders)
    tau_sampling = 1e-15  # s (femtosecond timescale)
    qi_passed, qi_diag = check_quantum_inequality(T_00_modified, tau_sampling, location="bubble_wall")
    results['QI'] = qi_diag
    
    second_deriv_R = 1e5  # Placeholder curvature
    qnec_passed, qnec_diag = check_quantum_null_energy_condition(T_00_modified, second_deriv_R, "bubble_wall")
    results['QNEC'] = qnec_diag
    
    # Overall assessment
    all_passed = all(results[key]['passed'] for key in results)
    classical_passed = results['NEC']['passed'] and results['WEC']['passed']
    quantum_passed = results['QI']['passed'] and results['QNEC']['passed']
    
    results['summary'] = {
        'all_conditions_passed': all_passed,
        'classical_passed': classical_passed,
        'quantum_passed': quantum_passed,
        'portal_boost_applied': portal_boost,
        'exotic_energy_reduction': (1.0 - 1.0/portal_boost) * 100 if portal_boost > 1 else 0.0  # percent
    }
    
    return results
