#!/usr/bin/env python3
"""
Profile the field sweep to identify computational bottlenecks.

This will tell us whether:
1. 6j symbol computation is the bottleneck → Use generating functional
2. Matrix diagonalization is the bottleneck → Use sparse methods or parallelize
"""

import time
import cProfile
import pstats
from io import StringIO

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import importlib

# Import modules with numeric prefixes
topology_module = importlib.import_module('src.06_topology_exploration')
resonance_module = importlib.import_module('src.03_critical_effects.resonance_search')

from src.core.spin_network import SpinNetwork, wigner_6j
from src.core.constants import L_PLANCK, GAMMA_IMMIRZI

generate_topology = topology_module.generate_topology
GeometricHamiltonian = resonance_module.GeometricHamiltonian


def profile_hamiltonian_construction():
    """Profile building and diagonalizing a single Hamiltonian."""
    
    print("=" * 80)
    print("PROFILING: Hamiltonian Construction & Diagonalization")
    print("=" * 80)
    
    # Generate small octahedral network
    print("\nGenerating network...")
    network = generate_topology(topology_type='octahedral', avg_spin=1.0)
    print(f"  Nodes: {len(network.nodes)}, Edges: {len(network.edges)}")
    
    # Parameters
    mu = 0.5
    external_field = 0.0
    n_trials = 10
    
    print(f"\nProfiling {n_trials} Hamiltonian builds + diagonalizations...")
    
    # Profile complete operation
    profiler = cProfile.Profile()
    profiler.enable()
    
    for i in range(n_trials):
        ham = GeometricHamiltonian(
            network=network,
            mu=mu,
            external_field=external_field
        )
        eigenvalues, eigenvectors = ham.diagonalize()
    
    profiler.disable()
    
    # Print statistics
    s = StringIO()
    stats = pstats.Stats(profiler, stream=s)
    stats.strip_dirs()
    stats.sort_stats('cumulative')
    stats.print_stats(30)  # Top 30 functions
    
    print("\n" + "=" * 80)
    print("TOP 30 FUNCTIONS BY CUMULATIVE TIME")
    print("=" * 80)
    print(s.getvalue())
    
    # Also get timing breakdown
    print("\n" + "=" * 80)
    print("DETAILED TIMING BREAKDOWN")
    print("=" * 80)
    
    # Time just 6j symbols
    print("\nTiming 6j symbol calls...")
    start = time.perf_counter()
    for _ in range(1000):
        _ = wigner_6j(1.0, 1.0, 1.0, 1.0, 1.0, 1.0)
    t_6j = (time.perf_counter() - start) / 1000
    print(f"  Average 6j call: {t_6j*1e6:.2f} μs")
    
    # Time Hamiltonian construction (no diagonalization)
    print("\nTiming Hamiltonian construction...")
    start = time.perf_counter()
    for _ in range(n_trials):
        ham = GeometricHamiltonian(
            network=network,
            mu=mu,
            external_field=external_field
        )
        _ = ham.build_hamiltonian()  # Build matrix
    t_build = (time.perf_counter() - start) / n_trials
    print(f"  Average build time: {t_build*1000:.2f} ms")
    
    # Time just diagonalization
    print("\nTiming diagonalization...")
    ham = GeometricHamiltonian(network=network, mu=mu, external_field=external_field)
    H_matrix = ham.build_hamiltonian()
    
    start = time.perf_counter()
    for _ in range(n_trials):
        eigenvalues, eigenvectors = np.linalg.eigh(H_matrix)
    t_diag = (time.perf_counter() - start) / n_trials
    print(f"  Average diagonalization: {t_diag*1000:.2f} ms")
    print(f"  Matrix dimension: {H_matrix.shape}")
    
    # Summary
    print("\n" + "=" * 80)
    print("BOTTLENECK ANALYSIS")
    print("=" * 80)
    total_per_point = t_build + t_diag
    print(f"\nTime per grid point: {total_per_point*1000:.2f} ms")
    print(f"  - Hamiltonian construction: {t_build*1000:.2f} ms ({t_build/total_per_point*100:.1f}%)")
    print(f"  - Diagonalization:          {t_diag*1000:.2f} ms ({t_diag/total_per_point*100:.1f}%)")
    
    # Estimate full sweep time
    n_field = 20
    n_mu = 50
    total_points = n_field * n_mu
    estimated_time = total_points * total_per_point
    
    print(f"\nEstimated time for {n_field}×{n_mu} grid:")
    print(f"  Sequential: {estimated_time:.1f} s ({estimated_time/60:.1f} min)")
    print(f"  20-core parallel: {estimated_time/20:.1f} s ({estimated_time/20/60:.1f} min)")
    
    # Speedup potential
    print("\n" + "=" * 80)
    print("OPTIMIZATION OPPORTUNITIES")
    print("=" * 80)
    
    if t_build > 0.5 * total_per_point:
        print("\n✓ Hamiltonian construction is dominant (>50% of time)")
        print("  → Optimizing 6j symbols could help")
        print("  → Use generating functional approach")
        print(f"  → Potential speedup: 2-10× if 6j symbols are the bottleneck")
    else:
        print("\n✓ Diagonalization is dominant")
        print("  → Optimizing 6j symbols won't help much")
        print("  → Use sparse matrix methods or parallel execution")
    
    print("\n✓ Parallel execution opportunities:")
    print("  - Each field value is independent → 20× speedup possible")
    print("  - Each μ value is independent → 50× speedup possible")
    print("  - Combined: up to 1000× speedup with proper infrastructure")
    
    return {
        't_6j': t_6j,
        't_build': t_build,
        't_diag': t_diag,
        'matrix_dim': H_matrix.shape[0]
    }


def profile_6j_cache_performance():
    """Test 6j symbol cache hit rate."""
    
    print("\n" + "=" * 80)
    print("6J SYMBOL CACHE PERFORMANCE")
    print("=" * 80)
    
    # Typical spin values in LQG
    spins = [0.5, 1.0, 1.5, 2.0]
    n_calls = 10000
    
    print(f"\nTesting {n_calls} 6j calls with typical LQG spins...")
    
    start = time.perf_counter()
    for i in range(n_calls):
        # Random but realistic 6j symbols
        j1 = np.random.choice(spins)
        j2 = np.random.choice(spins)
        j3 = np.random.choice(spins)
        j4 = np.random.choice(spins)
        j5 = np.random.choice(spins)
        j6 = np.random.choice(spins)
        
        _ = wigner_6j(j1, j2, j3, j4, j5, j6)
    
    elapsed = time.perf_counter() - start
    avg_time = elapsed / n_calls
    
    print(f"  Average time per 6j call: {avg_time*1e6:.2f} μs")
    print(f"  Total time for {n_calls} calls: {elapsed:.2f} s")
    
    # Compare with first-time calls (no cache)
    print("\n  Cache effectiveness:")
    print("    - With cache: Fast (most likely ~0.1-1 μs)")
    print("    - Without cache: Slow (SymPy recursion ~10-100 μs)")
    print("    → Generating functional could give ~10-100× here")


if __name__ == "__main__":
    print("\nLQG FIELD SWEEP PROFILING")
    print("=" * 80)
    print("Objective: Identify computational bottlenecks")
    print("=" * 80)
    
    # Profile Hamiltonian operations
    timing = profile_hamiltonian_construction()
    
    # Profile 6j cache
    profile_6j_cache_performance()
    
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    if timing['t_build'] > 2 * timing['t_diag']:
        print("\n1. PRIMARY: Optimize 6j symbols with generating functional")
        print("   - Expected speedup: 2-10×")
        print("   - Integrate code from su2-3nj-generating-functional")
        print("\n2. SECONDARY: Parallelize field sweep")
        print("   - Expected speedup: 10-20× (number of cores)")
    else:
        print("\n1. PRIMARY: Parallelize field sweep")
        print("   - Expected speedup: 10-20× (number of cores)")
        print("   - Each field value is independent")
        print("\n2. SECONDARY: Use sparse matrix methods")
        print("   - scipy.sparse.linalg.eigsh for large matrices")
        print("   - Only compute needed eigenvalues")
        print("\n3. TERTIARY: Optimize 6j symbols if needed")
        print("   - Expected additional speedup: 1.5-3×")
    
    print("\n" + "=" * 80)
