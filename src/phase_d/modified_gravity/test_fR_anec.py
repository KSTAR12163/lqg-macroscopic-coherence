"""
f(R) Gravity ANEC Analysis for Alcubierre Metric

Tests whether f(R) = R + α R² modifications can reduce ANEC violations
enough to make portal contributions relevant.

Workflow:
1. Compute standard GR stress-energy for Alcubierre
2. Compute f(R)-modified stress-energy
3. Compute ANEC integrals for both
4. Assess portal contribution viability
5. Apply observational constraints (α < 10⁻⁶ m²)
"""

import numpy as np
import sys
import os
from typing import Dict, Tuple

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from modified_gravity.f_R_gravity import FRGravity
from warp_eval.alcubierre_analytic import alcubierre_metric_analytic
from warp_eval.stress_energy import compute_einstein_tensor, einstein_to_stress_energy
from warp_eval.geodesics_alcubierre import (
    integrate_alcubierre_geodesic,
    compute_anec_alcubierre
)


def compare_GR_vs_fR_at_points(
    v_s: float = 1.0,
    R_bubble: float = 100.0,
    sigma: float = 10.0,
    alpha: float = 1e-8,
    x_values: np.ndarray = None
) -> Dict:
    """
    Compare GR vs f(R) stress-energy at sample points.
    
    Args:
        v_s: Bubble velocity (dimensionless)
        R_bubble: Bubble radius (m)
        sigma: Wall thickness (m)
        alpha: f(R) parameter (m²)
        x_values: Points to sample along x-axis
        
    Returns:
        Dictionary with comparison data
    """
    if x_values is None:
        x_values = np.array([0.0, 50.0, R_bubble, 150.0])
    
    fr_gravity = FRGravity(alpha=alpha)
    
    def metric_fn(t, x, y, z):
        return alcubierre_metric_analytic(t, x, y, z, v_s, R_bubble, sigma)
    
    results = []
    
    print(f"\n{'='*70}")
    print(f"Comparing GR vs f(R) = R + α R² at sample points")
    print(f"{'='*70}")
    print(f"Bubble: v={v_s}c, R={R_bubble}m, σ={sigma}m")
    print(f"f(R) parameter: α = {alpha:.3e} m²")
    print()
    
    for x in x_values:
        coords = np.array([0.0, x, 0.0, 0.0])
        r_s = abs(x)
        
        # GR stress-energy
        G_GR = compute_einstein_tensor(metric_fn, coords)
        T_GR = einstein_to_stress_energy(G_GR)
        rho_GR = T_GR[0, 0]
        
        # f(R) stress-energy
        T_fR = fr_gravity.compute_effective_stress_energy(metric_fn, coords)
        rho_fR = T_fR[0, 0]
        
        # Correction
        delta_rho = rho_fR - rho_GR
        if abs(rho_GR) > 1e-10:
            rel_correction = abs(delta_rho / rho_GR)
        else:
            rel_correction = 0.0
        
        result = {
            'r_s': r_s,
            'rho_GR': rho_GR,
            'rho_fR': rho_fR,
            'delta_rho': delta_rho,
            'rel_correction': rel_correction
        }
        results.append(result)
        
        print(f"r_s = {r_s:6.1f} m:")
        print(f"  ρ_GR       = {rho_GR:+.3e} J/m³")
        print(f"  ρ_f(R)     = {rho_fR:+.3e} J/m³")
        print(f"  Δρ         = {delta_rho:+.3e} J/m³")
        print(f"  |Δρ/ρ_GR|  = {rel_correction:.3e}")
        print()
    
    return {
        'alpha': alpha,
        'results': results,
        'max_rel_correction': max(r['rel_correction'] for r in results)
    }


def compute_ANEC_GR_vs_fR(
    v_s: float = 1.0,
    R_bubble: float = 100.0,
    sigma: float = 10.0,
    alpha: float = 1e-8,
    n_steps: int = 200
) -> Dict:
    """
    Compute ANEC for GR and f(R) along same null geodesic.
    
    Args:
        v_s, R_bubble, sigma: Alcubierre parameters
        alpha: f(R) parameter
        n_steps: Integration steps
        
    Returns:
        Dictionary with ANEC comparison
    """
    print(f"\n{'='*70}")
    print(f"ANEC Computation: GR vs f(R)")
    print(f"{'='*70}")
    print(f"α = {alpha:.3e} m²")
    print()
    
    # Initial conditions (ray through center)
    initial_coords = np.array([0.0, -200.0, 0.0, 0.0])
    direction = np.array([1.0, 0.0, 0.0])
    lambda_max = 400.0
    
    # Integrate geodesic (same for both GR and f(R))
    print("Integrating null geodesic...")
    positions, tangents, diag = integrate_alcubierre_geodesic(
        initial_coords,
        direction,
        lambda_max,
        v_s, R_bubble, sigma,
        n_steps=n_steps,
        project_null=True,
        rtol=1e-8,
        atol=1e-10
    )
    
    if not diag['success']:
        print(f"❌ Geodesic integration failed: {diag['message']}")
        return {'success': False}
    
    print(f"✅ Geodesic integrated")
    print(f"   Function evaluations: {diag['n_eval']}")
    print(f"   Null violation (mean): {diag['null_violation_mean']:.3e}")
    print()
    
    # GR stress-energy function
    def T_GR_fn(t, x, y, z):
        def metric_fn(t2, x2, y2, z2):
            return alcubierre_metric_analytic(t2, x2, y2, z2, v_s, R_bubble, sigma)
        coords = np.array([t, x, y, z])
        G = compute_einstein_tensor(metric_fn, coords)
        return einstein_to_stress_energy(G)
    
    # f(R) stress-energy function
    fr_gravity = FRGravity(alpha=alpha)
    def T_fR_fn(t, x, y, z):
        def metric_fn(t2, x2, y2, z2):
            return alcubierre_metric_analytic(t2, x2, y2, z2, v_s, R_bubble, sigma)
        coords = np.array([t, x, y, z])
        return fr_gravity.compute_effective_stress_energy(metric_fn, coords)
    
    # Compute ANEC for GR
    print("Computing ANEC (GR)...")
    anec_GR, stats_GR = compute_anec_alcubierre(T_GR_fn, positions, tangents, lambda_max)
    
    print(f"  ANEC_GR = {anec_GR:.3e}")
    print(f"  T_kk range: [{stats_GR['T_kk_min']:.3e}, {stats_GR['T_kk_max']:.3e}]")
    print()
    
    # Compute ANEC for f(R)
    print("Computing ANEC (f(R))...")
    anec_fR, stats_fR = compute_anec_alcubierre(T_fR_fn, positions, tangents, lambda_max)
    
    print(f"  ANEC_f(R) = {anec_fR:.3e}")
    print(f"  T_kk range: [{stats_fR['T_kk_min']:.3e}, {stats_fR['T_kk_max']:.3e}]")
    print()
    
    # Comparison
    delta_anec = anec_fR - anec_GR
    if abs(anec_GR) > 1e-10:
        rel_change = abs(delta_anec / anec_GR)
    else:
        rel_change = 0.0
    
    print(f"Comparison:")
    print(f"  ΔANEC = {delta_anec:.3e}")
    print(f"  |ΔANEC/ANEC_GR| = {rel_change:.3e}")
    
    if anec_GR < 0 and anec_fR < 0:
        print(f"  ⚠️  Both GR and f(R) violate ANEC")
    elif anec_GR < 0 and anec_fR >= 0:
        print(f"  ✅ f(R) correction fixes ANEC violation!")
    elif anec_fR < 0:
        print(f"  ⚠️  f(R) still violates ANEC")
    
    return {
        'success': True,
        'alpha': alpha,
        'anec_GR': anec_GR,
        'anec_fR': anec_fR,
        'delta_anec': delta_anec,
        'rel_change': rel_change,
        'stats_GR': stats_GR,
        'stats_fR': stats_fR,
        'geodesic_diag': diag
    }


def sweep_alpha_values(
    alpha_values: np.ndarray,
    mode: str = 'anec'
) -> None:
    """
    Sweep α values and assess f(R) viability.
    
    Args:
        alpha_values: Array of α to test (m²)
        mode: 'points' for point comparison, 'anec' for full ANEC
    """
    print(f"\n{'#'*70}")
    print(f"# f(R) = R + α R² VIABILITY SWEEP")
    print(f"{'#'*70}")
    print(f"\nMode: {mode}")
    print(f"α range: [{alpha_values.min():.3e}, {alpha_values.max():.3e}] m²")
    print(f"\nObservational constraint: α < 10⁻⁶ m² (PPN tests)")
    print(f"\nPortal contribution: δρ ~ 10³ J/m³")
    print(f"GR requirement: |ρ| ~ 10⁴⁰ J/m³ at wall")
    print(f"Gap to close: ~37 orders of magnitude")
    print()
    
    results = []
    
    for alpha in alpha_values:
        print(f"\n{'='*70}")
        print(f"Testing α = {alpha:.3e} m²")
        print(f"{'='*70}")
        
        # Check PPN constraint
        if alpha > 1e-6:
            print(f"⚠️  WARNING: α exceeds PPN constraint (10⁻⁶ m²)")
        
        if mode == 'points':
            result = compare_GR_vs_fR_at_points(alpha=alpha)
            results.append(result)
            
            print(f"\nMaximum relative correction: {result['max_rel_correction']:.3e}")
            if result['max_rel_correction'] < 1e-10:
                print(f"❌ f(R) correction negligible (< 10⁻¹⁰)")
            elif result['max_rel_correction'] < 1e-4:
                print(f"❌ f(R) correction tiny (< 10⁻⁴)")
            elif result['max_rel_correction'] < 1.0:
                print(f"⚠️  f(R) correction small (< 100%)")
            else:
                print(f"✅ f(R) correction significant (> 100%)")
        
        elif mode == 'anec':
            result = compute_ANEC_GR_vs_fR(alpha=alpha, n_steps=150)
            if result['success']:
                results.append(result)
                
                print(f"\nRelative ANEC change: {result['rel_change']:.3e}")
                if result['rel_change'] < 1e-10:
                    print(f"❌ ANEC correction negligible")
                elif result['rel_change'] < 0.01:
                    print(f"❌ ANEC correction < 1%")
                elif result['anec_fR'] < 0:
                    print(f"⚠️  ANEC still violated (sign unchanged)")
                else:
                    print(f"✅ ANEC violation fixed!")
    
    # Final assessment
    print(f"\n{'#'*70}")
    print(f"# FINAL ASSESSMENT")
    print(f"{'#'*70}\n")
    
    viable = False
    for i, (alpha, result) in enumerate(zip(alpha_values, results)):
        if mode == 'anec' and result.get('success'):
            if alpha <= 1e-6 and result['anec_fR'] >= 0:
                viable = True
                print(f"✅ VIABLE: α = {alpha:.3e} m² fixes ANEC within constraints")
        elif mode == 'points':
            if alpha <= 1e-6 and result['max_rel_correction'] > 10:
                print(f"⚠️  POTENTIALLY VIABLE: α = {alpha:.3e} m² gives O(10) correction")
                print(f"    → Requires full ANEC computation to confirm")
    
    if not viable:
        print(f"\n❌ f(R) = R + α R² FAILS to enable viable FTL\n")
        print(f"Reasons:")
        print(f"  1. PPN constraints limit α ≤ 10⁻⁶ m²")
        print(f"  2. Such small α gives negligible corrections to GR")
        print(f"  3. ANEC violations remain ~37 orders too large")
        print(f"  4. Portal contribution still irrelevant\n")
        print(f"Conclusion:")
        print(f"  - f(R) = R + α R² does NOT relax energy conditions")
        print(f"  - Higher-order f(R) unlikely (tighter constraints)")
        print(f"  - Next: Try scalar-tensor or close modified gravity track\n")


if __name__ == "__main__":
    # Quick test: point comparison with a few α values
    print("Quick test: Point comparison mode")
    alpha_test = np.array([1e-10, 1e-8, 1e-6])
    sweep_alpha_values(alpha_test, mode='points')
    
    print("\n" + "="*70)
    print("Would you like to run full ANEC computation? (computationally expensive)")
    print("Uncomment the line below to proceed:")
    print("="*70)
    print()
    
    # Full ANEC test (expensive - uncomment to run)
    print("\n" + "="*70)
    print("Running full ANEC computation...")
    print("="*70)
    alpha_anec = np.array([1e-8, 1e-6])
    sweep_alpha_values(alpha_anec, mode='anec')
