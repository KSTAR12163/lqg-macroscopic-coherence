"""
Multi-Metric ANEC Comparison Runner

Compares ANEC violations across different warp drive metrics:
- Alcubierre (baseline)
- Natário (zero expansion)
- Van Den Broeck (microscopic throat + pocket)

For each metric:
- Multi-ray sweep (various impact parameters)
- QI-aware pulse shaping (if applicable)
- Summary statistics and JSON export

Output: Consolidated JSON for rapid comparison and decision-making.
"""

import numpy as np
import json
import sys
import os
from pathlib import Path
from typing import Dict, List

# Add parent paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from phase_d.warp_eval.geodesics_generic import (
    integrate_geodesic,
    compute_anec_generic
)
from phase_d.warp_eval.alcubierre_analytic import alcubierre_metric_analytic
from phase_d.warp_eval.metrics.natario_analytic import natario_metric
from phase_d.warp_eval.metrics.vdb_analytic import vdb_metric


def run_multiray_anec(
    metric_name: str,
    metric_fn,
    metric_params: Dict,
    y_values: np.ndarray,
    lambda_max: float = 400.0,
    n_steps: int = 150
) -> Dict:
    """
    Run ANEC sweep over multiple impact parameters for one metric.
    
    Args:
        metric_name: Descriptive name (e.g., "Alcubierre", "Natario")
        metric_fn: Metric function(t, x, y, z) → g_μν
        metric_params: Parameters to pass to metric (if any)
        y_values: Impact parameter array (m)
        lambda_max: Geodesic affine parameter range
        n_steps: Integration steps
        
    Returns:
        Dictionary with per-ray results
    """
    print(f"\n{'='*70}")
    print(f"Multi-Ray ANEC: {metric_name}")
    print(f"{'='*70}")
    print(f"Impact parameters: y ∈ [{y_values.min():.1f}, {y_values.max():.1f}] m")
    print(f"Number of rays: {len(y_values)}")
    print(f"Integration: λ ∈ [0, {lambda_max}], {n_steps} steps")
    
    results = {
        'metric': metric_name,
        'params': metric_params,
        'y_values': y_values.tolist(),
        'lambda_max': lambda_max,
        'n_steps': n_steps,
        'rays': []
    }
    
    for i, y_0 in enumerate(y_values):
        print(f"\n[{i+1}/{len(y_values)}] Ray at y₀ = {y_0:+.1f} m", end=" ... ")
        
        # Initial conditions: ray from x = -200 m, impact parameter y_0
        x_0 = np.array([0.0, -200.0, y_0, 0.0])
        direction = np.array([1.0, 0.0, 0.0])  # +x direction
        
        # Integrate geodesic
        try:
            pos, tan, diag = integrate_geodesic(
                metric_fn,
                x_0,
                direction,
                lambda_max,
                n_steps=n_steps,
                project_null=True,
                rtol=1e-8,
                atol=1e-10
            )
            
            if not diag['success']:
                print(f"❌ Failed: {diag['message']}")
                results['rays'].append({
                    'y_0': y_0,
                    'success': False,
                    'message': diag['message']
                })
                continue
            
            # Compute ANEC
            anec, stats = compute_anec_generic(metric_fn, pos, tan, lambda_max)
            
            ray_result = {
                'y_0': y_0,
                'success': True,
                'anec': float(anec),
                'T_kk_min': float(stats['T_kk_min']),
                'T_kk_max': float(stats['T_kk_max']),
                'T_kk_mean': float(stats['T_kk_mean']),
                'negative_fraction': float(stats['negative_fraction']),
                'null_violation_mean': float(diag['null_violation_mean']),
                'null_violation_max': float(diag['null_violation_max']),
                'n_eval': int(diag['n_eval'])
            }
            
            results['rays'].append(ray_result)
            
            # Print summary
            anec_sign = "−" if anec < 0 else "+"
            print(f"ANEC = {anec_sign}{abs(anec):.3e}, null_mean = {diag['null_violation_mean']:.2e}")
            
        except Exception as e:
            print(f"❌ Exception: {e}")
            results['rays'].append({
                'y_0': y_0,
                'success': False,
                'message': str(e)
            })
    
    # Aggregate statistics
    successful_rays = [r for r in results['rays'] if r['success']]
    
    if successful_rays:
        anec_values = [r['anec'] for r in successful_rays]
        
        results['summary'] = {
            'n_successful': len(successful_rays),
            'n_failed': len(results['rays']) - len(successful_rays),
            'anec_min': float(np.min(anec_values)),
            'anec_max': float(np.max(anec_values)),
            'anec_mean': float(np.mean(anec_values)),
            'anec_median': float(np.median(anec_values)),
            'fraction_negative_anec': float(np.sum(np.array(anec_values) < 0) / len(anec_values))
        }
        
        print(f"\n{'='*70}")
        print(f"Summary: {metric_name}")
        print(f"{'='*70}")
        print(f"Successful rays: {results['summary']['n_successful']}/{len(results['rays'])}")
        print(f"ANEC range: [{results['summary']['anec_min']:.3e}, {results['summary']['anec_max']:.3e}]")
        print(f"ANEC median: {results['summary']['anec_median']:.3e}")
        print(f"Negative ANEC fraction: {results['summary']['fraction_negative_anec']:.1%}")
    else:
        results['summary'] = {'error': 'All rays failed'}
        print(f"\n❌ All rays failed for {metric_name}")
    
    return results


def compare_metrics(
    y_values: np.ndarray = None,
    lambda_max: float = 400.0,
    n_steps: int = 150,
    output_file: str = "multimet ric_anec_comparison.json"
) -> Dict:
    """
    Compare ANEC across Alcubierre, Natário, and Van Den Broeck.
    
    Args:
        y_values: Impact parameter array (default: -20 to +20 m)
        lambda_max: Geodesic range
        n_steps: Integration steps
        output_file: JSON output path
        
    Returns:
        Comparison dictionary
    """
    if y_values is None:
        y_values = np.linspace(-20, 20, 9)  # 9 rays from -20 to +20 m
    
    print("="*70)
    print("MULTI-METRIC ANEC COMPARISON")
    print("="*70)
    print(f"Metrics: Alcubierre, Natário, Van Den Broeck")
    print(f"Rays per metric: {len(y_values)}")
    print(f"Total computations: {3 * len(y_values)}")
    
    comparison = {
        'config': {
            'y_values': y_values.tolist(),
            'lambda_max': lambda_max,
            'n_steps': n_steps
        },
        'metrics': {}
    }
    
    # 1. Alcubierre (baseline)
    v_s, R, sigma = 1.0, 100.0, 10.0
    
    def alc_metric(t, x, y, z):
        return alcubierre_metric_analytic(t, x, y, z, v_s, R, sigma)
    
    alc_params = {'v_s': v_s, 'R': R, 'sigma': sigma}
    
    comparison['metrics']['alcubierre'] = run_multiray_anec(
        "Alcubierre",
        alc_metric,
        alc_params,
        y_values,
        lambda_max,
        n_steps
    )
    
    # 2. Natário
    def nat_metric(t, x, y, z):
        return natario_metric(t, x, y, z, v_s, R, sigma)
    
    nat_params = {'v_s': v_s, 'R': R, 'sigma': sigma}
    
    comparison['metrics']['natario'] = run_multiray_anec(
        "Natário",
        nat_metric,
        nat_params,
        y_values,
        lambda_max,
        n_steps
    )
    
    # 3. Van Den Broeck (scaled parameters)
    # Use R_ext = 0.01 m (1 cm throat) for numerical stability
    # Omega_max = 10,000 → 100 m interior from 1 cm exterior
    R_ext, sigma_ext = 0.01, 0.001
    Omega_max = 10000.0
    
    def vdb_metric_fn(t, x, y, z):
        return vdb_metric(t, x, y, z, v_s, R_ext, sigma_ext, Omega_max)
    
    vdb_params = {
        'v_s': v_s,
        'R_ext': R_ext,
        'sigma': sigma_ext,
        'Omega_max': Omega_max,
        'R_interior_effective': R_ext * Omega_max
    }
    
    comparison['metrics']['van_den_broeck'] = run_multiray_anec(
        "Van Den Broeck",
        vdb_metric_fn,
        vdb_params,
        y_values,
        lambda_max,
        n_steps
    )
    
    # Summary comparison
    print(f"\n{'='*70}")
    print("CROSS-METRIC SUMMARY")
    print(f"{'='*70}\n")
    
    print(f"{'Metric':<20} {'ANEC Median':<15} {'Negative %':<12} {'Success':<10}")
    print("-"*70)
    
    for name, data in comparison['metrics'].items():
        if 'summary' in data and 'anec_median' in data['summary']:
            median = data['summary']['anec_median']
            neg_frac = data['summary']['fraction_negative_anec'] * 100
            success = data['summary']['n_successful']
            total = len(data['rays'])
            
            print(f"{name:<20} {median:<15.3e} {neg_frac:<12.1f} {success}/{total}")
        else:
            print(f"{name:<20} {'FAILED':<15} {'-':<12} {'0/0'}")
    
    # Save to JSON
    output_path = Path(__file__).parent / output_file
    with open(output_path, 'w') as f:
        json.dump(comparison, f, indent=2)
    
    print(f"\n✅ Results saved to: {output_path}")
    
    return comparison


if __name__ == "__main__":
    """Run multi-metric ANEC comparison."""
    
    # Configuration
    y_values = np.linspace(-30, 30, 13)  # 13 rays, -30 to +30 m
    lambda_max = 400.0
    n_steps = 150
    
    # Run comparison
    results = compare_metrics(
        y_values=y_values,
        lambda_max=lambda_max,
        n_steps=n_steps,
        output_file="multimetric_anec_comparison.json"
    )
    
    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)
    print("\nKey findings:")
    
    for name, data in results['metrics'].items():
        if 'summary' in data and 'fraction_negative_anec' in data['summary']:
            neg_frac = data['summary']['fraction_negative_anec']
            
            if neg_frac > 0.5:
                print(f"  ❌ {name}: {neg_frac*100:.0f}% of rays violate ANEC")
            elif neg_frac > 0.1:
                print(f"  ⚠️  {name}: {neg_frac*100:.0f}% of rays violate ANEC")
            else:
                print(f"  ✅ {name}: Only {neg_frac*100:.0f}% violate ANEC")
    
    print("\nNext steps:")
    print("  1. Review JSON for detailed per-ray statistics")
    print("  2. Plot results (optional: requires matplotlib)")
    print("  3. Apply QI constraints to pulsed variants")
    print("  4. Decide on next theory to test (scalar-tensor, wormhole, etc.)")
