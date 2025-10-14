#!/usr/bin/env python3
"""
Week 1 Day 3: Topology Optimization Study

Compare scaling exponents across different network topologies:
- Complete graph (all-to-all)
- Cubic lattice (nearest-neighbor)  
- Ring (1D periodic)

Also test higher spin values (j > 1/2).
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple

from src.phase_d.tier1_collective.network_construction import (
    create_complete_network,
    create_lattice_network,
    create_ring_network
)
from src.phase_d.tier1_collective.collective_hamiltonian import (
    measure_collective_coupling_v2,
    extract_scaling_exponent
)
from src.core.spin_network import SpinNetwork, SpinNetworkEdge


def modify_edge_spins(network: SpinNetwork, spin_value: float) -> SpinNetwork:
    """
    Create new network with modified spin values.
    
    Args:
        network: Original network
        spin_value: New spin value for all edges
        
    Returns:
        New network with updated spins
    """
    new_network = SpinNetwork()
    
    # Add all nodes
    for node in network.nodes:
        new_network.add_node(node.node_id)
    
    # Add all edges with new spin value
    for edge in network.edges:
        new_network.add_edge(edge.node_i, edge.node_j, spin_value)
    
    return new_network


def test_topology(
    topology: str,
    N_values: List[int],
    dim: int = 16
) -> Tuple[float, float, Dict]:
    """
    Measure scaling exponent for a specific topology.
    
    Args:
        topology: "complete", "lattice", or "ring"
        N_values: List of N to test
        dim: Hilbert space dimension
        
    Returns:
        (alpha, g0, fit_info)
    """
    print(f"\n{'='*70}")
    print(f"Testing {topology.upper()} topology")
    print(f"{'='*70}")
    
    g_values = []
    edge_counts = []
    
    for N in N_values:
        print(f"N={N}...", end=" ", flush=True)
        
        # Create network
        if topology == "complete":
            network, edges = create_complete_network(N)
        elif topology == "lattice":
            network, edges = create_lattice_network(N)
        elif topology == "ring":
            network, edges = create_ring_network(N)
        else:
            raise ValueError(f"Unknown topology: {topology}")
        
        # Measure coupling
        g_coll, gap, enh = measure_collective_coupling_v2(network, dim=dim)
        
        g_values.append(g_coll)
        edge_counts.append(len(edges))
        
        print(f"edges={len(edges)}, g={g_coll:.3e} J, enh={enh:.2e}×")
    
    # Extract scaling
    alpha, g0, fit_info = extract_scaling_exponent(N_values, g_values)
    
    print(f"\nScaling: g(N) = {g0:.3e} × N^{alpha:.3f}")
    print(f"RMS residual: {fit_info['rms_residual']:.3f}")
    
    # Add edge count info to fit_info
    fit_info['edge_counts'] = edge_counts
    fit_info['topology'] = topology
    
    return alpha, g0, fit_info


def test_spin_scaling(
    topology: str,
    N: int,
    spin_values: List[float],
    dim: int = 16
) -> Dict:
    """
    Test how coupling scales with spin value.
    
    Args:
        topology: Network topology
        N: Network size
        spin_values: List of spin values to test
        dim: Hilbert space dimension
        
    Returns:
        Dictionary with results
    """
    print(f"\n{'='*70}")
    print(f"Testing SPIN SCALING for {topology} (N={N})")
    print(f"{'='*70}")
    
    results = {
        'spin_values': [],
        'g_values': [],
        'enh_values': []
    }
    
    # Create base network
    if topology == "complete":
        network, _ = create_complete_network(N)
    elif topology == "lattice":
        network, _ = create_lattice_network(N)
    elif topology == "ring":
        network, _ = create_ring_network(N)
    else:
        raise ValueError(f"Unknown topology: {topology}")
    
    for j in spin_values:
        print(f"j={j}...", end=" ", flush=True)
        
        # Modify spins
        net_j = modify_edge_spins(network, j)
        
        # Measure
        g_coll, gap, enh = measure_collective_coupling_v2(net_j, dim=dim)
        
        results['spin_values'].append(j)
        results['g_values'].append(g_coll)
        results['enh_values'].append(enh)
        
        print(f"g={g_coll:.3e} J, enh={enh:.2e}×")
    
    # Fit spin scaling: g(j) ∝ j^β
    log_j = np.log(results['spin_values'])
    log_g = np.log(results['g_values'])
    
    A = np.vstack([log_j, np.ones(len(log_j))]).T
    fit_result = np.linalg.lstsq(A, log_g, rcond=None)
    beta, log_g0 = fit_result[0]
    
    results['beta'] = beta
    results['g0_spin'] = np.exp(log_g0)
    
    print(f"\nSpin scaling: g(j) ∝ j^{beta:.3f}")
    
    return results


def plot_topology_comparison(results: Dict[str, Dict]):
    """
    Create comparison plot for all topologies.
    
    Args:
        results: Dictionary of {topology: fit_info}
    """
    plt.figure(figsize=(12, 5))
    
    # Plot 1: Scaling comparison
    plt.subplot(1, 2, 1)
    
    colors = {'complete': 'blue', 'lattice': 'green', 'ring': 'red'}
    markers = {'complete': 'o', 'lattice': 's', 'ring': '^'}
    
    for topology, info in results.items():
        N_vals = info['N_values']
        g_vals = info['g_values']
        alpha = info['alpha']
        
        plt.loglog(N_vals, g_vals, 
                  marker=markers.get(topology, 'o'),
                  color=colors.get(topology, 'black'),
                  label=f"{topology} (α={alpha:.2f})",
                  linewidth=2, markersize=8)
    
    plt.xlabel('Number of Nodes (N)', fontsize=12)
    plt.ylabel('Collective Coupling g_coll (J)', fontsize=12)
    plt.title('Topology Comparison: Scaling Exponents', fontsize=14, fontweight='bold')
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    
    # Plot 2: Enhancement vs N
    plt.subplot(1, 2, 2)
    
    for topology, info in results.items():
        N_vals = info['N_values']
        g_vals = info['g_values']
        g_single = 3.96e-121  # Baseline
        enh_vals = [g / g_single for g in g_vals]
        
        plt.semilogy(N_vals, enh_vals,
                    marker=markers.get(topology, 'o'),
                    color=colors.get(topology, 'black'),
                    label=topology,
                    linewidth=2, markersize=8)
    
    plt.xlabel('Number of Nodes (N)', fontsize=12)
    plt.ylabel('Enhancement Factor', fontsize=12)
    plt.title('Enhancement vs. Network Size', fontsize=14, fontweight='bold')
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('week1_day3_topology_comparison.png', dpi=150, bbox_inches='tight')
    print("\n✅ Plot saved: week1_day3_topology_comparison.png")


def main():
    """Run Day 3 topology optimization study."""
    
    print("="*70)
    print("WEEK 1 DAY 3: TOPOLOGY OPTIMIZATION")
    print("="*70)
    print("\nObjective: Compare scaling exponents across topologies")
    print("Expected: Complete (α~2) > Lattice (α~1) > Ring (α~0.5)")
    print("\nThis will take 5-10 minutes...\n")
    
    # Test parameters
    N_small = [4, 6, 8, 10, 15]  # Quick test
    dim = 16  # Reduced for speed
    
    # Test all topologies
    results = {}
    
    for topology in ['complete', 'lattice', 'ring']:
        alpha, g0, fit_info = test_topology(topology, N_small, dim=dim)
        results[topology] = fit_info
    
    # Summary comparison
    print("\n" + "="*70)
    print("TOPOLOGY COMPARISON SUMMARY")
    print("="*70)
    
    print("\n{:<15} {:<10} {:<15} {:<15}".format(
        "Topology", "α", "Prediction", "Match?"))
    print("-"*70)
    
    predictions = {
        'complete': (2.0, "Quadratic (N²)"),
        'lattice': (1.0, "Linear (N)"),
        'ring': (0.5, "Sqrt (√N)")
    }
    
    for topology in ['complete', 'lattice', 'ring']:
        alpha = results[topology]['alpha']
        pred_alpha, pred_name = predictions[topology]
        match = "✅" if abs(alpha - pred_alpha) < 0.5 else "❌"
        
        print(f"{topology:<15} {alpha:>6.3f}    {pred_name:<15} {match}")
    
    # Find best topology
    best_topology = max(results.keys(), key=lambda k: results[k]['alpha'])
    best_alpha = results[best_topology]['alpha']
    
    print("\n" + "="*70)
    print(f"BEST TOPOLOGY: {best_topology.upper()} (α = {best_alpha:.3f})")
    print("="*70)
    
    # Test spin scaling on best topology
    print("\n\nTesting higher spins on best topology...")
    spin_results = test_spin_scaling(
        topology=best_topology,
        N=10,
        spin_values=[0.5, 1.0, 1.5, 2.0],
        dim=dim
    )
    
    print("\n" + "="*70)
    print("SPIN SCALING RESULT")
    print("="*70)
    beta = spin_results['beta']
    print(f"g(j) ∝ j^{beta:.3f}")
    print(f"\nExpected: β ≈ 2 (from j(j+1) in volume operator)")
    print(f"Measured: β = {beta:.3f}")
    
    if abs(beta - 2.0) < 0.5:
        print("✅ Matches expectation!")
    else:
        print("⚠️  Deviates from expectation")
    
    # Create comparison plot
    print("\n\nGenerating comparison plots...")
    plot_topology_comparison(results)
    
    # Final recommendations
    print("\n" + "="*70)
    print("DAY 3 CONCLUSIONS")
    print("="*70)
    
    print(f"\n1. Best Topology: {best_topology} (α = {best_alpha:.2f})")
    print(f"2. Spin Scaling: g ∝ j^{beta:.2f}")
    print(f"3. Recommendation for Days 4-5:")
    
    if best_alpha >= 1.5:
        print(f"   ✅ Use {best_topology} topology for full N-scan")
        print(f"   ✅ Test higher spins (j = 1, 2) to boost coupling")
    else:
        print(f"   ⚠️  All topologies show weak scaling")
        print(f"   ⚠️  Consider alternative mechanisms")
    
    print("\n" + "="*70)
    print("✅ DAY 3 COMPLETE")
    print("="*70)
    print("\nNext: Days 4-5 - Full N-scanning study with optimized parameters")
    
    return results, spin_results


if __name__ == "__main__":
    results, spin_results = main()
