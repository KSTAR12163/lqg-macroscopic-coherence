#!/usr/bin/env python3
"""
Phase C - Step 1: SENSITIVITY ANALYSIS (WORKING BACKWARDS)

GOAL: Determine the minimum bare coupling (g₀) required for warp viability,
      assuming realistic engineering constraints.

This script answers the question:
  "If we had a perfect amplifier, what is the minimum g₀ our physics
   model must provide to close the 10^14× gap in a human timescale?"

METHOD:
1. Define realistic engineering parameters:
   - Purcell factor F_p (1 to 10^9)
   - Gain γ_gain (10^-6 to 1)
   - Timescale (1 year)

2. Calculate the required growth rate to achieve the goal.

3. For each (F_p, γ_gain) pair, work backwards to find the g₀ needed
   to produce that growth rate.

This provides a concrete target for future fundamental physics research.
"""

import numpy as np
import sys
from pathlib import Path
from scipy.optimize import brentq

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.floquet_instability.floquet_scan import (
    FloquetScanConfig,
    floquet_growth_rate,
)

print("=" * 80)
print("PHASE C - STEP 1: SENSITIVITY ANALYSIS")
print("=" * 80)
print("\n🎯 GOAL: Find the minimum bare coupling g₀ for warp viability")
print("   Assuming realistic engineering constraints.\n")

# ============================================================================
# REALISTIC ENGINEERING & TARGETS
# ============================================================================

# Physical parameters (from previous steps)
DELTA = 6.543e-16  # J (energy gap)
OMEGA_DRIVE = 7.906e-4  # rad/s (drive frequency)
AMPLITUDE = 0.01

# Target: Close 10^14x gap in 1 year
TARGET_TIME_YEARS = 1.0
YEAR_SECS = 365.25 * 24 * 3600
TARGET_TIME_SECS = TARGET_TIME_YEARS * YEAR_SECS
REQUIRED_GROWTH_RATE = np.log(1e14) / TARGET_TIME_SECS

# Realistic engineering parameters to scan
PURCELL_FACTORS = np.logspace(0, 9, 10)  # 1 to 10^9 (Achievable to Challenging)
GAMMA_GAINS = np.logspace(-6, 0, 7)     # 10^-6 to 1 (Weak to Strong Gain)

print("Target Performance:")
print(f"  Close 10^14× gap in: {TARGET_TIME_YEARS:.1f} year(s)")
print(f"  Required growth rate: {REQUIRED_GROWTH_RATE:.3e} s⁻¹")
print("\nRealistic Engineering Constraints (Scan Range):")
print(f"  Purcell Factors (F_p): 10^0 to 10^9")
print(f"  Gain (γ_gain):         10^-6 to 1")

# ============================================================================
# COMPUTATION: SOLVING FOR g₀
# ============================================================================

print("\n" + "=" * 80)
print("COMPUTING REQUIRED BARE COUPLING g₀")
print("=" * 80)

results_g0 = []

# Pre-calculate required growth per period
required_growth_per_period = REQUIRED_GROWTH_RATE * (2 * np.pi) / OMEGA_DRIVE

def find_required_g0(F_p, gamma_gain):
    """
    For a given F_p and gamma_gain, find the g₀ that yields the
    target growth rate using a root-finding algorithm.
    """
    
    def objective_func(log_g0):
        """Function whose root we want to find."""
        g0 = 10**log_g0
        g_eff = np.sqrt(F_p) * g0
        
        config = FloquetScanConfig(
            delta=DELTA,
            g0=g_eff,
            amplitude=AMPLITUDE,
            omega=OMEGA_DRIVE,
            gamma_gain=gamma_gain,
        )
        
        growth_per_period, _ = floquet_growth_rate(config)
        return growth_per_period - required_growth_per_period

    try:
        # Search for g₀ in a plausible range (10^-60 to 10^-10 J)
        log_g0_solution = brentq(objective_func, a=-60, b=-10, xtol=1e-3, rtol=1e-3)
        return 10**log_g0_solution
    except ValueError:
        # If no solution found in the range, it's likely out of bounds
        return np.nan

total = len(PURCELL_FACTORS) * len(GAMMA_GAINS)
count = 0
print(f"\nScanning {total} combinations of (F_p, γ_gain)...")

for F_p in PURCELL_FACTORS:
    for gamma_gain in GAMMA_GAINS:
        required_g0 = find_required_g0(F_p, gamma_gain)
        
        results_g0.append({
            'F_p': F_p,
            'gamma_gain': gamma_gain,
            'required_g0': required_g0,
        })
        count += 1
        if count % 10 == 0:
            print(f"  Progress: {count}/{total} ({100*count/total:.1f}%)")

print("✓ Scan complete.")

# ============================================================================
# ANALYSIS & HEATMAP
# ============================================================================

print("\n" + "=" * 80)
print("ANALYSIS: REQUIRED BARE COUPLING g₀")
print("=" * 80)

# Reshape for heatmap
g0_map = np.full((len(GAMMA_GAINS), len(PURCELL_FACTORS)), np.nan)
for r in results_g0:
    i = np.where(GAMMA_GAINS == r['gamma_gain'])[0][0]
    j = np.where(PURCELL_FACTORS == r['F_p'])[0][0]
    g0_map[i, j] = r['required_g0']

# Find best-case (minimum required g₀)
min_g0 = np.nanmin(g0_map)
if not np.isnan(min_g0):
    best_idx = np.unravel_index(np.nanargmin(g0_map), g0_map.shape)
    best_gamma = GAMMA_GAINS[best_idx[0]]
    best_Fp = PURCELL_FACTORS[best_idx[1]]
    
    print(f"\n🎯 Best Case (Minimum Required g₀):")
    print(f"  Required g₀:      {min_g0:.3e} J")
    print(f"  Achieved with:")
    print(f"    Purcell Factor: {best_Fp:.1e}")
    print(f"    Gain (γ_gain):  {best_gamma:.1e}")
    
    # Compare to our model's g₀
    MODEL_G0 = 3.957e-121  # The value from our LQG model
    print(f"\n  Current Model g₀: {MODEL_G0:.3e} J")
    print(f"  Discrepancy:      {min_g0 / MODEL_G0:.2e} orders of magnitude")
    
else:
    print("\n❌ No solution found within the search space.")
    print("   The required g₀ is likely outside the 10^-60 to 10^-10 J range.")

# Generate Heatmap
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Use log10 for the color scale
    g0_map_plot = np.log10(g0_map)
    
    im = ax.pcolormesh(np.log10(PURCELL_FACTORS), np.log10(GAMMA_GAINS),
                       g0_map_plot, cmap='plasma_r', shading='auto')
    
    ax.set_xlabel('log₁₀(Purcell Factor F_p)', fontsize=12)
    ax.set_ylabel('log₁₀(Gain γ_gain)', fontsize=12)
    ax.set_title('Required Bare Coupling g₀ (log₁₀ J) for 1-Year Amplification', fontsize=14, fontweight='bold')
    
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('log₁₀(Required g₀ in Joules)', fontsize=11)
    
    plt.tight_layout()
    plt.savefig('phase_c_sensitivity_analysis.png', dpi=150)
    print("\n✓ Heatmap saved: phase_c_sensitivity_analysis.png")

except ImportError:
    print("\n⚠️ Matplotlib not found. Skipping heatmap generation.")
    print("   Install with: pip install matplotlib")

# ============================================================================
# CONCLUSION & NEXT STEPS
# ============================================================================

print("\n" + "=" * 80)
print("PHASE C CONCLUSION: A TARGET FOR FUNDAMENTAL PHYSICS")
print("=" * 80)

if not np.isnan(min_g0):
    print(f"""
This analysis provides a clear, quantitative target for future research.

To make warp drive viable within 1 year, a fundamental theory must produce
a bare coupling constant of at least:

  g₀ ≈ {min_g0:.1e} J

This is the minimum requirement, assuming optimistic but physically plausible
engineering (F_p={best_Fp:.1e}, γ_gain={best_gamma:.1e}).

Our current model yields g₀ ≈ {MODEL_G0:.1e} J, a shortfall of ~{min_g0 / MODEL_G0:.0e}×.

NEXT STEPS:
1.  **Document Phase B & C Results**: Write a final paper summarizing:
    - The discovery of the active gain mechanism.
    - The numerical invalidity of the initial "breakthrough".
    - The quantitative target (g₀ ≈ {min_g0:.1e} J) for future theories.

2.  **Launch Theoretical Search (Phase D)**: Begin a search for new physics
    that could bridge this gap. This involves exploring:
    - **Collective Effects**: Can N-particle entanglement enhance g₀?
    - **Higher-Order LQG Terms**: Are there non-minimal couplings?
    - **Exotic Matter/Geometries**: Do other spin representations or graph
      topologies yield stronger coupling?

3.  **Archive Current Framework**: The existing codebase is a valuable tool for
    testing new theories. Once a new candidate for g₀ is found, it can be
    plugged into this framework to rapidly assess its viability.

This concludes the analysis of the current model. The path forward is now
a theoretical one, aimed at discovering a fundamentally stronger coupling.
""")
else:
    print("\nCould not determine a target g₀. The problem may be outside the search bounds.")

print("\n" + "=" * 80)
print("PHASE C COMPLETE")
print("=" * 80)
