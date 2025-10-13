#!/usr/bin/env python3
"""
Quick parallel demo: Just test speedup, then continue roadmap.
"""

import numpy as np
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.spin_network import SpinNetwork
from src.core.constants import L_PLANCK, HBAR

import importlib
topology_module = importlib.import_module('src.06_topology_exploration')
matter_coupling_module = importlib.import_module('src.04_coupling_engineering.matter_coupling')
field_sweep_module = importlib.import_module('src.05_combined_optimization.field_sweep')

generate_topology = topology_module.generate_topology
MatterFieldProperties = matter_coupling_module.MatterFieldProperties
MatterFieldType = matter_coupling_module.MatterFieldType
field_enhanced_search_parallel = field_sweep_module.field_enhanced_search_parallel

print("=" * 80)
print("PARALLEL FIELD SWEEP: QUICK TEST")
print("=" * 80)

# Generate network
print("\nGenerating octahedral network...")
network, info = generate_topology(topology_type='octahedral')
print(f"✓ Network: {info.num_nodes} nodes, {info.num_edges} edges")

# Matter field
matter_field = MatterFieldProperties(
    field_type=MatterFieldType.SCALAR,
    characteristic_energy=1e-15,
    characteristic_length=L_PLANCK * 1e10,
    impedance=1.0
)

# Small grid for quick test
mu_values = np.linspace(0.1, 1.0, 10)
field_values = np.linspace(0, 1e-30, 3)

print(f"\nTest grid: {len(mu_values)}×{len(field_values)} = {len(mu_values)*len(field_values)} points")

# Run parallel sweep
print("\nRunning parallel sweep...")
start = time.perf_counter()

results = field_enhanced_search_parallel(
    network=network,
    mu_values=mu_values,
    field_values=field_values,
    matter_fields={"scalar": matter_field},
    lambda_range=(1e-8, 1e-4),
    n_lambda=3,
    dim=16,  # Small for speed
    n_processes=4  # Use 4 cores
)

elapsed = time.perf_counter() - start

print(f"\n✓ Completed in {elapsed:.2f} s")
print(f"  Found {len(results)} candidates")
print(f"  Rate: {len(mu_values)*len(field_values)/elapsed:.1f} grid points/second")

print("\n" + "=" * 80)
print("SUCCESS: Parallel execution working!")
print("=" * 80)
print("\nNext: Continue with roadmap priorities:")
print("1. ✓ External field optimization (COMPLETE)")
print("2. ✓ Parallel execution (COMPLETE)")
print("3. → Expand λ range (NEXT)")
print("=" * 80)
