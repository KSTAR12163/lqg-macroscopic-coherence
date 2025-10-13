#!/usr/bin/env python3
"""
Phase B - Step 5: MULTI-TONE AND CHIRPED DRIVING

Single-tone driving: g(t) = g₀(1 + A·cos(ωt))
  → Can miss resonances if ω not exactly matched

Multi-tone: g(t) = g₀(1 + Σᵢ Aᵢ·cos(ωᵢt))
  → Sweeps multiple frequencies simultaneously
  → Faster capture into instability tongues
  → Expected: 2-10× speedup

Chirped: g(t) = g₀(1 + A·cos(φ(t))), φ(t) = ω₀t + (α/2)t²
  → Frequency ramps linearly: ω(t) = ω₀ + αt
  → Guaranteed to hit resonance
  → Expected: Similar or better than multi-tone

GOAL: Maximize growth rate through optimized drive waveforms
"""

import numpy as np
import sys
from pathlib import Path
from scipy.linalg import expm, eig
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 80)
print("PHASE B - STEP 5: MULTI-TONE & CHIRPED DRIVING")
print("=" * 80)
print("\n🎯 GOAL: Optimize drive waveform for maximum growth rate")
print("     Test: Single-tone vs Multi-tone vs Chirped\n")

# ============================================================================
# PARAMETERS
# ============================================================================

# Two-level system (abstract model from Step 1)
DELTA = 0.1  # Energy gap
G0 = 1e-4    # Coupling

# Gain (from Step 4 analysis - use moderate value)
GAMMA_GAIN = 1e-6

# Time parameters
STEPS_PER_PERIOD = 200
NUM_PERIODS = 100  # Run longer to see growth

# Frequency range (from Step 1 optimization)
OMEGA_BASE = 7.906e-4  # Optimal single-tone frequency

print("System parameters:")
print(f"  Δ: {DELTA}")
print(f"  g₀: {G0}")
print(f"  γ_gain: {GAMMA_GAIN}")
print(f"  ω_base: {OMEGA_BASE:.4e}")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def two_level_hamiltonian(delta, g, gamma_gain=0.0):
    """Two-level Hamiltonian with optional PT gain."""
    H = np.array([[-0.5 * delta, g], [g, 0.5 * delta]], dtype=complex)
    if gamma_gain != 0.0:
        nonherm = -1j * np.array([[+0.5 * gamma_gain, 0.0], 
                                  [0.0, -0.5 * gamma_gain]])
        H = H + nonherm
    return H


def evolve_with_drive(delta, g0, gamma_gain, drive_func, omega_ref, num_periods, steps_per_period):
    """
    Evolve system with arbitrary drive function.
    
    Args:
        drive_func: Function of time returning drive amplitude
        omega_ref: Reference frequency (for period calculation)
    
    Returns:
        times, amplitudes, growth_rate
    """
    T = 2 * np.pi / omega_ref
    dt = T / steps_per_period
    total_steps = num_periods * steps_per_period
    
    U = np.eye(2, dtype=complex)
    t = 0.0
    
    times = []
    amplitudes = []
    
    for step in range(total_steps):
        # Drive amplitude from function
        drive_amp = drive_func(t)
        g_t = g0 * drive_amp
        
        # Hamiltonian
        H_t = two_level_hamiltonian(delta, g_t, gamma_gain)
        
        # Evolve
        U = expm(-1j * H_t * dt) @ U
        
        # Track amplitude growth
        if step % steps_per_period == 0:  # Sample once per period
            vals, _ = eig(U)
            max_mag = np.max(np.abs(vals))
            times.append(t)
            amplitudes.append(max_mag)
        
        t += dt
    
    # Compute growth rate from amplitude vs time
    times = np.array(times)
    amps = np.array(amplitudes)
    
    # Fit exponential: A(t) = A₀ exp(γt)
    # ln(A) = ln(A₀) + γt
    if len(amps) > 5 and np.all(amps > 0):
        log_amps = np.log(amps)
        coeffs = np.polyfit(times, log_amps, 1)
        growth_rate = coeffs[0] * omega_ref / (2 * np.pi)  # Convert to per-time
    else:
        growth_rate = 0.0
    
    return times, amps, growth_rate


# ============================================================================
# TEST 1: SINGLE-TONE (BASELINE)
# ============================================================================

print("\n" + "=" * 80)
print("TEST 1: SINGLE-TONE DRIVING (BASELINE)")
print("=" * 80)

amplitude_single = 0.01

def drive_single(t):
    return 1.0 + amplitude_single * np.cos(OMEGA_BASE * t)

print(f"\nDrive: g(t) = g₀ × (1 + {amplitude_single}·cos(ωt))")
print(f"  ω = {OMEGA_BASE:.4e}")

times_1, amps_1, growth_1 = evolve_with_drive(
    DELTA, G0, GAMMA_GAIN, drive_single, OMEGA_BASE, NUM_PERIODS, STEPS_PER_PERIOD
)

print(f"\n✓ Evolution complete")
print(f"  Final amplitude: {amps_1[-1]:.6f}")
print(f"  Growth rate: {growth_1:.6e} s⁻¹")

# ============================================================================
# TEST 2: DUAL-TONE
# ============================================================================

print("\n" + "=" * 80)
print("TEST 2: DUAL-TONE DRIVING")
print("=" * 80)

# Two frequencies: one below, one above optimal
omega_1 = 0.5 * OMEGA_BASE
omega_2 = 2.0 * OMEGA_BASE
A1 = 0.005
A2 = 0.005

def drive_dual(t):
    return 1.0 + A1 * np.cos(omega_1 * t) + A2 * np.cos(omega_2 * t)

print(f"\nDrive: g(t) = g₀ × (1 + A₁·cos(ω₁t) + A₂·cos(ω₂t))")
print(f"  ω₁ = {omega_1:.4e} (0.5× base)")
print(f"  ω₂ = {omega_2:.4e} (2.0× base)")
print(f"  A₁ = {A1}, A₂ = {A2}")

times_2, amps_2, growth_2 = evolve_with_drive(
    DELTA, G0, GAMMA_GAIN, drive_dual, OMEGA_BASE, NUM_PERIODS, STEPS_PER_PERIOD
)

print(f"\n✓ Evolution complete")
print(f"  Final amplitude: {amps_2[-1]:.6f}")
print(f"  Growth rate: {growth_2:.6e} s⁻¹")
print(f"  Speedup vs single: {growth_2/growth_1:.2f}×")

# ============================================================================
# TEST 3: TRI-TONE
# ============================================================================

print("\n" + "=" * 80)
print("TEST 3: TRI-TONE DRIVING")
print("=" * 80)

omega_1 = 0.5 * OMEGA_BASE
omega_2 = 1.0 * OMEGA_BASE
omega_3 = 2.0 * OMEGA_BASE
A1 = 0.0033
A2 = 0.0033
A3 = 0.0033

def drive_tri(t):
    return 1.0 + A1 * np.cos(omega_1 * t) + A2 * np.cos(omega_2 * t) + A3 * np.cos(omega_3 * t)

print(f"\nDrive: g(t) = g₀ × (1 + Σ Aᵢ·cos(ωᵢt)), i=1,2,3")
print(f"  ω₁ = {omega_1:.4e}")
print(f"  ω₂ = {omega_2:.4e}")
print(f"  ω₃ = {omega_3:.4e}")

times_3, amps_3, growth_3 = evolve_with_drive(
    DELTA, G0, GAMMA_GAIN, drive_tri, OMEGA_BASE, NUM_PERIODS, STEPS_PER_PERIOD
)

print(f"\n✓ Evolution complete")
print(f"  Final amplitude: {amps_3[-1]:.6f}")
print(f"  Growth rate: {growth_3:.6e} s⁻¹")
print(f"  Speedup vs single: {growth_3/growth_1:.2f}×")

# ============================================================================
# TEST 4: LINEAR CHIRP
# ============================================================================

print("\n" + "=" * 80)
print("TEST 4: LINEAR CHIRP")
print("=" * 80)

# Chirp from 0.1× to 10× base frequency over evolution time
omega_start = 0.1 * OMEGA_BASE
omega_end = 10.0 * OMEGA_BASE
T_total = NUM_PERIODS * (2 * np.pi / OMEGA_BASE)
alpha = (omega_end - omega_start) / T_total  # Chirp rate

amplitude_chirp = 0.01

def drive_chirp(t):
    phase = omega_start * t + 0.5 * alpha * t**2
    return 1.0 + amplitude_chirp * np.cos(phase)

print(f"\nDrive: g(t) = g₀ × (1 + A·cos(φ(t)))")
print(f"  φ(t) = ω₀t + (α/2)t²")
print(f"  ω(t) = ω₀ + αt (linear ramp)")
print(f"  ω_start = {omega_start:.4e}")
print(f"  ω_end = {omega_end:.4e}")
print(f"  α = {alpha:.4e}")

times_4, amps_4, growth_4 = evolve_with_drive(
    DELTA, G0, GAMMA_GAIN, drive_chirp, OMEGA_BASE, NUM_PERIODS, STEPS_PER_PERIOD
)

print(f"\n✓ Evolution complete")
print(f"  Final amplitude: {amps_4[-1]:.6f}")
print(f"  Growth rate: {growth_4:.6e} s⁻¹")
print(f"  Speedup vs single: {growth_4/growth_1:.2f}×")

# ============================================================================
# TEST 5: OPTIMIZED MULTI-TONE (Scan)
# ============================================================================

print("\n" + "=" * 80)
print("TEST 5: OPTIMIZED MULTI-TONE (PARAMETER SCAN)")
print("=" * 80)

print("\nScanning amplitude ratios...")

best_multi = None
best_growth_multi = 0

# Try different amplitude distributions
amp_ratios = [
    (0.5, 0.3, 0.2),  # Decreasing
    (0.33, 0.33, 0.34),  # Equal
    (0.2, 0.3, 0.5),  # Increasing
    (0.6, 0.2, 0.2),  # Emphasis on low freq
    (0.2, 0.2, 0.6),  # Emphasis on high freq
]

for i, (a1, a2, a3) in enumerate(amp_ratios, 1):
    total_amp = 0.01
    A1 = total_amp * a1
    A2 = total_amp * a2
    A3 = total_amp * a3
    
    def drive_opt(t):
        return 1.0 + A1 * np.cos(0.5*OMEGA_BASE * t) + \
                     A2 * np.cos(1.0*OMEGA_BASE * t) + \
                     A3 * np.cos(2.0*OMEGA_BASE * t)
    
    _, _, growth = evolve_with_drive(
        DELTA, G0, GAMMA_GAIN, drive_opt, OMEGA_BASE, NUM_PERIODS, STEPS_PER_PERIOD
    )
    
    print(f"  Config {i}: ({a1:.2f}, {a2:.2f}, {a3:.2f}) → growth = {growth:.6e} s⁻¹")
    
    if growth > best_growth_multi:
        best_growth_multi = growth
        best_multi = (a1, a2, a3)

print(f"\n✓ Best configuration: {best_multi}")
print(f"  Growth rate: {best_growth_multi:.6e} s⁻¹")
print(f"  Speedup vs single: {best_growth_multi/growth_1:.2f}×")

# ============================================================================
# COMPARISON
# ============================================================================

print("\n" + "=" * 80)
print("SUMMARY: DRIVE WAVEFORM COMPARISON")
print("=" * 80)

results_summary = [
    ("Single-tone", growth_1, 1.0),
    ("Dual-tone", growth_2, growth_2/growth_1),
    ("Tri-tone", growth_3, growth_3/growth_1),
    ("Chirped", growth_4, growth_4/growth_1),
    ("Optimized multi", best_growth_multi, best_growth_multi/growth_1),
]

print(f"\n{'Drive Type':<20} {'Growth Rate (s⁻¹)':<20} {'Speedup':<10}")
print("-" * 60)
for name, rate, speedup in results_summary:
    print(f"{name:<20} {rate:<20.6e} {speedup:<10.2f}×")

best_overall = max(results_summary, key=lambda x: x[1])
print(f"\n🏆 BEST: {best_overall[0]}")
print(f"   Growth rate: {best_overall[1]:.6e} s⁻¹")
print(f"   Speedup: {best_overall[2]:.2f}×")

# ============================================================================
# PLOT RESULTS
# ============================================================================

print("\n" + "=" * 80)
print("GENERATING PLOTS")
print("=" * 80)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Plot 1: Amplitude growth (log scale)
ax1.semilogy(times_1, amps_1, 'b-', linewidth=2, label=f'Single-tone ({growth_1:.2e} s⁻¹)')
ax1.semilogy(times_2, amps_2, 'g-', linewidth=2, label=f'Dual-tone ({growth_2:.2e} s⁻¹)')
ax1.semilogy(times_3, amps_3, 'r-', linewidth=2, label=f'Tri-tone ({growth_3:.2e} s⁻¹)')
ax1.semilogy(times_4, amps_4, 'm-', linewidth=2, label=f'Chirped ({growth_4:.2e} s⁻¹)')
ax1.set_xlabel('Time (s)', fontsize=12)
ax1.set_ylabel('Amplitude', fontsize=12)
ax1.set_title('Amplitude Growth: Different Drive Waveforms', fontsize=14, fontweight='bold')
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)

# Plot 2: Speedup comparison (bar chart)
names = [r[0] for r in results_summary]
speedups = [r[2] for r in results_summary]
colors = ['blue', 'green', 'red', 'magenta', 'orange']

bars = ax2.bar(range(len(names)), speedups, color=colors, alpha=0.7, edgecolor='black')
ax2.axhline(1.0, color='black', linestyle='--', linewidth=1, label='Baseline (single-tone)')
ax2.set_xticks(range(len(names)))
ax2.set_xticklabels(names, rotation=45, ha='right')
ax2.set_ylabel('Speedup Factor', fontsize=12)
ax2.set_title('Growth Rate Speedup vs Single-Tone', fontsize=14, fontweight='bold')
ax2.grid(True, alpha=0.3, axis='y')
ax2.legend()

# Add value labels on bars
for i, (bar, val) in enumerate(zip(bars, speedups)):
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height,
             f'{val:.2f}×', ha='center', va='bottom', fontsize=10, fontweight='bold')

plt.tight_layout()
plt.savefig('phase_b_multitone_results.png', dpi=150, bbox_inches='tight')
print("✓ Saved: phase_b_multitone_results.png")

# ============================================================================
# SAVE RESULTS
# ============================================================================

print("\n" + "=" * 80)
print("SAVING RESULTS")
print("=" * 80)

np.savez(
    'phase_b_multitone_results.npz',
    growth_single=growth_1,
    growth_dual=growth_2,
    growth_tri=growth_3,
    growth_chirp=growth_4,
    growth_optimized=best_growth_multi,
    best_config=best_multi,
    times_single=times_1,
    amps_single=amps_1,
    times_multi=times_3,
    amps_multi=amps_3,
)

print("✓ Saved: phase_b_multitone_results.npz")

# ============================================================================
# ASSESSMENT
# ============================================================================

print("\n" + "=" * 80)
print("ASSESSMENT: MULTI-TONE OPTIMIZATION")
print("=" * 80)

max_speedup = best_overall[2]

if max_speedup > 5:
    print(f"\n🚀 EXCELLENT: {max_speedup:.1f}× speedup achieved!")
    print(f"   Multi-tone driving significantly improves performance")
    print(f"   Recommendation: Use {best_overall[0]} for all future simulations")
elif max_speedup > 2:
    print(f"\n✅ GOOD: {max_speedup:.1f}× speedup achieved")
    print(f"   Multi-tone provides moderate improvement")
    print(f"   Worth using for optimization")
elif max_speedup > 1.1:
    print(f"\n→ MINOR: {max_speedup:.1f}× speedup")
    print(f"   Small improvement, may not justify complexity")
else:
    print(f"\n→ NEGLIGIBLE: {max_speedup:.1f}× speedup")
    print(f"   Single-tone is sufficient")

print("\n" + "=" * 80)
print("STEP 5 COMPLETE: MULTI-TONE & CHIRPED DRIVING")
print("=" * 80)
print(f"\nBest speedup: {max_speedup:.2f}×")
print("Combined with Purcell enhancement, this optimizes the amplification path!")
