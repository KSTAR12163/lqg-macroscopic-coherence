"""
Demonstration of combined resonance + coupling optimization (researcher).

This is the highest priority next step: finding parameter "sweet spots" (μ*, λ*)
where geometric resonances dramatically enhance matter-geometry coupling strength,
potentially achieving Γ_driven >> γ.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import importlib

from src.core.spin_network import SpinNetwork

# Import modules
combined_module = importlib.import_module('src.05_combined_optimization.resonant_coupling_search')
combined_resonance_coupling_search = combined_module.combined_resonance_coupling_search
plot_resonant_coupling_map = combined_module.plot_resonant_coupling_map
analyze_top_candidates = combined_module.analyze_top_candidates

coupling_module = importlib.import_module('src.04_coupling_engineering.matter_coupling')
MATTER_FIELDS = coupling_module.MATTER_FIELDS


def main():
    print("=" * 80)
    print("researcher PRIORITY #1: COMBINED RESONANCE + COUPLING OPTIMIZATION")
    print("=" * 80)
    print("\nObjective: Find parameter 'sweet spots' (μ*, λ*) where:")
    print("  • Geometric resonance exists (avoided crossing)")
    print("  • Matter-geometry coupling is strong (|⟨f|H_int|i⟩| >> 0)")
    print("  • Driven rate exceeds decoherence (Γ_driven >> γ)")
    print("\nThis is the critical path to overcoming impedance mismatch.\n")
    
    # ========================================================================
    # 1. Build test network
    # ========================================================================
    network = SpinNetwork()
    nodes = [network.add_node(i) for i in range(4)]
    edges = [
        (0, 1, 1.0), (0, 2, 1.0), (0, 3, 1.0),
        (1, 2, 0.5), (1, 3, 0.5), (2, 3, 0.5)
    ]
    for (i, j, spin) in edges:
        network.add_edge(i, j, spin)

    print(f"Test network: {len(network.nodes)} nodes, {len(network.edges)} edges\n")
    # ========================================================================
    # 2. Parameter sweep (wider range per researcher recommendation)
    # ========================================================================
    print("Parameter sweep configuration:")
    print("  μ range: [0.001, 3.0] (extended from [0.01, 1.0])")
    print("  μ resolution: 150 points (vs 100 previously)")
    print("  λ range: [1e-8, 1e-4] (broader than before)")
    print("  λ samples: 15 per resonance")
    print("  Gap threshold: 1e-36 J (slightly relaxed)\n")
    
    mu_values = np.linspace(0.001, 3.0, 150)
    
    # ========================================================================
    # 3. Run combined optimization
    # ========================================================================
    print("Running combined optimization...")
    print("(This will take a few moments as we optimize λ at each resonance)\n")
    
    results = combined_resonance_coupling_search(
        network,
        mu_values,
        MATTER_FIELDS,
        lambda_range=(1e-8, 1e-4),
        n_lambda=15,
        min_gap_threshold=1e-36,
        dim=32
    )
    
    # ========================================================================
    # 4. Visualize and analyze results
    # ========================================================================
    if len(results) > 0:
        print(f"\n{'=' * 80}")
        print("RESULTS VISUALIZATION")
        print("=" * 80)
        
        # Generate plots
        import os
        os.makedirs("outputs", exist_ok=True)
        plot_resonant_coupling_map(results)
        
        # Analyze top candidates
        print()
        analyze_top_candidates(results, gamma=0.01, n_top=5)
        
        # ====================================================================
        # 5. Key findings summary
        # ====================================================================
        print(f"\n{'=' * 80}")
        print("KEY FINDINGS")
        print("=" * 80)
        
        promising = [r for r in results if r.driven_rate > 0.01]
        
        if len(promising) > 0:
            best = promising[0]
            print(f"\n✓ SUCCESS: Found {len(promising)} promising sweet spot(s)!")
            print(f"\nBest candidate:")
            print(f"  Matter field: {best.field_type}")
            print(f"  μ* = {best.mu:.4f}")
            print(f"  λ* = {best.lambda_opt:.3e}")
            print(f"  Γ_driven = {best.driven_rate:.2e} Hz")
            print(f"  Γ_driven/γ = {best.driven_rate/0.01:.2e} (SNR)")
            print(f"\nThis represents a {best.driven_rate/1e-186:.2e}× enhancement over")
            print(f"non-resonant coupling from Direction #4!")
        else:
            print("\n⚠️  No promising sweet spots found with current parameters.")
            print("\nPossible reasons:")
            print("  • Tetrahedral topology may not support strong resonances")
            print("  • Need external field perturbation to induce mixing")
            print("  • λ range may not include optimal values")
            print("\nRecommended next steps:")
            print("  1. Try different topologies (cubic, octahedral)")
            print("  2. Add weak external field (breaks degeneracies)")
            print("  3. Extend λ range to [1e-10, 1e-2]")
            print("  4. Test non-uniform spin distributions")
        
        print(f"\n{'=' * 80}")
        print("INTERPRETATION")
        print("=" * 80)
        print("\nThe combined optimization approach addresses the key challenge:")
        print("  • Direction #3 alone: finds resonances, but doesn't guarantee strong coupling")
        print("  • Direction #4 alone: optimizes coupling, but misses resonant enhancement")
        print("  • Combined: identifies (μ*, λ*) pairs where BOTH conditions hold")
        print("\nThis is the critical path to observable macroscopic LQG effects.")
        
    else:
        print(f"\n{'=' * 80}")
        print("NO RESULTS FOUND")
        print("=" * 80)
        print("\n⚠️  No resonances detected in the μ sweep.")
        print("\nDiagnostic steps:")
        print("  1. Check gap threshold (current: 1e-36 J)")
        print("  2. Verify network topology (tetrahedral may be too simple)")
        print("  3. Add external field to induce level mixing")
        print("  4. Try logarithmic μ grid near suspected transitions")
    
    print(f"\n{'=' * 80}")
    print("NEXT STEPS (researcher recommendations)")
    print("=" * 80)
    print("\n1. ⏳ Driven response curves (Rabi-like lineshapes)")
    print("2. ⏳ Systematic topology study (cubic, octahedral, complex)")
    print("3. ⏳ HPC parameter sweep infrastructure (Direction #5)")
    print("4. ⏳ Experimental design based on best sweet spots")
    print("=" * 80)


if __name__ == "__main__":
    main()
