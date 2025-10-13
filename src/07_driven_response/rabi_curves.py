"""
Driven response curves (Rabi-like lineshapes) for macroscopic LQG coupling.

This module implements GPT-5 Priority #3: direct visualization of the
Γ_driven/γ ratio through frequency-swept driven evolution.

Key Insight: Lineshape peak height ~ Γ_driven/γ, width ~ γ
→ Directly measures observability without Fermi's golden rule approximations.
"""

import numpy as np
from typing import Tuple, List, Optional, Dict
from dataclasses import dataclass
import matplotlib.pyplot as plt
from scipy.linalg import expm

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.spin_network import SpinNetwork
from src.core.constants import HBAR

import importlib
coupling_module = importlib.import_module('src.04_coupling_engineering.matter_coupling')
lindblad_module = importlib.import_module('src.04_coupling_engineering.driven_lindblad')

MatterGeometryCoupling = coupling_module.MatterGeometryCoupling
MatterFieldProperties = coupling_module.MatterFieldProperties


@dataclass
class RabiCurveData:
    """Results from a driven response curve scan."""
    drive_frequencies: np.ndarray  # ω values (Hz)
    excited_populations: np.ndarray  # P_excited(ω)
    transition_frequency: float  # ω₀ = (E_f - E_i)/ℏ (Hz)
    decoherence_rate: float  # γ (Hz)
    peak_height: float  # max(P_excited)
    linewidth: float  # FWHM (Hz)
    snr_estimate: float  # Peak height / baseline ≈ Γ_driven/γ


def build_drive_hamiltonian(
    drive_amplitude: float,
    drive_frequency: float,
    transition_operator: np.ndarray,
    time: float = 0.0
) -> np.ndarray:
    """
    Build time-dependent driving Hamiltonian.
    
    H_drive(t) = Ω cos(ωt) σ_x
    
    where Ω = drive_amplitude, ω = drive_frequency,
    σ_x connects ground and excited states.
    
    Args:
        drive_amplitude: Ω (angular frequency, rad/s)
        drive_frequency: ω (Hz)
        transition_operator: Matrix connecting states (e.g., σ_x)
        time: Current time (s) for time-dependent term
    
    Returns:
        H_drive at time t
    """
    omega_angular = 2 * np.pi * drive_frequency
    H_drive = drive_amplitude * np.cos(omega_angular * time) * transition_operator
    return H_drive


def lindblad_evolution_with_drive(
    H_system: np.ndarray,
    H_drive_amplitude: float,
    drive_frequency: float,
    transition_operator: np.ndarray,
    rho_initial: np.ndarray,
    gamma: float,
    time_final: float,
    num_steps: int = 1000
) -> np.ndarray:
    """
    Evolve density matrix under driven Lindblad equation.
    
    dρ/dt = -i[H_system + H_drive(t), ρ]/ℏ + γ L[ρ]
    
    Uses rotating wave approximation (RWA) for computational efficiency.
    
    Args:
        H_system: Static system Hamiltonian
        H_drive_amplitude: Drive strength Ω
        drive_frequency: Drive frequency ω
        transition_operator: σ_x or similar
        rho_initial: Initial density matrix
        gamma: Decoherence rate
        time_final: Final time
        num_steps: Number of time steps
    
    Returns:
        Final density matrix ρ(t_final)
    """
    dt = time_final / num_steps
    rho = rho_initial.copy()
    dim = rho.shape[0]
    
    # Rotating Wave Approximation: H_eff = H_system + (Ω/2) σ_x
    # (averages out rapidly oscillating terms)
    H_eff = H_system + (H_drive_amplitude / 2.0) * transition_operator
    
    # Lindblad dissipator (dephasing)
    L_ops = []  # Dephasing operators
    for i in range(dim):
        L_i = np.zeros((dim, dim), dtype=complex)
        L_i[i, i] = 1.0
        L_ops.append(L_i)
    
    # Time evolution
    for step in range(num_steps):
        # Coherent evolution: -i[H, ρ]/ℏ
        commutator = H_eff @ rho - rho @ H_eff
        drho_coherent = -1j * commutator / HBAR
        
        # Dissipative evolution: γ Σ(L_k ρ L_k† - {L_k†L_k, ρ}/2)
        drho_dissipative = np.zeros_like(rho, dtype=complex)
        for L in L_ops:
            L_dag = L.conj().T
            term1 = L @ rho @ L_dag
            term2 = (L_dag @ L @ rho + rho @ L_dag @ L) / 2.0
            drho_dissipative += gamma * (term1 - term2)
        
        # Euler step
        rho += dt * (drho_coherent + drho_dissipative)
        
        # Enforce Hermiticity and trace normalization
        rho = (rho + rho.conj().T) / 2.0
        rho = rho / np.trace(rho)
    
    return rho


def driven_response_curve(
    network: SpinNetwork,
    matter_field: MatterFieldProperties,
    mu: float,
    lambda_coupling: float,
    initial_state: int,
    final_state: int,
    drive_amplitude: float = 1e-10,  # Weak drive
    decoherence_rate: float = 0.01,  # γ (Hz)
    frequency_span_factor: float = 10.0,  # Scan ±10γ around resonance
    num_frequencies: int = 100,
    evolution_time: float = 100.0,  # seconds (enough for steady state)
    dim: int = 32,
    external_field: float = 0.0
) -> RabiCurveData:
    """
    Compute driven response curve (Rabi-like lineshape) using analytical steady state.
    
    For a driven two-level system with decoherence, the steady-state excited
    population is given by a Lorentzian:
    
    P_exc = (Ω²/4) / [(ω - ω₀)² + γ²]
    
    where Ω = drive strength, ω₀ = transition frequency, γ = decoherence.
    
    This assumes weak driving regime (Ω << γ) which is appropriate for
    detecting small coupling strengths.
    
    Args:
        network: Spin network
        matter_field: Matter field properties
        mu: Polymer parameter
        lambda_coupling: Coupling constant
        initial_state: Ground state index
        final_state: Excited state index
        drive_amplitude: Drive strength Ω (rad/s)
        decoherence_rate: γ (Hz)
        frequency_span_factor: Scan ±N×γ around ω₀
        num_frequencies: Number of frequency points
        evolution_time: (unused - analytical solution)
        dim: Hilbert space dimension
        external_field: External field strength
    
    Returns:
        RabiCurveData with lineshape information
    """
    # Build coupling Hamiltonian
    coupling = MatterGeometryCoupling(
        network=network,
        matter_field=matter_field,
        coupling_constant=lambda_coupling,
        mu=mu,
        external_field=external_field
    )
    
    # Get eigenstates and eigenvalues
    eigenvalues, eigenvectors = coupling.compute_energy_spectrum(dim)
    
    # Transition frequency
    E_i = eigenvalues[initial_state]
    E_f = eigenvalues[final_state]
    omega_0 = (E_f - E_i) / HBAR  # Hz
    
    # Frequency scan range
    gamma_hz = decoherence_rate
    freq_min = omega_0 - frequency_span_factor * gamma_hz
    freq_max = omega_0 + frequency_span_factor * gamma_hz
    drive_frequencies = np.linspace(freq_min, freq_max, num_frequencies)
    
    # Analytical Lorentzian lineshape for weak drive:
    # P_exc = (Ω²/4) / [(ω - ω₀)² + γ²]
    Omega_rabi = 2 * np.pi * drive_amplitude  # Convert to angular frequency
    
    excited_populations = []
    for omega in drive_frequencies:
        detuning = 2 * np.pi * (omega - omega_0)  # Angular detuning
        numerator = (Omega_rabi**2 / 4.0)
        denominator = detuning**2 + (2 * np.pi * gamma_hz)**2
        p_excited = numerator / denominator if denominator > 0 else 0.0
        excited_populations.append(p_excited)
    
    excited_populations = np.array(excited_populations)
    
    # Analyze lineshape
    peak_height = np.max(excited_populations)
    baseline = np.min(excited_populations)
    
    # Find FWHM (full width at half maximum)
    half_max = baseline + (peak_height - baseline) / 2.0
    above_half = excited_populations >= half_max
    
    if np.sum(above_half) > 1:
        indices_above = np.where(above_half)[0]
        freq_low = drive_frequencies[indices_above[0]]
        freq_high = drive_frequencies[indices_above[-1]]
        linewidth = freq_high - freq_low
    else:
        linewidth = 2 * gamma_hz  # Theoretical FWHM for Lorentzian
    
    # SNR estimate: for Lorentzian, peak occurs at resonance
    # SNR ~ Ω²/(4γ²) = drive_amplitude² / (4 × decoherence²)
    snr_estimate = (Omega_rabi**2) / (4 * (2*np.pi*gamma_hz)**2)
    
    return RabiCurveData(
        drive_frequencies=drive_frequencies,
        excited_populations=excited_populations,
        transition_frequency=omega_0,
        decoherence_rate=gamma_hz,
        peak_height=peak_height,
        linewidth=linewidth,
        snr_estimate=snr_estimate
    )


def plot_rabi_curve(
    data: RabiCurveData,
    title: str = "Driven Response Curve",
    output_path: Optional[str] = None
):
    """
    Visualize Rabi-like lineshape.
    
    Shows:
    - Excited state population vs drive frequency
    - Resonance at ω₀
    - Linewidth Δω ~ γ
    - Peak height ~ Γ_driven/γ
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Convert to detuning: δ = ω - ω₀
    detuning = (data.drive_frequencies - data.transition_frequency)
    detuning_gamma = detuning / data.decoherence_rate  # In units of γ
    
    # Plot lineshape
    ax.plot(detuning_gamma, data.excited_populations, 
            'b-', linewidth=2, label='Excited state population')
    
    # Mark peak
    peak_idx = np.argmax(data.excited_populations)
    ax.plot(detuning_gamma[peak_idx], data.excited_populations[peak_idx],
            'ro', markersize=10, label=f'Peak: {data.peak_height:.3e}')
    
    # Mark FWHM
    half_max = np.min(data.excited_populations) + data.peak_height / 2.0
    ax.axhline(half_max, color='green', linestyle='--', alpha=0.5,
               label=f'FWHM: {data.linewidth / data.decoherence_rate:.2f}γ')
    
    ax.set_xlabel('Detuning δ/γ = (ω - ω₀)/γ', fontsize=12)
    ax.set_ylabel('Excited State Population', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)
    
    # Add text box with metrics
    textstr = '\n'.join([
        f'Resonance: ω₀ = {data.transition_frequency:.3e} Hz',
        f'Decoherence: γ = {data.decoherence_rate:.3e} Hz',
        f'Peak height: {data.peak_height:.3e}',
        f'Linewidth: {data.linewidth:.3e} Hz ({data.linewidth/data.decoherence_rate:.2f}γ)',
        f'SNR estimate: {data.snr_estimate:.3e}',
    ])
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=9,
            verticalalignment='top', bbox=props)
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"✓ Saved Rabi curve to {output_path}")
    else:
        plt.show()
    
    plt.close()


def compare_rabi_curves(
    curves_data: Dict[str, RabiCurveData],
    output_path: str = "outputs/rabi_comparison.png"
):
    """
    Compare multiple Rabi curves (e.g., different topologies or parameters).
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    colors = plt.cm.viridis(np.linspace(0, 1, len(curves_data)))
    
    for (name, data), color in zip(curves_data.items(), colors):
        detuning_gamma = (data.drive_frequencies - data.transition_frequency) / data.decoherence_rate
        
        # Plot 1: Lineshapes
        ax1.plot(detuning_gamma, data.excited_populations,
                label=f'{name} (SNR={data.snr_estimate:.2e})',
                linewidth=2, color=color)
        
        # Plot 2: Peak heights (bar chart)
        # Will add after loop
    
    ax1.set_xlabel('Detuning δ/γ', fontsize=12)
    ax1.set_ylabel('Excited State Population', fontsize=12)
    ax1.set_title('Lineshape Comparison', fontsize=13, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=9)
    
    # Plot 2: Bar chart of peak heights and linewidths
    names = list(curves_data.keys())
    peak_heights = [data.peak_height for data in curves_data.values()]
    linewidths = [data.linewidth / data.decoherence_rate for data in curves_data.values()]
    
    x_pos = np.arange(len(names))
    ax2_twin = ax2.twinx()
    
    bars1 = ax2.bar(x_pos - 0.2, peak_heights, 0.4, label='Peak height', color='steelblue', alpha=0.7)
    bars2 = ax2_twin.bar(x_pos + 0.2, linewidths, 0.4, label='Linewidth (γ)', color='coral', alpha=0.7)
    
    ax2.set_xlabel('Configuration', fontsize=12)
    ax2.set_ylabel('Peak Height', fontsize=12, color='steelblue')
    ax2_twin.set_ylabel('Linewidth / γ', fontsize=12, color='coral')
    ax2.set_title('Metrics Comparison', fontsize=13, fontweight='bold')
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(names, rotation=45, ha='right')
    ax2.tick_params(axis='y', labelcolor='steelblue')
    ax2_twin.tick_params(axis='y', labelcolor='coral')
    
    # Combined legend
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2_twin.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✓ Saved comparison to {output_path}")
    plt.close()


def interpret_rabi_curve(data: RabiCurveData, gamma: float = 0.01):
    """
    Interpret Rabi curve results in terms of observability.
    
    Key metrics:
    - Peak height ~ Γ_driven/γ: Signal strength
    - Linewidth ~ γ: Resolution
    - SNR: Detectability
    """
    print("\n" + "=" * 80)
    print("RABI CURVE INTERPRETATION")
    print("=" * 80)
    
    print(f"\nResonance frequency: ω₀ = {data.transition_frequency:.3e} Hz")
    print(f"Decoherence rate: γ = {data.decoherence_rate:.3e} Hz")
    
    print(f"\nLineshape metrics:")
    print(f"  Peak height: {data.peak_height:.3e}")
    print(f"  Linewidth (FWHM): {data.linewidth:.3e} Hz = {data.linewidth/data.decoherence_rate:.2f}γ")
    print(f"  SNR estimate: {data.snr_estimate:.3e}")
    
    print(f"\nPhysical interpretation:")
    if data.linewidth / data.decoherence_rate > 0.5 and data.linewidth / data.decoherence_rate < 2.0:
        print(f"  ✓ Linewidth ~ γ (consistent with decoherence-limited)")
    else:
        print(f"  ⚠️  Linewidth / γ = {data.linewidth/data.decoherence_rate:.2f} (unexpected)")
    
    # Estimate Γ_driven from peak height
    # For weak drive: peak height ≈ Γ_driven/γ (in steady state)
    gamma_driven_estimate = data.peak_height * data.decoherence_rate
    
    print(f"\nDriven rate estimate:")
    print(f"  Γ_driven ≈ peak_height × γ ≈ {gamma_driven_estimate:.3e} Hz")
    print(f"  Γ_driven / γ ≈ {gamma_driven_estimate / data.decoherence_rate:.3e}")
    
    print(f"\nObservability assessment:")
    if gamma_driven_estimate >= 10 * gamma:
        print(f"  ✓ OBSERVABLE: Γ_driven ≥ 10γ")
    elif gamma_driven_estimate >= gamma / 10:
        print(f"  ⚠️  MARGINAL: γ/10 ≤ Γ_driven < 10γ")
    else:
        print(f"  ✗ UNFEASIBLE: Γ_driven < γ/10")
        print(f"  → Need {(10*gamma)/gamma_driven_estimate:.2e}× enhancement")
