"""
Demo: Systematic topology comparison (researcher Priority #1 - HIGHEST IMPACT).

Tests whether network structure determines coupling strength.
Goal: Find topologies with |⟨f|H_int|i⟩| ≥ 10^20× tetrahedral baseline.
"""

import numpy as np
import sys
from pathlib import Path
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.spin_network import SpinNetwork

import importlib
topo_module = importlib.import_module('src.06_topology_exploration.topology_generator')
combined_module = importlib.import_module('src.05_combined_optimization.resonant_coupling_search')
coupling_module = importlib.import_module('src.04_coupling_engineering.matter_coupling')

generate_topology_suite = topo_module.generate_topology_suite
print_topology_summary = topo_module.print_topology_summary
combined_resonance_coupling_search = combined_module.combined_resonance_coupling_search
MATTER_FIELDS = coupling_module.MATTER_FIELDS


def compare_topologies():
    """
    Systematic topology comparison.
    
    For each topology:
      1. Run combined resonance-coupling search
      2. Extract best coupling strength
      3. Compare to tetrahedral baseline
    """
    print("╔" + "=" * 78 + "╗")
    print("║ SYSTEMATIC TOPOLOGY COMPARISON - researcher Priority #1 (HIGHEST IMPACT)       ║")
    print("║ Goal: Find topologies with |⟨f|H_int|i⟩| ≥ 10²⁰× tetrahedral baseline     ║")
    print("╚" + "=" * 78 + "╝")
    
    # Generate topology suite
    print("\nGenerating topology suite...")
    suite = generate_topology_suite()
    print(f"  ✓ Generated {len(suite)} topologies")
    
    # Parameter setup
    mu_values = np.linspace(0.1, 2.0, 100)  # Reduced for speed
    matter_fields_subset = {
        'optical': MATTER_FIELDS['optical'],
    }
    
    print("\nParameter configuration:")
    print(f"  μ range: [{mu_values.min():.2f}, {mu_values.max():.2f}] × {len(mu_values)} points")
    print(f"  λ range: [1e-8, 1e-4] × 10 samples")
    print(f"  Matter fields: {list(matter_fields_subset.keys())}")
    print(f"  Density of states: ρ ~ 1/gap (α=1, physical)\n")
    
    # Store results
    results = {}
    baseline_coupling = None
    
    # Run comparison
    for topo_name, (network, info) in suite.items():
        print("\n" + "=" * 80)
        print_topology_summary(info)
        print("=" * 80)
        
        # Skip topologies with no edges
        if info.num_edges == 0:
            print("\n⚠️  Skipping topology with no edges")
            results[topo_name] = {
                'info': info,
                'num_candidates': 0,
                'best_coupling': 0.0,
                'best_rate': 0.0,
                'best_gap': np.inf
            }
            continue
        
        try:
            # Run combined optimization
            candidates = combined_resonance_coupling_search(
                network=network,
                mu_values=mu_values,
                matter_fields=matter_fields_subset,
                lambda_range=(1e-8, 1e-4),
                n_lambda=10,
                min_gap_threshold=1e-36,
                dim=32,
                rho_exponent=1.0  # Physical
            )
            
            if len(candidates) > 0:
                # Extract best coupling
                best = candidates[0]
                results[topo_name] = {
                    'info': info,
                    'best_candidate': best,
                    'num_candidates': len(candidates),
                    'best_coupling': best.coupling_strength,
                    'best_rate': best.driven_rate,
                    'best_gap': best.energy_gap
                }
                
                print(f"\n✓ Best candidate:")
                print(f"  μ* = {best.mu:.3f}, λ* = {best.lambda_opt:.3e}")
                print(f"  |⟨f|H_int|i⟩| = {best.coupling_strength:.3e} J")
                print(f"  Γ_driven = {best.driven_rate:.3e} Hz")
                print(f"  Gap = {best.energy_gap:.3e} J")
                
                # Track baseline (tetrahedral)
                if 'tetrahedral' in topo_name and baseline_coupling is None:
                    baseline_coupling = best.coupling_strength
                    print(f"  → BASELINE for comparison")
            else:
                print("\n⚠️  No candidates found (no resonances detected)")
                results[topo_name] = {
                    'info': info,
                    'best_candidate': None,
                    'num_candidates': 0,
                    'best_coupling': 0.0,
                    'best_rate': 0.0,
                    'best_gap': np.inf
                }
        
        except Exception as e:
            print(f"\n✗ Error processing {topo_name}: {e}")
            results[topo_name] = {
                'info': info,
                'error': str(e),
                'num_candidates': 0
            }
    
    # ========================================================================
    # Analysis and Comparison
    # ========================================================================
    
    print("\n\n" + "=" * 80)
    print("TOPOLOGY COMPARISON SUMMARY")
    print("=" * 80)
    
    # Sort by coupling strength
    valid_results = {k: v for k, v in results.items() if v['num_candidates'] > 0}
    
    if not valid_results:
        print("\n⚠️  No valid results to compare.")
        return results
    
    sorted_results = sorted(valid_results.items(), 
                           key=lambda x: x[1]['best_coupling'], 
                           reverse=True)
    
    print(f"\nTopologies ranked by coupling strength:")
    print(f"{'Rank':<6} {'Topology':<30} {'Coupling (J)':<15} {'Enhancement':<15} {'Resonances':<12}")
    print("-" * 80)
    
    for rank, (topo_name, data) in enumerate(sorted_results, 1):
        coupling = data['best_coupling']
        enhancement = coupling / baseline_coupling if baseline_coupling and baseline_coupling > 0 else 0.0
        num_res = data['num_candidates']
        
        print(f"{rank:<6} {topo_name:<30} {coupling:<15.3e} {enhancement:<15.3e} {num_res:<12}")
    
    # Check for acceptance criterion
    print("\n" + "=" * 80)
    print("ACCEPTANCE CRITERION (researcher)")
    print("=" * 80)
    print("\nGoal: Find topology with |M| ≥ 10²⁰× tetrahedral baseline")
    
    if baseline_coupling and baseline_coupling > 0:
        best_topo, best_data = sorted_results[0]
        best_coupling = best_data['best_coupling']
        enhancement = best_coupling / baseline_coupling
        
        print(f"\nBaseline (tetrahedral): |M| = {baseline_coupling:.3e} J")
        print(f"Best topology ({best_topo}): |M| = {best_coupling:.3e} J")
        print(f"Enhancement: {enhancement:.3e}×")
        
        if enhancement >= 1e20:
            print(f"\n✓ MILESTONE ACHIEVED: {enhancement:.2e}× ≥ 10²⁰×")
        elif enhancement >= 1e10:
            print(f"\n⚠️  SIGNIFICANT PROGRESS: {enhancement:.2e}× (continue optimization)")
        elif enhancement >= 10:
            print(f"\n⚠️  MODEST IMPROVEMENT: {enhancement:.2e}× (topology helps but insufficient)")
        else:
            print(f"\n✗ INSUFFICIENT: {enhancement:.2e}× << 10²⁰×")
            print("   → Topology alone may not solve impedance mismatch")
            print("   → Consider: external fields, different H_int operators, etc.")
    
    # Rate comparison
    print("\n" + "=" * 80)
    print("DRIVEN RATE COMPARISON")
    print("=" * 80)
    
    gamma = 0.01  # Decoherence rate
    print(f"\nDecoherence rate: γ = {gamma} Hz")
    print(f"Target: Γ_driven ≥ 10γ = {10*gamma} Hz\n")
    
    for rank, (topo_name, data) in enumerate(sorted_results[:5], 1):
        rate = data['best_rate']
        snr = rate / gamma
        
        if snr >= 10:
            status = "✓ OBSERVABLE"
        elif snr >= 0.1:
            status = "⚠️  MARGINAL"
        else:
            status = "✗ UNFEASIBLE"
        
        print(f"{rank}. {topo_name}: Γ = {rate:.3e} Hz, SNR = {snr:.3e} {status}")
    
    # Visualization
    plot_topology_comparison(results, baseline_coupling)
    
    return results


def plot_topology_comparison(results, baseline_coupling):
    """Visualize topology comparison results."""
    valid_results = {k: v for k, v in results.items() if v['num_candidates'] > 0}
    
    if not valid_results:
        print("\nNo results to plot.")
        return
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Sort by coupling
    sorted_items = sorted(valid_results.items(), 
                         key=lambda x: x[1]['best_coupling'],
                         reverse=True)
    
    names = [k for k, _ in sorted_items]
    couplings = [v['best_coupling'] for _, v in sorted_items]
    rates = [v['best_rate'] for _, v in sorted_items]
    
    # Plot 1: Coupling strength
    bars1 = ax1.barh(names, couplings, color='steelblue', alpha=0.7)
    ax1.set_xlabel('Coupling Strength |⟨f|H_int|i⟩| (J)', fontsize=11)
    ax1.set_title('Topology Comparison: Coupling Strength', fontsize=12, fontweight='bold')
    ax1.set_xscale('log')
    ax1.grid(True, alpha=0.3, axis='x')
    
    # Highlight baseline
    if baseline_coupling:
        ax1.axvline(baseline_coupling, color='red', linestyle='--', 
                   linewidth=2, alpha=0.7, label='Tetrahedral baseline')
        ax1.legend()
    
    # Plot 2: Driven rate
    bars2 = ax2.barh(names, rates, color='darkorange', alpha=0.7)
    ax2.set_xlabel('Driven Rate Γ_driven (Hz)', fontsize=11)
    ax2.set_title('Topology Comparison: Transition Rate', fontsize=12, fontweight='bold')
    ax2.set_xscale('log')
    ax2.grid(True, alpha=0.3, axis='x')
    
    # Observability threshold
    gamma = 0.01
    ax2.axvline(10 * gamma, color='green', linestyle='--',
               linewidth=2, alpha=0.7, label='Observability (10γ)')
    ax2.legend()
    
    plt.tight_layout()
    output_path = "outputs/topology_comparison.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n✓ Saved comparison plot to {output_path}")
    plt.close()


def main():
    """Run topology comparison."""
    results = compare_topologies()
    
    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    
    # Check if any topology shows significant improvement
    valid_results = {k: v for k, v in results.items() if v['num_candidates'] > 0}
    
    if valid_results:
        sorted_results = sorted(valid_results.items(),
                               key=lambda x: x[1]['best_coupling'],
                               reverse=True)
        
        best_topo, best_data = sorted_results[0]
        
        # If tetrahedral is best, topology didn't help
        if 'tetrahedral' in best_topo:
            print("\n1. ⚠️  Tetrahedral remains best → topology alone insufficient")
            print("2. Try: External field perturbation (researcher Priority #2)")
            print("3. Try: Different H_int operators (volume vs area vs curvature)")
            print("4. Try: Larger coupling constants λ ∈ [1e-6, 1e-2]")
        else:
            print(f"\n1. ✓ {best_topo} outperforms tetrahedral!")
            print(f"2. Deep dive: Optimize (μ, λ, h) for {best_topo}")
            print("3. Test: Driven response curves on this topology")
            print("4. Explore: Similar topologies (variations on best structure)")
    
    print("\n✓ Topology comparison complete!")


if __name__ == "__main__":
    main()
