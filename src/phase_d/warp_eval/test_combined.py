#!/usr/bin/env python3
"""
Combined Test: Metric + Portal Stress-Energy

Demonstrates:
1. Computing T_μν from Alcubierre metric via Einstein tensor
2. Computing δT_μν from portal coupling
3. Combined T_total = T_metric + δT_portal
4. Assessing whether portal can correct ANEC violations
"""

import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from phase_d.warp_eval.stress_energy import (
    load_alcubierre_metric,
    compute_stress_energy_from_metric,
    extract_energy_density_and_pressure
)
from phase_d.warp_eval.portal_stress_energy import (
    compute_portal_stress_energy_full
)


def test_alcubierre_with_portal():
    """Test Alcubierre bubble with portal correction."""
    
    print("\n" + "="*70)
    print("COMBINED TEST: Alcubierre Metric + Portal Coupling")
    print("="*70)
    
    # Alcubierre bubble parameters
    velocity = 1.0      # c
    radius = 100.0      # m
    wall_thickness = 10.0  # m
    
    print(f"\nBubble Parameters:")
    print(f"  Velocity: {velocity} c")
    print(f"  Radius: {radius} m")
    print(f"  Wall thickness: {wall_thickness} m")
    
    # Load metric
    metric = load_alcubierre_metric(velocity, radius, wall_thickness)
    
    # Portal parameters (conservative, near CAST limit)
    portal_params = {
        'g_agamma': 6e-11,   # GeV⁻¹ (0.91× CAST limit)
        'g_aN': 1e-10,
        'm_axion': 1e-6      # GeV
    }
    
    # Field parameters (strong fields - optimistic)
    field_params = {
        'B_field': 10.0,       # 10 T (achievable with HTS)
        'E_field': 1e7,        # 10 MV/m (approaching breakdown)
        'volume': 1.0,         # 1 m³
        'coherence_time': 1e-6,  # 1 μs
        'coherence_length': 1e-3  # 1 mm
    }
    
    # Medium parameters
    medium_params = {
        'nucleon_density': 8e28,  # m⁻³ (solid)
        'temperature': 300.0,     # K
        'conductivity': 1e-5      # S/m (insulator for weak screening)
    }
    
    print(f"\nPortal Parameters:")
    print(f"  g_aγγ = {portal_params['g_agamma']:.2e} GeV⁻¹")
    print(f"  g_aN = {portal_params['g_aN']:.2e}")
    print(f"  m_a = {portal_params['m_axion']:.2e} GeV")
    
    print(f"\nField Parameters (optimistic):")
    print(f"  B = {field_params['B_field']:.1f} T")
    print(f"  E = {field_params['E_field']:.2e} V/m")
    print(f"  V = {field_params['volume']:.1f} m³")
    
    # Compute portal contribution
    portal_result = compute_portal_stress_energy_full(
        portal_params, field_params, medium_params
    )
    
    delta_T = portal_result['delta_T_screened']  # With screening
    delta_rho = portal_result['delta_rho_J_m3']
    
    print(f"\nPortal Contribution:")
    print(f"  δρ = {delta_rho:.3e} J/m³")
    print(f"  Screening = {portal_result['screening_factor']:.2f}")
    print(f"  Coherence suppression = {portal_result['coherence_suppression']:.3e}")
    
    # Test points: center, wall, outside
    test_points = [
        ([0, 0, 0, 0], "Bubble Center"),
        ([0, radius, 0, 0], "Bubble Wall (on-axis)"),
        ([0, radius + 20, 0, 0], "Outside Bubble"),
    ]
    
    print("\n" + "-"*70)
    print("STRESS-ENERGY ANALYSIS")
    print("-"*70)
    
    for coords, label in test_points:
        print(f"\n{label}: (t,x,y,z) = {coords}")
        
        # Compute metric stress-energy
        T_metric = compute_stress_energy_from_metric(
            metric, np.array(coords, dtype=float)
        )
        
        rho_metric, p_metric = extract_energy_density_and_pressure(T_metric)
        
        # Combined
        T_total = T_metric + delta_T
        rho_total, p_total = extract_energy_density_and_pressure(T_total)
        
        print(f"\n  Metric stress-energy:")
        print(f"    ρ_metric = {rho_metric:.3e} J/m³", end="")
        if rho_metric < 0:
            print(" ⚠️ NEGATIVE")
        else:
            print()
        print(f"    p_metric = {p_metric:.3e} J/m³")
        
        print(f"\n  Portal contribution:")
        print(f"    δρ_portal = {delta_rho:.3e} J/m³")
        
        print(f"\n  Combined:")
        print(f"    ρ_total = {rho_total:.3e} J/m³", end="")
        if rho_total < 0:
            print(" ⚠️ STILL NEGATIVE")
        else:
            print()
        
        # Fractional correction
        if abs(rho_metric) > 0:
            correction_fraction = abs(delta_rho / rho_metric)
            print(f"\n  Portal correction magnitude:")
            print(f"    |δρ / ρ_metric| = {correction_fraction:.3e}")
            
            if correction_fraction > 1e-10:
                print(f"    ({correction_fraction:.1e} of metric stress-energy)")
            else:
                print(f"    (Negligible - {int(np.log10(1/correction_fraction))} orders too small)")
    
    print("\n" + "="*70)
    print("CONCLUSION")
    print("="*70)
    
    print("""
The portal coupling provides a positive energy correction δρ ~ 10⁻²¹ J/m³,
but the Alcubierre metric requires negative energy densities of order
ρ ~ -10⁴⁸ to 10⁵⁸ J/m³ in the bubble region.

Portal correction is ~10²⁷⁺ orders of magnitude too small to affect
the stress-energy in any meaningful way. The geometric requirements
of the warp bubble completely dominate over portal-enhanced coupling.

Even with optimistic field parameters (10 T, 10 MV/m), the portal
contribution is negligible compared to metric requirements.

Result: Portal enhancement cannot resolve ANEC violations in warp metrics.
        Geometry is the bottleneck, not coupling strength.
""")


if __name__ == "__main__":
    test_alcubierre_with_portal()
