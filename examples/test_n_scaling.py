#!/usr/bin/env python3
"""
researcher Theory Priority #1: N-Scaling Analysis

CRITICAL QUESTION: Does f_eff scale superlinearly with network size N?

If f_eff ∝ N²: Need N ~ 10⁶·⁵ ~ 3 million nodes → FEASIBLE!
If f_eff ∝ N³: Need N ~ 10⁴·³ ~ 20,000 nodes → VERY FEASIBLE!
If f_eff saturates: Path 1 (new physics) is dead → Pivot required

This is the single most important theoretical check.
"""

import numpy as np
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.constants import L_PLANCK
from src.core.spin_network import SpinNetwork

import importlib
matter_coupling_module = importlib.import_module('src.04_coupling_engineering.matter_coupling')

MatterFieldProperties = matter_coupling_module.MatterFieldProperties
MatterFieldType = matter_coupling_module.MatterFieldType
MatterGeometryCoupling = matter_coupling_module.MatterGeometryCoupling

print("=" * 80)
print("CRITICAL THEORY TEST: N-SCALING ANALYSIS")
print("=" * 80)
print("\nresearcher Question: Does coupling scale superlinearly with network size?")
print("\nScaling laws to test:")
print("  • f_eff ∝ N⁰ (saturation) → Dead end")
print("  • f_eff ∝ N¹ (linear) → Need N ~ 10¹³ → Impossible")
print("  • f_eff ∝ N² (quadratic) → Need N ~ 10⁶·⁵ → FEASIBLE!")
print("  • f_eff ∝ N³ (cubic) → Need N ~ 10⁴·³ → VERY FEASIBLE!")
print("\nThis determines if Path 1 (new physics) is viable.\n")

# Matter field
matter_field = MatterFieldProperties(
    field_type=MatterFieldType.SCALAR,
    characteristic_energy=1e-15,
    characteristic_length=L_PLANCK * 1e10,
    impedance=1.0
)

# Optimal parameters from breakthrough
lambda_val = 1.0  # NEW LIMIT!
mu = 0.1
dim = 32

def create_test_network(num_nodes, topology_type='random'):
    """
    Create test networks of varying sizes.
    
    topologies:
    - 'random': Random graph (Erdős-Rényi)
    - 'regular': Regular lattice
    - 'chain': Linear chain
    - 'complete': Fully connected
    """
    network = SpinNetwork()
    
    # Add nodes
    nodes = [network.add_node(i) for i in range(num_nodes)]
    
    if topology_type == 'chain':
        # Linear chain: N nodes, N-1 edges
        for i in range(num_nodes - 1):
            network.add_edge(i, i+1, 0.5)
    
    elif topology_type == 'regular':
        # Regular lattice (each node connects to nearest neighbors)
        edges_per_node = min(4, num_nodes - 1)  # 4-regular or complete
        added_edges = set()
        for i in range(num_nodes):
            for j in range(1, edges_per_node // 2 + 1):
                neighbor = (i + j) % num_nodes
                edge_key = tuple(sorted([i, neighbor]))
                if edge_key not in added_edges:
                    network.add_edge(i, neighbor, 0.5)
                    added_edges.add(edge_key)
    
    elif topology_type == 'complete':
        # Complete graph: N(N-1)/2 edges
        for i in range(num_nodes):
            for j in range(i+1, num_nodes):
                network.add_edge(i, j, 0.5)
    
    elif topology_type == 'random':
        # Random graph with probability p ~ log(N)/N for connectivity
        p = min(0.5, 4.0 / num_nodes if num_nodes > 4 else 0.8)
        for i in range(num_nodes):
            for j in range(i+1, num_nodes):
                if np.random.rand() < p:
                    network.add_edge(i, j, 0.5)
    
    return network

def compute_coupling_strength(network, lambda_val, mu, dim):
    """Compute effective coupling strength |⟨f|H_int|i⟩|."""
    try:
        coupling = MatterGeometryCoupling(network, matter_field, lambda_val, mu=mu)
        
        # Compute spectrum
        energies, eigenvectors = coupling.compute_energy_spectrum(dim)
        
        # Build interaction Hamiltonian
        H_int = coupling.build_interaction_hamiltonian(dim)
        
        # Coupling matrix element
        coupling_element = abs(eigenvectors[:, 1].conj() @ H_int @ eigenvectors[:, 0])
        
        return coupling_element
        
    except Exception as e:
        print(f"    Error: {e}")
        return 0.0

# Test network sizes
print("=" * 80)
print("TESTING MULTIPLE NETWORK SIZES")
print("=" * 80)

network_sizes = [4, 6, 8, 10, 12, 16, 20]  # Start small for speed
topology_type = 'regular'  # Regular lattice for consistency

print(f"\nTopology: {topology_type}")
print(f"Parameters: λ={lambda_val}, μ={mu}, dim={dim}")
print(f"Testing N = {network_sizes}\n")

results = []
start_time = time.time()

for N in network_sizes:
    print(f"\nN = {N:3d} nodes:", end=" ", flush=True)
    
    # Create network
    network = create_test_network(N, topology_type)
    num_edges = len(network.edges)
    
    print(f"{num_edges:3d} edges →", end=" ", flush=True)
    
    # Compute coupling
    t0 = time.time()
    coupling = compute_coupling_strength(network, lambda_val, mu, dim)
    dt = time.time() - t0
    
    print(f"coupling = {coupling:.4e} J ({dt:.2f}s)")
    
    results.append({
        'N': N,
        'edges': num_edges,
        'coupling': coupling,
        'time': dt
    })

elapsed = time.time() - start_time
print(f"\n✓ All tests complete in {elapsed:.1f} seconds")

# Analyze scaling
print("\n" + "=" * 80)
print("SCALING ANALYSIS")
print("=" * 80)

# Extract data
N_values = np.array([r['N'] for r in results])
coupling_values = np.array([r['coupling'] for r in results])

# Filter valid points
valid_idx = coupling_values > 0
N_valid = N_values[valid_idx]
coupling_valid = coupling_values[valid_idx]

if len(N_valid) < 3:
    print("\n✗ Insufficient valid data points for scaling analysis")
    sys.exit(1)

# Fit power laws: coupling ∝ N^α
log_N = np.log(N_valid)
log_coupling = np.log(coupling_valid)

# Linear fit in log-log space
coeffs = np.polyfit(log_N, log_coupling, 1)
alpha = coeffs[0]
log_A = coeffs[1]
A = np.exp(log_A)

print(f"\nPower law fit: coupling ∝ A × N^α")
print(f"  α (scaling exponent) = {alpha:.3f}")
print(f"  A (prefactor) = {A:.4e}")

# Compute R²
log_coupling_fit = alpha * log_N + log_A
ss_res = np.sum((log_coupling - log_coupling_fit)**2)
ss_tot = np.sum((log_coupling - np.mean(log_coupling))**2)
r_squared = 1 - ss_res / ss_tot

print(f"  R² (goodness of fit) = {r_squared:.4f}")

# Detailed table
print(f"\n{'N':>5s} {'Edges':>7s} {'Coupling':>15s} {'N^α Fit':>15s} {'Ratio':>10s}")
print("-" * 80)
for i, r in enumerate(results):
    if r['coupling'] > 0:
        fit = A * r['N']**alpha
        ratio = r['coupling'] / fit
        print(f"{r['N']:5d} {r['edges']:7d} {r['coupling']:15.4e} {fit:15.4e} {ratio:10.3f}")

# Interpretation
print("\n" + "=" * 80)
print("INTERPRETATION")
print("=" * 80)

print(f"\nScaling exponent α = {alpha:.3f}")

if alpha < 0.5:
    scaling_type = "SUB-LINEAR (saturation)"
    verdict = "❌ DEAD END"
    explanation = "Coupling saturates with network size. No macroscopic amplification."
elif alpha < 1.5:
    scaling_type = "LINEAR"
    verdict = "❌ INSUFFICIENT"
    explanation = "Need N ~ 10¹³ nodes for observability. Not feasible."
elif alpha < 2.5:
    scaling_type = "QUADRATIC (N²)"
    verdict = "✅ PROMISING!"
    explanation = "Need N ~ 10⁶·⁵ ~ 3 million nodes. Large but feasible!"
elif alpha < 3.5:
    scaling_type = "CUBIC (N³)"
    verdict = "✅ VERY PROMISING!"
    explanation = "Need N ~ 10⁴·³ ~ 20,000 nodes. Very feasible!"
else:
    scaling_type = "SUPER-CUBIC"
    verdict = "✅ EXCEPTIONAL!"
    explanation = "Even stronger than N³. Path to observability is clear!"

print(f"  Type: {scaling_type}")
print(f"  Verdict: {verdict}")
print(f"  {explanation}")

# Extrapolation
print("\n" + "=" * 80)
print("EXTRAPOLATION TO OBSERVABILITY")
print("=" * 80)

# Current best (N=20)
if results[-1]['coupling'] > 0:
    coupling_N20 = results[-1]['coupling']
    
    # Target coupling for SNR ~ 10
    # Current SNR ~ 10⁻¹³, need 10 → need 10¹³× enhancement
    target_enhancement = 1e13
    target_coupling = coupling_N20 * target_enhancement
    
    # Solve: A × N^α = target_coupling
    # N = (target_coupling / A)^(1/α)
    N_required = (target_coupling / A) ** (1/alpha)
    
    print(f"\nCurrent (N={results[-1]['N']}): coupling = {coupling_N20:.4e} J")
    print(f"Target: coupling = {target_coupling:.4e} J")
    print(f"Required enhancement: {target_enhancement:.2e}×")
    print(f"\n✓ Estimated N required: {N_required:.2e} nodes")
    
    if N_required < 1e5:
        feasibility = "✅ VERY FEASIBLE (laptop scale)"
    elif N_required < 1e7:
        feasibility = "✅ FEASIBLE (cluster scale)"
    elif N_required < 1e9:
        feasibility = "⚠ CHALLENGING (supercomputer scale)"
    else:
        feasibility = "❌ NOT FEASIBLE (beyond current compute)"
    
    print(f"  Feasibility: {feasibility}")

# Conclusion
print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)

if alpha >= 1.5:
    print(f"\n✅ SUPERLINEAR SCALING DETECTED (α = {alpha:.3f})")
    print(f"\n🎯 PATH 1 (NEW PHYSICS) IS VIABLE!")
    print(f"\nNext steps:")
    print(f"  1. Extend to larger N (100, 1000 nodes)")
    print(f"  2. Test different topologies (random, complete, etc.)")
    print(f"  3. Compute required N precisely")
    print(f"  4. Analyze physical mechanism (why N^{alpha:.1f}?)")
    print(f"  5. Build proof-of-concept large network")
else:
    print(f"\n❌ LINEAR OR SUB-LINEAR SCALING (α = {alpha:.3f})")
    print(f"\n→ Path 1 (new physics) NOT viable with this mechanism")
    print(f"\nRecommendation:")
    print(f"  • Try different topologies (may have different scaling)")
    print(f"  • Look for critical points (diverging susceptibility)")
    print(f"  • Or PIVOT to Path 2 (cosmology) or Path 3 (document)")

print("=" * 80)
