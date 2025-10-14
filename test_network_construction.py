#!/usr/bin/env python3
"""
Test network construction for Week 1 Day 2.

This script validates the network construction implementations
and measures collective coupling for small N values.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.phase_d.tier1_collective.network_construction import (
    measure_collective_coupling,
    run_scaling_study
)

print("=" * 70)
print("WEEK 1 DAY 2: NETWORK CONSTRUCTION TEST")
print("=" * 70)
print()

# ============================================================================
# TEST 1: Single Node (N=4, tetrahedral equivalent)
# ============================================================================

print("TEST 1: N=4 (Complete Graph)")
print("-" * 70)

try:
    result = measure_collective_coupling(4, topology="complete", dim=32)
    print(f"\n✅ SUCCESS")
    print(f"   N = {result.N}")
    print(f"   g_single = {result.g_single:.2e} J")
    print(f"   g_coll = {result.g_coll:.2e} J")
    print(f"   Enhancement = {result.enhancement:.2f}×")
    print(f"   Gap Δ = {result.Delta:.2e} J")
except Exception as e:
    print(f"\n❌ FAILED: {e}")
    import traceback
    traceback.print_exc()

print()

# ============================================================================
# TEST 2: Larger Network (N=10)
# ============================================================================

print("TEST 2: N=10 (Complete Graph)")
print("-" * 70)

try:
    result = measure_collective_coupling(10, topology="complete", dim=32)
    print(f"\n✅ SUCCESS")
    print(f"   N = {result.N}")
    print(f"   g_coll = {result.g_coll:.2e} J")
    print(f"   Enhancement = {result.enhancement:.2f}×")
except Exception as e:
    print(f"\n❌ FAILED: {e}")
    import traceback
    traceback.print_exc()

print()

# ============================================================================
# TEST 3: Small Scaling Study
# ============================================================================

print("TEST 3: Small Scaling Study (N = 4, 10)")
print("-" * 70)

try:
    N_values = [4, 10]
    study_results = run_scaling_study(N_values, topology="complete")
    
    print(f"\n✅ SUCCESS")
    print(f"   Fitted α = {study_results['scaling_exponent']:.3f}")
    print(f"   Prefactor A = {study_results['A']:.2e} J")
    
    # Check if results make sense
    alpha = study_results['scaling_exponent']
    if 0.3 <= alpha <= 2.5:
        print(f"   ✓ α in reasonable range [0.3, 2.5]")
    else:
        print(f"   ⚠️ α outside expected range")
        
except Exception as e:
    print(f"\n❌ FAILED: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)
print("NETWORK CONSTRUCTION TESTS COMPLETE")
print("=" * 70)
print()
print("Next steps:")
print("  - If all tests pass: Ready for Days 4-5 full scaling study")
print("  - If tests fail: Debug issues before proceeding")
print()
print("For full Week 1 scan, run:")
print("  python -c \"from src.phase_d.tier1_collective.network_construction import run_scaling_study; run_scaling_study([10, 50, 100])\"")
