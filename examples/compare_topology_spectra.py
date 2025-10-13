#!/usr/bin/env python3
"""
Compare energy spectra and state structure between octahedral and icosahedral topologies.
"""

import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.constants import L_PLANCK

import importlib
topology_module = importlib.import_module('src.06_topology_exploration')
matter_coupling_module = importlib.import_module('src.04_coupling_engineering.matter_coupling')

generate_topology = topology_module.generate_topology
MatterFieldProperties = matter_coupling_module.MatterFieldProperties
MatterFieldType = matter_coupling_module.MatterFieldType
MatterGeometryCoupling = matter_coupling_module.MatterGeometryCoupling

print("=" * 80)
print("DETAILED TOPOLOGY COMPARISON: ENERGY SPECTRA")
print("=" * 80)

# Generate topologies
network_oct, info_oct = generate_topology(topology_type='octahedral')
network_ico, info_ico = generate_topology(topology_type='icosahedral')

coord_oct = 2 * info_oct.num_edges / info_oct.num_nodes
coord_ico = 2 * info_ico.num_edges / info_ico.num_nodes

print(f"\nTopology info:")
print(f"  Octahedral: {info_oct.num_nodes} nodes, {info_oct.num_edges} edges, coord={coord_oct:.1f}")
print(f"  Icosahedral: {info_ico.num_nodes} nodes, {info_ico.num_edges} edges, coord={coord_ico:.1f}")

# Set up matter field
matter_field = MatterFieldProperties(
    field_type=MatterFieldType.SCALAR,
    characteristic_energy=1e-15,
    characteristic_length=L_PLANCK * 1e10,
    impedance=1.0
)

# Test parameters
lambda_val = 1e-4
mu = 0.5
dim = 32

print(f"\nTest parameters: λ={lambda_val:.0e}, μ={mu}, dim={dim}")

# Compute spectra
print("\nComputing energy spectra...")
coupling_oct = MatterGeometryCoupling(network_oct, matter_field, lambda_val, mu=mu)
energies_oct, eigvec_oct = coupling_oct.compute_energy_spectrum(dim)

coupling_ico = MatterGeometryCoupling(network_ico, matter_field, lambda_val, mu=mu)
energies_ico, eigvec_ico = coupling_ico.compute_energy_spectrum(dim)

print("\nEnergy spectrum comparison:")
print(f"  Octahedral ground state: {energies_oct[0]:.6e} J")
print(f"  Icosahedral ground state: {energies_ico[0]:.6e} J")
print(f"  Ratio (ico/oct): {energies_ico[0]/energies_oct[0]:.4f}")

print(f"\n  Octahedral first excited: {energies_oct[1]:.6e} J")
print(f"  Icosahedral first excited: {energies_ico[1]:.6e} J")
print(f"  Ratio (ico/oct): {energies_ico[1]/energies_oct[1]:.4f}")

gap_oct = energies_oct[1] - energies_oct[0]
gap_ico = energies_ico[1] - energies_ico[0]
print(f"\n  Octahedral gap: {gap_oct:.6e} J")
print(f"  Icosahedral gap: {gap_ico:.6e} J")
print(f"  Ratio (ico/oct): {gap_ico/gap_oct:.4f}")

# Compute coupling matrix elements
print("\nCoupling matrix elements:")
H_int_oct = coupling_oct.build_interaction_hamiltonian(dim)
H_int_ico = coupling_ico.build_interaction_hamiltonian(dim)

M_oct = abs(eigvec_oct[:, 1].conj() @ H_int_oct @ eigvec_oct[:, 0])
M_ico = abs(eigvec_ico[:, 1].conj() @ H_int_ico @ eigvec_ico[:, 0])

print(f"  Octahedral |⟨1|H_int|0⟩|: {M_oct:.6e} J")
print(f"  Icosahedral |⟨1|H_int|0⟩|: {M_ico:.6e} J")
print(f"  Enhancement: {M_ico/M_oct:.4f}×")

# Check interaction Hamiltonian norms
H_int_oct_norm = np.linalg.norm(H_int_oct, 'fro')
H_int_ico_norm = np.linalg.norm(H_int_ico, 'fro')

print(f"\nInteraction Hamiltonian Frobenius norms:")
print(f"  Octahedral ||H_int||_F: {H_int_oct_norm:.6e} J")
print(f"  Icosahedral ||H_int||_F: {H_int_ico_norm:.6e} J")
print(f"  Ratio (ico/oct): {H_int_ico_norm/H_int_oct_norm:.4f}")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)

if abs(M_ico/M_oct - 1.0) < 0.1:
    print("✓ Coordination number does NOT significantly affect coupling")
    print("  → Topology optimization requires different approach")
    print("  → 400× octahedral enhancement likely from spin structure, not coordination")
else:
    print(f"✓ Icosahedral provides {M_ico/M_oct:.2f}× enhancement")
    print("  → Higher coordination DOES improve coupling")

print("=" * 80)
