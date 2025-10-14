"""
Collective Hamiltonian for N-node spin networks.

This module constructs interaction Hamiltonians that explicitly
scale with network size N, unlike the base MatterGeometryCoupling
which was designed for single-edge analysis.

CRITICAL FIX: The base matter_coupling module builds H_int independent
of network size. For collective enhancement studies, we need:
    H_int = Σ_edges λ_edge O_geom^edge ⊗ O_matter^edge

This gives proper N-scaling for complete graphs:
    - N nodes → N(N-1)/2 edges
    - H ~ N² for complete graphs (if all edges couple)
    - H ~ N for lattices (fixed coordination)
"""

import numpy as np
from typing import Tuple
from dataclasses import dataclass

from ...core.constants import L_PLANCK, HBAR
from ...core.spin_network import SpinNetwork


@dataclass
class CollectiveHamiltonianResult:
    """Result of collective Hamiltonian construction."""
    H_geom: np.ndarray  # Geometry part
    H_matter: np.ndarray  # Matter part
    H_int: np.ndarray  # Interaction (sum over edges)
    H_total: np.ndarray  # Total
    num_edges: int
    coupling_per_edge: float


def build_collective_hamiltonian(
    network: SpinNetwork,
    dim: int,
    lambda_coupling: float = 1.0,
    matter_energy: float = 1e-15
) -> CollectiveHamiltonianResult:
    """
    Build Hamiltonian that explicitly sums over all network edges.
    
    Args:
        network: Spin network (nodes + edges)
        dim: Hilbert space dimension
        lambda_coupling: Coupling strength per edge (J)
        matter_energy: Matter field energy scale (J)
        
    Returns:
        CollectiveHamiltonianResult with all Hamiltonian components
        
    Physics:
        Each edge contributes an interaction term:
            H_int^(edge) = λ × V_edge × Φ_matter
            
        Total interaction:
            H_int = Σ_edges H_int^(edge)
            
        For complete graph (N nodes):
            - Number of edges = N(N-1)/2
            - Total coupling ∝ N² (if all edges add coherently)
            
        Expected scaling:
            - Complete: g_eff ∝ N² (all-to-all)
            - Lattice: g_eff ∝ N (nearest-neighbor)
            - Ring: g_eff ∝ N (1D chain)
    """
    # Geometry operator (volume fluctuations)
    # Each edge contributes a volume quantum ~ L_P^3 × j(j+1)
    H_geom = np.zeros((dim, dim))
    
    avg_spin = np.mean([e.spin for e in network.edges]) if network.edges else 0.5
    vol_per_edge = L_PLANCK**3 * avg_spin * (avg_spin + 1)
    
    # Diagonal: total volume = sum over edges
    total_volume = vol_per_edge * len(network.edges)
    for i in range(dim):
        H_geom[i, i] = total_volume * (1 + 0.1 * i / dim)
    
    # Off-diagonal: volume fluctuations
    fluctuation = 0.1 * total_volume
    for i in range(dim - 1):
        H_geom[i, i+1] = fluctuation
        H_geom[i+1, i] = fluctuation
    
    # Matter operator (field oscillator)
    H_matter = np.zeros((dim, dim))
    for i in range(dim):
        H_matter[i, i] = matter_energy * (i + 0.5)
    
    # Interaction: each edge contributes
    # H_int = λ × (geometry operator) × (matter operator)
    #       = λ × N_edges × (volume per edge) × (matter coupling)
    H_int = np.zeros((dim, dim))
    
    for edge_idx, edge in enumerate(network.edges):
        # Volume contribution from this edge
        vol_edge = L_PLANCK**3 * edge.spin * (edge.spin + 1)
        
        # Coupling term (simplified: O_geom ⊗ O_matter → diagonal × off-diagonal)
        for i in range(dim):
            for j in range(dim):
                if i == j:
                    # Diagonal: energy shift
                    H_int[i, j] += lambda_coupling * vol_edge * matter_energy
                elif abs(i - j) == 1:
                    # Off-diagonal: transitions
                    H_int[i, j] += lambda_coupling * vol_edge * matter_energy * 0.5
    
    # Total Hamiltonian
    H_total = H_geom + H_matter + H_int
    
    return CollectiveHamiltonianResult(
        H_geom=H_geom,
        H_matter=H_matter,
        H_int=H_int,
        H_total=H_total,
        num_edges=len(network.edges),
        coupling_per_edge=lambda_coupling
    )


def measure_collective_coupling_v2(
    network: SpinNetwork,
    dim: int = 32,
    lambda_coupling: float = 1.0,
    matter_energy: float = 1e-15
) -> Tuple[float, float, float]:
    """
    Measure effective coupling with proper edge summation.
    
    Args:
        network: Spin network
        dim: Hilbert space dimension
        lambda_coupling: Coupling per edge (J)
        matter_energy: Matter field energy (J)
        
    Returns:
        (g_coll, gap, enhancement)
        
    Usage:
        network, _ = create_complete_network(N)
        g_coll, gap, enh = measure_collective_coupling_v2(network)
        print(f"N={N}: g_coll = {g_coll:.3e} J, enhancement = {enh:.2f}×")
    """
    # Build collective Hamiltonian
    result = build_collective_hamiltonian(network, dim, lambda_coupling, matter_energy)
    
    # Compute spectrum
    eigvals, eigvecs = np.linalg.eigh(result.H_total)
    
    # Ground and first excited state
    E0 = eigvals[0]
    E1 = eigvals[1]
    gap = abs(E1 - E0)
    
    psi0 = eigvecs[:, 0]
    psi1 = eigvecs[:, 1]
    
    # Coupling strength: g = |⟨1|H_int|0⟩|
    g_coll = abs(np.dot(np.conj(psi1), result.H_int @ psi0))
    
    # Baseline: single edge coupling
    g_single = lambda_coupling * (L_PLANCK**3 * 0.5 * 1.5) * matter_energy
    
    # Enhancement factor
    enhancement = g_coll / g_single if g_single > 0 else 0.0
    
    return g_coll, gap, enhancement


def extract_scaling_exponent(
    N_values: list,
    g_values: list
) -> Tuple[float, float, dict]:
    """
    Extract scaling exponent α from g(N) measurements.
    
    Fits: log(g) = log(g0) + α log(N)
    
    Args:
        N_values: List of N values
        g_values: Corresponding g_eff measurements
        
    Returns:
        (α, g0, fit_info)
        
    Interpretation:
        α ~ 0.5: √N scaling (weak collective)
        α ~ 1.0: Linear scaling (moderate)
        α ~ 2.0: Quadratic scaling (strong collective, complete graph)
        α > 2.0: Super-quadratic (unrealistic, likely numerical artifact)
    """
    # Remove any zero or negative values
    valid = [(N, g) for N, g in zip(N_values, g_values) if g > 0]
    if not valid:
        return 0.0, 0.0, {"error": "No valid data points"}
    
    N_valid, g_valid = zip(*valid)
    
    # Log-log fit
    log_N = np.log(N_valid)
    log_g = np.log(g_valid)
    
    # Linear regression: log_g = α log_N + log_g0
    A = np.vstack([log_N, np.ones(len(log_N))]).T
    result = np.linalg.lstsq(A, log_g, rcond=None)
    alpha, log_g0 = result[0]
    g0 = np.exp(log_g0)
    
    # Residuals
    log_g_fit = alpha * log_N + log_g0
    residuals = log_g - log_g_fit
    rms_residual = np.sqrt(np.mean(residuals**2))
    
    fit_info = {
        "alpha": alpha,
        "g0": g0,
        "rms_residual": rms_residual,
        "N_values": list(N_valid),
        "g_values": list(g_valid),
        "predictions": {
            "sqrt_N": 0.5,
            "linear": 1.0,
            "quadratic": 2.0
        },
        "closest_prediction": "sqrt_N" if abs(alpha - 0.5) < 0.3 
                            else ("linear" if abs(alpha - 1.0) < 0.3 
                            else ("quadratic" if abs(alpha - 2.0) < 0.5 
                            else "other"))
    }
    
    return alpha, g0, fit_info


if __name__ == "__main__":
    """Quick test of collective Hamiltonian."""
    from network_construction import create_complete_network
    
    print("Testing collective Hamiltonian construction...")
    print("=" * 60)
    
    # Test N=4 and N=10
    for N in [4, 10]:
        network, edges = create_complete_network(N)
        g_coll, gap, enh = measure_collective_coupling_v2(network, dim=16)
        
        print(f"\nN={N}:")
        print(f"  Edges: {len(edges)}")
        print(f"  g_coll = {g_coll:.6e} J")
        print(f"  Gap = {gap:.6e} J")
        print(f"  Enhancement = {enh:.2e}×")
    
    print("\n" + "=" * 60)
    print("✅ Collective Hamiltonian test complete")
