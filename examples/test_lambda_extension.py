#!/usr/bin/env python3
"""
researcher Priority A: Quick λ Extension Test

Test if λ > 10⁻² breaks perturbative regime.
If any values remain perturbative (ratio < 0.1), we get another 10-100× easily.

This is the critical first check to rule out easy gains.
"""

import numpy as np
import sys
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
print("CRITICAL TEST: λ EXTENSION BEYOND 10⁻²")
print("=" * 80)
print("\nresearcher Question: Can we push λ higher and still stay perturbative?")
print("Criterion: |H_int| / |H_geom| << 0.1")
print("\nIf YES → Another 10-100× for free")
print("If NO → 10⁻² is the hard limit\n")

# Matter field
matter_field = MatterFieldProperties(
    field_type=MatterFieldType.SCALAR,
    characteristic_energy=1e-15,
    characteristic_length=L_PLANCK * 1e10,
    impedance=1.0
)

# Test with optimal parameters from grid search
topology_name = 'tetrahedral'  # Optimal from grid
mu = 0.1  # Optimal from grid
dim = 32

print(f"Test configuration: {topology_name}, μ={mu}, dim={dim}")
print("-" * 80)

# Generate topology
network, info = generate_topology(topology_name)

# Test λ values
lambda_values = [1e-4, 1e-3, 1e-2, 0.1, 0.5, 1.0]
print(f"\nTesting λ values: {lambda_values}\n")

results = []

for lambda_val in lambda_values:
    try:
        # Create coupling
        coupling = MatterGeometryCoupling(network, matter_field, lambda_val, mu=mu)
        
        # Build Hamiltonians
        H_full = coupling.build_full_hamiltonian(dim)
        H_int = coupling.build_interaction_hamiltonian(dim)
        
        # Compute norms
        H_int_norm = np.linalg.norm(H_int, 'fro')
        H_full_norm = np.linalg.norm(H_full, 'fro')
        
        # Perturbative ratio
        ratio = H_int_norm / H_full_norm
        
        # Coupling matrix element
        energies, eigvec = coupling.compute_energy_spectrum(dim)
        coupling_element = abs(eigvec[:, 1].conj() @ H_int @ eigvec[:, 0])
        
        # Store results
        results.append({
            'lambda': lambda_val,
            'ratio': ratio,
            'coupling': coupling_element,
            'perturbative': ratio < 0.1
        })
        
        # Print result
        status = "✓ VALID" if ratio < 0.1 else "✗ NON-PERTURBATIVE"
        print(f"λ = {lambda_val:5.1e}: ratio = {ratio:.4e} {status}")
        print(f"           coupling = {coupling_element:.4e} J")
        
    except Exception as e:
        print(f"λ = {lambda_val:5.1e}: ERROR - {e}")
        results.append({
            'lambda': lambda_val,
            'ratio': float('nan'),
            'coupling': 0.0,
            'perturbative': False
        })

# Analysis
print("\n" + "=" * 80)
print("RESULTS ANALYSIS")
print("=" * 80)

# Find highest valid λ
valid_lambdas = [r for r in results if r['perturbative']]
if valid_lambdas:
    max_valid = max(valid_lambdas, key=lambda x: x['lambda'])
    baseline = next(r for r in results if r['lambda'] == 1e-4)
    
    print(f"\n✓ Highest valid λ: {max_valid['lambda']:.2e}")
    print(f"  Perturbative ratio: {max_valid['ratio']:.4e}")
    print(f"  Coupling: {max_valid['coupling']:.4e} J")
    
    enhancement = max_valid['coupling'] / baseline['coupling']
    print(f"\n✓ Enhancement over baseline (λ=10⁻⁴): {enhancement:.1f}×")
    
    if max_valid['lambda'] > 1e-2:
        gain = enhancement / 100  # Relative to known 100× at λ=10⁻²
        print(f"\n🎯 EXTRA GAIN BEYOND λ=10⁻²: {gain:.1f}×")
        print("   → This is NEW TERRITORY!")
    else:
        print(f"\n→ Confirms λ=10⁻² is the limit")
        print("   → No easy gains beyond this point")
else:
    print("\n✗ No valid λ values found (all non-perturbative)")

# Detailed breakdown
print("\n" + "=" * 80)
print("DETAILED BREAKDOWN")
print("=" * 80)
print(f"\n{'λ':>10s} {'Ratio':>12s} {'Coupling':>15s} {'vs 1e-4':>10s} {'Status':>20s}")
print("-" * 80)

baseline = next(r for r in results if r['lambda'] == 1e-4)
for r in results:
    if r['coupling'] > 0:
        enhancement = r['coupling'] / baseline['coupling']
        status = "✓ Perturbative" if r['perturbative'] else "✗ Non-perturbative"
        print(f"{r['lambda']:>10.2e} {r['ratio']:>12.4e} {r['coupling']:>15.4e} {enhancement:>10.1f}× {status:>20s}")
    else:
        print(f"{r['lambda']:>10.2e} {'ERROR':>12s} {'ERROR':>15s} {'N/A':>10s} {'✗ Failed':>20s}")

# Conclusion
print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)

if valid_lambdas:
    max_lambda = max(r['lambda'] for r in valid_lambdas)
    if max_lambda > 1e-2:
        print(f"\n✅ CAN push λ beyond 10⁻² to {max_lambda:.2e}")
        print(f"   → Additional enhancement: {enhancement/100:.1f}× beyond known 100×")
        print(f"   → Total from λ alone: {enhancement:.1f}×")
        print("\n🎯 THIS IS A SIGNIFICANT FINDING!")
        print("   Update all calculations with new λ limit")
    else:
        print(f"\n❌ CANNOT push λ beyond 10⁻²")
        print(f"   → λ=10⁻² is the perturbative limit (ratio = {max_valid['ratio']:.4e})")
        print(f"   → Known 100× enhancement is the maximum from λ")
        print("\n→ No easy gains available")
        print("   → Must pursue new physics mechanisms")
else:
    print("\n❌ All λ values non-perturbative or failed")
    print("   → Something wrong with setup or parameters")

print("\n" + "=" * 80)
print("NEXT STEPS")
print("=" * 80)

if valid_lambdas and max(r['lambda'] for r in valid_lambdas) > 1e-2:
    print("\n1. Update baseline λ to maximum valid value")
    print("2. Re-run multi-parameter optimization with new λ range")
    print("3. Recalculate cumulative enhancement")
    print("4. Check if this closes gap meaningfully (unlikely but check)")
else:
    print("\n1. ✓ Confirm λ=10⁻² is hard limit")
    print("2. → Move to researcher Path 1: Theory investigation")
    print("3.    a) N-scaling analysis (does f_eff ∝ N² exist?)")
    print("4.    b) Critical point search (diverging susceptibility?)")
    print("5.    c) Topological protection calculation")
    print("6. → Concurrent: Write Phase 1 paper (Path 3)")

print("=" * 80)
