#!/usr/bin/env python3
"""
Portal Coupling Viability Assessment

Compare old vs refined portal models and assess physical realism.

Usage:
    python examples/recompute_viability.py
"""

import json
from pathlib import Path
import sys
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.phase_d.tier3_exotic.portal_physics import (
    E_PLANCK,
    GEV_TO_J,
    HBAR,
    C
)


def load_results(path: Path) -> dict:
    """Load JSON results."""
    with open(path) as f:
        return json.load(f)


def assess_field_parameters(B_T: float, E_V_m: float, volume_m3: float) -> dict:
    """
    Assess whether field parameters are physically realistic.
    
    Args:
        B_T: Magnetic field (Tesla)
        E_V_m: Electric field (V/m)
        volume_m3: Volume (m³)
        
    Returns:
        Assessment with realistic ranges
    """
    # Realistic field ranges
    realistic_B = {
        'Earth_surface': 5e-5,  # T
        'lab_magnet': 1.0,  # T (achievable)
        'superconducting_magnet': 20.0,  # T (LHC-class)
        'neutron_star': 1e8,  # T (exotic astrophysics)
    }
    
    realistic_E = {
        'breakdown_air': 3e6,  # V/m (air breakdown)
        'capacitor': 1e7,  # V/m (good capacitor)
        'dielectric_breakdown': 1e8,  # V/m (hard limit for solids)
        'atomic': 5e11,  # V/m (atomic field strength)
    }
    
    # Check if parameters are realistic
    B_realistic = B_T <= realistic_B['superconducting_magnet']
    E_realistic = E_V_m <= realistic_E['dielectric_breakdown']
    volume_reasonable = 1e-9 <= volume_m3 <= 1e3  # nm³ to km³
    
    # Field energy density
    epsilon_0 = 8.854187817e-12  # F/m
    mu_0 = 4 * np.pi * 1e-7  # H/m
    
    u_E = 0.5 * epsilon_0 * E_V_m**2  # J/m³
    u_B = 0.5 * B_T**2 / mu_0  # J/m³
    u_total = u_E + u_B
    
    total_energy = u_total * volume_m3  # J
    
    return {
        'B_field_T': B_T,
        'E_field_V_m': E_V_m,
        'volume_m3': volume_m3,
        'B_realistic': B_realistic,
        'E_realistic': E_realistic,
        'volume_reasonable': volume_reasonable,
        'all_realistic': B_realistic and E_realistic and volume_reasonable,
        'field_energy_density_J_m3': u_total,
        'total_field_energy_J': total_energy,
        'vs_proton_mass': total_energy / (0.938 * GEV_TO_J),
        'realistic_ranges': {
            'B_field': realistic_B,
            'E_field': realistic_E
        }
    }


def compare_old_vs_refined():
    """Generate comparison report."""
    
    print(f"{'='*70}")
    print("PORTAL COUPLING VIABILITY ASSESSMENT")
    print(f"{'='*70}\n")
    
    # Load results
    old_path = Path('results/portal_g0_bounds.json')
    refined_path = Path('results/portal_g0_bounds_refined.json')
    
    if not old_path.exists():
        print(f"❌ Old results not found: {old_path}")
        return
    
    if not refined_path.exists():
        print(f"❌ Refined results not found: {refined_path}")
        return
    
    old = load_results(old_path)
    refined = load_results(refined_path)
    
    # Extract key values
    old_g_eff = old['best_overall']['g_eff']
    refined_g_eff = refined['best_configuration']['g_eff']
    
    print("## 1. MODEL COMPARISON\n")
    print(f"Old model g_eff:     {old_g_eff:.4e} J")
    print(f"Refined model g_eff: {refined_g_eff:.4e} J")
    print(f"Ratio (refined/old): {refined_g_eff/old_g_eff:.2e}×\n")
    
    # Baseline comparisons
    g_baseline = 1e-121  # J
    g_threshold = 1e-50  # J
    
    print("## 2. THRESHOLD COMPARISONS\n")
    print(f"Metric                | Old Model      | Refined Model")
    print(f"----------------------|----------------|---------------")
    print(f"vs LQG baseline       | {old_g_eff/g_baseline:.2e}× | {refined_g_eff/g_baseline:.2e}×")
    print(f"vs threshold (1e-50 J)| {old_g_eff/g_threshold:.2e}× | {refined_g_eff/g_threshold:.2e}×")
    print(f"Exceeds threshold?    | {'YES' if old_g_eff >= g_threshold else 'NO'} | {'YES' if refined_g_eff >= g_threshold else 'NO'}\n")
    
    # Dimensionless coupling
    print("## 3. DIMENSIONLESS COUPLING\n")
    kappa_old = old_g_eff / E_PLANCK
    kappa_refined = refined['best_configuration']['kappa_eff']
    
    print(f"Old κ_eff:     {kappa_old:.4e}")
    print(f"Refined κ_eff: {kappa_refined:.4e}")
    print(f"Both << 1?     {kappa_old < 1 and kappa_refined < 1} (required for perturbative physics)\n")
    
    # Field parameter assessment
    print("## 4. PHYSICAL REALISM CHECK\n")
    
    scan_params = refined['scan_parameters']
    assessment = assess_field_parameters(
        scan_params['B_field_T'],
        scan_params['E_field_V_m'],
        scan_params['volume_m3']
    )
    
    print(f"Field parameters used:")
    print(f"  B-field: {assessment['B_field_T']:.2e} T")
    print(f"  E-field: {assessment['E_field_V_m']:.2e} V/m")
    print(f"  Volume:  {assessment['volume_m3']:.2e} m³")
    print()
    print(f"Realism assessment:")
    print(f"  B-field realistic? {assessment['B_realistic']} (≤ 20 T superconducting)")
    print(f"  E-field realistic? {assessment['E_realistic']} (≤ 1e8 V/m breakdown)")
    print(f"  Volume reasonable? {assessment['volume_reasonable']} (nm³ to km³)")
    print(f"  All realistic?     {assessment['all_realistic']}")
    print()
    print(f"Field energy:")
    print(f"  Energy density: {assessment['field_energy_density_J_m3']:.4e} J/m³")
    print(f"  Total energy:   {assessment['total_field_energy_J']:.4e} J")
    print(f"  (vs proton mass: {assessment['vs_proton_mass']:.2e}×)\n")
    
    # Experimental constraints
    print("## 5. EXPERIMENTAL CONSTRAINTS\n")
    
    best_config = refined['best_configuration']
    print(f"Best configuration:")
    print(f"  g_aγγ = {best_config['g_agamma']:.4e} GeV⁻¹")
    print(f"  m_a   = {best_config['m_axion']:.4e} GeV")
    print(f"  g_aN  = {best_config['g_aN']:.4e}")
    print()
    
    # CAST limit
    cast_limit = 6.6e-11  # GeV⁻¹
    below_cast = best_config['g_agamma'] <= cast_limit
    print(f"CAST constraint (g_aγ < {cast_limit:.2e} GeV⁻¹):")
    print(f"  g_aγγ / CAST_limit = {best_config['g_agamma']/cast_limit:.2f}")
    print(f"  Satisfies constraint? {below_cast}\n")
    
    # SN1987A
    sn_limit = 1e-10  # GeV⁻¹
    below_sn = best_config['g_agamma'] <= sn_limit
    print(f"SN1987A constraint (g_aγ < {sn_limit:.2e} GeV⁻¹):")
    print(f"  g_aγγ / SN_limit = {best_config['g_agamma']/sn_limit:.2f}")
    print(f"  Satisfies constraint? {below_sn}\n")
    
    # Overall constraint satisfaction
    passes_constraints = refined['constraints']['passed_constraints']
    total_configs = refined['constraints']['total_configs']
    
    print(f"Constraint filtering:")
    print(f"  Configurations tested:  {total_configs}")
    print(f"  Passed all constraints: {passes_constraints}")
    print(f"  Exclusion rate:         {100 * refined['constraints']['exclusion_rate']:.1f}%\n")
    
    # Critical assessment
    print(f"{'='*70}")
    print("CRITICAL ASSESSMENT")
    print(f"{'='*70}\n")
    
    if refined_g_eff > old_g_eff * 1e10:
        print("⚠️  Refined model gives g_eff >> old model (>10¹⁰×)")
        print("    This suggests:")
        print("    1. Old model had unjustified dimensional suppression")
        print("    2. OR refined model has unrealistic field assumptions\n")
        
        if not assessment['all_realistic']:
            print("⚠️  Field parameters are NOT all realistic:")
            if not assessment['B_realistic']:
                print(f"    - B-field ({assessment['B_field_T']:.1f} T) exceeds lab capabilities")
            if not assessment['E_realistic']:
                print(f"    - E-field ({assessment['E_field_V_m']:.2e} V/m) exceeds breakdown limit")
            if not assessment['volume_reasonable']:
                print(f"    - Volume ({assessment['volume_m3']:.2e} m³) is unreasonable")
            print()
    
    # Week 4 gate decision
    print("## WEEK 4 GATE DECISION\n")
    
    if refined_g_eff >= g_threshold and assessment['all_realistic']:
        print("✅ GATE PASSED (with realistic fields)")
        print(f"   g_eff = {refined_g_eff:.2e} J ≥ {g_threshold:.2e} J")
        print(f"   All field parameters realistic")
        print(f"   All experimental constraints satisfied")
        print(f"\n   ➡️  RECOMMENDATION: Proceed to warp bubble evaluation")
    elif refined_g_eff >= g_threshold and not assessment['all_realistic']:
        print("⚠️  GATE CONDITIONALLY PASSED (unrealistic fields)")
        print(f"   g_eff = {refined_g_eff:.2e} J ≥ {g_threshold:.2e} J")
        print(f"   BUT field parameters are not all realistic:")
        print(f"     - Requires {assessment['B_field_T']:.1f} T, {assessment['E_field_V_m']:.2e} V/m")
        print(f"     - Field energy: {assessment['total_field_energy_J']:.2e} J")
        print(f"\n   ➡️  RECOMMENDATION: Recompute with realistic field limits")
    else:
        print("❌ GATE FAILED")
        print(f"   g_eff = {refined_g_eff:.2e} J < {g_threshold:.2e} J")
        print(f"   Shortfall: {g_threshold/refined_g_eff:.2e}×")
        print(f"\n   ➡️  RECOMMENDATION: Explore alternative portals or admit coupling limit")
    
    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    compare_old_vs_refined()
