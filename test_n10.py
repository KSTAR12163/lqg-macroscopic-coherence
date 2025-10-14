#!/usr/bin/env python3
"""Quick test with N=10 to see scaling trend."""

from src.phase_d.tier1_collective.network_construction import measure_collective_coupling

print("Testing N=4 and N=10 to see scaling trend...")
print("(This will take 2-3 minutes)\n")

# Test N=4
print("=" * 60)
print("Test 1: N=4")
print("=" * 60)
result4 = measure_collective_coupling(N=4, topology="complete", dim=16)
print(f"\nN=4: g_coll = {result4.g_coll:.3e} J")
print(f"     Enhancement = {result4.enhancement:.2f}×\n")

# Test N=10
print("=" * 60)
print("Test 2: N=10")
print("=" * 60)
result10 = measure_collective_coupling(N=10, topology="complete", dim=16)
print(f"\nN=10: g_coll = {result10.g_coll:.3e} J")
print(f"      Enhancement = {result10.enhancement:.2f}×\n")

# Compare
print("=" * 60)
print("COMPARISON")
print("=" * 60)
ratio = result10.g_coll / result4.g_coll if result4.g_coll > 0 else 0
N_ratio = 10 / 4

print(f"g_coll(N=10) / g_coll(N=4) = {ratio:.3f}")
print(f"N ratio = {N_ratio:.2f}")

if ratio > N_ratio ** 1.5:
    print("📈 Super-linear scaling (better than N^1.5) - GOOD!")
elif ratio > N_ratio:
    print("📊 Super-linear scaling (between N and N^1.5)")
elif ratio > N_ratio ** 0.5:
    print("📉 Sub-linear scaling (between √N and N)")
else:
    print("❌ Very weak scaling (worse than √N)")

print("\n✅ Scaling test complete. Ready for full study.")
