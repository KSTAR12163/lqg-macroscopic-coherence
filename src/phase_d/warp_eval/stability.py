"""
Warp Bubble Stability Analysis

Perturbation analysis and stability diagnostics.
"""

from typing import Dict, Tuple
import numpy as np


def analyze_perturbation_spectrum(
    metric_components: Dict[str, np.ndarray],
    portal_boost: float = 1.0
) -> Tuple[bool, Dict]:
    """
    Analyze perturbation modes around warp bubble.
    
    Linear stability requires all eigenvalues of perturbation operator
    to have Re(λ) ≤ 0 (no exponential growth).
    
    Args:
        metric_components: Metric tensor components
        portal_boost: Coupling enhancement factor
        
    Returns:
        (stable, diagnostics)
    """
    # TODO: Proper perturbation theory
    # For now, placeholder eigenvalue analysis
    
    # Simulate eigenvalues (in reality: from linearized Einstein equations)
    n_modes = 10
    eigenvalues_real = np.random.uniform(-0.1, 0.05, n_modes)  # Some unstable modes
    eigenvalues_imag = np.random.uniform(-1, 1, n_modes)
    
    # Portal boost might affect growth rates (speculation)
    eigenvalues_real_modified = eigenvalues_real / np.sqrt(portal_boost)
    
    # Check for instabilities
    max_growth_rate = np.max(eigenvalues_real_modified)
    unstable_modes = np.sum(eigenvalues_real_modified > 1e-6)
    
    stable = max_growth_rate <= 1e-6  # s⁻¹ threshold
    
    return stable, {
        'n_modes': n_modes,
        'max_growth_rate': float(max_growth_rate),
        'unstable_modes': int(unstable_modes),
        'eigenvalues_real': eigenvalues_real_modified.tolist(),
        'eigenvalues_imag': eigenvalues_imag.tolist(),
        'stable': stable,
        'portal_boost_applied': portal_boost
    }


def check_causality_violations(
    metric_components: Dict[str, np.ndarray],
    velocity: float
) -> Tuple[bool, Dict]:
    """
    Check for closed timelike curves and causality violations.
    
    Args:
        metric_components: Metric tensor
        velocity: Bubble velocity (units of c)
        
    Returns:
        (no_violations, diagnostics)
    """
    # Placeholder: Check if any region has dt² coefficient negative
    # (signature violation)
    
    # In Alcubierre: g_tt can become negative in certain regions
    g_tt_min = -1.0 if velocity > 1.0 else 1.0  # Schematic
    
    has_ctc = g_tt_min < 0
    
    return not has_ctc, {
        'velocity_c': velocity,
        'g_tt_min': g_tt_min,
        'closed_timelike_curves': has_ctc,
        'causality_preserved': not has_ctc
    }


def evaluate_stability(
    candidate: Dict,
    portal_boost: float = 1.0
) -> Dict:
    """
    Full stability evaluation.
    
    Args:
        candidate: Bubble specification
        portal_boost: Portal coupling enhancement
        
    Returns:
        Stability diagnostics
    """
    # Placeholder metric
    metric_components = {
        'g_tt': np.ones(10),
        'g_rr': np.ones(10),
        'g_thth': np.ones(10),
        'g_phph': np.ones(10)
    }
    
    velocity = candidate.get('velocity', 1.0)
    
    # Perturbation analysis
    stable, pert_diag = analyze_perturbation_spectrum(metric_components, portal_boost)
    
    # Causality check
    causal, caus_diag = check_causality_violations(metric_components, velocity)
    
    return {
        'perturbation_stability': pert_diag,
        'causality': caus_diag,
        'overall_stable': stable and causal
    }
