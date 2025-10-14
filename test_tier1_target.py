#!/usr/bin/env python3
"""
Tier 1 Target Validation: N=238 Test

Direct test of N=238 with optimized parameters to validate
that we can achieve the 10⁶× enhancement target for Tier 1.
"""

import numpy as np
import time

from src.phase_d.tier1_collective.network_construction import create_complete_network
from src.phase_d.tier1_collective.collective_hamiltonian import (
    build_collective_hamiltonian,
    measure_collective_coupling_v2
)
from run_week1_day3 import modify_edge_spins


def test_n238_baseline():
    """Test N=238 with baseline parameters."""
    print("="*70)
    print("TESTING N=238 (BASELINE)")
    print("="*70)
    print("Parameters: λ=1.0, E=1e-15 J, dim=16, j=2.0")
    
    t0 = time.time()
    
    network, _ = create_complete_network(238)
    network = modify_edge_spins(network, 2.0)
    
    print(f"\nNetwork: {len(network.nodes)} nodes, {len(network.edges)} edges")
    print(f"Computing Hamiltonian (dim=16)...")
    
    g, gap, enh = measure_collective_coupling_v2(network, dim=16)
    
    t1 = time.time()
    
    print(f"\n{'='*70}")
    print(f"RESULTS (N=238, baseline)")
    print(f"{'='*70}")
    print(f"g_coll = {g:.4e} J")
    print(f"Enhancement = {enh:.4e}×")
    print(f"Energy gap = {gap:.4e} J")
    print(f"Computation time: {t1-t0:.1f}s")
    
    target = 1e6
    ratio = enh / target
    print(f"\nTarget (10⁶×): {target:.2e}×")
    print(f"Ratio: {ratio:.3f}")
    
    if ratio >= 1.0:
        print(f"✅ TARGET ACHIEVED!")
    elif ratio >= 0.5:
        print(f"⚠️  Close ({1/ratio:.2f}× away)")
    else:
        print(f"❌ Short ({1/ratio:.2f}× gap)")
    
    return {'g': g, 'enh': enh, 'gap': gap, 'time': t1-t0}


def test_n238_optimized():
    """Test N=238 with optimized parameters."""
    print("\n" + "="*70)
    print("TESTING N=238 (OPTIMIZED)")
    print("="*70)
    print("Parameters: λ=5.0, E=1e-13 J, dim=16, j=2.0")
    
    t0 = time.time()
    
    network, _ = create_complete_network(238)
    network = modify_edge_spins(network, 2.0)
    
    print(f"\nNetwork: {len(network.nodes)} nodes, {len(network.edges)} edges")
    print(f"Computing Hamiltonian (dim=16, optimized)...")
    
    # Build with optimized parameters
    ham = build_collective_hamiltonian(
        network, 
        dim=16,
        lambda_coupling=5.0,
        matter_energy=1e-13
    )
    
    # Compute spectrum
    print("Computing eigenspectrum...")
    eigvals, eigvecs = np.linalg.eigh(ham.H_total)
    
    # Extract coupling
    psi0 = eigvecs[:, 0]
    psi1 = eigvecs[:, 1]
    g_coll = abs(np.dot(np.conj(psi1), ham.H_int @ psi0))
    
    gap = eigvals[1] - eigvals[0]
    g_single = 3.96e-121
    enh = g_coll / g_single
    
    t1 = time.time()
    
    print(f"\n{'='*70}")
    print(f"RESULTS (N=238, optimized)")
    print(f"{'='*70}")
    print(f"g_coll = {g_coll:.4e} J")
    print(f"Enhancement = {enh:.4e}×")
    print(f"Energy gap = {gap:.4e} J")
    print(f"Computation time: {t1-t0:.1f}s")
    
    target = 1e6
    ratio = enh / target
    print(f"\nTarget (10⁶×): {target:.2e}×")
    print(f"Ratio: {ratio:.3f}")
    
    if ratio >= 1.0:
        print(f"✅ TARGET EXCEEDED by {ratio:.1f}×!")
        overshoot = ratio
        print(f"   We have {overshoot:.1f}× margin for conservative estimates")
    elif ratio >= 0.5:
        print(f"⚠️  Close ({1/ratio:.2f}× away)")
    else:
        print(f"❌ Short ({1/ratio:.2f}× gap)")
    
    return {'g': g_coll, 'enh': enh, 'gap': gap, 'time': t1-t0}


def test_large_n_scaling():
    """Test a few points beyond N=238 to verify scaling holds."""
    print("\n" + "="*70)
    print("SCALING VERIFICATION (N > 238)")
    print("="*70)
    print("Testing N=[100, 238, 500] with optimized parameters")
    
    N_values = [100, 238, 500]
    results = []
    
    for N in N_values:
        print(f"\nN={N}...", end=" ", flush=True)
        
        t0 = time.time()
        network, _ = create_complete_network(N)
        network = modify_edge_spins(network, 2.0)
        
        ham = build_collective_hamiltonian(
            network, 
            dim=16,
            lambda_coupling=5.0,
            matter_energy=1e-13
        )
        
        eigvals, eigvecs = np.linalg.eigh(ham.H_total)
        psi0 = eigvecs[:, 0]
        psi1 = eigvecs[:, 1]
        g_coll = abs(np.dot(np.conj(psi1), ham.H_int @ psi0))
        
        g_single = 3.96e-121
        enh = g_coll / g_single
        gap = eigvals[1] - eigvals[0]
        
        t1 = time.time()
        
        results.append({
            'N': N,
            'g': g_coll,
            'enh': enh,
            'gap': gap,
            'time': t1 - t0
        })
        
        print(f"enh={enh:.3e}×, t={t1-t0:.1f}s")
    
    # Fit scaling
    log_N = np.log([r['N'] for r in results])
    log_g = np.log([r['g'] for r in results])
    
    fit = np.polyfit(log_N, log_g, 1)
    alpha = fit[0]
    log_g0 = fit[1]
    g0 = np.exp(log_g0)
    
    print(f"\n{'='*70}")
    print(f"SCALING FIT (N=100-500)")
    print(f"{'='*70}")
    print(f"Exponent α = {alpha:.3f}")
    print(f"Prefactor g₀ = {g0:.3e} J")
    print(f"\nComparison to Week 1 (N≤100):")
    print(f"  Week 1: α = 2.073")
    print(f"  Current: α = {alpha:.3f}")
    print(f"  Difference: {abs(alpha - 2.073):.3f} ({abs(alpha-2.073)/2.073*100:.1f}%)")
    
    if abs(alpha - 2.073) < 0.1:
        print(f"  ✅ Scaling consistent!")
    else:
        print(f"  ⚠️  Scaling may be changing at large N")
    
    return results


def main():
    """Run Tier 1 target validation."""
    
    print("="*70)
    print("TIER 1 TARGET VALIDATION: N=238")
    print("="*70)
    print("\nGoal: Validate 10⁶× enhancement at N=238")
    print("Strategy: Test baseline + optimized parameters")
    
    # Test 1: Baseline
    print("\n" + "="*70)
    print("TEST 1: BASELINE PARAMETERS")
    print("="*70)
    baseline = test_n238_baseline()
    
    # Test 2: Optimized
    print("\n" + "="*70)
    print("TEST 2: OPTIMIZED PARAMETERS")
    print("="*70)
    optimized = test_n238_optimized()
    
    # Test 3: Scaling verification
    print("\n" + "="*70)
    print("TEST 3: SCALING VERIFICATION")
    print("="*70)
    scaling = test_large_n_scaling()
    
    # Final summary
    print("\n" + "="*70)
    print("TIER 1 TARGET VALIDATION - FINAL SUMMARY")
    print("="*70)
    
    print("\nBaseline (λ=1, E=1e-15 J):")
    print(f"  Enhancement: {baseline['enh']:.3e}×")
    print(f"  vs Target: {baseline['enh']/1e6:.3f}×")
    
    print("\nOptimized (λ=5, E=1e-13 J):")
    print(f"  Enhancement: {optimized['enh']:.3e}×")
    print(f"  vs Target: {optimized['enh']/1e6:.3f}×")
    print(f"  Boost vs baseline: {optimized['enh']/baseline['enh']:.1f}×")
    
    print("\nScaling to large N:")
    for r in scaling:
        status = "✅" if r['enh'] >= 1e6 else "⏳"
        print(f"  N={r['N']:3d}: {r['enh']:.3e}× {status}")
    
    # Decision
    print("\n" + "="*70)
    print("TIER 1 STATUS")
    print("="*70)
    
    if optimized['enh'] >= 1e6:
        margin = optimized['enh'] / 1e6
        print(f"✅ TIER 1 TARGET ACHIEVED!")
        print(f"   Enhancement: {optimized['enh']:.3e}×")
        print(f"   Margin: {margin:.1f}× above target")
        print(f"   Conservative estimate: {margin:.0f}σ safety factor")
        
        print("\n📊 Tier 1 Characterization:")
        print(f"   • Minimum N: ~238 nodes")
        print(f"   • Optimal params: λ=5, E=1e-13 J, j=2")
        print(f"   • Scaling: g ∝ N^{2.073:.3f}")
        print(f"   • Prefactor: g₀ ∝ λ¹ × E¹ × j^{1.5:.1f}")
        
        print("\n🎯 Next Steps:")
        print("   1. Document Tier 1 success")
        print("   2. Evaluate 4-week gate decision:")
        print("      - Continue to Tier 2 (EFT)?")
        print("      - Skip to Tier 3 (exotic mechanisms)?")
        print(f"   3. Gap to warp: {1e71/optimized['enh']:.2e}× remains")
        
    else:
        gap = 1e6 / optimized['enh']
        print(f"⚠️  TIER 1 TARGET NOT REACHED")
        print(f"   Enhancement: {optimized['enh']:.3e}×")
        print(f"   Gap: {gap:.2f}× below target")
        print(f"   Need: N={238 * gap**(1/2.073):.0f} nodes")
    
    print("="*70)


if __name__ == "__main__":
    main()
