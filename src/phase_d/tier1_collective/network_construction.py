"""
Phase D - Tier 1: Network Construction for N-Scaling Study

Implements various network topologies for collective coupling measurements.
"""

import numpy as np
import sys
from pathlib import Path
from typing import Tuple, List
from dataclasses import dataclass
import itertools
import importlib

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.core.spin_network import SpinNetwork
from src.core.constants import L_PLANCK, HBAR
from src.numerical_guardrails import validate_coupling, G_EFF_THRESHOLD

# Import matter coupling module dynamically
matter_coupling_module = importlib.import_module('src.04_coupling_engineering.matter_coupling')
MatterFieldProperties = matter_coupling_module.MatterFieldProperties
MatterFieldType = matter_coupling_module.MatterFieldType
MatterGeometryCoupling = matter_coupling_module.MatterGeometryCoupling


@dataclass
class CollectiveResult:
    """Results from N-body collective coupling measurement."""
    N: int
    g_single: float  # J
    g_coll: float  # J
    enhancement: float
    topology: str
    Delta: float  # Energy gap (J)
    omega_gap: float  # Gap frequency (rad/s)


# ============================================================================
# NETWORK CONSTRUCTORS
# ============================================================================

def create_complete_network(N: int) -> Tuple[SpinNetwork, List[Tuple[int, int]]]:
    """
    Create complete graph K_N (all-to-all connectivity).
    
    Args:
        N: Number of nodes
        
    Returns:
        (network, edge_list) tuple
        
    Properties:
        - N nodes
        - N(N-1)/2 edges (every pair connected)
        - Uniform spin j=0.5 on all edges
    """
    network = SpinNetwork()
    
    # Add nodes
    nodes = [network.add_node(i) for i in range(N)]
    
    # Add all edges (complete graph)
    edges = list(itertools.combinations(range(N), 2))
    
    for i, j in edges:
        network.add_edge(i, j, spin=0.5)
    
    print(f"  Created complete network: {N} nodes, {len(edges)} edges")
    
    return network, edges


def create_lattice_network(N: int) -> Tuple[SpinNetwork, List[Tuple[int, int]]]:
    """
    Create cubic lattice network.
    
    Args:
        N: Number of nodes (will use closest L³ where L³ ≥ N)
        
    Returns:
        (network, edge_list) tuple
        
    Properties:
        - L×L×L cubic lattice
        - Nearest-neighbor connectivity only
        - 3L² - 3L + 1 edges for L³ nodes
    """
    # Find L such that L³ ≥ N
    L = int(np.ceil(N**(1/3)))
    actual_N = L**3
    
    network = SpinNetwork()
    
    # Add nodes (3D grid)
    node_map = {}
    node_idx = 0
    for x in range(L):
        for y in range(L):
            for z in range(L):
                node_map[(x, y, z)] = network.add_node(node_idx)
                node_idx += 1
    
    # Add nearest-neighbor edges
    edges = []
    for x in range(L):
        for y in range(L):
            for z in range(L):
                # Connect to neighbors in +x, +y, +z directions
                for dx, dy, dz in [(1, 0, 0), (0, 1, 0), (0, 0, 1)]:
                    nx, ny, nz = x + dx, y + dy, z + dz
                    if nx < L and ny < L and nz < L:
                        i = node_map[(x, y, z)]
                        j = node_map[(nx, ny, nz)]
                        network.add_edge(i, j, spin=0.5)
                        edges.append((i, j))
    
    print(f"  Created lattice network: {actual_N} nodes ({L}³), {len(edges)} edges")
    
    return network, edges


def create_ring_network(N: int) -> Tuple[SpinNetwork, List[Tuple[int, int]]]:
    """
    Create ring network (1D periodic boundary).
    
    Args:
        N: Number of nodes
        
    Returns:
        (network, edge_list) tuple
    """
    network = SpinNetwork()
    
    # Add nodes
    nodes = [network.add_node(i) for i in range(N)]
    
    # Add edges (ring topology)
    edges = []
    for i in range(N):
        j = (i + 1) % N
        network.add_edge(i, j, spin=0.5)
        edges.append((i, j))
    
    print(f"  Created ring network: {N} nodes, {N} edges")
    
    return network, edges


# ============================================================================
# COUPLING MEASUREMENT
# ============================================================================

def measure_collective_coupling(N: int,
                                topology: str = "complete",
                                lambda_val: float = 1.0,
                                mu: float = 0.1,
                                dim: int = 32) -> CollectiveResult:
    """
    Measure effective coupling for N-node spin network.
    
    Args:
        N: Number of nodes
        topology: "complete", "lattice", or "ring"
        lambda_val: Polymer scale parameter
        mu: Matter field scale
        dim: Hilbert space dimension for spectrum calculation
        
    Returns:
        CollectiveResult with measured coupling
    """
    print(f"\nMeasuring collective coupling for N={N} ({topology})...")
    
    # Create network
    if topology == "complete":
        network, edges = create_complete_network(N)
    elif topology == "lattice":
        network, edges = create_lattice_network(N)
    elif topology == "ring":
        network, edges = create_ring_network(N)
    else:
        raise ValueError(f"Unknown topology: {topology}")
    
    # Matter field (same as Phase B)
    matter_field = MatterFieldProperties(
        field_type=MatterFieldType.SCALAR,
        characteristic_energy=1e-15,  # Joules
        characteristic_length=L_PLANCK * 1e10,
        impedance=1.0
    )
    
    # Create coupling
    coupling = MatterGeometryCoupling(network, matter_field, lambda_val, mu=mu)
    
    # Compute energy spectrum
    print(f"  Computing spectrum (dim={dim})...")
    energies, eigvec = coupling.compute_energy_spectrum(dim)
    
    # Extract gap
    E0 = energies[0]
    E1 = energies[1]
    Delta = abs(E1 - E0)
    omega_gap = Delta / HBAR
    
    print(f"  Gap Δ = {Delta:.6e} J")
    print(f"  Gap frequency = {omega_gap:.6e} rad/s")
    
    # Compute coupling strength (matrix element)
    # g = |⟨1|H_int|0⟩|
    H_int = coupling.build_interaction_hamiltonian(dim)
    psi0 = eigvec[:, 0]
    psi1 = eigvec[:, 1]
    g_coll = abs(np.dot(np.conj(psi1), H_int @ psi0))
    
    print(f"  Collective coupling g_coll = {g_coll:.6e} J")
    
    # Baseline single-node coupling (from Phase B-C)
    g_single = 3.96e-121  # J
    enhancement = g_coll / g_single if g_single > 0 else 0.0
    
    print(f"  Enhancement = {enhancement:.2e}×")
    
    # Validate with guardrails (expect warning)
    result = validate_coupling(g_coll, name=f"g_coll(N={N})")
    if not result.is_valid:
        print(f"  ⚠️  {result.message}")
        print(f"  (Expected - measuring scaling law, not reaching viability)")
    
    return CollectiveResult(
        N=N,
        g_single=g_single,
        g_coll=g_coll,
        enhancement=enhancement,
        topology=topology,
        Delta=Delta,
        omega_gap=omega_gap
    )


# ============================================================================
# SCALING STUDY
# ============================================================================

def run_scaling_study(N_values: List[int],
                     topology: str = "complete",
                     lambda_val: float = 1.0,
                     mu: float = 0.1) -> dict:
    """
    Run complete N-scaling study.
    
    Args:
        N_values: List of N to measure
        topology: Network topology
        lambda_val: Polymer parameter
        mu: Matter field scale
        
    Returns:
        Dictionary with:
            - N_values: List of N
            - g_eff_values: List of measured couplings
            - enhancement_values: List of enhancements
            - scaling_exponent: Fitted α from g ∝ N^α
            - results: List of CollectiveResult objects
    """
    print("=" * 70)
    print(f"N-SCALING STUDY: {topology.upper()} TOPOLOGY")
    print("=" * 70)
    
    results = []
    g_eff_values = []
    enhancement_values = []
    
    for N in N_values:
        result = measure_collective_coupling(N, topology, lambda_val, mu)
        results.append(result)
        g_eff_values.append(result.g_coll)
        enhancement_values.append(result.enhancement)
    
    # Fit scaling law: log(g) = log(A) + α*log(N)
    log_N = np.log(N_values)
    log_g = np.log(g_eff_values)
    
    # Linear fit
    coeffs = np.polyfit(log_N, log_g, 1)
    alpha = coeffs[0]
    log_A = coeffs[1]
    A = np.exp(log_A)
    
    print("\n" + "=" * 70)
    print("SCALING ANALYSIS")
    print("=" * 70)
    print(f"\nFitted scaling: g_eff = A × N^α")
    print(f"  α = {alpha:.3f}")
    print(f"  A = {A:.6e} J")
    
    # Compare to predictions
    print(f"\nComparison to predictions:")
    print(f"  α = 0.5 (√N, incoherent):   {'✓' if abs(alpha - 0.5) < 0.2 else '✗'}")
    print(f"  α = 1.0 (N, coherent):      {'✓' if abs(alpha - 1.0) < 0.2 else '✗'}")
    print(f"  α = 2.0 (N², superradiant): {'✓' if abs(alpha - 2.0) < 0.3 else '✗'}")
    
    # Extrapolation
    g_target = 1e-50  # J (warp viability)
    if alpha > 0:
        N_required = (g_target / A)**(1/alpha)
        print(f"\nExtrapolation to g₀ = 1e-50 J:")
        print(f"  Required N = {N_required:.2e}")
        
        if N_required > 1e80:
            assessment = "IMPOSSIBLE (exceeds atoms in universe)"
        elif N_required > 1e40:
            assessment = "INFEASIBLE (unphysical)"
        elif N_required > 1e23:
            assessment = "EXTREMELY CHALLENGING (exceeds Avogadro's number)"
        else:
            assessment = "CONCEIVABLE (within macroscopic matter)"
        print(f"  Assessment: {assessment}")
    
    return {
        'N_values': N_values,
        'g_eff_values': g_eff_values,
        'enhancement_values': enhancement_values,
        'scaling_exponent': alpha,
        'A': A,
        'results': results
    }


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    # Quick test
    print("Testing network construction...")
    
    # Test small N
    result = measure_collective_coupling(4, topology="complete")
    print(f"\n✅ Test passed: N=4 measured successfully")
    print(f"   g_coll = {result.g_coll:.2e} J")
    print(f"   Enhancement = {result.enhancement:.2f}×")
