#!/usr/bin/env python3
"""
Alternative N-Scaling Test: Network-Dependent Quantities

The previous test showed coupling is constant because the matter field
Hamiltonian doesn't depend on network topology directly.

Test network-dependent quantities instead:
1. Total interaction strength (sum over all matrix elements)
2. Participation ratio (how many states couple)
3. Collective coupling (coherent sum effects)
4. Susceptibility to external perturbations
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
print("ALTERNATIVE N-SCALING: NETWORK-DEPENDENT QUANTITIES")
print("=" * 80)

# Matter field
matter_field = MatterFieldProperties(
    field_type=MatterFieldType.SCALAR,
    characteristic_energy=1e-15,
    characteristic_length=L_PLANCK * 1e10,
    impedance=1.0
)

lambda_val = 1.0
mu = 0.1
dim = 32

def create_regular_network(num_nodes):
    """Create regular lattice network."""
    network = SpinNetwork()
    nodes = [network.add_node(i) for i in range(num_nodes)]
    
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

def analyze_network_coupling(network, lambda_val, mu, dim):
    """Compute network-dependent coupling quantities."""
    try:
        coupling = MatterGeometryCoupling(network, matter_field, lambda_val, mu=mu)
        
        # Compute spectrum
        energies, eigenvectors = coupling.compute_energy_spectrum(dim)
        
        # Build Hamiltonians
        H_int = coupling.build_interaction_hamiltonian(dim)
        H_full = coupling.build_full_hamiltonian(dim)
        
        # 1. Single transition coupling (as before)
        single_coupling = abs(eigenvectors[:, 1].conj() @ H_int @ eigenvectors[:, 0])
        
        # 2. Total interaction strength (Frobenius norm)
        total_strength = np.linalg.norm(H_int, 'fro')
        
        # 3. Number of non-zero matrix elements
        threshold = 1e-130
        nonzero_elements = np.sum(np.abs(H_int) > threshold)
        
        # 4. Participation ratio (how many states significantly coupled)
        # Compute all transition strengths
        all_transitions = []
        for i in range(min(10, dim)):
            for j in range(i+1, min(10, dim)):
                trans = abs(eigenvectors[:, j].conj() @ H_int @ eigenvectors[:, i])
                if trans > 0:
                    all_transitions.append(trans)
        
        if len(all_transitions) > 0:
            # Participation ratio: (sum M_ij)² / sum(M_ij²)
            sum_M = np.sum(all_transitions)
            sum_M2 = np.sum(np.array(all_transitions)**2)
            participation = sum_M**2 / sum_M2 if sum_M2 > 0 else 0
        else:
            participation = 0
        
        # 5. Collective enhancement factor
        # If coupling adds coherently: expect ~ sqrt(N) enhancement
        # If incoherent: expect ~ 1
        num_nodes = len(network.nodes)
        collective_factor = single_coupling * np.sqrt(num_nodes)
        
        return {
            'single_coupling': single_coupling,
            'total_strength': total_strength,
            'nonzero_elements': nonzero_elements,
            'participation': participation,
            'collective_factor': collective_factor,
        }
        
    except Exception as e:
        return None

# Test network sizes
network_sizes = [4, 6, 8, 10, 12, 16, 20, 24, 30]

print(f"\nParameters: λ={lambda_val}, μ={mu}, dim={dim}")
print(f"Testing N = {network_sizes}\n")

results = []

for N in network_sizes:
    print(f"N = {N:3d}:", end=" ", flush=True)
    
    network = create_regular_network(N)
    num_edges = len(network.edges)
    
    analysis = analyze_network_coupling(network, lambda_val, mu, dim)
    
    if analysis:
        print(f"single={analysis['single_coupling']:.2e}, " +
              f"total={analysis['total_strength']:.2e}, " +
              f"nonzero={analysis['nonzero_elements']}, " +
              f"part={analysis['participation']:.1f}")
        
        results.append({
            'N': N,
            'edges': num_edges,
            **analysis
        })
    else:
        print("ERROR")

# Analyze scaling
print("\n" + "=" * 80)
print("SCALING ANALYSIS")
print("=" * 80)

if len(results) < 3:
    print("\nInsufficient data")
    sys.exit(1)

N_values = np.array([r['N'] for r in results])

# Test different quantities
quantities = {
    'Single coupling': 'single_coupling',
    'Total strength': 'total_strength',
    'Nonzero elements': 'nonzero_elements',
    'Participation': 'participation',
    'Collective factor': 'collective_factor',
}

print("\nScaling exponents (coupling ∝ N^α):\n")
print(f"{'Quantity':<20s} {'α':>8s} {'R²':>8s} {'Interpretation':>20s}")
print("-" * 80)

best_alpha = -999
best_quantity = None

for name, key in quantities.items():
    values = np.array([r[key] for r in results])
    
    if np.all(values > 0):
        log_N = np.log(N_values)
        log_values = np.log(values)
        
        coeffs = np.polyfit(log_N, log_values, 1)
        alpha = coeffs[0]
        
        # R²
        log_fit = np.polyval(coeffs, log_N)
        ss_res = np.sum((log_values - log_fit)**2)
        ss_tot = np.sum((log_values - np.mean(log_values))**2)
        r_squared = 1 - ss_res / ss_tot
        
        # Interpretation
        if alpha < 0.5:
            interp = "Saturation"
        elif alpha < 1.5:
            interp = "Linear (N)"
        elif alpha < 2.5:
            interp = "Quadratic (N²)"
        else:
            interp = f"N^{alpha:.1f}"
        
        print(f"{name:<20s} {alpha:8.3f} {r_squared:8.4f} {interp:>20s}")
        
        if alpha > best_alpha:
            best_alpha = alpha
            best_quantity = name
    else:
        print(f"{name:<20s} {'N/A':>8s} {'N/A':>8s} {'(contains zeros)':>20s}")

# Conclusion
print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)

print(f"\nBest scaling: {best_quantity} with α = {best_alpha:.3f}")

if best_alpha >= 2.0:
    print(f"\n✅ SUPERLINEAR SCALING FOUND!")
    print(f"   {best_quantity} scales as N^{best_alpha:.1f}")
    print(f"\n🎯 This could provide macroscopic enhancement")
    print(f"\nNext: Identify physical mechanism behind this scaling")
elif best_alpha >= 1.0:
    print(f"\n⚠ LINEAR SCALING")
    print(f"   {best_quantity} scales as N^{best_alpha:.1f}")
    print(f"\n→ Not sufficient for observability")
    print(f"   Need N ~ 10¹³ nodes (not feasible)")
else:
    print(f"\n❌ SATURATION (α < 1)")
    print(f"   No network-size enhancement")
    print(f"\n→ Path 1 (macroscopic coherence) NOT viable")
    print(f"→ PIVOT to Path 2 (cosmology) or Path 3 (document)")

print("\n" + "=" * 80)
