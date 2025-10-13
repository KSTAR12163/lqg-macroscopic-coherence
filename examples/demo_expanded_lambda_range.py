#!/usr/bin/env python3
"""
Test: Expanded coupling constant range [10⁻⁶, 10⁻²]

Objectives:
1. Test if λ=10⁻² is still perturbative (|H_int| << |H_geom|)
2. If valid, run full sweep with expanded range
3. Measure actual enhancement vs baseline [10⁻⁸, 10⁻⁴]

Expected: 10²~10⁴× coupling enhancement from stronger λ values
"""

import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.spin_network import SpinNetwork
from src.core.constants import L_PLANCK, HBAR

import importlib
topology_module = importlib.import_module('src.06_topology_exploration')
matter_coupling_module = importlib.import_module('src.04_coupling_engineering.matter_coupling')
field_sweep_module = importlib.import_module('src.05_combined_optimization.field_sweep')

generate_topology = topology_module.generate_topology
MatterFieldProperties = matter_coupling_module.MatterFieldProperties
MatterFieldType = matter_coupling_module.MatterFieldType
MatterGeometryCoupling = matter_coupling_module.MatterGeometryCoupling
field_enhanced_search_parallel = field_sweep_module.field_enhanced_search_parallel


def test_perturbative_validity(network, matter_field, lambda_test=1e-2, mu=0.5, dim=32):
    """
    Test if given λ is in perturbative regime.
    
    Criterion: |H_int| << |H_geom| (interaction much smaller than geometry)
    
    Returns:
        (is_valid, ratio_H_int_to_H_geom)
    """
    print(f"\nTesting λ = {lambda_test:.3e} perturbative validity...")
    
    # Build coupling
    coupling = MatterGeometryCoupling(
        network=network,
        matter_field=matter_field,
        coupling_constant=lambda_test,
        mu=mu
    )
    
    # Build matrices
    H_geom = coupling.build_geometry_operator(dim)
    H_int = coupling.build_interaction_hamiltonian(dim)
    
    # Compute norms
    norm_geom = np.linalg.norm(H_geom)
    norm_int = np.linalg.norm(H_int)
    
    ratio = norm_int / norm_geom
    
    print(f"  |H_geom| = {norm_geom:.3e} J")
    print(f"  |H_int|  = {norm_int:.3e} J")
    print(f"  Ratio    = {ratio:.3e}")
    
    # Perturbative regime: ratio < 0.1 (interaction < 10% of geometry)
    is_valid = ratio < 0.1
    
    if is_valid:
        print(f"  ✓ VALID: Ratio {ratio:.3e} < 0.1 (perturbative)")
    else:
        print(f"  ✗ INVALID: Ratio {ratio:.3e} ≥ 0.1 (non-perturbative)")
    
    return is_valid, ratio


def compare_lambda_ranges(network, matter_field):
    """
    Compare baseline vs expanded λ range.
    
    Baseline: [10⁻⁸, 10⁻⁴]
    Expanded: [10⁻⁶, 10⁻²]
    """
    print("=" * 80)
    print("COMPARING λ RANGES")
    print("=" * 80)
    
    # Test boundaries
    print("\n1. Testing baseline range [10⁻⁸, 10⁻⁴]:")
    valid_min, ratio_min = test_perturbative_validity(network, matter_field, 1e-8)
    valid_max, ratio_max = test_perturbative_validity(network, matter_field, 1e-4)
    
    print("\n2. Testing expanded range [10⁻⁶, 10⁻²]:")
    valid_exp_min, ratio_exp_min = test_perturbative_validity(network, matter_field, 1e-6)
    valid_exp_max, ratio_exp_max = test_perturbative_validity(network, matter_field, 1e-2)
    
    print("\n" + "=" * 80)
    print("VALIDITY SUMMARY")
    print("=" * 80)
    
    print(f"\nBaseline [10⁻⁸, 10⁻⁴]:")
    print(f"  λ=10⁻⁸: {'✓ Valid' if valid_min else '✗ Invalid'} (ratio={ratio_min:.3e})")
    print(f"  λ=10⁻⁴: {'✓ Valid' if valid_max else '✗ Invalid'} (ratio={ratio_max:.3e})")
    
    print(f"\nExpanded [10⁻⁶, 10⁻²]:")
    print(f"  λ=10⁻⁶: {'✓ Valid' if valid_exp_min else '✗ Invalid'} (ratio={ratio_exp_min:.3e})")
    print(f"  λ=10⁻²: {'✓ Valid' if valid_exp_max else '✗ Invalid'} (ratio={ratio_exp_max:.3e})")
    
    # Recommendation
    print("\n" + "=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)
    
    if valid_exp_max:
        print("\n✓ Expanded range [10⁻⁶, 10⁻²] is VALID")
        print("  → Proceed with full sweep")
        print(f"  → Expected coupling boost: {1e-2/1e-4:.0f}× from λ increase")
        return True, (1e-6, 1e-2)
    else:
        # Find maximum valid λ
        test_lambdas = np.logspace(-4, -2, 10)
        max_valid_lambda = 1e-4
        
        for lam in test_lambdas:
            valid, ratio = test_perturbative_validity(network, matter_field, lam)
            if valid:
                max_valid_lambda = lam
            else:
                break
        
        print(f"\n⚠️ Full expansion to 10⁻² is NON-PERTURBATIVE")
        print(f"  → Maximum valid λ ≈ {max_valid_lambda:.3e}")
        print(f"  → Recommend range: [10⁻⁶, {max_valid_lambda:.3e}]")
        return False, (1e-6, max_valid_lambda)


def run_expanded_sweep(network, matter_field, lambda_range):
    """
    Run full sweep with expanded λ range.
    """
    print("\n" + "=" * 80)
    print(f"RUNNING SWEEP WITH λ ∈ [{lambda_range[0]:.3e}, {lambda_range[1]:.3e}]")
    print("=" * 80)
    
    # Parameter grid
    mu_values = np.linspace(0.1, 1.0, 30)  # 30 μ points
    field_values = np.linspace(0, 1e-30, 5)  # 5 field points
    
    print(f"\nGrid: {len(mu_values)}×{len(field_values)} = {len(mu_values)*len(field_values)} points")
    print(f"λ samples: 10 (log-spaced in [{lambda_range[0]:.3e}, {lambda_range[1]:.3e}])\n")
    
    results = field_enhanced_search_parallel(
        network=network,
        mu_values=mu_values,
        field_values=field_values,
        matter_fields={"scalar": matter_field},
        lambda_range=lambda_range,
        n_lambda=10,
        dim=32,
        n_processes=4
    )
    
    # Analyze results
    if results:
        print("\n" + "=" * 80)
        print("TOP 5 RESULTS")
        print("=" * 80)
        
        for idx, r in enumerate(results[:5], 1):
            print(f"\n{idx}. λ*={r.lambda_opt:.3e}, μ={r.mu:.3f}, h={r.external_field:.3e}")
            print(f"   Coupling: {r.coupling_strength:.3e} J")
            print(f"   Driven rate: {r.driven_rate:.3e} Hz")
    
    return results


def main():
    print("=" * 80)
    print("PRIORITY #1: EXPAND λ RANGE")
    print("=" * 80)
    print("\nObjective: Test [10⁻⁶, 10⁻²] for perturbative validity")
    print("Expected: 10²~10⁴× coupling enhancement if valid\n")
    
    # Generate network
    print("Generating octahedral network...")
    network, info = generate_topology(topology_type='octahedral')
    print(f"✓ Network: {info.num_nodes} nodes, {info.num_edges} edges")
    
    # Matter field
    matter_field = MatterFieldProperties(
        field_type=MatterFieldType.SCALAR,
        characteristic_energy=1e-15,
        characteristic_length=L_PLANCK * 1e10,
        impedance=1.0
    )
    
    # Test validity
    is_valid, lambda_range = compare_lambda_ranges(network, matter_field)
    
    # Run sweep with appropriate range
    print("\n" + "=" * 80)
    input("Press Enter to run full sweep with expanded λ range...")
    
    results = run_expanded_sweep(network, matter_field, lambda_range)
    
    print("\n" + "=" * 80)
    print("PRIORITY #1 COMPLETE")
    print("=" * 80)
    print(f"\n✓ Tested λ range: [{lambda_range[0]:.3e}, {lambda_range[1]:.3e}]")
    print(f"✓ Found {len(results)} candidates")
    print("\nNext: Priority #2 (Fix icosahedral topology)")
    print("=" * 80)


if __name__ == "__main__":
    main()
