#!/usr/bin/env python3
"""
Measure scaling exponent α for collective enhancement.

Uses corrected collective_hamiltonian module that properly
sums over all edges.
"""

from src.phase_d.tier1_collective.network_construction import create_complete_network
from src.phase_d.tier1_collective.collective_hamiltonian import (
    measure_collective_coupling_v2,
    extract_scaling_exponent
)

print("=" * 70)
print("WEEK 1 DAY 2: Collective Coupling Scaling Study")
print("=" * 70)
print("\nMeasuring g_eff(N) for complete graphs...")
print("(This will take 2-3 minutes)\n")

# Test with small N values (fast)
N_values = [4, 6, 8, 10, 15]
g_values = []
enh_values = []

for N in N_values:
    print(f"N={N}...", end=" ", flush=True)
    network, edges = create_complete_network(N)
    g_coll, gap, enh = measure_collective_coupling_v2(network, dim=16)
    g_values.append(g_coll)
    enh_values.append(enh)
    print(f"g={g_coll:.3e} J, enhancement={enh:.2e}×")

# Extract scaling exponent
print("\n" + "=" * 70)
print("SCALING ANALYSIS")
print("=" * 70)

alpha, g0, fit_info = extract_scaling_exponent(N_values, g_values)

print(f"\nFitted scaling: g(N) = {g0:.3e} × N^{alpha:.3f}")
print(f"RMS residual: {fit_info['rms_residual']:.3f}")
print(f"\nClosest prediction: {fit_info['closest_prediction']}")
print(f"  √N scaling:   α = 0.5")
print(f"  Linear (N):   α = 1.0")
print(f"  Quadratic:    α = 2.0")
print(f"  Measured:     α = {alpha:.3f}")

# Interpretation
print("\n" + "=" * 70)
print("INTERPRETATION")
print("=" * 70)

if alpha >= 1.5:
    print(f"✅ SUPER-LINEAR SCALING (α = {alpha:.2f} > 1.5)")
    print("   Collective effects are significant!")
    print("   Strong constructive interference between edges.")
    if alpha >= 2.0:
        print("   ⚠️  Approaching quadratic (complete graph ideal case)")
elif alpha >= 0.7:
    print(f"📊 LINEAR SCALING (α = {alpha:.2f} ≈ 1.0)")
    print("   Moderate collective enhancement.")
    print("   Edges add incoherently (typical for lattices).")
else:
    print(f"📉 SUB-LINEAR SCALING (α = {alpha:.2f} < 0.7)")
    print("   Weak collective effects.")
    print("   Destructive interference or saturation.")

# Extrapolate to viability
print("\n" + "=" * 70)
print("VIABILITY EXTRAPOLATION")
print("=" * 70)

g_target = 1e-50  # J (Phase D threshold)
g_current = g_values[-1]  # Last measurement (N=15)
N_current = N_values[-1]

# Solve: g_target = g0 × N_required^α
# N_required = (g_target / g0)^(1/α)
if alpha > 0 and g0 > 0:
    N_required = (g_target / g0) ** (1.0 / alpha)
    print(f"Target coupling: g = {g_target:.1e} J")
    print(f"Current (N={N_current}): g = {g_current:.3e} J")
    print(f"Gap: {g_target / g_current:.2e}×")
    print(f"\nRequired N: {N_required:.3e}")
    
    # Feasibility assessment
    if N_required < 1e20:
        print("✅ Potentially feasible (N < 10²⁰)")
    elif N_required < 1e40:
        print("⚠️  Speculative (10²⁰ < N < 10⁴⁰)")
    else:
        print("❌ Infeasible (N > 10⁴⁰)")
else:
    print("❌ Cannot extrapolate (invalid fit)")

print("\n" + "=" * 70)
print("✅ SCALING STUDY COMPLETE")
print("=" * 70)
print("\nNext steps:")
print("- If α ≥ 1.3: Continue Tier 1 with optimization (Days 3-5)")
print("- If 0.7 < α < 1.3: Document and evaluate")
print("- If α < 0.7: Skip to Tier 3 (exotic mechanisms)")
