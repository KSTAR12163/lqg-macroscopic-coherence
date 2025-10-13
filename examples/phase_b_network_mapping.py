#!/usr/bin/env python3
"""
Phase B - Step 2: MAP FLOQUET MODEL TO REAL NETWORK

Extract physical parameters from MatterGeometryCoupling:
  - Δ = E₁ - E₀ (energy gap between ground and first excited)
  - g₀ = |⟨1|H_int|0⟩| (effective coupling strength)

Then plug into Floquet model to get PHYSICAL growth rate estimates.

This connects the abstract two-level instability to the ACTUAL LQG network!
"""

import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.constants import L_PLANCK, HBAR
from src.core.spin_network import SpinNetwork
from src.floquet_instability.floquet_scan import (
    FloquetScanConfig,
    floquet_growth_rate,
)

import importlib
matter_coupling_module = importlib.import_module('src.04_coupling_engineering.matter_coupling')

MatterFieldProperties = matter_coupling_module.MatterFieldProperties
MatterFieldType = matter_coupling_module.MatterFieldType
MatterGeometryCoupling = matter_coupling_module.MatterGeometryCoupling

print("=" * 80)
print("PHASE B - STEP 2: NETWORK PARAMETER EXTRACTION")
print("=" * 80)
print("\n🎯 GOAL: Extract Δ and g₀ from real LQG network")
print("     Then compute PHYSICAL growth rate\n")

# ============================================================================
# BUILD NETWORK (Optimal configuration from Phase 1)
# ============================================================================

print("Building optimal network configuration...")

# Matter field
matter_field = MatterFieldProperties(
    field_type=MatterFieldType.SCALAR,
    characteristic_energy=1e-15,  # Joules
    characteristic_length=L_PLANCK * 1e10,
    impedance=1.0
)

# Optimal parameters from Phase 1
lambda_opt = 1.0
mu_opt = 0.1
dim = 32

# Create tetrahedral network (N=4, simplest)
network = SpinNetwork()
nodes = [network.add_node(i) for i in range(4)]

# Tetrahedral edges
edges = [
    (0, 1), (0, 2), (0, 3),
    (1, 2), (1, 3),
    (2, 3)
]

for i, j in edges:
    network.add_edge(i, j, 0.5)

print(f"✓ Network: 4 nodes, {len(edges)} edges (tetrahedral)")
print(f"✓ λ = {lambda_opt}, μ = {mu_opt}, dim = {dim}")

# ============================================================================
# COMPUTE ENERGY SPECTRUM
# ============================================================================

print("\nComputing energy spectrum...")

coupling = MatterGeometryCoupling(network, matter_field, lambda_opt, mu=mu_opt)
energies, eigvec = coupling.compute_energy_spectrum(dim)

# Extract gap
E0 = energies[0]
E1 = energies[1]
Delta = abs(E1 - E0)

print(f"\n✓ Ground state energy E₀: {E0:.6e} J")
print(f"✓ First excited E₁:       {E1:.6e} J")
print(f"✓ Gap Δ = E₁ - E₀:        {Delta:.6e} J")

# Convert to frequency
omega_gap = Delta / HBAR
print(f"✓ Gap frequency ω_gap:    {omega_gap:.6e} rad/s")
print(f"✓ Gap frequency f_gap:    {omega_gap/(2*np.pi):.6e} Hz")

# ============================================================================
# COMPUTE COUPLING STRENGTH
# ============================================================================

print("\nComputing interaction coupling...")

H_int = coupling.build_interaction_hamiltonian(dim)

# Coupling matrix element: ⟨1|H_int|0⟩
g0 = abs(eigvec[:, 1].conj() @ H_int @ eigvec[:, 0])

print(f"\n✓ Coupling g₀ = |⟨1|H_int|0⟩|: {g0:.6e} J")

# Also compute full Hamiltonian for perturbative check
H_full = coupling.build_full_hamiltonian(dim)
H_geom = H_full - H_int

ratio = np.linalg.norm(H_int) / np.linalg.norm(H_geom)
print(f"✓ Perturbative ratio:      {ratio:.6e}")
print(f"✓ Status: {'PERTURBATIVE ✓' if ratio < 0.1 else 'NON-PERTURBATIVE ⚠️'}")

# ============================================================================
# PHYSICAL PARAMETER SUMMARY
# ============================================================================

print("\n" + "=" * 80)
print("EXTRACTED PHYSICAL PARAMETERS")
print("=" * 80)

print(f"""
Two-level model parameters (for Floquet analysis):

  Δ (energy gap):        {Delta:.6e} J
  g₀ (coupling):         {g0:.6e} J
  ω_gap (gap freq):      {omega_gap:.6e} rad/s
  
  Ratio g₀/Δ:            {g0/Delta:.6e}
  
These are the REAL values from optimized LQG network!
""")

# ============================================================================
# COMPUTE FLOQUET GROWTH WITH PHYSICAL PARAMETERS
# ============================================================================

print("=" * 80)
print("FLOQUET ANALYSIS WITH PHYSICAL PARAMETERS")
print("=" * 80)

print("\nTesting with physical Δ and g₀...")

# Test different gamma_gain values
gamma_gains = [1e-12, 1e-10, 1e-8, 1e-6, 1e-4]

# Drive parameters (scan around gap frequency)
omega_values = [0.01 * omega_gap, 0.1 * omega_gap, omega_gap, 10 * omega_gap]
amplitude_values = [0.1, 0.5, 1.0]

print(f"\nScanning:")
print(f"  γ_gain: {gamma_gains}")
print(f"  ω: [0.01×ω_gap ... 10×ω_gap]")
print(f"  A: {amplitude_values}")

best_physical = None
best_growth_rate = -np.inf

results = []

for gamma_gain in gamma_gains:
    for omega in omega_values:
        for amplitude in amplitude_values:
            config = FloquetScanConfig(
                delta=Delta,
                g0=g0,
                amplitude=amplitude,
                omega=omega,
                gamma_gain=gamma_gain,
                steps_per_period=200,
                periods=1,
            )
            
            growth_per_period, details = floquet_growth_rate(config)
            
            # Growth rate per time (key metric)
            growth_rate = growth_per_period * omega / (2 * np.pi)
            
            # Time to close 10^14 gap
            if growth_rate > 1e-30:
                time_to_1e14 = np.log(1e14) / growth_rate
            else:
                time_to_1e14 = np.inf
            
            results.append({
                'gamma_gain': gamma_gain,
                'omega': omega,
                'omega_gap_fraction': omega / omega_gap,
                'amplitude': amplitude,
                'growth_per_period': growth_per_period,
                'growth_rate': growth_rate,
                'time_to_1e14': time_to_1e14,
            })
            
            if growth_rate > best_growth_rate:
                best_growth_rate = growth_rate
                best_physical = results[-1]

# ============================================================================
# RESULTS WITH PHYSICAL PARAMETERS
# ============================================================================

print("\n" + "=" * 80)
print("BEST RESULT WITH PHYSICAL PARAMETERS")
print("=" * 80)

if best_physical:
    print(f"\n✅ BEST CONFIGURATION:")
    print(f"  γ_gain:           {best_physical['gamma_gain']:.6e}")
    print(f"  ω (drive):        {best_physical['omega']:.6e} rad/s")
    print(f"  ω/ω_gap:          {best_physical['omega_gap_fraction']:.4f}×")
    print(f"  A (amplitude):    {best_physical['amplitude']:.4f}")
    
    print(f"\n📊 GROWTH METRICS:")
    print(f"  Growth per period:    {best_physical['growth_per_period']:.6f}")
    print(f"  Growth rate per time: {best_physical['growth_rate']:.6e} s⁻¹")
    
    print(f"\n⏱️  TIME TO CLOSE GAP:")
    print(f"  Time to 10¹⁴×:    {best_physical['time_to_1e14']:.6e} s")
    
    YEAR = 365.25 * 24 * 3600
    if best_physical['time_to_1e14'] < np.inf:
        years = best_physical['time_to_1e14'] / YEAR
        print(f"                    = {years:.6e} years")
        
        if years < 1:
            print("\n🚀 EXCELLENT! Sub-year → potentially viable")
        elif years < 100:
            print("\n⚠️  DECADES: Need optimization (Purcell, higher gain)")
        elif years < 1e6:
            print("\n⚠️  CENTURIES: Major challenges")
        else:
            print("\n❌ COSMOLOGICAL: Not viable without breakthrough")
    else:
        print("                    = infinite (no growth)")

# ============================================================================
# DETAILED TABLE
# ============================================================================

print("\n" + "=" * 80)
print("TOP 10 CONFIGURATIONS (by growth rate)")
print("=" * 80)

sorted_results = sorted(results, key=lambda r: r['growth_rate'], reverse=True)

print(f"\n{'Rank':<6} {'γ_gain':<12} {'ω/ω_gap':<10} {'A':<8} {'Growth rate':<15} {'Time to 10¹⁴×':<15}")
print("-" * 80)

for i, r in enumerate(sorted_results[:10], 1):
    time_str = f"{r['time_to_1e14']:.3e}" if r['time_to_1e14'] < np.inf else "inf"
    print(f"{i:<6} {r['gamma_gain']:<12.3e} {r['omega_gap_fraction']:<10.4f} "
          f"{r['amplitude']:<8.2f} {r['growth_rate']:<15.3e} {time_str:<15}")

# ============================================================================
# SCALING ANALYSIS
# ============================================================================

print("\n" + "=" * 80)
print("REQUIRED γ_gain FOR DIFFERENT TIMESCALES")
print("=" * 80)

target_years = [1, 10, 100, 1000]

print(f"\nTo close 10¹⁴× gap in:")

for years in target_years:
    target_time = years * YEAR
    required_growth_rate = np.log(1e14) / target_time
    
    print(f"\n  {years} years ({target_time:.3e} s):")
    print(f"    Required growth rate: {required_growth_rate:.6e} s⁻¹")
    
    # Find minimum gamma_gain that achieves this (rough estimate)
    # Assume growth_rate scales linearly with gamma_gain (approximation)
    if best_growth_rate > 0:
        scaling_factor = required_growth_rate / best_growth_rate
        required_gamma = best_physical['gamma_gain'] * scaling_factor
        print(f"    Estimated γ_gain needed: {required_gamma:.6e}")
        
        if required_gamma < 1e-3:
            print(f"    ✓ Plausible (with optimization)")
        elif required_gamma < 1:
            print(f"    ⚠️  Challenging but possible")
        else:
            print(f"    ❌ Unrealistic")

# ============================================================================
# SAVE RESULTS
# ============================================================================

print("\n" + "=" * 80)
print("SAVING RESULTS")
print("=" * 80)

np.savez(
    'phase_b_network_mapping.npz',
    # Physical parameters
    Delta=Delta,
    g0=g0,
    omega_gap=omega_gap,
    # Best result
    best_gamma_gain=best_physical['gamma_gain'] if best_physical else 0,
    best_omega=best_physical['omega'] if best_physical else 0,
    best_amplitude=best_physical['amplitude'] if best_physical else 0,
    best_growth_rate=best_growth_rate,
    best_time_to_1e14=best_physical['time_to_1e14'] if best_physical else np.inf,
    # All results
    gamma_gains=gamma_gains,
    omega_values=omega_values,
    amplitude_values=amplitude_values,
)

print("✓ Saved to phase_b_network_mapping.npz")

print("\n" + "=" * 80)
print("STEP 2 COMPLETE")
print("=" * 80)
print("\nPhysical parameters extracted and mapped to Floquet model!")
print("Next: Implement pumped Lindblad dynamics (Step 3)")
