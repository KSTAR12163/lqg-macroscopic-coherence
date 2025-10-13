#!/usr/bin/env python3
"""
Phase B - Step 4: PURCELL FACTOR SCAN (CRITICAL TEST!)

The Purcell effect enhances coupling through density-of-states engineering:
  F_p = (3/4π²) × (λ/n)³ × (Q/V)

Where:
  - Q: Quality factor of cavity
  - V: Mode volume
  - Effective coupling: g_eff = √F_p × g_0

GOAL: Find required Purcell enhancement to close 10^14× gap in human timescales

THIS IS THE CRITICAL TEST FOR WARP VIABILITY:
  - F_p < 10^6: ✅ ACHIEVABLE (cavity QED, current tech)
  - F_p ~ 10^6-10^9: ⚠️ CHALLENGING (advanced metamaterials)
  - F_p > 10^12: ❌ NOT VIABLE (beyond current technology)

This scan will tell us: CAN WE BUILD A WARP DRIVE?
"""

import numpy as np
import sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.floquet_instability.floquet_scan import (
    FloquetScanConfig,
    floquet_growth_rate,
)

print("=" * 80)
print("PHASE B - STEP 4: PURCELL FACTOR SCAN")
print("=" * 80)
print("\n🎯 CRITICAL TEST: Can cavity enhancement make warp viable?")
print("\nPurcell enhancement: g_eff = √F_p × g_0")
print("  → Boosts weak coupling through DOS engineering\n")

# ============================================================================
# PHYSICAL PARAMETERS (from Step 2)
# ============================================================================

# From phase_b_network_mapping.py results
DELTA = 6.543e-16  # J (energy gap)
G0_BASE = 3.957e-121  # J (bare coupling - extremely weak!)
OMEGA_GAP = 6.204e18  # rad/s

print("Physical parameters from LQG network:")
print(f"  Δ (gap):        {DELTA:.3e} J")
print(f"  g₀ (bare):      {G0_BASE:.3e} J")
print(f"  ω_gap:          {OMEGA_GAP:.3e} rad/s")
print(f"\n  Bare coupling is EXTREMELY WEAK (~10^-121 J)")
print(f"  → This is why passive mechanisms failed!")

# ============================================================================
# PURCELL FACTOR SCAN
# ============================================================================

# Scan Purcell factors from 1 (no enhancement) to 10^20
PURCELL_FACTORS = np.logspace(0, 20, 41)  # [1, 10, 100, ..., 10^20]

# Drive parameters (from Step 1 optimization)
OMEGA_DRIVE = 7.906e-4  # From growth-per-time optimization
AMPLITUDE = 0.01

# Gain parameters to test
GAMMA_GAINS = [1e-10, 1e-8, 1e-6, 1e-4, 1e-2]

print(f"\nScan parameters:")
print(f"  Purcell factors: 10^0 to 10^20 ({len(PURCELL_FACTORS)} points)")
print(f"  γ_gain values: {GAMMA_GAINS}")
print(f"  ω_drive: {OMEGA_DRIVE:.3e} rad/s")
print(f"  A: {AMPLITUDE:.3f}")

# ============================================================================
# COMPUTATION
# ============================================================================

print("\n" + "=" * 80)
print("COMPUTING GROWTH RATES WITH PURCELL ENHANCEMENT")
print("=" * 80)

results = []

total = len(PURCELL_FACTORS) * len(GAMMA_GAINS)
count = 0

print(f"\nScanning {total} combinations...")

for F_p in PURCELL_FACTORS:
    # Enhanced coupling
    g_eff = np.sqrt(F_p) * G0_BASE
    
    for gamma_gain in GAMMA_GAINS:
        # Floquet analysis with enhanced coupling
        config = FloquetScanConfig(
            delta=DELTA,
            g0=g_eff,
            amplitude=AMPLITUDE,
            omega=OMEGA_DRIVE,
            gamma_gain=gamma_gain,
            steps_per_period=200,
            periods=1,
        )
        
        growth_per_period, details = floquet_growth_rate(config)
        
        # Growth rate per time
        growth_rate = growth_per_period * OMEGA_DRIVE / (2 * np.pi)
        
        # Time to close gap
        if growth_rate > 1e-30:
            time_to_1e14 = np.log(1e14) / growth_rate
        else:
            time_to_1e14 = np.inf
        
        results.append({
            'F_p': F_p,
            'g_eff': g_eff,
            'gamma_gain': gamma_gain,
            'growth_per_period': growth_per_period,
            'growth_rate': growth_rate,
            'time_to_1e14': time_to_1e14,
        })
        
        count += 1
        if count % 20 == 0:
            print(f"  Progress: {count}/{total} ({100*count/total:.1f}%)")

print(f"✓ Scan complete ({len(results)} results)")

# ============================================================================
# ANALYSIS: FIND VIABLE REGIMES
# ============================================================================

print("\n" + "=" * 80)
print("VIABILITY ANALYSIS")
print("=" * 80)

YEAR = 365.25 * 24 * 3600  # seconds

# Define timescale targets
targets = {
    '1 year': 1 * YEAR,
    '10 years': 10 * YEAR,
    '100 years': 100 * YEAR,
    '1000 years': 1000 * YEAR,
}

print("\nFinding minimum Purcell factor for each timescale...\n")

for target_name, target_time in targets.items():
    print(f"{'='*70}")
    print(f"TARGET: Close 10^14× gap in {target_name}")
    print(f"{'='*70}")
    
    # Find viable configurations
    viable = [r for r in results if r['time_to_1e14'] <= target_time]
    
    if viable:
        # Find minimum Purcell factor needed
        best = min(viable, key=lambda r: r['F_p'])
        
        print(f"\n✅ ACHIEVABLE with:")
        print(f"  Minimum F_p:      {best['F_p']:.3e}")
        print(f"  Required γ_gain:  {best['gamma_gain']:.3e}")
        print(f"  Effective g_eff:  {best['g_eff']:.3e} J")
        print(f"  Enhancement:      {best['g_eff']/G0_BASE:.3e}× over bare")
        print(f"  Growth rate:      {best['growth_rate']:.3e} s^-1")
        print(f"  Time to 10^14×:   {best['time_to_1e14']:.3e} s")
        
        # Technology assessment
        if best['F_p'] < 1e3:
            tech = "✅ STANDARD (optical cavity)"
        elif best['F_p'] < 1e6:
            tech = "✅ ACHIEVABLE (high-Q cavity, current tech)"
        elif best['F_p'] < 1e9:
            tech = "⚠️  CHALLENGING (advanced metamaterials)"
        elif best['F_p'] < 1e12:
            tech = "⚠️  VERY CHALLENGING (cutting-edge nanostructures)"
        else:
            tech = "❌ NOT VIABLE (beyond current technology)"
        
        print(f"\n  Technology level: {tech}")
        
        # Show top 5 configurations
        viable_sorted = sorted(viable, key=lambda r: r['F_p'])
        print(f"\n  Top 5 configurations:")
        print(f"  {'F_p':<12} {'γ_gain':<12} {'g_eff':<12} {'Time (years)':<15}")
        print(f"  {'-'*60}")
        for r in viable_sorted[:5]:
            years = r['time_to_1e14'] / YEAR
            print(f"  {r['F_p']:<12.2e} {r['gamma_gain']:<12.2e} "
                  f"{r['g_eff']:<12.2e} {years:<15.3e}")
    else:
        print(f"\n❌ NOT ACHIEVABLE (F_p up to 10^20 insufficient)")
        print(f"   Need higher gain or different approach")

# ============================================================================
# BEST OVERALL RESULT
# ============================================================================

print("\n" + "=" * 80)
print("BEST OVERALL CONFIGURATION")
print("=" * 80)

# Find fastest configuration (minimum time)
best_overall = min(results, key=lambda r: r['time_to_1e14'] if r['time_to_1e14'] < np.inf else 1e100)

if best_overall['time_to_1e14'] < np.inf:
    years = best_overall['time_to_1e14'] / YEAR
    
    print(f"\n🎯 OPTIMAL PARAMETERS:")
    print(f"  Purcell factor F_p:   {best_overall['F_p']:.3e}")
    print(f"  Gain γ_gain:          {best_overall['gamma_gain']:.3e}")
    print(f"  Effective g_eff:      {best_overall['g_eff']:.3e} J")
    print(f"  Enhancement factor:   {np.sqrt(best_overall['F_p']):.3e}×")
    
    print(f"\n📊 PERFORMANCE:")
    print(f"  Growth rate:          {best_overall['growth_rate']:.3e} s^-1")
    print(f"  Time to 10^14×:       {best_overall['time_to_1e14']:.3e} s")
    print(f"                        = {years:.3e} years")
    
    # Technology assessment
    if best_overall['F_p'] < 1e6:
        print(f"\n✅ TECHNOLOGY: ACHIEVABLE with current cavity QED")
        print(f"   → High-Q optical or microwave cavities")
        print(f"   → Standard fabrication techniques")
        viability = "VIABLE"
    elif best_overall['F_p'] < 1e9:
        print(f"\n⚠️  TECHNOLOGY: CHALLENGING but possible")
        print(f"   → Advanced metamaterials or plasmonics")
        print(f"   → Cutting-edge nanofabrication")
        viability = "CHALLENGING"
    else:
        print(f"\n❌ TECHNOLOGY: Beyond current capabilities")
        print(f"   → Requires breakthrough in materials science")
        print(f"   → Or qualitatively different approach")
        viability = "NOT VIABLE"
else:
    print("\n❌ No viable configuration found")
    viability = "NOT VIABLE"

# ============================================================================
# HEATMAPS
# ============================================================================

print("\n" + "=" * 80)
print("GENERATING HEATMAPS")
print("=" * 80)

# Reshape results for heatmap
F_p_unique = np.unique([r['F_p'] for r in results])
gamma_unique = np.unique([r['gamma_gain'] for r in results])

time_map = np.full((len(gamma_unique), len(F_p_unique)), np.inf)

for r in results:
    i = np.where(gamma_unique == r['gamma_gain'])[0][0]
    j = np.where(F_p_unique == r['F_p'])[0][0]
    time_map[i, j] = r['time_to_1e14'] / YEAR  # Convert to years

# Create figure with two subplots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# Heatmap 1: Time to 10^14× (log scale)
time_map_plot = np.log10(np.clip(time_map, 1e-10, 1e20))
im1 = ax1.pcolormesh(np.log10(F_p_unique), np.log10(gamma_unique), 
                      time_map_plot, cmap='RdYlGn_r', shading='auto')
ax1.set_xlabel('log₁₀(Purcell Factor F_p)', fontsize=12)
ax1.set_ylabel('log₁₀(Gain γ_gain)', fontsize=12)
ax1.set_title('Time to Close 10¹⁴× Gap (log₁₀ years)', fontsize=14, fontweight='bold')
cbar1 = plt.colorbar(im1, ax=ax1)
cbar1.set_label('log₁₀(years)', fontsize=11)

# Add viability contours
ax1.contour(np.log10(F_p_unique), np.log10(gamma_unique), time_map_plot,
            levels=[0, 1, 2, 3], colors='black', linewidths=1.5, alpha=0.5)
ax1.text(0.05, 0.95, '1 year', transform=ax1.transAxes, 
         fontsize=10, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
ax1.text(0.05, 0.85, '10 years', transform=ax1.transAxes,
         fontsize=10, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))

# Mark technology boundaries
ax1.axvline(np.log10(1e6), color='cyan', linestyle='--', linewidth=2, alpha=0.7, label='F_p=10⁶ (achievable)')
ax1.axvline(np.log10(1e9), color='orange', linestyle='--', linewidth=2, alpha=0.7, label='F_p=10⁹ (challenging)')
ax1.axvline(np.log10(1e12), color='red', linestyle='--', linewidth=2, alpha=0.7, label='F_p=10¹² (not viable)')
ax1.legend(loc='lower right', fontsize=9)

# Heatmap 2: Growth rate (log scale)
growth_map = np.zeros((len(gamma_unique), len(F_p_unique)))
for r in results:
    i = np.where(gamma_unique == r['gamma_gain'])[0][0]
    j = np.where(F_p_unique == r['F_p'])[0][0]
    growth_map[i, j] = r['growth_rate']

growth_map_plot = np.log10(np.clip(growth_map, 1e-30, 1e30))
im2 = ax2.pcolormesh(np.log10(F_p_unique), np.log10(gamma_unique),
                      growth_map_plot, cmap='viridis', shading='auto')
ax2.set_xlabel('log₁₀(Purcell Factor F_p)', fontsize=12)
ax2.set_ylabel('log₁₀(Gain γ_gain)', fontsize=12)
ax2.set_title('Growth Rate (log₁₀ s⁻¹)', fontsize=14, fontweight='bold')
cbar2 = plt.colorbar(im2, ax=ax2)
cbar2.set_label('log₁₀(growth rate, s⁻¹)', fontsize=11)

plt.tight_layout()
plt.savefig('phase_b_purcell_scan.png', dpi=150, bbox_inches='tight')
print("✓ Saved: phase_b_purcell_scan.png")

# ============================================================================
# SAVE RESULTS
# ============================================================================

print("\n" + "=" * 80)
print("SAVING RESULTS")
print("=" * 80)

np.savez(
    'phase_b_purcell_results.npz',
    F_p_values=F_p_unique,
    gamma_values=gamma_unique,
    time_map=time_map,
    growth_map=growth_map,
    best_F_p=best_overall['F_p'] if best_overall['time_to_1e14'] < np.inf else np.nan,
    best_gamma=best_overall['gamma_gain'] if best_overall['time_to_1e14'] < np.inf else np.nan,
    best_time=best_overall['time_to_1e14'] if best_overall['time_to_1e14'] < np.inf else np.inf,
    viability=viability,
)

print("✓ Saved: phase_b_purcell_results.npz")

# ============================================================================
# FINAL VERDICT
# ============================================================================

print("\n" + "=" * 80)
print("FINAL VERDICT: IS WARP DRIVE VIABLE?")
print("=" * 80)

if viability == "VIABLE":
    print(f"""
🚀 ✅ YES - WARP DRIVE IS POTENTIALLY VIABLE!

With Purcell enhancement F_p ~ {best_overall['F_p']:.2e} and gain γ ~ {best_overall['gamma_gain']:.2e}:

  → Can close 10^14× gap in {years:.1f} years
  → Technology level: ACHIEVABLE with current cavity QED
  → Next steps: Design cavity, calculate pump requirements, build prototype

THIS IS A PATH FORWARD! 🎯

Recommended actions:
  1. Design high-Q cavity (optical or microwave)
  2. Calculate required pump power (Step 5)
  3. Optimize multi-tone driving (increase speed)
  4. Build analog quantum simulator (Phase C)
  5. Scale toward lab demonstration (Phase D)

The physics works. The engineering is challenging but achievable.
WARP RESEARCH CONTINUES! 🚀
""")

elif viability == "CHALLENGING":
    print(f"""
⚠️  CHALLENGING - Requires Advanced Engineering

Required: F_p ~ {best_overall['F_p']:.2e}, γ ~ {best_overall['gamma_gain']:.2e}

  → Can close gap in {years:.1f} years
  → Technology: Advanced metamaterials, cutting-edge nanofab
  → Feasible but requires significant R&D investment

POSSIBLE but DIFFICULT. Recommend:
  1. Explore alternative geometries (lower F_p requirements)
  2. Investigate collective enhancement (multi-atom systems)
  3. Develop advanced metamaterials program
  4. Seek breakthrough in cavity/material design

Not immediate, but not impossible either.
""")

else:
    print(f"""
❌ NOT VIABLE - Beyond Current Technology

Even with F_p up to 10^20, cannot close gap in reasonable time.

Physics mechanism works (exponential growth proven) but:
  → Required Purcell enhancement too large
  → Coupling fundamentally too weak (g_0 ~ 10^-121 J)
  → Would need breakthrough in physics or materials

RECOMMENDATIONS:
  1. Document Phase B results (active gain mechanism proven)
  2. Publish paper: "Active Gain for Quantum-Geometry Amplification"
  3. Pivot to cosmology (where framework remains valuable)
  4. OR: Explore fundamentally different coupling mechanisms

The search for warp continues, but not with current model formulation.
This doesn't mean warp is impossible - just that THIS approach has limits.
""")

print("\n" + "=" * 80)
print("STEP 4 COMPLETE: PURCELL SCAN")
print("=" * 80)
print(f"\nViability: {viability}")
print("Next: Run Step 5 (multi-tone driving) to optimize further")
