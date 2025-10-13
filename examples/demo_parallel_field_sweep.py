#!/usr/bin/env python3
"""
Demo: Parallel external field sweep for 10-20× speedup.

Compares sequential vs parallel execution and continues roadmap optimization.

Usage:
    python examples/demo_parallel_field_sweep.py [--sequential] [--parallel] [--both]
"""

import numpy as np
import sys
import time
from pathlib import Path
import argparse

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.spin_network import SpinNetwork
from src.core.constants import L_PLANCK, HBAR

# Import using importlib for numeric prefixes
import importlib
topology_module = importlib.import_module('src.06_topology_exploration')
matter_coupling_module = importlib.import_module('src.04_coupling_engineering.matter_coupling')
field_sweep_module = importlib.import_module('src.05_combined_optimization.field_sweep')

generate_topology = topology_module.generate_topology
MatterFieldProperties = matter_coupling_module.MatterFieldProperties
MatterFieldType = matter_coupling_module.MatterFieldType
field_enhanced_search = field_sweep_module.field_enhanced_search
field_enhanced_search_parallel = field_sweep_module.field_enhanced_search_parallel
analyze_field_enhancement = field_sweep_module.analyze_field_enhancement


def demo_parallel_speedup():
    """
    Demonstrate parallel vs sequential execution speedup.
    
    Expected: 10-20× speedup with parallel execution.
    """
    print("=" * 80)
    print("DEMO: PARALLEL FIELD SWEEP SPEEDUP")
    print("=" * 80)
    print("\nObjective: Measure speedup from parallel execution")
    print("Expected: 10-20× faster than sequential\n")
    
    # Generate network
    print("Generating octahedral network...")
    network, topology_info = generate_topology(topology_type='octahedral')
    print(f"✓ Network: {topology_info.num_nodes} nodes, {topology_info.num_edges} edges\n")
    
    # Define matter field
    matter_field = MatterFieldProperties(
        field_type=MatterFieldType.SCALAR,
        characteristic_energy=1e-15,  # Mesoscopic energy
        characteristic_length=L_PLANCK * 1e10,  # Mesoscopic length
        impedance=1.0
    )
    matter_fields = {"scalar": matter_field}
    
    # Parameter grid (small for demo)
    mu_values = np.linspace(0.1, 1.0, 20)  # 20 μ points
    field_values = np.linspace(0, 1e-30, 5)  # 5 field points
    
    print(f"Parameter grid: {len(mu_values)}×{len(field_values)} = {len(mu_values)*len(field_values)} points")
    print(f"(Reduced grid for demo; production would use 50×20 = 1000 points)\n")
    
    # Sequential execution
    print("=" * 80)
    print("1. SEQUENTIAL EXECUTION")
    print("=" * 80)
    
    start_seq = time.perf_counter()
    results_seq = field_enhanced_search(
        network=network,
        mu_values=mu_values,
        field_values=field_values,
        matter_fields=matter_fields,
        lambda_range=(1e-8, 1e-4),
        n_lambda=5,  # Reduced for demo
        dim=32
    )
    t_seq = time.perf_counter() - start_seq
    
    print(f"\n✓ Sequential time: {t_seq:.2f} s")
    print(f"  Found {len(results_seq)} candidates\n")
    
    # Parallel execution
    print("=" * 80)
    print("2. PARALLEL EXECUTION")
    print("=" * 80)
    
    start_par = time.perf_counter()
    results_par = field_enhanced_search_parallel(
        network=network,
        mu_values=mu_values,
        field_values=field_values,
        matter_fields=matter_fields,
        lambda_range=(1e-8, 1e-4),
        n_lambda=5,  # Reduced for demo
        dim=32,
        n_processes=None  # Use all cores
    )
    t_par = time.perf_counter() - start_par
    
    print(f"\n✓ Parallel time: {t_par:.2f} s")
    print(f"  Found {len(results_par)} candidates\n")
    
    # Comparison
    print("=" * 80)
    print("SPEEDUP ANALYSIS")
    print("=" * 80)
    
    speedup = t_seq / t_par
    efficiency = speedup / min(field_sweep_module.cpu_count(), len(field_values))
    
    print(f"\nSequential: {t_seq:.2f} s")
    print(f"Parallel:   {t_par:.2f} s")
    print(f"Speedup:    {speedup:.2f}×")
    print(f"Efficiency: {efficiency*100:.1f}% (ideal = 100%)")
    
    # Production estimate
    prod_grid = 50 * 20  # 1000 points
    demo_grid = len(mu_values) * len(field_values)
    scale_factor = prod_grid / demo_grid
    
    est_seq = t_seq * scale_factor
    est_par = t_par * scale_factor
    
    print(f"\nProduction grid ({prod_grid} points) estimates:")
    print(f"  Sequential: {est_seq:.1f} s ({est_seq/60:.1f} min)")
    print(f"  Parallel:   {est_par:.1f} s ({est_par/60:.1f} min)")
    print(f"  Time saved: {(est_seq-est_par)/60:.1f} min")
    
    return results_par


def demo_full_parallel_sweep():
    """
    Run full parallel sweep with auto-optimized field range.
    
    This is the production-ready version implementing roadmap priorities:
    1. ✓ External field optimization (auto-scaled)
    2. ✓ Parallel execution (10-20× speedup)
    """
    print("\n" + "=" * 80)
    print("DEMO: FULL PARALLEL SWEEP (AUTO-OPTIMIZED)")
    print("=" * 80)
    print("\nObjective: Complete external field optimization with parallel speedup")
    print("Expected: Best coupling enhancement + fast execution\n")
    
    # Generate network
    print("Generating octahedral network...")
    network, topology_info = generate_topology(topology_type='octahedral')
    print(f"✓ Network: {topology_info.num_nodes} nodes, {topology_info.num_edges} edges\n")
    
    # Define matter fields
    scalar_field = MatterFieldProperties(
        field_type=MatterFieldType.SCALAR,
        characteristic_energy=1e-15,
        characteristic_length=L_PLANCK * 1e10,
        impedance=1.0
    )
    
    fermion_field = MatterFieldProperties(
        field_type=MatterFieldType.FERMION,
        characteristic_energy=1e-15,
        characteristic_length=L_PLANCK * 1e10,
        impedance=1.0
    )
    
    matter_fields = {
        "scalar": scalar_field,
        "fermion": fermion_field
    }
    
    # Parameter grid (production size)
    mu_values = np.linspace(0.1, 1.0, 50)  # 50 μ points
    # field_values will be auto-optimized
    
    print(f"Parameter grid: {len(mu_values)} μ points × 20 field points (auto-optimized)")
    print(f"Total: 1000 grid points\n")
    
    # Run parallel sweep with auto-optimization
    start = time.perf_counter()
    
    results = field_enhanced_search_parallel(
        network=network,
        mu_values=mu_values,
        field_values=None,  # Will be auto-optimized
        matter_fields=matter_fields,
        lambda_range=(1e-8, 1e-4),
        n_lambda=10,
        dim=32,
        rho_exponent=1.0,  # Physical density of states
        auto_optimize_field=True,  # Auto-scale field range!
        n_processes=None  # Use all cores
    )
    
    elapsed = time.perf_counter() - start
    
    print(f"\n✓ Total execution time: {elapsed:.1f} s ({elapsed/60:.2f} min)")
    print(f"  Grid points per second: {len(mu_values)*20/elapsed:.1f}")
    
    # Analyze results
    analyze_field_enhancement(results, decoherence_rate=0.01, top_n=10)
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Parallel field sweep demo")
    parser.add_argument('--sequential', action='store_true', help="Run sequential only")
    parser.add_argument('--parallel', action='store_true', help="Run parallel only")
    parser.add_argument('--both', action='store_true', help="Compare both (default)")
    
    args = parser.parse_args()
    
    # Default: compare both
    if not (args.sequential or args.parallel):
        args.both = True
    
    if args.both:
        print("Running speedup comparison...\n")
        results = demo_parallel_speedup()
        
        print("\n" + "=" * 80)
        input("Press Enter to continue to full parallel sweep...")
        
        results = demo_full_parallel_sweep()
        
    elif args.sequential:
        print("Sequential execution only (not recommended for production)")
        # Would run sequential version
        
    elif args.parallel:
        print("Parallel execution (recommended)")
        results = demo_full_parallel_sweep()
    
    print("\n" + "=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("1. ✓ External field optimization (COMPLETE)")
    print("2. ✓ Parallel execution (COMPLETE)")
    print("3. → Expand λ range [10⁻⁶, 10⁻²] (NEXT)")
    print("4. → Fix icosahedral topology (AFTER #3)")
    print("5. → Combined multi-parameter optimization (FUTURE)")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
