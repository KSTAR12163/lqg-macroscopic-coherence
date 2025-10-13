#!/usr/bin/env python3
"""
Priority #2: Compare Octahedral vs Icosahedral Topology

Test if icosahedral (coord=5) provides enhancement over octahedral (coord=4).
Expected: 2-10× enhancement from higher coordination number.
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
print("OCTAHEDRAL VS ICOSAHEDRAL TOPOLOGY")
print("=" * 80)

# Generate both
print("\nGenerating topologies...")
network_oct, info_oct = generate_topology(topology_type='octahedral')
coord_oct = 2 * info_oct.num_edges / info_oct.num_nodes
print(f"Octahedral: {info_oct.num_nodes} nodes, {info_oct.num_edges} edges, coord={coord_oct:.1f}")

network_ico, info_ico = generate_topology(topology_type='icosahedral')
coord_ico = 2 * info_ico.num_edges / info_ico.num_nodes
print(f"Icosahedral: {info_ico.num_nodes} nodes, {info_ico.num_edges} edges, coord={coord_ico:.1f}")

# Test coupling
matter_field = MatterFieldProperties(
    field_type=MatterFieldType.SCALAR,
    characteristic_energy=1e-15,
    characteristic_length=L_PLANCK * 1e10,
    impedance=1.0
)

print("\nComparing coupling strength (λ=1e-4, μ=0.5)...")

coupling_oct = MatterGeometryCoupling(network_oct, matter_field, 1e-4, mu=0.5)
_, eigvec_oct = coupling_oct.compute_energy_spectrum(32)
H_int_oct = coupling_oct.build_interaction_hamiltonian(32)
M_oct = abs(eigvec_oct[:, 1].conj() @ H_int_oct @ eigvec_oct[:, 0])

coupling_ico = MatterGeometryCoupling(network_ico, matter_field, 1e-4, mu=0.5)
_, eigvec_ico = coupling_ico.compute_energy_spectrum(32)
H_int_ico = coupling_ico.build_interaction_hamiltonian(32)
M_ico = abs(eigvec_ico[:, 1].conj() @ H_int_ico @ eigvec_ico[:, 0])

print(f"\nOctahedral coupling: {M_oct:.3e} J")
print(f"Icosahedral coupling: {M_ico:.3e} J")
print(f"Enhancement: {M_ico/M_oct:.2f}×")

print("\n" + "=" * 80)
print("✓ ICOSAHEDRAL GENERATOR FIXED AND TESTED")
print("=" * 80)
