#!/usr/bin/env python3
"""
Priority #4: Multi-Parameter Grid Optimization

Systematic grid search across key parameters to find global optimum:
- Topology: {tetrahedral, cubic, octahedral}
- μ: [0.1, 1.0]
- λ: [1e-6, 1e-2]
- dim: {16, 32, 64}

This will establish baseline before implementing Bayesian optimization.
"""

import numpy as np
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.constants import L_PLANCK

import importlib
topology_module = importlib.import_module('src.06_topology_exploration')
matter_coupling_module = importlib.import_module('src.04_coupling_engineering.matter_coupling')

generate_topology = topology_module.generate_topology
MatterFieldProperties = matter_coupling_module.MatterFieldProperties
MatterFieldType = matter_coupling_module.MatterFieldType
MatterGeometryCoupling = matter_coupling_module.MatterGeometryCoupling

print("=" * 80)
print("MULTI-PARAMETER GRID OPTIMIZATION")
print("=" * 80)

# Matter field (fixed)
matter_field = MatterFieldProperties(
    field_type=MatterFieldType.SCALAR,
    characteristic_energy=1e-15,
    characteristic_length=L_PLANCK * 1e10,
    impedance=1.0
)

def evaluate_point(topology_name, mu, lambda_val, dim):
    """Evaluate coupling strength at a parameter point."""
    try:
        # Generate topology
        network, info = generate_topology(topology_name)
        
        # Create coupling
        coupling = MatterGeometryCoupling(network, matter_field, lambda_val, mu=mu)
        
        # Compute spectrum
        energies, eigenvectors = coupling.compute_energy_spectrum(dim)
        
        # Build interaction Hamiltonian
        H_int = coupling.build_interaction_hamiltonian(dim)
        
        # Coupling matrix element
        coupling_element = abs(eigenvectors[:, 1].conj() @ H_int @ eigenvectors[:, 0])
        
        return coupling_element
        
    except Exception as e:
        return 0.0

print("\nDefining parameter grid...")

# Define grid
topologies = ['tetrahedral', 'cubic', 'octahedral']
mu_values = [0.1, 0.3, 0.5, 0.7, 0.9]
lambda_values = [1e-6, 1e-5, 1e-4, 1e-3, 1e-2]
dims = [32]  # Start with single dimension

total_points = len(topologies) * len(mu_values) * len(lambda_values) * len(dims)

print(f"\nGrid configuration:")
print(f"  Topologies: {topologies}")
print(f"  μ values: {mu_values}")
print(f"  λ values: {lambda_values}")
print(f"  dims: {dims}")
print(f"  Total points: {total_points}")

print(f"\nEstimated time: ~{total_points * 0.5:.0f} seconds (~{total_points * 0.5 / 60:.1f} minutes)")

# Run grid search
print("\n" + "=" * 80)
print("RUNNING GRID SEARCH")
print("=" * 80)

results = []
start_time = time.time()

for i, topology in enumerate(topologies):
    print(f"\nTopology: {topology}")
    print("-" * 40)
    
    for j, mu in enumerate(mu_values):
        for k, lambda_val in enumerate(lambda_values):
            for dim in dims:
                coupling = evaluate_point(topology, mu, lambda_val, dim)
                results.append({
                    'topology': topology,
                    'mu': mu,
                    'lambda': lambda_val,
                    'dim': dim,
                    'coupling': coupling
                })
                
                # Progress indicator
                idx = i * len(mu_values) * len(lambda_values) + j * len(lambda_values) + k
                progress = (idx + 1) / total_points * 100
                print(f"  [{progress:5.1f}%] μ={mu:.1f} λ={lambda_val:.0e} → {coupling:.3e} J", end='\r')
    
    print()  # Newline after topology

elapsed = time.time() - start_time
print(f"\n✓ Grid search complete in {elapsed:.1f} seconds")

# Analyze results
print("\n" + "=" * 80)
print("RESULTS ANALYSIS")
print("=" * 80)

# Sort by coupling (descending)
results_sorted = sorted(results, key=lambda x: x['coupling'], reverse=True)

# Top 10
print("\nTop 10 parameter combinations:")
print("-" * 80)
for i, r in enumerate(results_sorted[:10], 1):
    print(f"{i:2d}. {r['topology']:12s} μ={r['mu']:.1f} λ={r['lambda']:.2e} dim={r['dim']:2d} → {r['coupling']:.6e} J")

# Best result
best = results_sorted[0]
print("\n" + "=" * 80)
print("OPTIMAL PARAMETERS")
print("=" * 80)
print(f"\n✓ Best coupling: {best['coupling']:.6e} J")
print(f"  Topology: {best['topology']}")
print(f"  μ: {best['mu']}")
print(f"  λ: {best['lambda']:.2e}")
print(f"  dim: {best['dim']}")

# Baseline comparison
baseline_idx = next(i for i, r in enumerate(results_sorted) 
                   if r['topology'] == 'octahedral' and r['mu'] == 0.5 
                   and r['lambda'] == 1e-4 and r['dim'] == 32)
baseline = results_sorted[baseline_idx]

print(f"\nBaseline (octahedral, μ=0.5, λ=1e-4, dim=32):")
print(f"  Coupling: {baseline['coupling']:.6e} J")
print(f"  Rank: {baseline_idx + 1}/{total_points}")

enhancement = best['coupling'] / baseline['coupling']
print(f"\n✓ ENHANCEMENT: {enhancement:.2f}×")

# Analysis by parameter
print("\n" + "=" * 80)
print("PARAMETER IMPORTANCE")
print("=" * 80)

# λ dependence
print("\nλ dependence (octahedral, μ=0.5, dim=32):")
for lambda_val in lambda_values:
    r = next(r for r in results if r['topology'] == 'octahedral' 
             and r['mu'] == 0.5 and r['lambda'] == lambda_val and r['dim'] == 32)
    ratio = r['coupling'] / baseline['coupling']
    print(f"  λ={lambda_val:.0e}: {r['coupling']:.3e} J ({ratio:.1f}× baseline)")

# μ dependence
print(f"\nμ dependence (octahedral, λ=1e-4, dim=32):")
for mu in mu_values:
    r = next(r for r in results if r['topology'] == 'octahedral' 
             and r['mu'] == mu and r['lambda'] == 1e-4 and r['dim'] == 32)
    ratio = r['coupling'] / baseline['coupling']
    print(f"  μ={mu:.1f}: {r['coupling']:.3e} J ({ratio:.1f}× baseline)")

# Topology dependence
print(f"\nTopology dependence (μ=0.5, λ=1e-4, dim=32):")
for topology in topologies:
    r = next(r for r in results if r['topology'] == topology 
             and r['mu'] == 0.5 and r['lambda'] == 1e-4 and r['dim'] == 32)
    ratio = r['coupling'] / baseline['coupling']
    print(f"  {topology:12s}: {r['coupling']:.3e} J ({ratio:.1f}× baseline)")

print("\n" + "=" * 80)
print("KEY INSIGHTS")
print("=" * 80)

# Determine dominant factor
lambda_range = max(r['coupling'] for r in results) / min(r['coupling'] for r in results if r['coupling'] > 0)
print(f"\nParameter sensitivity:")
print(f"  λ range: {lambda_range:.1f}× (across 4 orders of magnitude)")

print("\nRecommendations:")
if enhancement > 100:
    print("  ✓ Significant optimization potential found!")
    print(f"  → Use optimal parameters: {best['topology']}, μ={best['mu']}, λ={best['lambda']:.0e}")
elif enhancement > 10:
    print("  ✓ Moderate improvement available")
    print(f"  → Consider using: {best['topology']}, μ={best['mu']}, λ={best['lambda']:.0e}")
else:
    print("  → Current baseline already near-optimal")
    print("  → Focus on other enhancement mechanisms")

print("\n" + "=" * 80)
print("NEXT STEPS")
print("=" * 80)
print("\n1. Refine grid around optimal region")
print("2. Test with dim=64 for best parameters")
print("3. Add external field optimization")
print("4. Implement Bayesian optimization (requires: pip install scikit-optimize)")
print("=" * 80)
