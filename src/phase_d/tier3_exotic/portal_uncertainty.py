#!/usr/bin/env python3
"""
Portal Coupling Uncertainty Quantification

Monte Carlo sampling over field parameters and portal couplings
to generate confidence intervals for g_eff.

Usage:
    python -m src.phase_d.tier3_exotic.portal_uncertainty \
        --samples 1000 \
        --out results/portal_uncertainty.json
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List
import numpy as np

from src.phase_d.tier3_exotic.portal_physics import (
    compute_axion_effective_coupling_refined,
    enforce_axion_constraints,
    E_PLANCK
)


def sample_field_parameters(n_samples: int, seed: int = 42) -> Dict[str, np.ndarray]:
    """
    Sample field parameters using Latin Hypercube within realistic ranges.
    
    Args:
        n_samples: Number of samples
        seed: Random seed for reproducibility
        
    Returns:
        Dictionary of parameter arrays
    """
    np.random.seed(seed)
    
    # Realistic ranges (log-uniform for spanning orders of magnitude)
    B_range = (0.1, 20.0)  # Tesla (0.1 T to 20 T superconducting)
    E_range = (1e5, 5e7)  # V/m (100 kV/m to 50 MV/m, below breakdown)
    V_range = (1e-3, 10.0)  # m³ (1 liter to 10 m³)
    photon_E_range = (0.5, 3.0)  # eV (visible to near-UV)
    
    # Log-uniform sampling
    B_samples = 10 ** np.random.uniform(np.log10(B_range[0]), np.log10(B_range[1]), n_samples)
    E_samples = 10 ** np.random.uniform(np.log10(E_range[0]), np.log10(E_range[1]), n_samples)
    V_samples = 10 ** np.random.uniform(np.log10(V_range[0]), np.log10(V_range[1]), n_samples)
    photon_E_samples = np.random.uniform(photon_E_range[0], photon_E_range[1], n_samples)
    
    return {
        'B_field': B_samples,
        'E_field': E_samples,
        'volume': V_samples,
        'photon_energy': photon_E_samples
    }


def sample_portal_parameters(
    n_samples: int,
    bounds: str = 'conservative',
    seed: int = 42
) -> Dict[str, np.ndarray]:
    """
    Sample portal coupling parameters within experimental bounds.
    
    Args:
        n_samples: Number of samples
        bounds: 'conservative' or 'aggressive'
        seed: Random seed
        
    Returns:
        Dictionary of coupling parameter arrays
    """
    np.random.seed(seed + 1)  # Different seed than field params
    
    if bounds == 'conservative':
        g_agamma_range = (1e-16, 6e-11)  # Just below CAST
        m_axion_range = (1e-6, 1e-3)  # GeV
        g_aN_range = (1e-15, 1e-10)  # Well below SN1987A
    elif bounds == 'aggressive':
        g_agamma_range = (1e-14, 1e-10)
        m_axion_range = (1e-5, 1e-2)
        g_aN_range = (1e-13, 1e-9)
    else:
        raise ValueError(f"Unknown bounds: {bounds}")
    
    # Log-uniform sampling
    g_agamma_samples = 10 ** np.random.uniform(
        np.log10(g_agamma_range[0]), np.log10(g_agamma_range[1]), n_samples
    )
    m_axion_samples = 10 ** np.random.uniform(
        np.log10(m_axion_range[0]), np.log10(m_axion_range[1]), n_samples
    )
    g_aN_samples = 10 ** np.random.uniform(
        np.log10(g_aN_range[0]), np.log10(g_aN_range[1]), n_samples
    )
    
    return {
        'g_agamma': g_agamma_samples,
        'm_axion': m_axion_samples,
        'g_aN': g_aN_samples
    }


def run_uncertainty_quantification(
    n_samples: int = 1000,
    bounds: str = 'conservative',
    model: str = 'conservative',
    seed: int = 42
) -> Dict:
    """
    Run Monte Carlo uncertainty quantification.
    
    Args:
        n_samples: Number of Monte Carlo samples
        bounds: Parameter space bounds
        model: 'conservative' or 'optimistic' coupling model
        seed: Random seed
        
    Returns:
        Dictionary with statistics and samples
    """
    print(f"{'='*70}")
    print(f"PORTAL COUPLING UNCERTAINTY QUANTIFICATION")
    print(f"{'='*70}")
    print(f"\nConfiguration:")
    print(f"  Samples: {n_samples}")
    print(f"  Bounds: {bounds}")
    print(f"  Model: {model}")
    print(f"  Seed: {seed}\n")
    
    # Sample parameters
    print("Sampling field parameters...")
    field_params = sample_field_parameters(n_samples, seed)
    
    print("Sampling portal parameters...")
    portal_params = sample_portal_parameters(n_samples, bounds, seed)
    
    # Compute g_eff for each sample
    print(f"\nComputing g_eff for {n_samples} configurations...")
    
    g_eff_samples = []
    kappa_eff_samples = []
    excluded_count = 0
    
    for i in range(n_samples):
        g_eff, diag = compute_axion_effective_coupling_refined(
            g_agamma=portal_params['g_agamma'][i],
            g_aN=portal_params['g_aN'][i],
            m_axion=portal_params['m_axion'][i],
            B_field=field_params['B_field'][i],
            E_field=field_params['E_field'][i],
            photon_energy=field_params['photon_energy'][i],
            volume=field_params['volume'][i],
            model=model
        )
        
        if diag.get('excluded', False):
            excluded_count += 1
            continue
        
        g_eff_samples.append(g_eff)
        kappa_eff_samples.append(g_eff / E_PLANCK)
    
    g_eff_array = np.array(g_eff_samples)
    kappa_eff_array = np.array(kappa_eff_samples)
    
    # Compute statistics
    print(f"\nExclusion statistics:")
    print(f"  Total samples: {n_samples}")
    print(f"  Excluded: {excluded_count} ({100*excluded_count/n_samples:.1f}%)")
    print(f"  Valid: {len(g_eff_samples)} ({100*len(g_eff_samples)/n_samples:.1f}%)")
    
    if len(g_eff_samples) == 0:
        print("\n❌ NO VALID SAMPLES - all excluded by constraints")
        return {
            'n_samples': n_samples,
            'n_valid': 0,
            'n_excluded': excluded_count,
            'error': 'All samples excluded'
        }
    
    # Percentiles
    percentiles = [2.5, 16, 50, 84, 97.5]
    g_eff_percentiles = np.percentile(g_eff_array, percentiles)
    kappa_percentiles = np.percentile(kappa_eff_array, percentiles)
    
    print(f"\n{'='*70}")
    print(f"RESULTS ({model.upper()} MODEL)")
    print(f"{'='*70}\n")
    
    print(f"g_eff distribution:")
    print(f"  Median (50%):   {g_eff_percentiles[2]:.4e} J")
    print(f"  68% CI:         [{g_eff_percentiles[1]:.4e}, {g_eff_percentiles[3]:.4e}] J")
    print(f"  95% CI:         [{g_eff_percentiles[0]:.4e}, {g_eff_percentiles[4]:.4e}] J")
    print(f"  Mean:           {np.mean(g_eff_array):.4e} J")
    print(f"  Std dev:        {np.std(g_eff_array):.4e} J")
    print(f"  Min:            {np.min(g_eff_array):.4e} J")
    print(f"  Max:            {np.max(g_eff_array):.4e} J")
    
    print(f"\nκ_eff distribution (dimensionless):")
    print(f"  Median (50%):   {kappa_percentiles[2]:.4e}")
    print(f"  68% CI:         [{kappa_percentiles[1]:.4e}, {kappa_percentiles[3]:.4e}]")
    print(f"  95% CI:         [{kappa_percentiles[0]:.4e}, {kappa_percentiles[4]:.4e}]")
    
    # Threshold comparisons
    g_threshold = 1e-50  # J
    exceeds_threshold = g_eff_array >= g_threshold
    fraction_above = np.sum(exceeds_threshold) / len(g_eff_array)
    
    print(f"\nThreshold analysis (1e-50 J):")
    print(f"  Samples above threshold: {np.sum(exceeds_threshold)} ({100*fraction_above:.1f}%)")
    print(f"  Median vs threshold:     {g_eff_percentiles[2]/g_threshold:.2e}×")
    print(f"  95% lower bound vs threshold: {g_eff_percentiles[0]/g_threshold:.2e}×")
    
    if g_eff_percentiles[0] >= g_threshold:
        print(f"\n  ✅ 95% CI EXCEEDS THRESHOLD")
    elif g_eff_percentiles[2] >= g_threshold:
        print(f"\n  ⚠️  MEDIAN EXCEEDS THRESHOLD (but lower bound may not)")
    else:
        print(f"\n  ❌ MEDIAN BELOW THRESHOLD")
    
    # Dynamic range
    dynamic_range = np.log10(np.max(g_eff_array) / np.min(g_eff_array))
    print(f"\nDynamic range: {dynamic_range:.1f} orders of magnitude")
    
    if dynamic_range > 10:
        print(f"  ⚠️  Very wide uncertainty (>{dynamic_range:.0f} orders)")
        print(f"     Dominant systematic: field parameter variation")
    elif dynamic_range > 5:
        print(f"  ⚠️  Moderate uncertainty (~{dynamic_range:.0f} orders)")
    else:
        print(f"  ✅ Narrow uncertainty (<5 orders)")
    
    results = {
        'configuration': {
            'n_samples': n_samples,
            'bounds': bounds,
            'model': model,
            'seed': seed
        },
        'statistics': {
            'n_valid': len(g_eff_samples),
            'n_excluded': excluded_count,
            'exclusion_fraction': excluded_count / n_samples
        },
        'g_eff_J': {
            'median': float(g_eff_percentiles[2]),
            'mean': float(np.mean(g_eff_array)),
            'std': float(np.std(g_eff_array)),
            'min': float(np.min(g_eff_array)),
            'max': float(np.max(g_eff_array)),
            'percentile_2.5': float(g_eff_percentiles[0]),
            'percentile_16': float(g_eff_percentiles[1]),
            'percentile_50': float(g_eff_percentiles[2]),
            'percentile_84': float(g_eff_percentiles[3]),
            'percentile_97.5': float(g_eff_percentiles[4]),
            'CI_68': [float(g_eff_percentiles[1]), float(g_eff_percentiles[3])],
            'CI_95': [float(g_eff_percentiles[0]), float(g_eff_percentiles[4])]
        },
        'kappa_eff': {
            'median': float(kappa_percentiles[2]),
            'CI_68': [float(kappa_percentiles[1]), float(kappa_percentiles[3])],
            'CI_95': [float(kappa_percentiles[0]), float(kappa_percentiles[4])]
        },
        'threshold_analysis': {
            'threshold_J': g_threshold,
            'fraction_above': float(fraction_above),
            'median_vs_threshold': float(g_eff_percentiles[2] / g_threshold),
            'CI_95_lower_vs_threshold': float(g_eff_percentiles[0] / g_threshold)
        },
        'dynamic_range_orders': float(dynamic_range)
    }
    
    return results


def main():
    """Main entry point."""
    
    parser = argparse.ArgumentParser(
        description="Uncertainty quantification for portal coupling"
    )
    parser.add_argument(
        '--samples',
        type=int,
        default=1000,
        help='Number of Monte Carlo samples'
    )
    parser.add_argument(
        '--bounds',
        choices=['conservative', 'aggressive'],
        default='conservative',
        help='Parameter space bounds'
    )
    parser.add_argument(
        '--model',
        choices=['conservative', 'optimistic'],
        default='conservative',
        help='Coupling scaling model'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility'
    )
    parser.add_argument(
        '--out',
        type=Path,
        default=Path('results/portal_uncertainty.json'),
        help='Output JSON path'
    )
    
    args = parser.parse_args()
    
    # Run uncertainty quantification
    results = run_uncertainty_quantification(
        n_samples=args.samples,
        bounds=args.bounds,
        model=args.model,
        seed=args.seed
    )
    
    # Save results
    args.out.parent.mkdir(parents=True, exist_ok=True)
    
    with open(args.out, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Results saved: {args.out}")
    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    main()
