#!/usr/bin/env python3
"""
Refined Portal Coupling Scanner

Physics-based scan with:
- Rigorous dimensional analysis
- Experimental constraint enforcement
- Dimensionless coupling metrics
- Comparison to baseline claims

Usage:
    python -m src.phase_d.tier3_exotic.portal_scan_refined \
        --bounds conservative \
        --out results/portal_g0_bounds_refined.json
"""

import argparse
import json
from pathlib import Path
from typing import Dict
import numpy as np

from src.phase_d.tier3_exotic.portal_physics import (
    scan_axion_parameter_space_refined,
    compute_dimensionless_coupling,
    validate_physical_scaling,
    E_PLANCK,
    GEV_TO_J
)


def compare_to_baseline(g_eff: float) -> Dict[str, float]:
    """Compare refined g_eff to previous claims."""
    
    # Previous claims
    g_baseline_lqg = 1e-121  # J (from LQG Tier 1)
    g_old_portal = 6.23e-36  # J (from old portal scan - questionable)
    g_threshold = 1e-50  # J (heuristic viability threshold)
    
    return {
        'vs_lqg_baseline': g_eff / g_baseline_lqg if g_baseline_lqg > 0 else float('inf'),
        'vs_old_portal_claim': g_eff / g_old_portal if g_old_portal > 0 else float('inf'),
        'vs_threshold': g_eff / g_threshold if g_threshold > 0 else float('inf'),
        'exceeds_threshold': g_eff >= g_threshold,
        'baseline_lqg_J': g_baseline_lqg,
        'old_portal_J': g_old_portal,
        'threshold_J': g_threshold
    }


def main():
    """Main entry point."""
    
    parser = argparse.ArgumentParser(
        description="Refined portal coupling scan with rigorous physics"
    )
    parser.add_argument(
        '--bounds',
        choices=['conservative', 'aggressive', 'theoretical'],
        default='conservative',
        help='Parameter space bounds (conservative = within experimental limits)'
    )
    parser.add_argument(
        '--n-points',
        type=int,
        default=10,
        help='Grid resolution per parameter'
    )
    parser.add_argument(
        '--B-field',
        type=float,
        default=1.0,
        help='Background magnetic field (Tesla)'
    )
    parser.add_argument(
        '--E-field',
        type=float,
        default=1e6,
        help='Background electric field (V/m)'
    )
    parser.add_argument(
        '--volume',
        type=float,
        default=1.0,
        help='Interaction volume (m³)'
    )
    parser.add_argument(
        '--out',
        type=Path,
        default=Path('results/portal_g0_bounds_refined.json'),
        help='Output JSON path'
    )
    
    args = parser.parse_args()
    
    print(f"{'='*70}")
    print(f"REFINED PORTAL COUPLING SCAN ({args.bounds.upper()} BOUNDS)")
    print(f"{'='*70}")
    print(f"\nPhysical parameters:")
    print(f"  Magnetic field: {args.B_field:.2e} T")
    print(f"  Electric field: {args.E_field:.2e} V/m")
    print(f"  Volume: {args.volume:.2e} m³")
    print(f"  Grid resolution: {args.n_points}³ = {args.n_points**3} points")
    
    # Run refined scan
    print(f"\nScanning axion parameter space...")
    results = scan_axion_parameter_space_refined(
        bounds=args.bounds,
        n_points=args.n_points,
        B_field=args.B_field,
        E_field=args.E_field,
        volume=args.volume
    )
    
    print(f"  Total configurations: {args.n_points**3}")
    print(f"  Passed constraints: {len(results)}")
    print(f"  Exclusion rate: {100 * (1 - len(results)/(args.n_points**3)):.1f}%")
    
    if not results:
        print("\n❌ NO CONFIGURATIONS SURVIVED EXPERIMENTAL CONSTRAINTS")
        return
    
    # Best configuration
    best = results[0]
    
    print(f"\n{'='*70}")
    print("BEST CONFIGURATION (REFINED MODEL)")
    print(f"{'='*70}")
    print(f"\nParameters:")
    print(f"  g_aγγ = {best['g_agamma']:.4e} GeV⁻¹")
    print(f"  g_aN = {best['g_aN']:.4e} (dimensionless)")
    print(f"  m_a = {best['m_axion']:.4e} GeV")
    print(f"  λ_a = {best['lambda_axion_m']:.4e} m (Compton wavelength)")
    
    print(f"\nEffective coupling:")
    print(f"  g_eff = {best['g_eff']:.4e} J")
    print(f"  κ_eff = {best['kappa_eff']:.4e} (dimensionless, vs E_Planck)")
    
    # Comparison to baselines
    comparison = compare_to_baseline(best['g_eff'])
    
    print(f"\nComparison to baselines:")
    print(f"  vs LQG baseline (1e-121 J): {comparison['vs_lqg_baseline']:.2e}×")
    print(f"  vs old portal claim (6.23e-36 J): {comparison['vs_old_portal_claim']:.2e}×")
    print(f"  vs threshold (1e-50 J): {comparison['vs_threshold']:.2e}×")
    
    if comparison['exceeds_threshold']:
        print(f"\n✅ EXCEEDS HEURISTIC THRESHOLD")
    else:
        shortfall = 1.0 / comparison['vs_threshold']
        print(f"\n❌ Below threshold by {shortfall:.2e}×")
    
    # Physical validation
    validation = validate_physical_scaling(best['g_eff'], context="Best axion config")
    
    print(f"\nPhysical sanity checks:")
    print(f"  Below Planck energy (κ < 1): {validation['below_planck_energy']}")
    print(f"  Above quantum gravity floor: {validation['above_quantum_gravity']}")
    print(f"  Physically reasonable range: {validation['physically_reasonable']}")
    
    # Energy scale context
    print(f"\nEnergy scale context:")
    kappa_detail = compute_dimensionless_coupling(best['g_eff'])
    print(f"  vs 1 GeV: {kappa_detail['vs_GeV']:.2e}")
    print(f"  vs 1 eV: {kappa_detail['vs_eV']:.2e}")
    print(f"  vs electron mass: {kappa_detail['vs_electron_mass']:.2e}")
    print(f"  vs proton mass: {kappa_detail['vs_proton_mass']:.2e}")
    
    # Distribution statistics
    g_effs = [r['g_eff'] for r in results]
    kappas = [r['kappa_eff'] for r in results]
    
    print(f"\nDistribution (all {len(results)} valid configs):")
    print(f"  g_eff range: [{min(g_effs):.2e}, {max(g_effs):.2e}] J")
    print(f"  κ_eff range: [{min(kappas):.2e}, {max(kappas):.2e}]")
    print(f"  Median g_eff: {np.median(g_effs):.2e} J")
    print(f"  Median κ_eff: {np.median(kappas):.2e}")
    
    # Save results
    args.out.parent.mkdir(parents=True, exist_ok=True)
    
    output = {
        'scan_parameters': {
            'bounds': args.bounds,
            'n_points_per_dim': int(args.n_points),
            'total_grid_points': int(args.n_points**3),
            'B_field_T': float(args.B_field),
            'E_field_V_m': float(args.E_field),
            'volume_m3': float(args.volume)
        },
        'constraints': {
            'total_configs': int(args.n_points**3),
            'passed_constraints': int(len(results)),
            'exclusion_rate': float(1 - len(results)/(args.n_points**3))
        },
        'best_configuration': {k: (float(v) if isinstance(v, (int, float, np.number)) else bool(v) if isinstance(v, np.bool_) else v) 
                               for k, v in best.items()},
        'comparison_to_baselines': {k: float(v) if isinstance(v, (int, float, np.number)) else bool(v) if isinstance(v, np.bool_) else v 
                                    for k, v in comparison.items()},
        'physical_validation': {k: (float(v) if isinstance(v, (int, float, np.number)) else bool(v) if isinstance(v, np.bool_) else v)
                                for k, v in validation.items()},
        'dimensionless_metrics': {k: float(v) for k, v in kappa_detail.items()},
        'top_10_configs': [{k: float(v) if isinstance(v, (int, float, np.number)) else bool(v) if isinstance(v, np.bool_) else v 
                            for k, v in r.items()} for r in results[:10]],
        'statistics': {
            'g_eff_min': float(min(g_effs)),
            'g_eff_max': float(max(g_effs)),
            'g_eff_median': float(np.median(g_effs)),
            'kappa_eff_min': float(min(kappas)),
            'kappa_eff_max': float(max(kappas)),
            'kappa_eff_median': float(np.median(kappas))
        }
    }
    
    with open(args.out, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Results saved: {args.out}")
    
    print(f"\n{'='*70}")
    print("✅ REFINED PORTAL SCAN COMPLETE")
    print(f"{'='*70}")
    
    # Critical assessment
    print(f"\n⚠️  CRITICAL ASSESSMENT:")
    if comparison['vs_old_portal_claim'] < 1e-10:
        print(f"   Refined model gives g_eff ~{1/comparison['vs_old_portal_claim']:.0e}× SMALLER than old claim.")
        print(f"   Previous 6e-36 J figure was likely due to unjustified dimensional scaling.")
    elif comparison['vs_old_portal_claim'] > 1e10:
        print(f"   Refined model gives g_eff ~{comparison['vs_old_portal_claim']:.0e}× LARGER than old claim.")
        print(f"   Field parameters may be unrealistic - verify physical context.")
    else:
        print(f"   Refined g_eff within {comparison['vs_old_portal_claim']:.1e}× of old claim.")
        print(f"   Physical model is self-consistent.")
    
    if not comparison['exceeds_threshold']:
        print(f"\n   ❌ WEEK 4 GATE STATUS: FAILED")
        print(f"      g_eff < 1e-50 J threshold by {1/comparison['vs_threshold']:.0e}×")
        print(f"      Coupling enhancement insufficient for warp viability.")
    else:
        print(f"\n   ✅ WEEK 4 GATE STATUS: PASSED")
        print(f"      g_eff ≥ 1e-50 J threshold")
        print(f"      Proceed with warp bubble evaluation.")


if __name__ == "__main__":
    main()
