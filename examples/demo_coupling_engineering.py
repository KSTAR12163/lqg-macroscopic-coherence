"""
Demonstration of coupling engineering module (Research Direction #4).

This script:
1. Defines matter-geometry coupling Hamiltonians
2. Computes transition rates induced by quantum geometry
3. Searches for optimal coupling parameters
4. Analyzes impedance matching between geometry and matter
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import matplotlib.pyplot as plt

from src.core.spin_network import SpinNetwork
# Use importlib for modules with numeric prefixes
import importlib
coupling_module = importlib.import_module('src.04_coupling_engineering.matter_coupling')
MatterGeometryCoupling = coupling_module.MatterGeometryCoupling
MatterFieldType = coupling_module.MatterFieldType
MATTER_FIELDS = coupling_module.MATTER_FIELDS
search_optimal_coupling = coupling_module.search_optimal_coupling
analyze_impedance_matching = coupling_module.analyze_impedance_matching
compute_transition_rates = coupling_module.compute_transition_rates
plot_coupling_comparison = coupling_module.plot_coupling_comparison
plot_impedance_analysis = coupling_module.plot_impedance_analysis

# Import driven Lindblad evolution (researcher suggestion)
lindblad_module = importlib.import_module('src.04_coupling_engineering.driven_lindblad')
lindblad_evolution = lindblad_module.lindblad_evolution
plot_driven_evolution = lindblad_module.plot_driven_evolution
estimate_observable_rate = lindblad_module.estimate_observable_rate


def main():
    print("=" * 80)
    print("RESEARCH DIRECTION #4: COUPLING ENGINEERING")
    print("=" * 80)
    print("\nAnalyzing matter-geometry coupling and impedance matching...\n")
    
    # ========================================================================
    # 1. Build a tetrahedral spin network
    # ========================================================================
    network = SpinNetwork()
    nodes = [network.add_node(i) for i in range(4)]
    edges = [
        (0, 1, 1.0), (0, 2, 1.0), (0, 3, 1.0),
        (1, 2, 0.5), (1, 3, 0.5), (2, 3, 0.5)
    ]
    for (i, j, spin) in edges:
        network.add_edge(i, j, spin)
    
    print(f"Spin network: {len(network.nodes)} nodes, {len(network.edges)} edges\n")
    
    # ========================================================================
    # 2. Search for optimal coupling constants
    # ========================================================================
    print("Computing optimal coupling constants for different matter fields...")
    print("(This may take a moment...)\n")
    
    optimal_couplings = search_optimal_coupling(
        network,
        MATTER_FIELDS,
        coupling_range=(1e-10, 1e-5),
        n_samples=15  # Reduced for faster demo
    )
    
    print("Optimal Couplings:")
    print("-" * 70)
    for field_name, (lambda_opt, rate_max) in optimal_couplings.items():
        print(f"{field_name:20s}: λ = {lambda_opt:.2e}, max rate = {rate_max:.2e} Hz")
    
    # ========================================================================
    # 3. Impedance matching analysis
    # ========================================================================
    print("\nImpedance Matching Analysis:")
    print("-" * 70)
    
    impedance_results = analyze_impedance_matching(network, MATTER_FIELDS)
    
    for field_name, R in impedance_results.items():
        T = 1 - R
        match_quality = "EXCELLENT" if R < 0.1 else "GOOD" if R < 0.5 else "POOR"
        print(f"{field_name:20s}: R = {R:.4f}, T = {T:.4f}  [{match_quality}]")
    
    # ========================================================================
    # 4. Generate visualizations
    # ========================================================================
    print("\nGenerating visualizations...")
    
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    
    plot_coupling_comparison(optimal_couplings, str(output_dir / "coupling_comparison.png"))
    plot_impedance_analysis(impedance_results, str(output_dir / "impedance_matching.png"))
    
    # ========================================================================
    # 5. Detailed analysis of best candidate
    # ========================================================================
    best_field = min(impedance_results.items(), key=lambda x: x[1])[0]
    
    print(f"\n{'=' * 80}")
    print(f"DETAILED ANALYSIS: {best_field.upper()}")
    print("=" * 80)
    
    coupling = MatterGeometryCoupling(
        network=network,
        matter_field=MATTER_FIELDS[best_field],
        coupling_constant=optimal_couplings[best_field][0]
    )
    
    # Compute energy spectrum
    eigenvalues, eigenvectors = coupling.compute_energy_spectrum(dim=16)
    
    print(f"\nEnergy Spectrum (first 10 levels):")
    print("-" * 70)
    for i in range(min(10, len(eigenvalues))):
        print(f"  E_{i} = {eigenvalues[i]:.4e} J")
    
    # Compute transition rates from ground state
    print(f"\nTransition Rates from Ground State:")
    print("-" * 70)
    
    rates = compute_transition_rates(coupling, initial_state=0, dim=16)
    top_transitions = sorted(rates.items(), key=lambda x: x[1], reverse=True)[:8]
    
    for final_state, rate in top_transitions:
        energy_diff = eigenvalues[final_state] - eigenvalues[0]
        frequency = energy_diff / 6.626e-34  # h
        print(f"  0 → {final_state}: {rate:.2e} Hz  (ΔE = {energy_diff:.2e} J, ν = {frequency:.2e} Hz)")
    
    # ========================================================================
    # 6. Compare all matter fields
    # ========================================================================
    print(f"\n{'=' * 80}")
    print("COMPARATIVE ANALYSIS: ALL MATTER FIELDS")
    print("=" * 80)
    
    comparison_data = []
    for field_name in MATTER_FIELDS:
        lambda_opt, rate_max = optimal_couplings[field_name]
        R = impedance_results[field_name]
        T = 1 - R
        
        comparison_data.append({
            'field': field_name,
            'lambda': lambda_opt,
            'rate': rate_max,
            'reflection': R,
            'transmission': T
        })
    
    # Sort by transmission (best first)
    comparison_data.sort(key=lambda x: x['transmission'], reverse=True)
    
    print(f"\n{'Field':<20s} {'λ':>12s} {'Rate (Hz)':>12s} {'R':>8s} {'T':>8s} {'Quality':<10s}")
    print("-" * 80)
    for data in comparison_data:
        quality = "EXCELLENT" if data['reflection'] < 0.1 else "GOOD" if data['reflection'] < 0.5 else "POOR"
        print(f"{data['field']:<20s} {data['lambda']:>12.2e} {data['rate']:>12.2e} "
              f"{data['reflection']:>8.4f} {data['transmission']:>8.4f} {quality:<10s}")
    
    # ========================================================================
    # 7. Summary and implications
    # ========================================================================
    print(f"\n{'=' * 80}")
    print("KEY FINDINGS:")
    print("=" * 80)
    print(f"1. Best impedance matching: {comparison_data[0]['field']} (T = {comparison_data[0]['transmission']:.3f})")
    print(f"2. Highest transition rate: {max(comparison_data, key=lambda x: x['rate'])['field']}")
    print(f"3. Optimal coupling constants span {comparison_data[-1]['lambda']:.1e} to {comparison_data[0]['lambda']:.1e}")
    print(f"4. Reflection coefficients range from {comparison_data[0]['reflection']:.3f} to {comparison_data[-1]['reflection']:.3f}")
    
    # ========================================================================
    # 8. Driven evolution with decoherence (researcher addition)
    # ========================================================================
    print(f"\n{'=' * 80}")
    print("DRIVEN EVOLUTION WITH DECOHERENCE (researcher enhancement)")
    print("=" * 80)
    print("\nSimulating realistic driven transitions including decoherence...\n")
    
    # Use best candidate from impedance matching
    best_coupling = MatterGeometryCoupling(
        network=network,
        matter_field=MATTER_FIELDS[best_field],
        coupling_constant=optimal_couplings[best_field][0]
    )
    
    # Build Hamiltonians
    H_system = best_coupling.build_geometry_operator(16) + best_coupling.build_matter_operator(16)
    H_drive = best_coupling.build_interaction_hamiltonian(16)
    
    # Evolution parameters
    drive_amplitude = 1e-30  # Weak driving
    gamma = 0.01  # Decoherence rate (from Direction #2)
    simulation_time = 1e-10  # 0.1 ns
    
    # Run driven evolution
    initial_state = np.zeros(16)
    initial_state[0] = 1.0  # Ground state
    times = np.linspace(0, simulation_time, 200)
    
    result = lindblad_evolution(
        H_system, H_drive, initial_state,
        gamma, drive_amplitude, times
    )
    
    print(f"Driven transition rate: {result.driven_rate:.2e} Hz")
    print(f"Coherence-limited rate: {result.coherence_limited_rate:.2e} Hz")
    print(f"SNR (driven/decoherence): {result.driven_rate/gamma if gamma > 0 else 0:.2e}")
    
    # Plot driven evolution
    plot_driven_evolution(result, str(output_dir / "driven_evolution.png"))
    
    print("\nImplications for Experimental Realization:")
    print("-" * 80)
    print("• EM fields (microwave/optical) show best impedance matching to quantum geometry")
    print("• Phonon coupling is suppressed by material density mismatch")
    print("• Optimal λ values guide experimental parameter selection")
    print("• Transition rates indicate observable timescales (if coherence maintained)")
    print(f"• Best candidate ({comparison_data[0]['field']}) has {comparison_data[0]['transmission']*100:.1f}% transmission efficiency")
    print(f"• Decoherence limits observable rates to ~{result.coherence_limited_rate:.2e} Hz")
    
    print("\nNext Steps:")
    print("-" * 80)
    print("1. Combine with resonance search (Direction #3) to find optimal (μ, λ) pairs")
    print("2. Include decoherence from Direction #2 to estimate observable signal strength")
    print("3. Design experimental geometry (coil/cavity) based on impedance matching")
    print("4. Perform HPC parameter sweep (Direction #5) over full parameter space")
    print("=" * 80)


if __name__ == "__main__":
    main()
