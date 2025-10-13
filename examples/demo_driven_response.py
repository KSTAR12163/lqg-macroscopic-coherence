"""
Demo: Driven response curves for best candidates.

Shows Rabi-like lineshapes to directly visualize Γ_driven/γ ratio.

Usage:
    python examples/demo_driven_response.py
"""

import numpy as np
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.spin_network import SpinNetwork
from src.core.constants import L_PLANCK, HBAR

# Import modules with numeric prefixes using importlib
import importlib
matter_coupling_module = importlib.import_module('src.04_coupling_engineering.matter_coupling')
MatterFieldProperties = matter_coupling_module.MatterFieldProperties

driven_response_module = importlib.import_module('src.07_driven_response')
driven_response_curve = driven_response_module.driven_response_curve
plot_rabi_curve = driven_response_module.plot_rabi_curve
compare_rabi_curves = driven_response_module.compare_rabi_curves
interpret_rabi_curve = driven_response_module.interpret_rabi_curve

# Import topology generator
topology_module = importlib.import_module('src.06_topology_exploration')
generate_topology = topology_module.generate_topology


def demo_single_rabi_curve():
    """
    Compute and visualize a single Rabi curve for the best known candidate.
    """
    print("\n" + "=" * 80)
    print("DEMO: Single Rabi Curve - Best Candidate")
    print("=" * 80)
    
    # Use octahedral network (400× enhancement discovered earlier)
    print("\nGenerating octahedral network...")
    network, info = generate_topology(
        topology_type='octahedral',
        spin_mode='uniform',
        spin_params={'spin_value': 2.0}
    )
    
    print(f"✓ Network: {info.num_nodes} nodes, {info.num_edges} edges")
    print(f"  Spin assignment: {info.spin_assignment}")
    
    # Matter field (scalar field)
    matter_field = MatterFieldProperties(
        field_type=matter_coupling_module.MatterFieldType.SCALAR,
        characteristic_energy=1e-15,  # 1 femtojoule (mesoscopic)
        characteristic_length=L_PLANCK * 1e10,  # 10^10 L_P
        impedance=377.0  # Vacuum impedance (Ω)
    )
    
    # Best parameters from previous optimization
    mu_best = 0.465
    lambda_best = 1e-4
    
    print(f"\nParameters:")
    print(f"  μ = {mu_best}")
    print(f"  λ = {lambda_best}")
    print(f"  External field: h = 0 (no field)")
    
    # Compute Rabi curve
    print("\nComputing driven response curve...")
    print("(This may take 1-2 minutes...)")
    
    data = driven_response_curve(
        network=network,
        matter_field=matter_field,
        mu=mu_best,
        lambda_coupling=lambda_best,
        initial_state=0,  # Ground state
        final_state=1,  # First excited state
        drive_amplitude=1e-10,  # Weak drive (rad/s)
        decoherence_rate=0.01,  # γ = 0.01 Hz (realistic for cryogenic systems)
        frequency_span_factor=10.0,  # Scan ±10γ
        num_frequencies=100,
        evolution_time=100.0,  # 100 seconds (reach steady state)
        dim=32
    )
    
    print("✓ Curve computed successfully")
    
    # Plot
    plot_rabi_curve(
        data,
        title="Driven Response: Octahedral Network (μ=0.465, λ=1e-4)",
        output_path="outputs/rabi_curve_octahedral.png"
    )
    
    # Interpret
    interpret_rabi_curve(data, gamma=0.01)
    
    return data


def demo_topology_comparison_rabi():
    """
    Compare Rabi curves for different topologies.
    """
    print("\n" + "=" * 80)
    print("DEMO: Rabi Curve Comparison - Topology Study")
    print("=" * 80)
    
    topologies = ['tetrahedral', 'cubic', 'octahedral']
    
    matter_field = MatterFieldProperties(
        field_type=matter_coupling_module.MatterFieldType.SCALAR,
        characteristic_energy=1e-15,
        characteristic_length=L_PLANCK * 1e10,
        impedance=377.0
    )
    
    curves_data = {}
    
    for topo in topologies:
        print(f"\n{topo.upper()}:")
        print("-" * 40)
        
        # Generate topology
        if topo == 'tetrahedral':
            network, info = generate_topology(topo, 'uniform', {'spin_value': 2.0})
        elif topo == 'cubic':
            network, info = generate_topology(topo, 'uniform', {'spin_value': 2.0})
        elif topo == 'octahedral':
            network, info = generate_topology(topo, 'uniform', {'spin_value': 2.0})
        
        print(f"  Network: {info.num_nodes} nodes, {info.num_edges} edges")
        
        # Compute Rabi curve
        print(f"  Computing driven response...")
        data = driven_response_curve(
            network=network,
            matter_field=matter_field,
            mu=0.465,
            lambda_coupling=1e-4,
            initial_state=0,
            final_state=1,
            drive_amplitude=1e-10,
            decoherence_rate=0.01,
            frequency_span_factor=10.0,
            num_frequencies=50,  # Fewer points for speed
            evolution_time=50.0,  # Shorter time for speed
            dim=32
        )
        
        curves_data[topo] = data
        print(f"  ✓ Peak height: {data.peak_height:.3e}, SNR: {data.snr_estimate:.3e}")
    
    # Compare
    print("\n" + "=" * 80)
    print("COMPARISON RESULTS")
    print("=" * 80)
    
    compare_rabi_curves(curves_data, output_path="outputs/rabi_comparison.png")
    
    # Rank by SNR
    ranking = sorted(curves_data.items(), key=lambda x: x[1].snr_estimate, reverse=True)
    
    print("\nRanking by SNR (highest first):")
    for i, (name, data) in enumerate(ranking, 1):
        gamma_driven = data.peak_height * data.decoherence_rate
        status = "OBSERVABLE" if gamma_driven >= 10*0.01 else "MARGINAL" if gamma_driven >= 0.01/10 else "UNFEASIBLE"
        
        print(f"{i}. {name:15s}: SNR = {data.snr_estimate:.3e}, "
              f"Γ/γ ~ {gamma_driven/0.01:.3e}, Status: {status}")
    
    return curves_data


def demo_parameter_sweep_rabi():
    """
    Show how Rabi curves change with coupling constant λ.
    """
    print("\n" + "=" * 80)
    print("DEMO: Rabi Curve vs Coupling Constant")
    print("=" * 80)
    
    # Use octahedral (best topology)
    network, info = generate_topology('octahedral', 'uniform', {'spin_value': 2.0})
    
    matter_field = MatterFieldProperties(
        field_type=matter_coupling_module.MatterFieldType.SCALAR,
        characteristic_energy=1e-15,
        characteristic_length=L_PLANCK * 1e10,
        impedance=377.0
    )
    
    lambda_values = [1e-5, 5e-5, 1e-4, 5e-4]
    curves_data = {}
    
    for lam in lambda_values:
        print(f"\nλ = {lam:.2e}:")
        
        data = driven_response_curve(
            network=network,
            matter_field=matter_field,
            mu=0.465,
            lambda_coupling=lam,
            initial_state=0,
            final_state=1,
            drive_amplitude=1e-10,
            decoherence_rate=0.01,
            frequency_span_factor=10.0,
            num_frequencies=50,
            evolution_time=50.0,
            dim=32
        )
        
        curves_data[f'λ={lam:.2e}'] = data
        print(f"  Peak height: {data.peak_height:.3e}")
    
    compare_rabi_curves(curves_data, output_path="outputs/rabi_vs_lambda.png")
    
    print("\n✓ Comparison saved to outputs/rabi_vs_lambda.png")
    
    return curves_data


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Driven response curve demos")
    parser.add_argument('--mode', choices=['single', 'topology', 'lambda', 'all'],
                       default='single',
                       help='Demo mode to run')
    
    args = parser.parse_args()
    
    # Create output directory
    Path("outputs").mkdir(exist_ok=True)
    
    if args.mode == 'single' or args.mode == 'all':
        data = demo_single_rabi_curve()
    
    if args.mode == 'topology' or args.mode == 'all':
        curves = demo_topology_comparison_rabi()
    
    if args.mode == 'lambda' or args.mode == 'all':
        curves_lambda = demo_parameter_sweep_rabi()
    
    print("\n" + "=" * 80)
    print("ALL DEMOS COMPLETE")
    print("=" * 80)
    print("\nOutputs saved to:")
    print("  - outputs/rabi_curve_octahedral.png")
    print("  - outputs/rabi_comparison.png")
    print("  - outputs/rabi_vs_lambda.png")
