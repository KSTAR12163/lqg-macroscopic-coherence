#!/usr/bin/env python3
"""
Test script for warp evaluation infrastructure

Validates:
1. stress_energy.py: Metric → T_μν computation
2. portal_stress_energy.py: Portal EFT → δT_μν
3. geodesics.py: Null geodesics → ANEC

Run: python test_infrastructure.py
"""

import numpy as np
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from phase_d.warp_eval.stress_energy import (
    load_alcubierre_metric,
    compute_stress_energy_from_metric
)
from phase_d.warp_eval.portal_stress_energy import (
    compute_portal_delta_T,
    estimate_screening_factor
)
from phase_d.warp_eval.geodesics import (
    compute_anec
)

# Physical constants
c = 2.998e8  # m/s
hbar = 1.055e-34  # J·s
G = 6.674e-11  # N·m²/kg²
GeV_to_J = 1.602e-10  # J/GeV

def test_alcubierre_stress_energy():
    """Test T_μν computation for Alcubierre metric"""
    print("\n" + "="*60)
    print("TEST 1: Alcubierre Stress-Energy")
    print("="*60)
    
    # Alcubierre bubble parameters
    v_s = 1.0      # Speed of light (c)
    R = 100.0      # 100 m radius
    sigma = 10.0   # 10 m wall thickness
    
    # Load metric function
    metric_fn = load_alcubierre_metric(velocity=v_s, radius=R, wall_thickness=sigma)

    # Test points: (t, x, y, z, label)
    positions = [
        (0.0,   0.0, 0.0, 0.0, "Bubble center"),
        (0.0, R+0.0, 0.0, 0.0, "Wall (on axis)"),
        (0.0, 2*R,   0.0, 0.0, "Outside bubble"),
    ]
    
    for t, x, y, z, label in positions:
        try:
            coords = np.array([t, x, y, z], dtype=float)
            T = compute_stress_energy_from_metric(metric_fn, coords)
            
            T_00 = T[0, 0]  # Energy density
            T_trace = np.trace(T)
            
            print(f"\n{label} (x={x:.1f} m):")
            print(f"  T_00 = {T_00:.3e} J/m³")
            print(f"  T_trace = {T_trace:.3e} J/m³")
            
            # Alcubierre requires negative energy in wall
            if x == R:
                if T_00 < 0:
                    print(f"  ✅ Negative energy density at wall (expected)")
                else:
                    print(f"  ⚠️  Positive energy at wall (unexpected)")
                    
        except Exception as e:
            print(f"\n{label}: ❌ Error - {e}")
    
    print("\n" + "-"*60)


def test_portal_stress_energy():
    """Test δT_μν from portal EFT"""
    print("\n" + "="*60)
    print("TEST 2: Portal Stress-Energy")
    print("="*60)
    
    # Portal parameters (conservative, near CAST limit)
    portal_params = {
        'g_agamma': 6e-11,   # GeV⁻¹
        'g_aN': 1e-10,
        'm_axion': 1e-6      # GeV
    }
    
    # Field parameters (realistic lab)
    # Field parameters (as scalars, matching API)
    B_vec = np.array([0, 0, 1.0])   # 1 T
    E_vec = np.array([1e6, 0, 0])   # 1 MV/m
    B_mag = float(np.linalg.norm(B_vec))
    E_mag = float(np.linalg.norm(E_vec))
    n_nucleon = 8e28
    volume = 1.0
    coherence_time = 1e-6
    
    try:
        delta_T = compute_portal_delta_T(
            g_agamma=portal_params['g_agamma'],
            g_aN=portal_params['g_aN'],
            m_axion=portal_params['m_axion'],
            B_field=B_mag,
            E_field=E_mag,
            nucleon_density=n_nucleon,
            volume=volume,
            coherence_time=coherence_time,
            coherence_length=1e-6
        )
        
        delta_T_00 = delta_T[0, 0]  # Energy density contribution
        delta_T_trace = np.trace(delta_T)
        
        print(f"\nPortal parameters:")
        print(f"  g_aγγ = {portal_params['g_agamma']:.2e} GeV⁻¹")
        print(f"  g_aN = {portal_params['g_aN']:.2e}")
        print(f"  m_a = {portal_params['m_axion']:.2e} GeV")
        
        print(f"\nField parameters:")
        print(f"  B = {B_mag:.1f} T")
        print(f"  E = {E_mag:.2e} V/m")
        print(f"  n_N = {n_nucleon:.2e} m⁻³")
        print(f"  V = {volume:.1f} m³")
        
        print(f"\nPortal contribution:")
        print(f"  δT_00 = {delta_T_00:.3e} J/m³")
        print(f"  δT_trace = {delta_T_trace:.3e} J/m³")
        
        # Compare to Planck density
        rho_planck = c**5 / (hbar * G**2)
        print(f"\nRatio to Planck density:")
        print(f"  δT_00 / ρ_Planck = {delta_T_00 / rho_planck:.3e}")
        
        # Coherence suppression
        screening = estimate_screening_factor(nucleon_density=n_nucleon)
        print(f"\nMedium effects:")
        print(f"  Screening factor (insulator default): {screening:.3f}")
        
        if abs(delta_T_00) > 0:
            print(f"  ✅ Non-zero portal contribution")
        else:
            print(f"  ⚠️  Zero contribution (check parameters)")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "-"*60)


def test_geodesic_anec():
    """Test ANEC computation along null geodesic"""
    print("\n" + "="*60)
    print("TEST 3: ANEC Integration")
    print("="*60)
    
    # Simple toy stress-energy: diagonal with T_00 = -ρ₀ exp(-r²/R²)
    R_gauss = 10.0  # Gaussian width
    rho_0 = -1e20   # Negative energy density (J/m³)

    # T_fn signature: (t, x, y, z)
    def toy_stress_energy(t, x, y, z):
        r = np.sqrt(x**2 + y**2 + z**2)
        rho = rho_0 * np.exp(-r**2 / R_gauss**2)
        
        # Diagonal: T = diag(-ρ, ρ/3, ρ/3, ρ/3) (radiation-like)
        T = np.diag([rho, -rho/3, -rho/3, -rho/3])
        return T
    
    # Simple flat metric for testing
    def flat_metric(t, x, y, z):
        return np.diag([-1.0, 1.0, 1.0, 1.0])
    
    # Null geodesic: radial infall along x-axis
    n_steps = 100
    lambda_max = 20.0  # Pass through Gaussian
    
    # Starting point and direction for compute_anec
    x0 = np.array([0.0, -lambda_max, 0.0, 0.0])  # (t, x, y, z)
    direction = np.array([1.0, 0.0, 0.0])        # along +x
    
    try:
        anec_value, diagnostics = compute_anec(
            metric=flat_metric,
            T_fn=toy_stress_energy,
            x0=x0,
            direction=direction,
            lambda_max=lambda_max,
            n_steps=n_steps
        )
        
        print(f"\nToy stress-energy:")
        print(f"  ρ₀ = {rho_0:.2e} J/m³ (negative)")
        print(f"  R_Gauss = {R_gauss:.1f} m")
        
        print(f"\nGeodesic:")
        print(f"  Type: Radial (flat space)")
        print(f"  Length: {lambda_max:.1f} m")
        print(f"  Steps: {n_steps}")
        
        print(f"\nANEC result:")
        print(f"  ∫ T_μν k^μ k^ν dλ = {anec_value:.3e}")
        print(f"  T_kk min = {diagnostics['T_kk_min']:.3e}")
        print(f"  T_kk max = {diagnostics['T_kk_max']:.3e}")
        print(f"  Negative fraction = {diagnostics['negative_region_fraction']:.2%}")
        
        if anec_value < 0:
            print(f"  ⚠️  ANEC violated (negative integral)")
        else:
            print(f"  ✅ ANEC satisfied")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "-"*60)


def test_combined_stress_energy():
    """Test T_total = T_metric + δT_portal"""
    print("\n" + "="*60)
    print("TEST 4: Combined Stress-Energy")
    print("="*60)
    
    # Alcubierre at wall
    x, y, z, t = 100.0, 0.0, 0.0, 0.0
    v_s, R, sigma = 1.0, 100.0, 10.0
    metric_fn = load_alcubierre_metric(velocity=v_s, radius=R, wall_thickness=sigma)
    
    # Portal parameters
    portal_params = {
        'g_agamma': 6e-11,
        'g_aN': 1e-10,
        'm_axion': 1e-6
    }
    # Field params as scalars (match API)
    B_mag = 10.0
    E_mag = 1e7
    n_nucleon = 8e28
    volume = 1.0
    coherence_time = 1e-6
    
    try:
        # Metric stress-energy
        T_metric = compute_stress_energy_from_metric(metric_fn, np.array([t, x, y, z], dtype=float))
        
        # Portal contribution
        delta_T = compute_portal_delta_T(
            g_agamma=portal_params['g_agamma'],
            g_aN=portal_params['g_aN'],
            m_axion=portal_params['m_axion'],
            B_field=B_mag,
            E_field=E_mag,
            nucleon_density=n_nucleon,
            volume=volume,
            coherence_time=coherence_time,
            coherence_length=1e-6
        )
        
        # Combined
        T_total = T_metric + delta_T
        
        print(f"\nAt bubble wall (x={x:.1f} m):")
        print(f"\nMetric stress-energy:")
        print(f"  T_00^metric = {T_metric[0,0]:.3e} J/m³")
        
        print(f"\nPortal contribution:")
        print(f"  δT_00 = {delta_T[0,0]:.3e} J/m³")
        
        print(f"\nCombined:")
        print(f"  T_00^total = {T_total[0,0]:.3e} J/m³")
        
        # Fractional contribution
        if abs(T_metric[0,0]) > 0:
            frac = abs(delta_T[0,0] / T_metric[0,0])
            print(f"\nPortal fraction of metric:")
            print(f"  |δT_00 / T_00^metric| = {frac:.3e}")
            
            if frac > 0.01:
                print(f"  ⚠️  Portal contributes > 1% (unexpected)")
            else:
                print(f"  ✅ Portal << metric (expected)")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "-"*60)


def main():
    """Run all infrastructure tests"""
    print("\n" + "="*60)
    print("WARP EVALUATION INFRASTRUCTURE TESTS")
    print("="*60)
    print("\nValidating stress-energy and ANEC computation modules")
    print("before integration into full evaluation pipeline.\n")
    
    test_alcubierre_stress_energy()
    test_portal_stress_energy()
    test_geodesic_anec()
    test_combined_stress_energy()
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print("""
✅ If all tests passed:
   - Modules are ready for integration
   - Can proceed to runner.py updates
   - Ready for Week 12 re-assessment

⚠️  If tests showed warnings:
   - Check physical expectations
   - Validate against known solutions
   - May need parameter tuning

❌ If tests failed:
   - Review derivations
   - Check unit conversions
   - Validate numerics (step sizes, tolerances)

Next steps:
1. Integrate into runner.py (replace placeholder logic)
2. Load real warp metrics from warp-bubble-* repos
3. Run full evaluation with diverse candidates
4. Make evidence-based Week 12 gate decision
""")


if __name__ == "__main__":
    main()
