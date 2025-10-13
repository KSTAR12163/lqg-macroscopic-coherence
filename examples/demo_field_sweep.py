"""
Demo: 2D (μ, external field) sweep for enhanced coupling (researcher Priority #1).

Tests whether external field perturbation can break degeneracies and induce
mixing to achieve observable coupling: Γ_driven/γ ≥ 10.
"""

import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.spin_network import SpinNetwork

import importlib
coupling_module = importlib.import_module('src.04_coupling_engineering.matter_coupling')
field_sweep_module = importlib.import_module('src.05_combined_optimization.field_sweep')

MATTER_FIELDS = coupling_module.MATTER_FIELDS
field_enhanced_search = field_sweep_module.field_enhanced_search
plot_field_landscape = field_sweep_module.plot_field_landscape
analyze_field_enhancement = field_sweep_module.analyze_field_enhancement


def main():
    """Run 2D field sweep demonstration."""
    print("╔" + "=" * 78 + "╗")
    print("║ 2D (μ, EXTERNAL FIELD) SWEEP - researcher Priority #1                          ║")
    print("║ Test: Can external fields break degeneracies and enhance coupling?        ║")
    print("╚" + "=" * 78 + "╝")
    
    # Create tetrahedral network
    print("\nCreating tetrahedral spin network...")
    network = SpinNetwork()
    nodes = [network.add_node(i) for i in range(4)]
    edges = [
        (0, 1, 1.0), (0, 2, 1.0), (0, 3, 1.0),
        (1, 2, 1.0), (1, 3, 1.0), (2, 3, 1.0)
    ]
    for (i, j, spin) in edges:
        network.add_edge(i, j, spin)
    
    print(f"  ✓ {len(network.nodes)} nodes, {len(network.edges)} edges")
    
    # Parameter grids (researcher recommended: μ×200, h×20)
    print("\nSetting up parameter grids...")
    mu_values = np.linspace(1e-3, 3.0, 200)  # Extended μ range
    
    # External field: test range [0, h_max]
    # Start with moderate h_max ~ L_Planck^3 scale
    from src.core.constants import L_PLANCK
    h_max = 1e-30  # Start small, can increase
    field_values = np.linspace(0.0, h_max, 20)
    
    print(f"  μ grid: {len(mu_values)} points, [{mu_values.min():.3e}, {mu_values.max():.3e}]")
    print(f"  Field grid: {len(field_values)} points, [0, {h_max:.3e}]")
    print(f"  Total evaluations: {len(mu_values)} × {len(field_values)} = {len(mu_values) * len(field_values)}")
    
    # Matter fields to test
    matter_fields_subset = {
        'optical': MATTER_FIELDS['optical'],
        'microwave': MATTER_FIELDS['microwave']
    }
    
    # Run 2D sweep
    print("\nExecuting 2D sweep...")
    print("(This may take a few minutes due to grid size)\n")
    
    results = field_enhanced_search(
        network=network,
        mu_values=mu_values,
        field_values=field_values,
        matter_fields=matter_fields_subset,
        lambda_range=(1e-8, 1e-4),
        n_lambda=15,
        min_gap_threshold=1e-36,
        dim=32,
        rho_exponent=1.0  # Physical density of states
    )
    
    # Analyze results
    if results:
        analyze_field_enhancement(results, decoherence_rate=0.01, top_n=15)
        plot_field_landscape(results, decoherence_rate=0.01)
    else:
        print("\n⚠️  No candidates found. Suggestions:")
        print("   - Increase h_max (try 1e-29 or 1e-28)")
        print("   - Widen μ range")
        print("   - Test different network topologies")
    
    # Acceptance criterion (researcher recommendation)
    print("\n" + "=" * 80)
    print("ACCEPTANCE CRITERION (GPT-5)")
    print("=" * 80)
    print("\nMilestone: Increase |⟨f|H_int|i⟩| and approach Γ_driven/γ ~ 10⁻³ to 10⁻⁶")
    
    if results:
        best = results[0]
        baseline_rate = 1e-189  # From h=0 baseline
        current_rate = best.driven_rate
        gamma = 0.01
        
        improvement = current_rate / baseline_rate if baseline_rate > 0 else float('inf')
        snr = current_rate / gamma
        
        print(f"\nBaseline (h=0, tetrahedral): Γ ~ {baseline_rate:.2e} Hz")
        print(f"Best with field: Γ = {current_rate:.2e} Hz")
        print(f"Improvement: {improvement:.2e}×")
        print(f"SNR (Γ/γ): {snr:.2e}")
        
        if snr >= 1e-3:
            print("\n✓ MILESTONE REACHED: SNR ≥ 10⁻³")
        elif snr >= 1e-6:
            print("\n⚠️  PARTIAL PROGRESS: SNR ≥ 10⁻⁶ (continue optimization)")
        else:
            print(f"\n✗ INSUFFICIENT: SNR = {snr:.2e} << 10⁻⁶")
            print("   Recommend: Try topology study (researcher Priority #2)")
    
    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print("\n1. If field helps: Expand h range, test different O_ext operators")
    print("2. If field insufficient: Topology study (cubic, octahedral, etc.)")
    print("3. Implement driven response curves (Rabi lineshapes)")
    print("4. HPC infrastructure for full parameter space exploration")
    
    print("\n✓ Demo complete!")


if __name__ == "__main__":
    main()
