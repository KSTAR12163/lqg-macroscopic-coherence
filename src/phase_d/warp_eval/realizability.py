"""
Warp Bubble Realizability Assessment

Check if required fields/matter distributions are physically achievable.
"""

from typing import Dict, Tuple
import numpy as np


def estimate_exotic_energy_requirement(
    candidate: Dict,
    portal_boost: float = 1.0
) -> Tuple[float, Dict]:
    """
    Estimate total exotic (negative) energy required.
    
    Args:
        candidate: Bubble specification
        portal_boost: Portal coupling factor
        
    Returns:
        (E_exotic_J, diagnostics)
    """
    # Extract parameters
    radius = candidate.get('bubble_radius', 100.0)  # m
    wall_thickness = candidate.get('wall_thickness', 10.0)  # m
    velocity = candidate.get('velocity', 1.0)  # units of c
    
    # Alcubierre-style scaling: E_exotic ∼ v² R² / σ
    # where σ = wall thickness
    
    c = 2.99792458e8  # m/s
    v_SI = velocity * c
    
    # Negative energy density (very rough estimate)
    rho_exotic = -1e10 * (velocity**2)  # J/m³
    
    # Volume estimate: shell of radius R, thickness σ
    V_shell = 4 * np.pi * radius**2 * wall_thickness
    
    # Total exotic energy (before portal correction)
    E_exotic_baseline = abs(rho_exotic) * V_shell
    
    # Portal boost HYPOTHESIS: reduces exotic energy requirement
    # (Unclear if this is physical - needs proper field theory)
    E_exotic_modified = E_exotic_baseline / portal_boost
    
    # Compare to mass-energy scales
    m_sun = 1.989e30  # kg
    E_sun = m_sun * c**2  # J
    
    return E_exotic_modified, {
        'radius_m': radius,
        'wall_thickness_m': wall_thickness,
        'velocity_c': velocity,
        'shell_volume_m3': V_shell,
        'rho_exotic_J_m3': rho_exotic,
        'E_exotic_baseline_J': E_exotic_baseline,
        'E_exotic_modified_J': E_exotic_modified,
        'portal_boost': portal_boost,
        'reduction_percent': (1.0 - 1.0/portal_boost) * 100 if portal_boost > 1 else 0.0,
        'vs_sun_mass_energy': E_exotic_modified / E_sun,
        'achievable': E_exotic_modified < 1e45  # J (arbitrary cutoff)
    }


def estimate_power_requirement(
    candidate: Dict,
    E_exotic: float,
    formation_time: float = 1.0  # s
) -> Tuple[float, Dict]:
    """
    Estimate power needed to establish bubble.
    
    Args:
        candidate: Bubble spec
        E_exotic: Exotic energy requirement (J)
        formation_time: Time to form bubble (s)
        
    Returns:
        (P_watts, diagnostics)
    """
    P = E_exotic / formation_time
    
    # Compare to global power production (~2e13 W)
    P_global = 2e13  # W
    
    return P, {
        'E_exotic_J': E_exotic,
        'formation_time_s': formation_time,
        'power_W': P,
        'vs_global_power': P / P_global,
        'achievable': P < 1e30  # W (arbitrary cutoff)
    }


def check_field_strength_requirements(
    candidate: Dict,
    portal_boost: float = 1.0
) -> Dict:
    """
    Check if required field strengths are achievable.
    
    Args:
        candidate: Bubble spec
        portal_boost: Portal enhancement
        
    Returns:
        Field strength diagnostics
    """
    # TODO: Map stress-energy to required B, E fields
    # For now, heuristic estimates
    
    velocity = candidate.get('velocity', 1.0)
    radius = candidate.get('bubble_radius', 100.0)
    
    # Rough scaling: B ∼ sqrt(ρ_exotic)
    B_required = 1e6 * velocity  # Tesla (placeholder)
    E_required = 1e12 * velocity  # V/m (placeholder)
    
    # Portal boost might reduce requirements (speculative)
    B_modified = B_required / np.sqrt(portal_boost)
    E_modified = E_required / np.sqrt(portal_boost)
    
    # Realistic limits
    B_max_lab = 20.0  # T (superconducting magnets)
    E_max_lab = 1e8  # V/m (dielectric breakdown)
    
    B_achievable = B_modified <= B_max_lab
    E_achievable = E_modified <= E_max_lab
    
    return {
        'B_field_required_T': B_modified,
        'E_field_required_V_m': E_modified,
        'B_achievable': B_achievable,
        'E_achievable': E_achievable,
        'both_achievable': B_achievable and E_achievable,
        'B_max_lab_T': B_max_lab,
        'E_max_lab_V_m': E_max_lab,
        'portal_boost': portal_boost
    }


def evaluate_realizability(
    candidate: Dict,
    portal_boost: float = 1.0
) -> Dict:
    """
    Full realizability assessment.
    
    Args:
        candidate: Bubble specification
        portal_boost: Portal coupling enhancement
        
    Returns:
        Realizability diagnostics
    """
    # Energy requirement
    E_exotic, energy_diag = estimate_exotic_energy_requirement(candidate, portal_boost)
    
    # Power requirement
    P, power_diag = estimate_power_requirement(candidate, E_exotic)
    
    # Field strengths
    field_diag = check_field_strength_requirements(candidate, portal_boost)
    
    # Overall realizability
    realizable = (
        energy_diag['achievable'] and
        power_diag['achievable'] and
        field_diag['both_achievable']
    )
    
    return {
        'energy_requirement': energy_diag,
        'power_requirement': power_diag,
        'field_requirements': field_diag,
        'realizable': realizable,
        'limiting_factor': _identify_limiting_factor(energy_diag, power_diag, field_diag)
    }


def _identify_limiting_factor(energy_diag: Dict, power_diag: Dict, field_diag: Dict) -> str:
    """Identify which requirement is most constraining."""
    
    if not energy_diag['achievable']:
        return f"Energy requirement: {energy_diag['E_exotic_modified_J']:.2e} J (too large)"
    
    if not power_diag['achievable']:
        return f"Power requirement: {power_diag['power_W']:.2e} W (too large)"
    
    if not field_diag['both_achievable']:
        if not field_diag['B_achievable']:
            return f"B-field: {field_diag['B_field_required_T']:.2e} T (exceeds {field_diag['B_max_lab_T']} T)"
        if not field_diag['E_achievable']:
            return f"E-field: {field_diag['E_field_required_V_m']:.2e} V/m (exceeds {field_diag['E_max_lab_V_m']:.2e} V/m)"
    
    return "All requirements achievable"
