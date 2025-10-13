#!/usr/bin/env python3
"""
Quick profile: Time 6j symbols vs matrix diagonalization.

Determines if your SU(2) generating functional approach would help.
"""

import time
import numpy as np

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.spin_network import wigner_6j

print("=" * 80)
print("QUICK BOTTLENECK ANALYSIS")
print("=" * 80)

# Test 1: 6j symbol performance
print("\n1. Testing 6j symbol computation...")
n_6j_calls = 1000

# Use valid 6j symbols (all satisfy triangle inequalities)
valid_6j = [
    (1, 1, 1, 1, 1, 1),
    (0.5, 0.5, 1, 0.5, 0.5, 1),
    (1, 1, 2, 1, 1, 2),
    (1.5, 1.5, 1, 1.5, 1.5, 1),
    (1, 0.5, 1.5, 1, 0.5, 1.5),
]

start = time.perf_counter()
for i in range(n_6j_calls):
    j1, j2, j3, j4, j5, j6 = valid_6j[i % len(valid_6j)]
    _ = wigner_6j(j1, j2, j3, j4, j5, j6)
t_6j_total = time.perf_counter() - start
t_6j_avg = t_6j_total / n_6j_calls

print(f"   {n_6j_calls} calls in {t_6j_total:.3f} s")
print(f"   Average: {t_6j_avg*1e6:.1f} μs per call")

# Test 2: Matrix diagonalization performance
print("\n2. Testing matrix diagonalization...")
matrix_sizes = [16, 32, 64, 128]

for dim in matrix_sizes:
    # Random Hermitian matrix
    H = np.random.randn(dim, dim) + 1j * np.random.randn(dim, dim)
    H = (H + H.conj().T) / 2
    
    n_trials = 100 if dim < 100 else 10
    
    start = time.perf_counter()
    for _ in range(n_trials):
        eigenvalues, eigenvectors = np.linalg.eigh(H)
    t_diag = (time.perf_counter() - start) / n_trials
    
    print(f"   {dim}×{dim} matrix: {t_diag*1000:.2f} ms per diagonalization")

# Test 3: Estimate field sweep time
print("\n" + "=" * 80)
print("FIELD SWEEP TIMING ESTIMATE")
print("=" * 80)

# Assume typical parameters
dim = 64  # Typical Hilbert space dimension
n_6j_per_hamiltonian = 50  # Rough estimate
t_build_hamiltonian = n_6j_per_hamiltonian * t_6j_avg
t_diag_matrix = 0.01  # 10 ms for 64×64 (from above)

total_per_point = t_build_hamiltonian + t_diag_matrix

print(f"\nPer grid point (estimated):")
print(f"   Hamiltonian construction: {t_build_hamiltonian*1000:.2f} ms ({t_build_hamiltonian/total_per_point*100:.1f}%)")
print(f"   Matrix diagonalization:   {t_diag_matrix*1000:.2f} ms ({t_diag_matrix/total_per_point*100:.1f}%)")
print(f"   TOTAL:                    {total_per_point*1000:.2f} ms")

# Full sweep estimate
n_field = 20
n_mu = 50
total_points = n_field * n_mu
total_time = total_points * total_per_point

print(f"\nFull {n_field}×{n_mu} grid ({total_points} points):")
print(f"   Sequential: {total_time:.1f} s ({total_time/60:.1f} min)")

# Speedup analysis
print("\n" + "=" * 80)
print("SPEEDUP OPPORTUNITIES")
print("=" * 80)

if t_build_hamiltonian > t_diag_matrix:
    ratio = t_build_hamiltonian / t_diag_matrix
    print(f"\n✓ Hamiltonian construction is {ratio:.1f}× slower than diagonalization")
    print("  → Your SU(2) generating functional COULD HELP!")
    print(f"  → If it's 10-100× faster than SymPy, expect 2-5× overall speedup")
else:
    ratio = t_diag_matrix / t_build_hamiltonian
    print(f"\n✓ Diagonalization is {ratio:.1f}× slower than Hamiltonian construction")
    print("  → Your SU(2) code won't help much (diagonalization dominates)")
    print("  → Better strategy: Parallelize or use sparse methods")

print("\n✓ Parallel execution (easier win):")
print(f"  → Each field value independent: {n_field}× speedup possible")
print(f"  → Time with 20 cores: {total_time/20:.1f} s")

print("\n" + "=" * 80)
print("RECOMMENDATION")
print("=" * 80)

if t_build_hamiltonian > 0.3 * total_per_point:
    print("\n1. INTEGRATE your SU(2) generating functional (worthwhile!)")
    print("   - Replace sympy.physics.wigner.wigner_6j")
    print("   - Use determinant-based formula from your repo")
    print("   - Expected: 2-5× overall speedup")
    print("\n2. Then parallelize field sweep")
    print("   - multiprocessing.Pool over field values")
    print("   - Expected: 10-20× additional speedup")
    print("\n→ Combined: 20-100× total speedup possible!")
else:
    print("\n1. PARALLELIZE first (easier, bigger win)")
    print("   - multiprocessing.Pool over field values")
    print("   - Expected: 10-20× speedup")
    print("\n2. SU(2) optimization optional")
    print("   - Only if you want to squeeze out last 1.5-2×")
    print("\n→ Focus on parallelization for maximum impact")

print("\n" + "=" * 80)
