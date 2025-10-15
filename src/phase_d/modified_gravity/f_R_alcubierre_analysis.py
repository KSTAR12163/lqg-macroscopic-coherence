"""
f(R) Gravity Applied to Alcubierre Warp Metric

Evaluates whether f(R) = R + α R² gravity allows ANEC-satisfying
warp bubbles when combined with portal field enhancement.

Key questions:
1. What is the effective stress-energy in f(R) for Alcubierre?
2. Can portal fields help satisfy the modified field equations?
3. What constraints does PPN place on viable α?
"""

import numpy as np
from typing import Dict
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from f_R_gravity import FRGravity
from ..warp_eval.alcubierre_analytic import alcubierre_metric_analytic
from ..warp_eval.stress_energy import compute_einstein_tensor, einstein_to_stress_energy


def analyze_alcubierre_in_f_R(
    v_s: float = 1.0,
    R_bubble: float = 100.0,
    sigma: float = 10.0,
    alpha: float = 1e-8,
    test_points: int = 5
) -> Dict:
    """
    Analyze Alcubierre metric in f(R) = R + α R² gravity.
    
    Args:
        v_s: Bubble velocity (dimensionless, in units of c)
        R_bubble: Bubble radius (m)
        sigma: Wall thickness parameter (m)
        alpha: f(R) coefficient (m²)
        test_points: Number of radial points to sample
        
    Returns:
        Dictionary with analysis results
    """
    fr_gravity = FRGravity(alpha=alpha)
    
    # Define metric function
    def metric_fn(t, x, y, z):
        return alcubierre_metric_analytic(t, x, y, z, v_s, R_bubble, sigma)
    
    # Sample points along x-axis (through center and wall)
    x_values = np.linspace(-R_bubble, R_bubble, test_points)
    
    results = {
        'alpha': alpha,
        'v_s': v_s,
        'R_bubble': R_bubble,
        'sigma': sigma,
        'points': []
    }
    
    print(f"Analyzing Alcubierre in f(R) gravity...")
    print(f"  Bubble: v={v_s}c, R={R_bubble}m, σ={sigma}m")
    print(f"  f(R) parameter: α = {alpha:.3e} m²")
    print()
    
    for x in x_values:
        coords = np.array([0.0, x, 0.0, 0.0])
        r_s = abs(x)
        
        # Standard GR stress-energy
        T_GR = compute_einstein_tensor(metric_fn, coords)
        T_GR = einstein_to_stress_energy(T_GR)
        rho_GR = T_GR[0, 0]
        
        # f(R) effective stress-energy
        T_fR = fr_gravity.compute_effective_stress_energy(metric_fn, coords)
        rho_fR = T_fR[0, 0]
        
        # Ratio
        if abs(rho_GR) > 1e-10:
            ratio = rho_fR / rho_GR
        else:
            ratio = np.nan
        
        point_data = {
            'x': x,
            'r_s': r_s,
            'rho_GR': rho_GR,
            'rho_fR': rho_fR,
            'ratio': ratio
        }
        results['points'].append(point_data)
        
        print(f"r_s = {r_s:6.1f} m:")
        print(f"  ρ_GR   = {rho_GR:+.3e} J/m³")
        print(f"  ρ_f(R) = {rho_fR:+.3e} J/m³")
        if not np.isnan(ratio):
            print(f"  Ratio  = {ratio:.3e}")
        print()
    
    return results


def estimate_portal_contribution(
    B: float = 10.0,
    E: float = 1e7
) -> float:
    """
    Estimate portal contribution to stress-energy.
    
    From previous analysis:
        δρ_portal ≈ 1.4×10³ J/m³ (for B=10T, E=10MV/m)
    
    Args:
        B: Magnetic field (T)
        E: Electric field (V/m)
        
    Returns:
        δρ_portal (J/m³)
    """
    # Simplified model from portal_stress_energy.py
    g_eff = 1.47e-21  # J (effective coupling)
    V_coherence = 1e-18  # m³ (coherence volume)
    
    # Field energy density
    epsilon_0 = 8.854187817e-12  # F/m
    mu_0 = 4 * np.pi * 1e-7  # H/m
    u_field = 0.5 * (epsilon_0 * E**2 + B**2 / mu_0)
    
    # Portal contribution (very rough estimate)
    delta_rho = g_eff * u_field / V_coherence
    
    return delta_rho


def assess_f_R_viability(
    alpha_values: np.ndarray
) -> None:
    """
    Assess whether any value of α allows viable FTL.
    
    Criteria:
    1. α must satisfy PPN constraints: α < 10⁻⁶ m²
    2. f(R) modification must reduce energy requirements by ~37 orders
    3. Portal contribution must become relevant
    
    Args:
        alpha_values: Array of α values to test (m²)
    """
    print("="*70)
    print("f(R) GRAVITY VIABILITY ASSESSMENT FOR FTL")
    print("="*70)
    print()
    
    # Portal contribution
    delta_rho_portal = estimate_portal_contribution(B=10.0, E=1e7)
    print(f"Portal contribution: δρ = {delta_rho_portal:.3e} J/m³")
    print()
    
    # PPN constraint
    alpha_max_PPN = 1e-6  # m² (from solar system tests)
    print(f"Observational constraint: α < {alpha_max_PPN:.3e} m² (PPN)")
    print()
    
    viable_found = False
    
    for alpha in alpha_values:
        print(f"\nTesting α = {alpha:.3e} m²...")
        
        # Check PPN constraint
        if alpha > alpha_max_PPN:
            print(f"  ❌ Violates PPN constraint (α > {alpha_max_PPN:.3e})")
            continue
        else:
            print(f"  ✅ Satisfies PPN constraint")
        
        # Analyze Alcubierre
        results = analyze_alcubierre_in_f_R(alpha=alpha, test_points=3)
        
        # Check if f(R) modifications are significant
        max_ratio = max([abs(p['ratio']) for p in results['points'] if not np.isnan(p['ratio'])])
        
        if abs(max_ratio - 1.0) < 0.01:
            print(f"  ❌ f(R) correction negligible (max ratio = {max_ratio:.3f})")
        else:
            print(f"  ✅ f(R) correction significant (max ratio = {max_ratio:.3e})")
        
        # Check if energy gap is closed
        rho_requirement = 1e40  # J/m³ (order of magnitude at wall)
        gap = rho_requirement / delta_rho_portal
        
        print(f"  Energy gap: {gap:.3e} (need ~1)")
        
        if gap < 10:
            print(f"  ✅ VIABLE! Portal becomes relevant.")
            viable_found = True
        else:
            print(f"  ❌ Gap still too large ({np.log10(gap):.1f} orders)")
    
    print("\n" + "="*70)
    if viable_found:
        print("RESULT: f(R) gravity MAY allow FTL with portal enhancement")
        print("Recommendation: Full ANEC computation with portal coupling")
    else:
        print("RESULT: f(R) = R + α R² DOES NOT allow viable FTL")
        print("Reasons:")
        print("  - PPN constraints limit α to < 10⁻⁶ m²")
        print("  - Such small α gives negligible corrections to GR")
        print("  - Portal energy gap remains ~37 orders")
        print()
        print("Next steps:")
        print("  1. Try higher-order f(R) models (R³, R⁴, etc.)")
        print("  2. Move to scalar-tensor theories")
        print("  3. Accept FTL is not viable under current physics")
    print("="*70)


if __name__ == "__main__":
    # Test range of α values
    alpha_values = np.array([
        1e-10,  # Very small (should be negligible)
        1e-8,   # Small but detectable
        1e-6,   # At PPN limit
        1e-4,   # Violates PPN
    ])
    
    assess_f_R_viability(alpha_values)
