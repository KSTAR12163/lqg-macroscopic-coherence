#!/usr/bin/env python3
"""
Parameter Optimization Study

Test variations to see if we can boost coupling beyond base N^2 scaling:
1. Coupling constant λ
2. Polymer parameter μ
3. Hilbert space dimension
4. Matter field energy scale
5. Combined optimizations

Goal: Push closer to N=238 viability threshold or discover parameter sensitivities.
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple, Dict
import json

from src.phase_d.tier1_collective.network_construction import create_complete_network
from src.phase_d.tier1_collective.collective_hamiltonian import (
    build_collective_hamiltonian,
    measure_collective_coupling_v2
)
from run_week1_day3 import modify_edge_spins


def test_coupling_constant(N: int, lambda_values: List[float], j: float = 2.0, dim: int = 16):
    """Test effect of coupling constant λ."""
    print(f"\n{'='*70}")
    print(f"TESTING COUPLING CONSTANT λ (N={N}, j={j})")
    print(f"{'='*70}")
    
    network, _ = create_complete_network(N)
    if j != 0.5:
        network = modify_edge_spins(network, j)
    
    results = {'lambda': [], 'g': [], 'enh': []}
    
    for lam in lambda_values:
        print(f"λ={lam:.2f}...", end=" ", flush=True)
        
        # Build Hamiltonian with specific λ
        ham_result = build_collective_hamiltonian(network, dim, lambda_coupling=lam)
        
        # Compute spectrum
        eigvals, eigvecs = np.linalg.eigh(ham_result.H_total)
        
        psi0 = eigvecs[:, 0]
        psi1 = eigvecs[:, 1]
        g_coll = abs(np.dot(np.conj(psi1), ham_result.H_int @ psi0))
        
        g_single = 3.96e-121
        enh = g_coll / g_single
        
        results['lambda'].append(lam)
        results['g'].append(g_coll)
        results['enh'].append(enh)
        
        print(f"g={g_coll:.3e} J, enh={enh:.2e}×")
    
    # Check scaling
    if len(lambda_values) > 2:
        log_lam = np.log(lambda_values)
        log_g = np.log(results['g'])
        fit = np.polyfit(log_lam, log_g, 1)
        beta = fit[0]
        print(f"\nScaling: g ∝ λ^{beta:.3f}")
        results['beta_lambda'] = beta
    
    return results


def test_matter_energy(N: int, energy_values: List[float], j: float = 2.0, dim: int = 16):
    """Test effect of matter field energy scale."""
    print(f"\n{'='*70}")
    print(f"TESTING MATTER ENERGY SCALE (N={N}, j={j})")
    print(f"{'='*70}")
    
    network, _ = create_complete_network(N)
    if j != 0.5:
        network = modify_edge_spins(network, j)
    
    results = {'energy': [], 'g': [], 'enh': []}
    
    for E in energy_values:
        print(f"E={E:.2e} J...", end=" ", flush=True)
        
        ham_result = build_collective_hamiltonian(network, dim, matter_energy=E)
        eigvals, eigvecs = np.linalg.eigh(ham_result.H_total)
        
        psi0 = eigvecs[:, 0]
        psi1 = eigvecs[:, 1]
        g_coll = abs(np.dot(np.conj(psi1), ham_result.H_int @ psi0))
        
        g_single = 3.96e-121
        enh = g_coll / g_single
        
        results['energy'].append(E)
        results['g'].append(g_coll)
        results['enh'].append(enh)
        
        print(f"g={g_coll:.3e} J, enh={enh:.2e}×")
    
    # Check scaling
    if len(energy_values) > 2:
        log_E = np.log(energy_values)
        log_g = np.log(results['g'])
        fit = np.polyfit(log_E, log_g, 1)
        beta = fit[0]
        print(f"\nScaling: g ∝ E^{beta:.3f}")
        results['beta_energy'] = beta
    
    return results


def test_dimension_convergence(N: int, dim_values: List[int], j: float = 2.0):
    """Test convergence with Hilbert space dimension."""
    print(f"\n{'='*70}")
    print(f"TESTING DIMENSION CONVERGENCE (N={N}, j={j})")
    print(f"{'='*70}")
    
    network, _ = create_complete_network(N)
    if j != 0.5:
        network = modify_edge_spins(network, j)
    
    results = {'dim': [], 'g': [], 'enh': [], 'time': []}
    
    import time
    
    for d in dim_values:
        print(f"dim={d}...", end=" ", flush=True)
        
        t0 = time.time()
        g_coll, gap, enh = measure_collective_coupling_v2(network, dim=d)
        t1 = time.time()
        
        results['dim'].append(d)
        results['g'].append(g_coll)
        results['enh'].append(enh)
        results['time'].append(t1 - t0)
        
        print(f"g={g_coll:.3e} J, enh={enh:.2e}×, t={t1-t0:.2f}s")
    
    # Check convergence
    if len(dim_values) > 2:
        g_vals = np.array(results['g'])
        relative_change = np.abs(np.diff(g_vals) / g_vals[:-1])
        print(f"\nConvergence: max relative change = {np.max(relative_change):.3f}")
        results['converged'] = np.max(relative_change) < 0.1
    
    return results


def test_optimal_configuration(N: int, j: float = 2.0):
    """Test potentially optimal configuration."""
    print(f"\n{'='*70}")
    print(f"TESTING OPTIMAL CONFIGURATION (N={N}, j={j})")
    print(f"{'='*70}")
    
    network, _ = create_complete_network(N)
    if j != 0.5:
        network = modify_edge_spins(network, j)
    
    # Test combinations
    configs = [
        {'lambda': 1.0, 'E': 1e-15, 'dim': 16, 'name': 'baseline'},
        {'lambda': 2.0, 'E': 1e-15, 'dim': 16, 'name': 'lambda_2x'},
        {'lambda': 5.0, 'E': 1e-15, 'dim': 16, 'name': 'lambda_5x'},
        {'lambda': 1.0, 'E': 1e-14, 'dim': 16, 'name': 'energy_10x'},
        {'lambda': 1.0, 'E': 1e-13, 'dim': 16, 'name': 'energy_100x'},
        {'lambda': 2.0, 'E': 1e-14, 'dim': 16, 'name': 'lambda_2x_energy_10x'},
        {'lambda': 5.0, 'E': 1e-13, 'dim': 16, 'name': 'lambda_5x_energy_100x'},
        {'lambda': 1.0, 'E': 1e-15, 'dim': 32, 'name': 'dim_32'},
    ]
    
    results = []
    
    for config in configs:
        print(f"\n{config['name']}...", end=" ")
        
        ham = build_collective_hamiltonian(
            network, 
            config['dim'], 
            lambda_coupling=config['lambda'],
            matter_energy=config['E']
        )
        
        eigvals, eigvecs = np.linalg.eigh(ham.H_total)
        psi0 = eigvecs[:, 0]
        psi1 = eigvecs[:, 1]
        g_coll = abs(np.dot(np.conj(psi1), ham.H_int @ psi0))
        
        g_single = 3.96e-121
        enh = g_coll / g_single
        
        config['g'] = g_coll
        config['enh'] = enh
        results.append(config)
        
        print(f"g={g_coll:.3e} J, enh={enh:.2e}×")
    
    # Find best
    best = max(results, key=lambda x: x['enh'])
    print(f"\n{'='*70}")
    print(f"BEST: {best['name']}")
    print(f"  λ={best['lambda']}, E={best['E']:.2e} J, dim={best['dim']}")
    print(f"  Enhancement: {best['enh']:.2e}×")
    print(f"  Boost vs baseline: {best['enh']/results[0]['enh']:.2f}×")
    print(f"{'='*70}")
    
    return results


def create_optimization_plots(results_dict: Dict):
    """Visualize optimization results."""
    fig = plt.figure(figsize=(15, 10))
    
    # Plot 1: λ sensitivity
    if 'lambda' in results_dict:
        ax1 = plt.subplot(2, 3, 1)
        r = results_dict['lambda']
        ax1.loglog(r['lambda'], r['g'], 'bo-', linewidth=2, markersize=8)
        ax1.set_xlabel('Coupling Constant λ', fontsize=12)
        ax1.set_ylabel('g_coll (J)', fontsize=12)
        ax1.set_title(f"λ Sensitivity (β={r.get('beta_lambda', 0):.2f})", fontsize=13, fontweight='bold')
        ax1.grid(True, alpha=0.3)
    
    # Plot 2: Energy sensitivity
    if 'energy' in results_dict:
        ax2 = plt.subplot(2, 3, 2)
        r = results_dict['energy']
        ax2.loglog(r['energy'], r['g'], 'go-', linewidth=2, markersize=8)
        ax2.set_xlabel('Matter Energy (J)', fontsize=12)
        ax2.set_ylabel('g_coll (J)', fontsize=12)
        ax2.set_title(f"Energy Sensitivity (β={r.get('beta_energy', 0):.2f})", fontsize=13, fontweight='bold')
        ax2.grid(True, alpha=0.3)
    
    # Plot 3: Dimension convergence
    if 'dimension' in results_dict:
        ax3 = plt.subplot(2, 3, 3)
        r = results_dict['dimension']
        ax3.semilogx(r['dim'], r['g'], 'ro-', linewidth=2, markersize=8)
        ax3.set_xlabel('Hilbert Dimension', fontsize=12)
        ax3.set_ylabel('g_coll (J)', fontsize=12)
        converged = "✓" if r.get('converged', False) else "✗"
        ax3.set_title(f"Dimension Convergence {converged}", fontsize=13, fontweight='bold')
        ax3.grid(True, alpha=0.3)
    
    # Plot 4: Configuration comparison (enhancement)
    if 'optimal' in results_dict:
        ax4 = plt.subplot(2, 3, 4)
        configs = results_dict['optimal']
        names = [c['name'] for c in configs]
        enhs = [c['enh'] for c in configs]
        
        colors = ['blue' if i == 0 else 'green' if c['enh'] == max(enhs) else 'gray' 
                  for i, c in enumerate(configs)]
        
        bars = ax4.barh(range(len(names)), enhs, color=colors, alpha=0.7)
        ax4.set_yticks(range(len(names)))
        ax4.set_yticklabels(names, fontsize=9)
        ax4.set_xlabel('Enhancement', fontsize=12)
        ax4.set_xscale('log')
        ax4.set_title('Configuration Comparison', fontsize=13, fontweight='bold')
        ax4.grid(True, alpha=0.3, axis='x')
    
    # Plot 5: Boost factors
    if 'optimal' in results_dict:
        ax5 = plt.subplot(2, 3, 5)
        configs = results_dict['optimal']
        baseline_enh = configs[0]['enh']
        boost_factors = [c['enh'] / baseline_enh for c in configs]
        
        ax5.barh(range(len(names)), boost_factors, alpha=0.7)
        ax5.set_yticks(range(len(names)))
        ax5.set_yticklabels(names, fontsize=9)
        ax5.set_xlabel('Boost Factor (vs baseline)', fontsize=12)
        ax5.axvline(1.0, color='red', linestyle='--', linewidth=2)
        ax5.set_title('Parameter Boost Analysis', fontsize=13, fontweight='bold')
        ax5.grid(True, alpha=0.3, axis='x')
    
    # Plot 6: Time vs dimension
    if 'dimension' in results_dict:
        ax6 = plt.subplot(2, 3, 6)
        r = results_dict['dimension']
        ax6.loglog(r['dim'], r['time'], 'mo-', linewidth=2, markersize=8)
        ax6.set_xlabel('Hilbert Dimension', fontsize=12)
        ax6.set_ylabel('Computation Time (s)', fontsize=12)
        ax6.set_title('Computational Scaling', fontsize=13, fontweight='bold')
        ax6.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('parameter_optimization.png', dpi=150, bbox_inches='tight')
    print("\n✅ Optimization plot saved: parameter_optimization.png")


def main():
    """Run parameter optimization study."""
    
    print("="*70)
    print("PARAMETER OPTIMIZATION STUDY")
    print("="*70)
    print("\nGoal: Find parameter combinations that boost coupling")
    print("Test N=20 for speed (can scale up if promising)")
    
    N_test = 20
    j_opt = 2.0
    
    results = {}
    
    # Test 1: Coupling constant
    lambda_vals = [0.5, 1.0, 2.0, 5.0, 10.0]
    results['lambda'] = test_coupling_constant(N_test, lambda_vals, j=j_opt)
    
    # Test 2: Matter energy
    energy_vals = [1e-16, 1e-15, 1e-14, 1e-13, 1e-12]
    results['energy'] = test_matter_energy(N_test, energy_vals, j=j_opt)
    
    # Test 3: Dimension convergence
    dim_vals = [8, 16, 32, 64]
    results['dimension'] = test_dimension_convergence(N_test, dim_vals, j=j_opt)
    
    # Test 4: Optimal combinations
    results['optimal'] = test_optimal_configuration(N_test, j=j_opt)
    
    # Analysis
    print("\n" + "="*70)
    print("OPTIMIZATION SUMMARY")
    print("="*70)
    
    # λ scaling
    if 'beta_lambda' in results['lambda']:
        beta_lam = results['lambda']['beta_lambda']
        print(f"\n1. Coupling constant: g ∝ λ^{beta_lam:.3f}")
        if beta_lam > 0.9:
            print(f"   ✅ LINEAR scaling - λ directly multiplies coupling")
        else:
            print(f"   ⚠️  Sub-linear - diminishing returns")
    
    # Energy scaling
    if 'beta_energy' in results['energy']:
        beta_E = results['energy']['beta_energy']
        print(f"\n2. Matter energy: g ∝ E^{beta_E:.3f}")
        if beta_E > 0.9:
            print(f"   ✅ LINEAR scaling - E directly multiplies coupling")
        else:
            print(f"   ⚠️  Sub-linear - diminishing returns")
    
    # Dimension convergence
    if 'converged' in results['dimension']:
        conv = results['dimension']['converged']
        print(f"\n3. Dimension: {'✅ Converged' if conv else '⚠️  Not converged'}")
        if not conv:
            print("   Recommend dim≥32 for accurate results")
    
    # Best configuration
    best = max(results['optimal'], key=lambda x: x['enh'])
    baseline = results['optimal'][0]
    boost = best['enh'] / baseline['enh']
    
    print(f"\n4. Best configuration: {best['name']}")
    print(f"   λ={best['lambda']}, E={best['E']:.2e} J, dim={best['dim']}")
    print(f"   Boost vs baseline: {boost:.2f}×")
    
    if boost > 10:
        print(f"   ✅ SIGNIFICANT boost found!")
    elif boost > 2:
        print(f"   ✅ Moderate boost")
    else:
        print(f"   ⚠️  Minimal improvement")
    
    # Projection to N=238
    print(f"\n5. Projection to N=238 (Tier 1 target):")
    # Current at N=20: use best config
    g_N20_best = best['g']
    alpha = 2.073  # From Week 1
    
    # Extrapolate
    g_N238 = g_N20_best * (238/20)**alpha
    target = 3.96e-121 * 1e6
    ratio = g_N238 / target
    
    print(f"   Expected g(N=238, optimized): {g_N238:.3e} J")
    print(f"   Target (10⁶×): {target:.3e} J")
    print(f"   Ratio: {ratio:.3f}")
    
    if ratio >= 1.0:
        print(f"   ✅ TARGET REACHED with optimization!")
    elif ratio >= 0.5:
        print(f"   ⚠️  Close - {1/ratio:.1f}× away")
    else:
        print(f"   ❌ Still short - {1/ratio:.1f}× gap remains")
    
    # Save results
    print("\n" + "="*70)
    print("SAVING RESULTS")
    print("="*70)
    
    # Convert to JSON-serializable
    save_data = {
        'N_test': N_test,
        'j_opt': j_opt,
        'lambda': {k: [float(v) for v in val] if isinstance(val, list) else float(val) 
                   for k, val in results['lambda'].items()},
        'energy': {k: [float(v) for v in val] if isinstance(val, list) else float(val)
                   for k, val in results['energy'].items()},
        'dimension': {k: [float(v) if not isinstance(v, bool) else v for v in val] 
                      if isinstance(val, list) else (float(val) if not isinstance(val, bool) else val)
                      for k, val in results['dimension'].items()},
        'optimal': [{k: (float(v) if isinstance(v, (int, float, np.number)) else v) 
                     for k, v in config.items()} for config in results['optimal']]
    }
    
    with open('parameter_optimization.json', 'w') as f:
        json.dump(save_data, f, indent=2)
    
    print("✅ Data saved: parameter_optimization.json")
    
    # Create plots
    create_optimization_plots(results)
    
    print("\n" + "="*70)
    print("✅ PARAMETER OPTIMIZATION COMPLETE")
    print("="*70)
    
    return results


if __name__ == "__main__":
    results = main()
