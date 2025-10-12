"""
Driven Lindblad evolution for matter-geometry coupling.

Implements realistic decoherence during driven transitions to estimate
observable rates and signal-to-noise ratios.
"""

import numpy as np
from typing import Tuple, List
from dataclasses import dataclass
import matplotlib.pyplot as plt

from ..core.constants import HBAR


@dataclass
class DrivenLindbladResult:
    """Results from driven Lindblad simulation."""
    times: np.ndarray
    populations: np.ndarray  # Shape (n_times, n_states)
    purity: np.ndarray
    driven_rate: float  # Effective transition rate with driving
    coherence_limited_rate: float  # Rate limited by decoherence


def lindblad_evolution(
    H_system: np.ndarray,
    H_drive: np.ndarray,
    initial_state: np.ndarray,
    gamma: float,
    drive_amplitude: float,
    times: np.ndarray
) -> DrivenLindbladResult:
    """
    Evolve density matrix under driven Lindblad equation.
    
    dρ/dt = -i[H_total, ρ]/ℏ + γ(L[ρ])
    
    where H_total = H_system + Ω(t) H_drive
    and L[ρ] is the Lindblad dissipator.
    
    Args:
        H_system: Time-independent Hamiltonian
        H_drive: Driving Hamiltonian (e.g., H_int)
        initial_state: Initial state vector (will be converted to density matrix)
        gamma: Decoherence rate
        drive_amplitude: Ω (drive strength)
        times: Time points for evolution
    
    Returns:
        DrivenLindbladResult with populations, purity, and rates
    """
    dim = H_system.shape[0]
    
    # Initialize density matrix
    if initial_state.ndim == 1:
        rho = np.outer(initial_state, initial_state.conj())
    else:
        rho = initial_state.copy()
    
    # Storage
    populations = np.zeros((len(times), dim))
    purity_trace = np.zeros(len(times))
    
    # Time evolution (simple Euler method for demo)
    dt = times[1] - times[0] if len(times) > 1 else 1.0
    
    for idx, t in enumerate(times):
        # Store observables
        populations[idx, :] = np.diag(rho).real
        purity_trace[idx] = np.trace(rho @ rho).real
        
        if idx < len(times) - 1:
            # Total Hamiltonian (constant drive for simplicity)
            H_total = H_system + drive_amplitude * H_drive
            
            # Unitary evolution: -i[H, ρ]/ℏ
            commutator = H_total @ rho - rho @ H_total
            drho_unitary = -1j * commutator / HBAR
            
            # Lindblad dissipator (dephasing model)
            # L[ρ] = -γ/2 {N, ρ} + γ N ρ N†
            # where N = number operator (diagonal)
            N = np.diag(np.arange(dim))
            drho_dephasing = -gamma * (N @ rho + rho @ N) / 2
            for i in range(dim):
                n_i = np.zeros((dim, dim))
                n_i[i, i] = 1.0
                drho_dephasing += gamma * n_i @ rho @ n_i
            
            # Total evolution
            drho = drho_unitary + drho_dephasing
            
            # Euler step
            rho = rho + drho * dt
            
            # Ensure Hermitian and normalized
            rho = (rho + rho.conj().T) / 2
            rho = rho / np.trace(rho)
    
    # Estimate driven transition rate
    # Rate from ground state population decay
    if populations[0, 0] > 0.5:
        # Find time when population drops to half
        half_pop = populations[0, 0] / 2
        crossing_idx = np.where(populations[:, 0] < half_pop)[0]
        if len(crossing_idx) > 0:
            t_half = times[crossing_idx[0]]
            driven_rate = 1.0 / t_half if t_half > 0 else 0.0
        else:
            driven_rate = 0.0
    else:
        driven_rate = 0.0
    
    # Coherence-limited rate (when purity < 0.5)
    purity_half_idx = np.where(purity_trace < 0.5)[0]
    if len(purity_half_idx) > 0:
        t_decohere = times[purity_half_idx[0]]
        coherence_limited_rate = 1.0 / t_decohere if t_decohere > 0 else 0.0
    else:
        coherence_limited_rate = 1.0 / times[-1] if len(times) > 0 else 0.0
    
    return DrivenLindbladResult(
        times=times,
        populations=populations,
        purity=purity_trace,
        driven_rate=driven_rate,
        coherence_limited_rate=coherence_limited_rate
    )


def plot_driven_evolution(
    result: DrivenLindbladResult,
    output_path: str = "outputs/driven_evolution.png"
):
    """Plot driven evolution results."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))
    
    # Plot state populations
    n_states = result.populations.shape[1]
    for i in range(min(n_states, 5)):  # Plot first 5 states
        ax1.plot(result.times, result.populations[:, i], 
                label=f"State {i}", linewidth=2)
    
    ax1.set_xlabel("Time (s)", fontsize=12)
    ax1.set_ylabel("Population", fontsize=12)
    ax1.set_title("State Populations During Driven Evolution", fontsize=14)
    ax1.legend(loc='best')
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim([0, 1])
    
    # Plot purity decay
    ax2.plot(result.times, result.purity, 'r-', linewidth=2, label='Purity')
    ax2.axhline(0.5, color='k', linestyle='--', alpha=0.5, label='50% threshold')
    
    ax2.set_xlabel("Time (s)", fontsize=12)
    ax2.set_ylabel("Purity Tr(ρ²)", fontsize=12)
    ax2.set_title("Purity Decay During Driven Evolution", fontsize=14)
    ax2.legend(loc='best')
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim([0, 1.1])
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Driven evolution plot saved to {output_path}")
    plt.close()


def estimate_observable_rate(
    H_system: np.ndarray,
    H_drive: np.ndarray,
    drive_amplitude: float,
    gamma: float,
    simulation_time: float = 1e-10
) -> Tuple[float, float, float]:
    """
    Estimate observable transition rate including decoherence.
    
    Returns:
        (driven_rate, coherence_limited_rate, SNR)
        where SNR = driven_rate / decoherence_rate
    """
    dim = H_system.shape[0]
    initial_state = np.zeros(dim)
    initial_state[0] = 1.0  # Start in ground state
    
    # Time grid
    n_points = 200
    times = np.linspace(0, simulation_time, n_points)
    
    # Evolve
    result = lindblad_evolution(
        H_system, H_drive, initial_state,
        gamma, drive_amplitude, times
    )
    
    # SNR: driven rate vs decoherence
    decoherence_rate = gamma
    SNR = result.driven_rate / decoherence_rate if decoherence_rate > 0 else 0.0
    
    return result.driven_rate, result.coherence_limited_rate, SNR
