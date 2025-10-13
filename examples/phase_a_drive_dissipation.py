#!/usr/bin/env python3
"""
Phase A: Drive & Dissipation Search

Test for non-equilibrium amplification mechanisms that static analysis missed:
1. Time-periodic driving (Floquet engineering)
2. Parametric resonance (driven μ(t), λ(t))
3. Dissipative criticality (Lindblad dynamics)

Goal: Find any parameter regime where susceptibility > 1000× baseline
This is the single most promising path to discovering amplification.
"""

import numpy as np
import sys
import time
from pathlib import Path
from scipy.linalg import expm

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.constants import L_PLANCK, HBAR
from src.core.spin_network import SpinNetwork

import importlib
matter_coupling_module = importlib.import_module('src.04_coupling_engineering.matter_coupling')

MatterFieldProperties = matter_coupling_module.MatterFieldProperties
MatterFieldType = matter_coupling_module.MatterFieldType
MatterGeometryCoupling = matter_coupling_module.MatterGeometryCoupling

print("=" * 80)
print("PHASE A: DRIVE & DISSIPATION SEARCH")
print("=" * 80)
print("\nSearching for non-equilibrium amplification mechanisms:")
print("  1. Parametric driving (time-periodic coupling)")
print("  2. Resonant pumping (driven μ(t), λ(t))")
print("  3. Dissipative enhancement")
print("\nGoal: Find susceptibility > 1000× baseline")
print("This is the CRITICAL test for warp viability.\n")

# Matter field
matter_field = MatterFieldProperties(
    field_type=MatterFieldType.SCALAR,
    characteristic_energy=1e-15,
    characteristic_length=L_PLANCK * 1e10,
    impedance=1.0
)

# Optimal parameters from Phase 1
lambda_base = 1.0
mu_base = 0.1
dim = 32

def create_test_network(num_nodes=8):
    """Create small test network for quick iterations."""
    network = SpinNetwork()
    nodes = [network.add_node(i) for i in range(num_nodes)]
    
    # Regular lattice
    edges_per_node = min(4, num_nodes - 1)
    added_edges = set()
    for i in range(num_nodes):
        for j in range(1, edges_per_node // 2 + 1):
            neighbor = (i + j) % num_nodes
            edge_key = tuple(sorted([i, neighbor]))
            if edge_key not in added_edges:
                network.add_edge(i, neighbor, 0.5)
                added_edges.add(edge_key)
    
    return network

def compute_static_susceptibility(network, lambda_val, mu, dim, perturbation=0.01):
    """
    Baseline: static susceptibility to parameter changes.
    χ = ∂⟨coupling⟩/∂μ
    """
    # Compute at base parameters
    coupling_base = MatterGeometryCoupling(network, matter_field, lambda_val, mu=mu)
    energies_base, eigvec_base = coupling_base.compute_energy_spectrum(dim)
    H_int_base = coupling_base.build_interaction_hamiltonian(dim)
    coupling_val_base = abs(eigvec_base[:, 1].conj() @ H_int_base @ eigvec_base[:, 0])
    
    # Compute at perturbed parameters
    mu_pert = mu + perturbation
    coupling_pert = MatterGeometryCoupling(network, matter_field, lambda_val, mu=mu_pert)
    energies_pert, eigvec_pert = coupling_pert.compute_energy_spectrum(dim)
    H_int_pert = coupling_pert.build_interaction_hamiltonian(dim)
    coupling_val_pert = abs(eigvec_pert[:, 1].conj() @ H_int_pert @ eigvec_pert[:, 0])
    
    # Susceptibility
    susceptibility = abs(coupling_val_pert - coupling_val_base) / perturbation
    
    return susceptibility, coupling_val_base

def compute_driven_response(network, lambda_val, mu, dim, 
                           drive_freq, drive_amplitude, num_periods=10):
    """
    Driven system: λ(t) = λ₀(1 + A·sin(ωt))
    
    Compute time-averaged coupling and effective susceptibility.
    Look for parametric resonance where response >> drive amplitude.
    """
    # Base Hamiltonian
    coupling = MatterGeometryCoupling(network, matter_field, lambda_val, mu=mu)
    energies, eigvec = coupling.compute_energy_spectrum(dim)
    H_full = coupling.build_full_hamiltonian(dim)
    H_int = coupling.build_interaction_hamiltonian(dim)
    
    # Characteristic energy scale (for setting drive frequency)
    E_gap = abs(energies[1] - energies[0])
    omega = drive_freq * E_gap / HBAR  # Drive frequency in rad/s
    
    # Time evolution with periodic drive
    period = 2 * np.pi / omega
    dt = period / 20  # 20 time steps per period
    num_steps = int(num_periods * period / dt)
    
    # Initial state (ground state)
    psi = eigvec[:, 0].copy()
    
    # Track coupling over time
    couplings = []
    
    for step in range(num_steps):
        t = step * dt
        
        # Time-dependent coupling: λ(t) = λ₀(1 + A·sin(ωt))
        lambda_t = lambda_val * (1 + drive_amplitude * np.sin(omega * t))
        
        # Build time-dependent Hamiltonian
        coupling_t = MatterGeometryCoupling(network, matter_field, lambda_t, mu=mu)
        H_int_t = coupling_t.build_interaction_hamiltonian(dim)
        H_t = H_full + H_int_t
        
        # Evolve: |ψ(t+dt)⟩ = exp(-iH(t)dt/ℏ) |ψ(t)⟩
        U = expm(-1j * H_t * dt / HBAR)
        psi = U @ psi
        
        # Compute instantaneous coupling to excited state
        coupling_inst = abs(eigvec[:, 1].conj() @ psi)
        couplings.append(coupling_inst)
    
    # Time-averaged coupling
    avg_coupling = np.mean(couplings)
    max_coupling = np.max(couplings)
    
    # Enhancement factor (vs static)
    static_coupling = abs(eigvec[:, 1].conj() @ eigvec[:, 0])  # Should be ~0
    
    # Better: compare to perturbative expectation
    # For small drive, expect response ∝ A (linear)
    # For resonance, expect response >> A (nonlinear amplification)
    
    enhancement = max_coupling / (drive_amplitude + 1e-20)
    
    return avg_coupling, max_coupling, enhancement

def compute_dissipative_steady_state(network, lambda_val, mu, dim, 
                                     dissipation_rate=0.1, num_steps=100):
    """
    Open system with Lindblad dissipation.
    
    Master equation: dρ/dt = -i[H,ρ]/ℏ + Σ(L_k ρ L_k† - {L_k†L_k, ρ}/2)
    
    Jump operators: L = √γ |ground⟩⟨excited| (decay to ground state)
    
    Look for enhanced steady-state coupling due to dissipative selection.
    """
    # Build Hamiltonians
    coupling = MatterGeometryCoupling(network, matter_field, lambda_val, mu=mu)
    energies, eigvec = coupling.compute_energy_spectrum(dim)
    H_full = coupling.build_full_hamiltonian(dim)
    H_int = coupling.build_interaction_hamiltonian(dim)
    H_total = H_full + H_int
    
    # Initial density matrix (ground state)
    rho = np.outer(eigvec[:, 0], eigvec[:, 0].conj())
    
    # Jump operator (decay from excited to ground)
    gamma = dissipation_rate * abs(energies[1] - energies[0])
    L = np.sqrt(gamma) * np.outer(eigvec[:, 0], eigvec[:, 1].conj())
    L_dag = L.conj().T
    
    # Lindblad superoperator
    dt = 0.01 / gamma  # Time step
    
    for step in range(num_steps):
        # Coherent evolution: -i[H,ρ]/ℏ
        commutator = -1j * (H_total @ rho - rho @ H_total) / HBAR
        
        # Dissipative part: Σ(L ρ L† - {L†L, ρ}/2)
        dissipator = (L @ rho @ L_dag - 
                     0.5 * (L_dag @ L @ rho + rho @ L_dag @ L))
        
        # Update
        drho = (commutator + dissipator) * dt
        rho = rho + drho
        
        # Normalize
        rho = rho / np.trace(rho)
    
    # Steady-state coupling
    # Compute ⟨excited|ρ|ground⟩ (off-diagonal coherence)
    steady_coupling = abs(eigvec[:, 1].conj() @ rho @ eigvec[:, 0])
    
    return steady_coupling

# ============================================================================
# TEST 1: STATIC SUSCEPTIBILITY (BASELINE)
# ============================================================================

print("=" * 80)
print("TEST 1: STATIC SUSCEPTIBILITY (BASELINE)")
print("=" * 80)

network = create_test_network(8)

susceptibility_static, coupling_static = compute_static_susceptibility(
    network, lambda_base, mu_base, dim
)

print(f"\nStatic coupling: {coupling_static:.4e} J")
print(f"Static susceptibility (∂coupling/∂μ): {susceptibility_static:.4e} J")
print(f"\nThis is the baseline to beat (need >1000× enhancement)")

baseline_susceptibility = susceptibility_static

# ============================================================================
# TEST 2: PARAMETRIC DRIVING
# ============================================================================

print("\n" + "=" * 80)
print("TEST 2: PARAMETRIC DRIVING")
print("=" * 80)
print("\nScanning drive frequency and amplitude...")

# Scan drive parameters
drive_frequencies = [0.5, 1.0, 2.0, 4.0]  # Multiples of gap frequency
drive_amplitudes = [0.01, 0.05, 0.1, 0.2]

best_enhancement = 0
best_params = None

results_driven = []

for freq in drive_frequencies:
    for amp in drive_amplitudes:
        print(f"\n  ω/ω_gap = {freq:.1f}, A = {amp:.2f}:", end=" ", flush=True)
        
        try:
            avg, max_coup, enh = compute_driven_response(
                network, lambda_base, mu_base, dim,
                drive_freq=freq, drive_amplitude=amp, num_periods=5
            )
            
            print(f"max_coupling = {max_coup:.3e}, enhancement = {enh:.1f}×")
            
            results_driven.append({
                'freq': freq,
                'amp': amp,
                'max_coupling': max_coup,
                'enhancement': enh
            })
            
            if enh > best_enhancement:
                best_enhancement = enh
                best_params = (freq, amp)
                
        except Exception as e:
            print(f"ERROR: {e}")

print(f"\n✓ Best parametric enhancement: {best_enhancement:.1f}×")
if best_params:
    print(f"  at ω/ω_gap = {best_params[0]:.1f}, A = {best_params[1]:.2f}")

susceptibility_driven = best_enhancement * baseline_susceptibility

# ============================================================================
# TEST 3: DISSIPATIVE ENHANCEMENT
# ============================================================================

print("\n" + "=" * 80)
print("TEST 3: DISSIPATIVE ENHANCEMENT")
print("=" * 80)
print("\nScanning dissipation rates...")

dissipation_rates = [0.01, 0.05, 0.1, 0.5, 1.0, 2.0]

results_dissipative = []

for gamma in dissipation_rates:
    print(f"\n  γ = {gamma:.2f}:", end=" ", flush=True)
    
    try:
        steady = compute_dissipative_steady_state(
            network, lambda_base, mu_base, dim,
            dissipation_rate=gamma, num_steps=50
        )
        
        enhancement = steady / (coupling_static + 1e-200)
        
        print(f"steady_coupling = {steady:.3e}, enhancement = {enhancement:.1f}×")
        
        results_dissipative.append({
            'gamma': gamma,
            'steady_coupling': steady,
            'enhancement': enhancement
        })
        
    except Exception as e:
        print(f"ERROR: {e}")

if results_dissipative:
    best_diss = max(results_dissipative, key=lambda x: x['enhancement'])
    print(f"\n✓ Best dissipative enhancement: {best_diss['enhancement']:.1f}×")
    print(f"  at γ = {best_diss['gamma']:.2f}")

# ============================================================================
# SUMMARY & DECISION
# ============================================================================

print("\n" + "=" * 80)
print("PHASE A RESULTS")
print("=" * 80)

print(f"\n{'Mechanism':<30s} {'Enhancement':>15s} {'vs Baseline':>15s}")
print("-" * 80)

print(f"{'Static (baseline)':<30s} {1.0:>15.1f}× {'---':>15s}")

if results_driven:
    print(f"{'Parametric driving':<30s} {best_enhancement:>15.1f}× " +
          f"{'✓' if best_enhancement > 10 else '---':>15s}")

if results_dissipative:
    diss_enh = best_diss['enhancement']
    print(f"{'Dissipative steady-state':<30s} {diss_enh:>15.1f}× " +
          f"{'✓' if diss_enh > 10 else '---':>15s}")

# Check for amplification
max_found = max(best_enhancement if results_driven else 0,
                best_diss['enhancement'] if results_dissipative else 0)

print("\n" + "=" * 80)
print("CRITICAL ASSESSMENT")
print("=" * 80)

threshold_moderate = 10
threshold_strong = 100
threshold_exceptional = 1000

if max_found > threshold_exceptional:
    print(f"\n🎯 EXCEPTIONAL AMPLIFICATION FOUND: {max_found:.0f}×")
    print("\n✅ This could be the missing mechanism!")
    print("\nImmediate next steps:")
    print("  1. Scale to larger networks (N=20, 50, 100)")
    print("  2. Test if enhancement grows with N")
    print("  3. Optimize drive parameters further")
    print("  4. THIS IS THE PATH TO WARP!")
    
elif max_found > threshold_strong:
    print(f"\n⚠ STRONG AMPLIFICATION FOUND: {max_found:.0f}×")
    print("\n→ Promising but need more")
    print("\nNext steps:")
    print("  1. Optimize parameters more carefully")
    print("  2. Try combined drive + dissipation")
    print("  3. Test other drive waveforms (square, sawtooth)")
    print("  4. Scale to larger systems")
    
elif max_found > threshold_moderate:
    print(f"\n→ MODERATE AMPLIFICATION: {max_found:.0f}×")
    print("\n→ Better than static but far from target")
    print("\nNext steps:")
    print("  1. Try Phase B (exotic topologies, larger N)")
    print("  2. Test Floquet resonances more carefully")
    print("  3. Consider multi-frequency driving")
    
else:
    print(f"\n❌ NO SIGNIFICANT AMPLIFICATION: {max_found:.0f}×")
    print("\n→ Non-equilibrium effects don't help in this regime")
    print("\nConclusion:")
    print("  • Static and driven responses are similar")
    print("  • No parametric resonance or dissipative criticality found")
    print("  • Current model doesn't support amplification")
    print("\nOptions:")
    print("  1. Try Phase B (large-N, exotic topologies)")
    print("  2. Pivot to cosmology (Path 2)")
    print("  3. Document null results (Path 3)")

print("\n" + "=" * 80)
print("PHASE A COMPLETE")
print("=" * 80)

# Save results
print("\nSaving results to phase_a_results.npz...")
np.savez('phase_a_results.npz',
         baseline_susceptibility=baseline_susceptibility,
         driven_results=results_driven,
         dissipative_results=results_dissipative,
         max_enhancement=max_found)

print("✓ Results saved")
print("\n" + "=" * 80)
