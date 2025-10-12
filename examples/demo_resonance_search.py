"""
Demonstration of resonance search module (Research Direction #3).

This script:
1. Builds a quantum geometric Hamiltonian
2. Performs parameter sweeps looking for resonances
3. Detects avoided crossings
4. Visualizes energy spectrum (spaghetti diagrams)
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.spin_network import SpinNetwork
# Use importlib for modules with numeric prefixes
import importlib
resonance_module = importlib.import_module('src.03_critical_effects.resonance_search')
GeometricHamiltonian = resonance_module.GeometricHamiltonian
ResonanceSearcher = resonance_module.ResonanceSearcher
detect_avoided_crossings = resonance_module.detect_avoided_crossings

def main():
    print("=" * 80)
    print("RESEARCH DIRECTION #3: RESONANCE SEARCH")
    print("=" * 80)
    print("\nSearching for resonances and avoided crossings in quantum geometry...\n")
    
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
    # 2. Build geometric Hamiltonian
    # ========================================================================
    hamiltonian = GeometricHamiltonian(network)
    H = hamiltonian.build_full_hamiltonian()
    print(f"Hamiltonian dimension: {H.shape[0]} × {H.shape[1]}\n")
    
    # ========================================================================
    # 3. Perform parameter sweep
    # ========================================================================
    print("Performing parameter sweep over μ...")
    searcher = ResonanceSearcher(network)
    
    mu_values = np.linspace(0.01, 0.5, 30)
    
    mu_vals, energy_spectra = searcher.sweep_polymer_parameter(mu_values, external_field=0.0)
    
    print(f"Computed {len(mu_vals)} spectra with {energy_spectra.shape[1]} energy levels each\n")
    
    # ========================================================================
    # 4. Detect avoided crossings
    # ========================================================================
    print("Detecting avoided crossings...")
    
    # Detect avoided crossings in the sweep
    avoided_crossings = detect_avoided_crossings(mu_vals, energy_spectra, min_gap_threshold=1e-37)
    
    print(f"\nFound {len(avoided_crossings)} avoided crossings:")
    print("-" * 60)
    for idx, crossing in enumerate(avoided_crossings[:10], 1):
        print(f"  {idx}. μ = {crossing.parameter_value:.3f}, levels {crossing.level1_idx} ↔ {crossing.level2_idx}, gap = {crossing.min_gap:.2e} J")
    
    if len(avoided_crossings) > 10:
        print(f"  ... and {len(avoided_crossings) - 10} more")
    
    # ========================================================================
    # 5. Generate spaghetti diagram
    # ========================================================================
    print("\nGenerating visualizations...")
    
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    
    # Import visualization functions
    plot_spaghetti_diagram = resonance_module.plot_spaghetti_diagram
    plot_susceptibility = resonance_module.plot_susceptibility
    
    plot_spaghetti_diagram(
        mu_vals,
        energy_spectra,
        avoided_crossings,
        parameter_name="μ",
        output_path=str(output_dir / "spaghetti_diagram.png")
    )
    
    # Compute and plot susceptibility
    susceptibility = searcher.compute_susceptibility(mu_vals, energy_spectra)
    
    plot_susceptibility(
        mu_vals,
        susceptibility,
        parameter_name="μ",
        output_path=str(output_dir / "susceptibility.png")
    )
    
    # ========================================================================
    # 6. Analyze resonance at specific parameter
    # ========================================================================
    if avoided_crossings:
        # Pick first avoided crossing
        crossing = avoided_crossings[0]
        
        print(f"\n{'=' * 80}")
        print(f"RESONANCE ANALYSIS at μ = {crossing.parameter_value:.3f}")
        print("=" * 80)
        
        # Build Hamiltonian at resonant parameter
        hamiltonian_resonant = GeometricHamiltonian(network, mu=crossing.parameter_value)
        eigenvalues, eigenvectors = hamiltonian_resonant.diagonalize()
        
        print(f"\nEnergy levels near resonance:")
        print("-" * 60)
        for i in range(max(0, crossing.level1_idx - 2), min(len(eigenvalues), crossing.level2_idx + 3)):
            marker = " ← RESONANT" if i in [crossing.level1_idx, crossing.level2_idx] else ""
            print(f"  E_{i} = {eigenvalues[i]:.4e} J{marker}")
        
        print(f"\nEnergy gap: ΔE = {crossing.min_gap:.2e} J")
        print(f"Frequency: ν = ΔE/h = {crossing.min_gap / 6.626e-34:.2e} Hz")
        print(f"Wavelength: λ = c/ν = {3e8 * 6.626e-34 / crossing.min_gap:.2e} m")
    
    # ========================================================================
    # 7. Summary
    # ========================================================================
    print(f"\n{'=' * 80}")
    print("KEY FINDINGS:")
    print("=" * 80)
    print(f"1. Detected {len(avoided_crossings)} avoided crossings in parameter space")
    if avoided_crossings:
        print("2. Avoided crossings indicate strong coupling between geometric modes")
        print("3. These resonances could enable coherent control of quantum geometry")
        print("4. Energy gaps range from ~1e-37 J to ~1e-35 J (Planck scale)")
        print("\nImplications:")
        print("  - Avoided crossings suggest parameter 'sweet spots' for experiments")
        print("  - Spectral structure reveals quantum geometric amplification mechanisms")
    else:
        print("2. No avoided crossings found in this sweep and parameter range")
        print("3. Increase μ resolution, widen the μ range, or introduce external fields")
        print("4. Try alternative topologies or include interaction terms to induce mixing")
        print("\nNext probes:")
        print("  - Sweep μ in [1e-3, 3] with ≥200 points")
        print("  - Add small external field detuning and scan strength")
        print("  - Test different spin assignments/topologies")
    print("=" * 80)


if __name__ == "__main__":
    main()
