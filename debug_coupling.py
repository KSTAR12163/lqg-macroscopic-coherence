#!/usr/bin/env python3
"""Debug: Why is coupling independent of N?"""

from src.phase_d.tier1_collective.network_construction import create_complete_network
from src.core.constants import HBAR, L_PLANCK
import importlib
import numpy as np

# Create networks of different sizes
print("Creating networks...")
net4, edges4 = create_complete_network(4)
net10, edges10 = create_complete_network(10)

print(f"N=4: {len(net4.nodes)} nodes, {len(edges4)} edges")
print(f"N=10: {len(net10.nodes)} nodes, {len(edges10)} edges")

# Import coupling module
print("\nImporting coupling module...")
matter_module = importlib.import_module('src.04_coupling_engineering.matter_coupling')
MatterGeometryCoupling = matter_module.MatterGeometryCoupling
MatterFieldProperties = matter_module.MatterFieldProperties
MatterFieldType = matter_module.MatterFieldType

# Create matter field properties
matter = MatterFieldProperties(
    field_type=MatterFieldType.SCALAR,
    characteristic_energy=1e-15,  # J
    characteristic_length=L_PLANCK * 1e10,
    impedance=377.0  # vacuum impedance
)

# Create coupling objects
print("\nCreating coupling objects...")
coupling4 = MatterGeometryCoupling(net4, matter, 1.0, mu=1.0)
coupling10 = MatterGeometryCoupling(net10, matter, 1.0, mu=1.0)

# Check if coupling depends on network
print("\nChecking coupling attributes...")
print(f"coupling4.network: {coupling4.network}")
print(f"coupling10.network: {coupling10.network}")
print(f"coupling4.network.nodes: {len(coupling4.network.nodes)}")
print(f"coupling10.network.nodes: {len(coupling10.network.nodes)}")

# Build Hamiltonians
dim = 8  # Small for fast testing
print(f"\nBuilding Hamiltonians (dim={dim})...")
H4 = coupling4.build_interaction_hamiltonian(dim)
H10 = coupling10.build_interaction_hamiltonian(dim)

print(f"H4 shape: {H4.shape}")
print(f"H10 shape: {H10.shape}")
print(f"H4 norm: {np.linalg.norm(H4):.6e}")
print(f"H10 norm: {np.linalg.norm(H10):.6e}")

# Check if Hamiltonians are different
if np.allclose(H4, H10):
    print("\n❌ PROBLEM: H4 and H10 are identical!")
    print("   The Hamiltonian doesn't depend on network size.")
    print("   Need to fix: MatterGeometryCoupling should scale with N.")
else:
    print("\n✅ H4 and H10 are different.")
    ratio = np.linalg.norm(H10) / np.linalg.norm(H4)
    print(f"   Norm ratio: {ratio:.3f}")

# Compute spectrum
print("\nComputing spectra...")
eig4 = np.linalg.eigvalsh(H4)
eig10 = np.linalg.eigvalsh(H10)

print(f"E0(N=4) = {eig4[0]:.6e} J")
print(f"E0(N=10) = {eig10[0]:.6e} J")
print(f"E1(N=4) = {eig4[1]:.6e} J")
print(f"E1(N=10) = {eig10[1]:.6e} J")

if np.isclose(eig4[0], eig10[0]) and np.isclose(eig4[1], eig10[1]):
    print("\n❌ CONFIRMED: Energy levels are identical.")
    print("   This means MatterGeometryCoupling ignores the network structure.")
    print("\n🔧 SOLUTION NEEDED:")
    print("   We need to manually scale the Hamiltonian by N or use")
    print("   a different construction that sums over all edges.")
else:
    print("\n✅ Energy levels scale with N.")
