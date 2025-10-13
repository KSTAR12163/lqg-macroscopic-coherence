#!/usr/bin/env python3
"""
Phase B - Step 1: MAXIMIZE GROWTH PER TIME (Not Per Period)

KEY INSIGHT from Floquet scan:
- Growth per period is misleading (small ω → large per-period gain but slow in time)
- Growth per TIME is what matters: growth_rate = ln(|λ_F|_max) × ω/(2π)

GOAL: Find parameter region with MAXIMUM growth_rate to close ~10^14× gap FAST

This is WARP-FIRST: aggressively hunt for fastest exponential amplification.
"""

import numpy as np
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Tuple, Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.floquet_instability.floquet_scan import (
    FloquetScanConfig,
    floquet_growth_rate,
)

print("=" * 80)
print("PHASE B - STEP 1: GROWTH RATE OPTIMIZATION (WARP-FIRST)")
print("=" * 80)
print("\n🎯 MISSION: Find fastest exponential amplification path")
print("\nKey insight: growth_rate = ln(|λ_F|) × ω/(2π)")
print("  → We need FAST growth in TIME, not just per period\n")

# ============================================================================
# CONFIGURATION
# ============================================================================

# Two-level system parameters (will map from network in Step 2)
DELTA = 1e-2  # Energy gap (placeholder, will use real network value)
G0 = 1e-4     # Coupling strength (placeholder)

# PT gain parameter
GAMMA_GAIN = 1e-6  # Non-zero for instability

# Scan ranges (AGGRESSIVE and WIDE)
OMEGA_MIN = 1e-8  # Very low frequency
OMEGA_MAX = 1e-2  # Up to gap frequency
NUM_OMEGA = 50    # Dense scan

AMPLITUDE_VALUES = [0.01, 0.05, 0.1, 0.2, 0.5, 1.0]  # Drive strengths

DELTA_VALUES = [1e-3, 1e-2, 1e-1]  # Different gaps

print("Scan parameters:")
print(f"  ω range: [{OMEGA_MIN:.2e}, {OMEGA_MAX:.2e}] ({NUM_OMEGA} points)")
print(f"  A values: {AMPLITUDE_VALUES}")
print(f"  Δ values: {DELTA_VALUES}")
print(f"  γ_gain: {GAMMA_GAIN:.2e}")
print(f"  g0: {G0:.2e}")

# ============================================================================
# OPTIMIZATION ENGINE
# ============================================================================

@dataclass
class GrowthRateResult:
    """Store growth rate and associated parameters."""
    growth_per_period: float
    growth_rate_per_time: float  # KEY METRIC
    omega: float
    amplitude: float
    delta: float
    period: float
    time_to_10x: float  # Time to achieve 10× amplification
    time_to_1e14: float  # Time to close the gap!


def compute_growth_rate_per_time(
    delta: float, omega: float, amplitude: float, g0: float, gamma_gain: float
) -> GrowthRateResult:
    """
    Compute growth rate per unit time (the critical metric).
    
    growth_rate = ln(|λ_F|_max) × ω/(2π)
    
    This tells us how fast amplitude grows in PHYSICAL TIME.
    """
    config = FloquetScanConfig(
        delta=delta,
        g0=g0,
        amplitude=amplitude,
        omega=omega,
        gamma_gain=gamma_gain,
        steps_per_period=200,
        periods=1,  # Only need 1 period for monodromy
    )
    
    growth_per_period, details = floquet_growth_rate(config)
    
    # Convert to growth per time
    period = 2 * np.pi / omega
    growth_rate = growth_per_period * omega / (2 * np.pi)
    
    # Time to achieve various amplifications
    # A(t) = A(0) * exp(growth_rate * t)
    # t = ln(A(t)/A(0)) / growth_rate
    
    if growth_rate > 1e-20:  # Positive growth
        time_to_10x = np.log(10) / growth_rate
        time_to_1e14 = np.log(1e14) / growth_rate
    else:
        time_to_10x = np.inf
        time_to_1e14 = np.inf
    
    return GrowthRateResult(
        growth_per_period=growth_per_period,
        growth_rate_per_time=growth_rate,
        omega=omega,
        amplitude=amplitude,
        delta=delta,
        period=period,
        time_to_10x=time_to_10x,
        time_to_1e14=time_to_1e14,
    )


def optimize_growth_rate(
    delta_values: List[float],
    omega_grid: np.ndarray,
    amplitude_values: List[float],
    g0: float,
    gamma_gain: float,
) -> Tuple[GrowthRateResult, List[GrowthRateResult]]:
    """
    Exhaustive scan to find maximum growth rate per time.
    
    Returns:
        best: Best result found
        all_results: All results for analysis
    """
    all_results = []
    best = None
    
    total = len(delta_values) * len(omega_grid) * len(amplitude_values)
    count = 0
    
    print(f"\nScanning {total} parameter combinations...")
    print("(This may take a few minutes)\n")
    
    for delta in delta_values:
        for omega in omega_grid:
            for amplitude in amplitude_values:
                result = compute_growth_rate_per_time(
                    delta, omega, amplitude, g0, gamma_gain
                )
                all_results.append(result)
                
                if best is None or result.growth_rate_per_time > best.growth_rate_per_time:
                    best = result
                
                count += 1
                if count % 100 == 0:
                    print(f"  Progress: {count}/{total} ({100*count/total:.1f}%)")
    
    return best, all_results


# ============================================================================
# EXECUTE SCAN
# ============================================================================

print("\n" + "=" * 80)
print("EXECUTING GROWTH RATE OPTIMIZATION")
print("=" * 80)

# Create logarithmic omega grid
omega_grid = np.logspace(np.log10(OMEGA_MIN), np.log10(OMEGA_MAX), NUM_OMEGA)

best, all_results = optimize_growth_rate(
    DELTA_VALUES,
    omega_grid,
    AMPLITUDE_VALUES,
    G0,
    GAMMA_GAIN,
)

# ============================================================================
# ANALYZE RESULTS
# ============================================================================

print("\n" + "=" * 80)
print("RESULTS: MAXIMUM GROWTH RATE")
print("=" * 80)

print(f"\n✅ BEST PARAMETERS FOUND:")
print(f"  Δ (gap):           {best.delta:.4e}")
print(f"  ω (drive freq):    {best.omega:.4e}")
print(f"  A (drive amp):     {best.amplitude:.4f}")
print(f"  γ_gain:            {GAMMA_GAIN:.4e}")

print(f"\n📊 GROWTH METRICS:")
print(f"  Growth per period:     {best.growth_per_period:.6f}")
print(f"  Period T:              {best.period:.4e} s")
print(f"  Growth rate per time:  {best.growth_rate_per_time:.6e} s⁻¹")

print(f"\n⏱️  TIME TO AMPLIFICATION:")
print(f"  Time to 10×:       {best.time_to_10x:.4e} s")
print(f"  Time to 10¹⁴×:     {best.time_to_1e14:.4e} s")

# Convert to years for context
YEAR = 365.25 * 24 * 3600  # seconds
if best.time_to_1e14 < np.inf:
    years_to_1e14 = best.time_to_1e14 / YEAR
    print(f"                     ({years_to_1e14:.4e} years)")
else:
    print(f"                     (infinite)")

# ============================================================================
# COMPARE: GROWTH PER PERIOD vs GROWTH PER TIME
# ============================================================================

print("\n" + "=" * 80)
print("ANALYSIS: WHY GROWTH PER TIME MATTERS")
print("=" * 80)

# Sort by growth per period
sorted_by_period = sorted(all_results, key=lambda r: r.growth_per_period, reverse=True)

# Sort by growth per time
sorted_by_time = sorted(all_results, key=lambda r: r.growth_rate_per_time, reverse=True)

print("\n🔴 TOP 5 BY GROWTH PER PERIOD (MISLEADING!):")
print(f"{'Rank':<6} {'ω':<12} {'A':<8} {'Growth/period':<15} {'Growth/time':<15} {'Time to 10¹⁴×':<15}")
print("-" * 90)
for i, r in enumerate(sorted_by_period[:5], 1):
    time_str = f"{r.time_to_1e14:.3e}" if r.time_to_1e14 < np.inf else "inf"
    print(f"{i:<6} {r.omega:<12.3e} {r.amplitude:<8.2f} {r.growth_per_period:<15.6f} "
          f"{r.growth_rate_per_time:<15.3e} {time_str:<15}")

print("\n✅ TOP 5 BY GROWTH PER TIME (CORRECT METRIC!):")
print(f"{'Rank':<6} {'ω':<12} {'A':<8} {'Growth/period':<15} {'Growth/time':<15} {'Time to 10¹⁴×':<15}")
print("-" * 90)
for i, r in enumerate(sorted_by_time[:5], 1):
    time_str = f"{r.time_to_1e14:.3e}" if r.time_to_1e14 < np.inf else "inf"
    print(f"{i:<6} {r.omega:<12.3e} {r.amplitude:<8.2f} {r.growth_per_period:<15.6f} "
          f"{r.growth_rate_per_time:<15.3e} {time_str:<15}")

print("\n💡 KEY INSIGHT:")
print("  Low ω → high growth per period BUT slow in real time")
print("  High ω → lower growth per period BUT faster in real time")
print("  → Optimal point balances both!")

# ============================================================================
# HEATMAP DATA (for plotting)
# ============================================================================

print("\n" + "=" * 80)
print("HEATMAP: GROWTH RATE vs ω and A (at best Δ)")
print("=" * 80)

# Extract results for best delta
best_delta_results = [r for r in all_results if r.delta == best.delta]

# Create 2D arrays for heatmap
omega_unique = np.unique([r.omega for r in best_delta_results])
amp_unique = np.unique([r.amplitude for r in best_delta_results])

growth_map = np.zeros((len(amp_unique), len(omega_unique)))

for r in best_delta_results:
    i = np.where(amp_unique == r.amplitude)[0][0]
    j = np.where(omega_unique == r.omega)[0][0]
    growth_map[i, j] = r.growth_rate_per_time

print(f"\nΔ = {best.delta:.4e}")
print(f"Heatmap shape: {growth_map.shape} (amplitude × omega)")
print(f"Max growth rate: {np.max(growth_map):.6e} s⁻¹")
print(f"At: ω = {omega_unique[np.argmax(np.max(growth_map, axis=0))]:.4e}, "
      f"A = {amp_unique[np.argmax(np.max(growth_map, axis=1))]:.4f}")

# ============================================================================
# SAVE RESULTS
# ============================================================================

print("\n" + "=" * 80)
print("SAVING RESULTS")
print("=" * 80)

np.savez(
    'phase_b_growth_rate_results.npz',
    best_delta=best.delta,
    best_omega=best.omega,
    best_amplitude=best.amplitude,
    best_growth_per_period=best.growth_per_period,
    best_growth_rate=best.growth_rate_per_time,
    best_time_to_1e14=best.time_to_1e14,
    omega_grid=omega_grid,
    amplitude_values=AMPLITUDE_VALUES,
    delta_values=DELTA_VALUES,
    growth_map=growth_map,
    omega_unique=omega_unique,
    amp_unique=amp_unique,
)

print("✓ Saved to phase_b_growth_rate_results.npz")

# ============================================================================
# ASSESSMENT
# ============================================================================

print("\n" + "=" * 80)
print("WARP-FIRST ASSESSMENT")
print("=" * 80)

print(f"\n🎯 BEST GROWTH RATE: {best.growth_rate_per_time:.6e} s⁻¹")

if best.time_to_1e14 < np.inf:
    years = best.time_to_1e14 / YEAR
    
    print(f"\n⏱️  TIME TO CLOSE 10¹⁴× GAP:")
    print(f"    {best.time_to_1e14:.4e} seconds")
    print(f"    = {years:.4e} years")
    
    if years < 1:
        print("\n🚀 EXCELLENT! Sub-year timescale → potentially viable!")
        print("   Next: Map to real network parameters (Step 2)")
        print("   Then: Implement pumped Lindblad (Step 3)")
    elif years < 100:
        print("\n⚠️  MODERATE: Decades timescale")
        print("   Need to: (1) Optimize γ_gain, (2) Add Purcell factor (Step 4)")
    elif years < 1e6:
        print("\n⚠️  LONG: >100 years but < cosmological")
        print("   Need: Strong DOS boosting + higher gain")
    else:
        print("\n❌ TOO SLOW: Cosmological timescale")
        print("   Need: Much higher gain or different approach")
else:
    print("\n❌ NO GROWTH: Insufficient gain")
    print("   Need: Higher γ_gain or different parameter regime")

print("\n" + "=" * 80)
print("STEP 1 COMPLETE")
print("=" * 80)
print("\nNext: Run Step 2 (map to real network) and Step 3 (pumped Lindblad)")
