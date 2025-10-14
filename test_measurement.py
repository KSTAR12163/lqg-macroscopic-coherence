#!/usr/bin/env python3
"""
Minimal test of collective coupling measurement.
Tests with N=4 only (fastest).
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("Testing collective coupling measurement...")
print("This may take 1-2 minutes for spectrum calculation...\n")

try:
    from src.phase_d.tier1_collective.network_construction import measure_collective_coupling
    
    result = measure_collective_coupling(N=4, topology="complete", dim=16)  # Reduced dim for speed
    
    print("\n" + "=" * 70)
    print("✅ MEASUREMENT SUCCESSFUL")
    print("=" * 70)
    print(f"N = {result.N}")
    print(f"Topology = {result.topology}")
    print(f"g_single = {result.g_single:.6e} J (baseline)")
    print(f"g_coll = {result.g_coll:.6e} J (measured)")
    print(f"Enhancement = {result.enhancement:.2f}×")
    print(f"Gap Δ = {result.Delta:.6e} J")
    print(f"Gap frequency = {result.omega_gap:.6e} rad/s")
    print("=" * 70)
    
    # Interpretation
    if result.enhancement > 2.0:
        print("\n🎯 Enhancement > 2× suggests some collective effect!")
    elif result.enhancement > 1.5:
        print("\n📊 Enhancement > 1.5× shows weak collective behavior")
    else:
        print("\n📉 Enhancement ≤ 1.5× indicates minimal collective effect")
    
    print("\n✅ Network construction code is working!")
    print("Ready for full Week 1 scanning study.")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    print("\nDiagnostic: Check if matter_coupling module is available")
