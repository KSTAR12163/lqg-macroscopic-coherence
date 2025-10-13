"""
Combined resonance and coupling optimization (Gemini 2.5 Pro recommendation).

This module implements the critical next step: finding parameter "sweet spots" (μ*, λ*)
where geometric resonances (Direction #3) dramatically enhance matter-geometry
coupling strength (Direction #4), potentially overcoming impedance mismatch.

Key Innovation: Instead of treating resonance search and coupling engineering
separately, we compute coupling matrix elements |⟨f|H_int|i⟩| AT resonant
parameters to identify regimes where Γ_driven >> γ.
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
import matplotlib.pyplot as plt
from scipy.linalg import eigh

# Import from Direction #3 (Resonance Search)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.spin_network import SpinNetwork
from src.core.constants import HBAR, L_PLANCK

import importlib
resonance_module = importlib.import_module('src.03_critical_effects.resonance_search')
GeometricHamiltonian = resonance_module.GeometricHamiltonian
detect_avoided_crossings = resonance_module.detect_avoided_crossings

# Import from Direction #4 (Coupling Engineering)
coupling_module = importlib.import_module('src.04_coupling_engineering.matter_coupling')
MatterGeometryCoupling = coupling_module.MatterGeometryCoupling
MatterFieldProperties = coupling_module.MatterFieldProperties
MATTER_FIELDS = coupling_module.MATTER_FIELDS


@dataclass
class ResonantCouplingPoint:
    """A parameter point with both resonance and strong coupling."""
    mu: float  # Polymer parameter
    lambda_opt: float  # Optimal coupling constant
    field_type: str  # Matter field type
    level1_idx: int  # First resonant level
    level2_idx: int  # Second resonant level
    energy_gap: float  # Gap at resonance (J)
    coupling_strength: float  # |⟨f|H_int|i⟩| (J)
    driven_rate: float  # Estimated Γ_driven (Hz)
    susceptibility: float  # ∂E/∂μ (J)
    figure_of_merit: float  # Combined metric


def compute_coupling_at_resonance(
    network: SpinNetwork,
    mu: float,
    matter_field: MatterFieldProperties,
    lambda_val: float,
    level1: int,
    level2: int,
    dim: int = 32,
    rho_exponent: float = 1.0
) -> Tuple[float, float]:
    """
    Compute matter-geometry coupling strength at a specific resonance.
    
    Args:
        network: Spin network
        mu: Polymer parameter
        matter_field: Matter field properties
        lambda_val: Coupling constant
        level1, level2: Resonant energy levels
        dim: Hilbert space dimension
        rho_exponent: Density of states model ρ ~ 1/gap^α
            - α=1: Physical default (matches level spacing)
            - α=2: Previous default (emphasizes near-degeneracy)
    
    Returns:
        (coupling_strength, driven_rate) in Joules and Hz
        
    Notes:
        Driven rate via Fermi's golden rule: Γ ~ (2π/ħ) |⟨f|H_int|i⟩|² ρ(E)
        With ρ ~ 1/gap^α, we have Γ ~ |M|²/gap^α
        Physical interpretation:
          - α=1: Standard density of states for 1D level spacing
          - α>1: Heuristic to emphasize tiny gaps during exploration
    """
    # Build coupling Hamiltonian at this μ
    coupling = MatterGeometryCoupling(
        network=network,
        matter_field=matter_field,
        coupling_constant=lambda_val,
        mu=mu
    )
    
    # Get eigenstates
    eigenvalues, eigenvectors = coupling.compute_energy_spectrum(dim)
    
    # Build interaction Hamiltonian
    H_int = coupling.build_interaction_hamiltonian(dim)
    
    # Compute matrix element ⟨level2|H_int|level1⟩
    matrix_element = eigenvectors[:, level2].conj() @ H_int @ eigenvectors[:, level1]
    coupling_strength = abs(matrix_element)
    
    # Estimate driven rate via Fermi's golden rule
    # Γ ~ (2π/ħ) |⟨f|H_int|i⟩|² ρ(E)
    # Density of states model: ρ ~ 1/gap^α (configurable)
    energy_gap = abs(eigenvalues[level2] - eigenvalues[level1])
    if energy_gap > 0:
        rho_states = 1.0 / energy_gap**rho_exponent
    else:
        rho_states = 0.0
    
    driven_rate = (2 * np.pi / HBAR) * coupling_strength**2 * rho_states
    
    return coupling_strength, driven_rate


def combined_resonance_coupling_search(
    network: SpinNetwork,
    mu_values: np.ndarray,
    matter_fields: Dict[str, MatterFieldProperties],
    lambda_range: Tuple[float, float] = (1e-8, 1e-4),
    n_lambda: int = 10,
    min_gap_threshold: float = 1e-37,
    dim: int = 32,
    rho_exponent: float = 1.0
) -> List[ResonantCouplingPoint]:
    """
    Search for combined resonance + strong coupling "sweet spots".
    
    This is the key innovation: we sweep μ to find resonances, then for each
    resonance we optimize λ to maximize coupling strength at that resonance.
    
    Args:
        network: Spin network topology
        mu_values: Polymer parameter sweep values
        matter_fields: Dictionary of matter field types to test
        lambda_range: Range for coupling constant optimization
        n_lambda: Number of λ samples
        min_gap_threshold: Threshold for resonance detection
        dim: Hilbert space dimension
        rho_exponent: Density of states exponent (α=1 physical, α=2 gap-emphasis)
    
    Returns:
        List of ResonantCouplingPoint objects ranked by figure of merit
    """
    print("=" * 80)
    print("COMBINED RESONANCE + COUPLING OPTIMIZATION")
    print("=" * 80)
    print(f"\nSearching for parameter 'sweet spots' (μ*, λ*) where:")
    print("  1. Geometric resonance exists (avoided crossing)")
    print("  2. Matter-geometry coupling is strong (|⟨f|H_int|i⟩| >> 0)")
    print("  3. Driven rate exceeds decoherence (Γ_driven >> γ)")
    print(f"\nDensity of states model: ρ ~ 1/gap^{rho_exponent} ({'physical' if abs(rho_exponent - 1.0) < 0.01 else 'gap-emphasis'})\n")
    
    results = []
    
    # Step 1: Perform resonance search over μ
    print(f"Step 1: Resonance search over {len(mu_values)} μ values...")
    
    ResonanceSearcher = resonance_module.ResonanceSearcher
    searcher = ResonanceSearcher(network)
    mu_vals, energy_spectra = searcher.sweep_polymer_parameter(mu_values, external_field=0.0)
    
    # Detect avoided crossings
    avoided_crossings = detect_avoided_crossings(mu_vals, energy_spectra, min_gap_threshold)
    
    print(f"  Found {len(avoided_crossings)} avoided crossings\n")
    
    if len(avoided_crossings) == 0:
        print("  ⚠️  No resonances detected. Try:")
        print("     - Wider μ range")
        print("     - External field perturbation")
        print("     - Different network topology")
        return results
    
    # Compute susceptibility for additional metric
    susceptibility = searcher.compute_susceptibility(mu_vals, energy_spectra)
    
    # Step 2: For each resonance, optimize coupling
    print(f"Step 2: Optimizing coupling at each resonance...\n")
    
    lambda_values = np.logspace(np.log10(lambda_range[0]), np.log10(lambda_range[1]), n_lambda)
    
    for crossing_idx, crossing in enumerate(avoided_crossings[:20], 1):  # Limit to top 20
        mu_res = crossing.parameter_value
        level1 = crossing.level1_idx
        level2 = crossing.level2_idx
        gap = crossing.min_gap
        
        # Get susceptibility at this μ
        mu_idx = np.argmin(np.abs(mu_vals - mu_res))
        chi = np.mean([abs(susceptibility[mu_idx, level1]), abs(susceptibility[mu_idx, level2])])
        
        print(f"  Resonance {crossing_idx}/{len(avoided_crossings[:20])}: μ={mu_res:.3f}, levels {level1}↔{level2}, gap={gap:.2e} J")
        
        # Test each matter field type
        for field_name, matter_field in matter_fields.items():
            best_lambda = lambda_values[0]
            best_coupling = 0.0
            best_rate = 0.0
            
            # Optimize λ for this resonance
            for lambda_val in lambda_values:
                coupling_strength, driven_rate = compute_coupling_at_resonance(
                    network, mu_res, matter_field, lambda_val,
                    level1, level2, dim, rho_exponent
                )
                
                if coupling_strength > best_coupling:
                    best_coupling = coupling_strength
                    best_rate = driven_rate
                    best_lambda = lambda_val
            
            # Figure of merit: driven_rate × susceptibility / gap
            # (Want high rate, high sensitivity, small gap for accessibility)
            if gap > 0:
                fom = best_rate * chi / gap
            else:
                fom = 0.0
            
            # Store result
            point = ResonantCouplingPoint(
                mu=mu_res,
                lambda_opt=best_lambda,
                field_type=field_name,
                level1_idx=level1,
                level2_idx=level2,
                energy_gap=gap,
                coupling_strength=best_coupling,
                driven_rate=best_rate,
                susceptibility=chi,
                figure_of_merit=fom
            )
            results.append(point)
            
            print(f"    {field_name:15s}: λ*={best_lambda:.2e}, |⟨f|H_int|i⟩|={best_coupling:.2e} J, Γ={best_rate:.2e} Hz")
    
    # Sort by figure of merit
    results.sort(key=lambda x: x.figure_of_merit, reverse=True)
    
    print(f"\n✓ Found {len(results)} resonant coupling points")
    
    return results


def plot_resonant_coupling_map(
    results: List[ResonantCouplingPoint],
    output_path: str = "outputs/resonant_coupling_map.png"
):
    """
    Visualize the resonant coupling landscape.
    
    Creates a 2D plot showing:
    - X-axis: μ (polymer parameter)
    - Y-axis: Driven rate Γ_driven
    - Color: Figure of merit
    - Size: Coupling strength
    """
    if len(results) == 0:
        print("No results to plot")
        return
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Extract data
    mu_vals = [r.mu for r in results]
    rates = [r.driven_rate for r in results]
    foms = [r.figure_of_merit for r in results]
    couplings = [r.coupling_strength for r in results]
    
    # Plot 1: Rate vs μ, colored by FOM
    scatter1 = ax1.scatter(mu_vals, rates, c=foms, s=100, alpha=0.7,
                          cmap='viridis', edgecolors='k', linewidths=0.5)
    ax1.set_xlabel("Polymer Parameter μ", fontsize=12)
    ax1.set_ylabel("Driven Rate Γ_driven (Hz)", fontsize=12)
    ax1.set_yscale('log')
    ax1.set_title("Resonant Coupling Landscape", fontsize=14)
    ax1.grid(True, alpha=0.3)
    cbar1 = plt.colorbar(scatter1, ax=ax1)
    cbar1.set_label("Figure of Merit", fontsize=10)
    
    # Plot 2: Coupling strength vs μ, sized by rate
    sizes = np.array(rates)
    sizes = (sizes / sizes.max()) * 500  # Normalize to reasonable size
    scatter2 = ax2.scatter(mu_vals, couplings, s=sizes, alpha=0.6,
                          c=foms, cmap='plasma', edgecolors='k', linewidths=0.5)
    ax2.set_xlabel("Polymer Parameter μ", fontsize=12)
    ax2.set_ylabel("Coupling Strength |⟨f|H_int|i⟩| (J)", fontsize=12)
    ax2.set_yscale('log')
    ax2.set_title("Coupling Strength at Resonances", fontsize=14)
    ax2.grid(True, alpha=0.3)
    cbar2 = plt.colorbar(scatter2, ax=ax2)
    cbar2.set_label("Figure of Merit", fontsize=10)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Resonant coupling map saved to {output_path}")
    plt.close()


def analyze_top_candidates(
    results: List[ResonantCouplingPoint],
    gamma: float = 0.01,
    n_top: int = 5
):
    """
    Analyze top candidates for experimental feasibility.
    
    Args:
        results: List of resonant coupling points
        gamma: Decoherence rate (from Direction #2)
        n_top: Number of top candidates to analyze
    """
    print("\n" + "=" * 80)
    print("TOP CANDIDATE ANALYSIS")
    print("=" * 80)
    print(f"\nCritical condition: Γ_driven >> γ = {gamma:.2e} Hz")
    print(f"Analyzing top {n_top} candidates by figure of merit...\n")
    
    for idx, point in enumerate(results[:n_top], 1):
        print(f"{'━' * 80}")
        print(f"Candidate #{idx}: {point.field_type.upper()}")
        print(f"{'━' * 80}")
        print(f"  Parameter sweet spot:")
        print(f"    μ* = {point.mu:.4f}")
        print(f"    λ* = {point.lambda_opt:.3e}")
        print(f"  Resonance properties:")
        print(f"    Levels: {point.level1_idx} ↔ {point.level2_idx}")
        print(f"    Energy gap: {point.energy_gap:.3e} J")
        print(f"    Frequency: {point.energy_gap/HBAR:.3e} rad/s")
        print(f"    Susceptibility: {point.susceptibility:.3e} J")
        print(f"  Coupling properties:")
        print(f"    Matrix element: |⟨f|H_int|i⟩| = {point.coupling_strength:.3e} J")
        print(f"    Driven rate: Γ_driven = {point.driven_rate:.3e} Hz")
        print(f"  Observable metrics:")
        print(f"    SNR: Γ_driven/γ = {point.driven_rate/gamma:.3e}")
        print(f"    Coherence time: τ_coh ≈ 1/γ = {1/gamma:.3e} s")
        print(f"    Integration time: T_int ≈ 1/(Γ_driven × SNR^0.5) = {1/(point.driven_rate * np.sqrt(point.driven_rate/gamma)):.3e} s")
        print(f"  Figure of merit: {point.figure_of_merit:.3e}")
        
        # Feasibility assessment
        if point.driven_rate > gamma:
            status = "✓ PROMISING"
            color = "green"
        elif point.driven_rate > gamma / 10:
            status = "⚠️  MARGINAL"
            color = "yellow"
        else:
            status = "✗ UNFEASIBLE"
            color = "red"
        
        print(f"\n  Status: {status} (Γ_driven/γ = {point.driven_rate/gamma:.2e})")
        print()
    
    # Summary statistics
    print("=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    
    promising = [r for r in results if r.driven_rate > gamma]
    marginal = [r for r in results if gamma/10 < r.driven_rate <= gamma]
    unfeasible = [r for r in results if r.driven_rate <= gamma/10]
    
    print(f"\nTotal candidates: {len(results)}")
    print(f"  ✓ Promising (Γ > γ):     {len(promising)} ({100*len(promising)/len(results):.1f}%)")
    print(f"  ⚠️  Marginal (γ/10 < Γ < γ): {len(marginal)} ({100*len(marginal)/len(results):.1f}%)")
    print(f"  ✗ Unfeasible (Γ < γ/10):  {len(unfeasible)} ({100*len(unfeasible)/len(results):.1f}%)")
    
    if len(promising) > 0:
        best = promising[0]
        print(f"\n🎯 Best candidate: {best.field_type} at μ={best.mu:.3f}, λ={best.lambda_opt:.2e}")
        print(f"   Γ_driven = {best.driven_rate:.2e} Hz ({best.driven_rate/gamma:.1e}× decoherence rate)")


def demonstrate_combined_optimization():
    """Demonstration of combined resonance + coupling optimization."""
    print("\n" + "=" * 80)
    print("GEMINI 2.5 PRO RECOMMENDATION: COMBINED OPTIMIZATION")
    print("=" * 80)
    print("\nFinding parameter 'sweet spots' where resonances enhance coupling...\n")
    
    # Build test network
    network = SpinNetwork()
    nodes = [network.add_node(i) for i in range(4)]
    edges = [
        (0, 1, 1.0), (0, 2, 1.0), (0, 3, 1.0),
        (1, 2, 0.5), (1, 3, 0.5), (2, 3, 0.5)
    ]
    for (i, j, spin) in edges:
        network.add_edge(i, j, spin)
    
    print(f"Test network: {len(network.nodes)} nodes, {len(network.edges)} edges")
    
    # Parameter sweep (wider range per Gemini suggestion)
    mu_values = np.linspace(0.001, 3.0, 150)  # Extended range
    
    # Run combined optimization
    results = combined_resonance_coupling_search(
        network,
        mu_values,
        MATTER_FIELDS,
        lambda_range=(1e-8, 1e-4),
        n_lambda=15,
        min_gap_threshold=1e-36,  # Slightly relaxed
        dim=32
    )
    
    if len(results) > 0:
        # Visualize
        import os
        os.makedirs("outputs", exist_ok=True)
        plot_resonant_coupling_map(results)
        
        # Analyze top candidates
        analyze_top_candidates(results, gamma=0.01, n_top=5)
    else:
        print("\n⚠️  No resonant coupling points found.")
        print("   Try: different topology, external fields, or broader parameter ranges")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    demonstrate_combined_optimization()
