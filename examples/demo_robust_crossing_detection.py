"""
Demo: Robust crossing detection with eigenvector tracking.

Compares old detection (gap-only) vs new detection (eigenvector tracking).

Usage:
    python examples/demo_robust_crossing_detection.py
"""

import numpy as np
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.spin_network import SpinNetwork, SpinNetworkEdge
from src.core.constants import L_PLANCK

# Import module with numeric prefix using importlib
import importlib
resonance_module = importlib.import_module('src.03_critical_effects.resonance_search')
ResonanceSearcher = resonance_module.ResonanceSearcher
detect_avoided_crossings = resonance_module.detect_avoided_crossings
plot_spaghetti_diagram = resonance_module.plot_spaghetti_diagram
compute_eigenvector_overlap_matrix = resonance_module.compute_eigenvector_overlap_matrix


def create_test_network():
    """Create a simple test network (triangle)."""
    network = SpinNetwork()
    
    # Add nodes
    for i in range(3):
        network.add_node(i)
    
    # Add edges (triangle)
    network.add_edge(0, 1, spin=1.0)
    network.add_edge(1, 2, spin=1.0)
    network.add_edge(2, 0, spin=1.0)
    
    return network


def demo_comparison():
    """
    Compare old vs new crossing detection.
    """
    print("\n" + "=" * 80)
    print("DEMO: Robust Crossing Detection with Eigenvector Tracking")
    print("=" * 80)
    
    # Create network
    print("\nCreating test network (triangle)...")
    network = create_test_network()
    print(f"✓ Network: {len(network.nodes)} nodes, {len(network.edges)} edges")
    
    # Create searcher
    searcher = ResonanceSearcher(network)
    
    # Sweep polymer parameter
    print("\nSweeping polymer parameter μ ∈ [0.1, 2.0]...")
    print("(Computing eigenvectors for tracking...)")
    
    mu_values = np.linspace(0.1, 2.0, 100)  # Fine grid
    mu_vals, energies, eigenvecs = searcher.sweep_polymer_parameter(
        mu_values=mu_values,
        external_field=0.0,
        store_eigenvectors=True
    )
    
    print(f"✓ Computed {len(mu_values)} parameter points")
    print(f"  Spectrum dimension: {energies.shape[1]} levels")
    
    # OLD METHOD: Gap-only detection
    print("\n" + "-" * 80)
    print("OLD METHOD: Gap-only detection")
    print("-" * 80)
    
    crossings_old = detect_avoided_crossings(
        parameter_values=mu_vals,
        energy_spectra=energies,
        min_gap_threshold=0.1,
        eigenvector_sequence=None,  # Don't use eigenvector tracking
        use_eigenvector_tracking=False
    )
    
    print(f"Found {len(crossings_old)} crossings (gap-only)")
    
    # Show distribution
    if len(crossings_old) > 0:
        gaps = [c.min_gap for c in crossings_old]
        print(f"  Gap range: [{min(gaps):.3e}, {max(gaps):.3e}]")
        print(f"  Median gap: {np.median(gaps):.3e}")
    
    # NEW METHOD: Eigenvector tracking
    print("\n" + "-" * 80)
    print("NEW METHOD: Eigenvector tracking")
    print("-" * 80)
    
    crossings_new = detect_avoided_crossings(
        parameter_values=mu_vals,
        energy_spectra=energies,
        min_gap_threshold=0.1,
        eigenvector_sequence=eigenvecs,
        use_eigenvector_tracking=True,
        min_parameter_separation=0.05  # Filter close duplicates
    )
    
    print(f"Found {len(crossings_new)} crossings (with eigenvector tracking)")
    
    # Show distribution
    if len(crossings_new) > 0:
        gaps = [c.min_gap for c in crossings_new]
        mixings = [c.eigenvector_mixing for c in crossings_new]
        print(f"  Gap range: [{min(gaps):.3e}, {max(gaps):.3e}]")
        print(f"  Median gap: {np.median(gaps):.3e}")
        print(f"  Eigenvector mixing range: [{min(mixings):.3f}, {max(mixings):.3f}]")
        print(f"  Median mixing: {np.median(mixings):.3f}")
    
    # Comparison
    print("\n" + "=" * 80)
    print("COMPARISON")
    print("=" * 80)
    
    reduction_factor = len(crossings_old) / len(crossings_new) if len(crossings_new) > 0 else float('inf')
    print(f"\nOld method: {len(crossings_old)} crossings")
    print(f"New method: {len(crossings_new)} crossings")
    print(f"Reduction: {reduction_factor:.1f}× fewer crossings")
    
    if len(crossings_new) > 0:
        print(f"\nInterpretation:")
        print(f"  - Old method overcounts by detecting numerical noise")
        print(f"  - New method filters false positives using eigenvector overlap")
        print(f"  - True crossings show eigenvector mixing > 0.1")
    
    # Show top 5 strongest crossings
    if len(crossings_new) > 0:
        print(f"\nTop 5 Strongest Crossings (by mixing):")
        sorted_crossings = sorted(crossings_new, key=lambda c: c.eigenvector_mixing, reverse=True)
        
        for i, crossing in enumerate(sorted_crossings[:5], 1):
            print(f"{i}. μ={crossing.parameter_value:.3f}, "
                  f"levels ({crossing.level1_idx},{crossing.level2_idx}), "
                  f"gap={crossing.min_gap:.3e}, "
                  f"mixing={crossing.eigenvector_mixing:.3f}")
    
    # Visualize
    print(f"\nGenerating spaghetti diagram...")
    Path("outputs").mkdir(exist_ok=True)
    
    plot_spaghetti_diagram(
        parameter_values=mu_vals,
        energy_spectra=energies,
        crossings=crossings_new,
        parameter_name="μ (polymer parameter)",
        output_path="outputs/spaghetti_robust.png"
    )
    
    print(f"✓ Saved to outputs/spaghetti_robust.png")
    
    # Statistics
    print("\n" + "=" * 80)
    print("STATISTICS")
    print("=" * 80)
    
    print(f"\nFalse positive rate: {(len(crossings_old) - len(crossings_new)) / len(crossings_old) * 100:.1f}%")
    print(f"  (assuming new method is ground truth)")
    
    if len(crossings_new) > 0:
        true_crossings = [c for c in crossings_new if c.is_strong_resonance()]
        print(f"\nStrong resonances (gap < 0.1, |dgap/dμ| > 1): {len(true_crossings)}")
        print(f"  → {len(true_crossings) / len(crossings_new) * 100:.1f}% of detected crossings")


def demo_eigenvector_continuity():
    """
    Visualize eigenvector overlap matrices.
    """
    print("\n" + "=" * 80)
    print("DEMO: Eigenvector Continuity Tracking")
    print("=" * 80)
    
    network = create_test_network()
    searcher = ResonanceSearcher(network)
    
    mu_values = np.linspace(0.5, 1.5, 20)  # Coarse grid for visualization
    mu_vals, energies, eigenvecs = searcher.sweep_polymer_parameter(
        mu_values=mu_values,
        store_eigenvectors=True
    )
    
    print(f"\nComputed {len(mu_values)} parameter points")
    
    # Compute overlap matrices (already imported at top)
    
    print(f"\nOverlap matrices between consecutive steps:")
    print(f"(Diagonal dominant = continuous evolution, off-diagonal = crossing)")
    
    for k in range(min(5, len(eigenvecs) - 1)):
        overlap = compute_eigenvector_overlap_matrix(eigenvecs[k], eigenvecs[k+1])
        
        print(f"\nStep {k} → {k+1} (μ={mu_vals[k]:.3f} → {mu_vals[k+1]:.3f}):")
        print(f"  Diagonal: {np.diag(overlap)[:5]}")  # First 5 levels
        print(f"  Max off-diagonal: {np.max(overlap - np.diag(np.diag(overlap))):.3f}")
        
        if np.max(overlap - np.diag(np.diag(overlap))) > 0.3:
            print(f"  ⚠️  Strong mixing detected!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Robust crossing detection demo")
    parser.add_argument('--mode', choices=['comparison', 'continuity', 'all'],
                       default='comparison',
                       help='Demo mode')
    
    args = parser.parse_args()
    
    Path("outputs").mkdir(exist_ok=True)
    
    if args.mode == 'comparison' or args.mode == 'all':
        demo_comparison()
    
    if args.mode == 'continuity' or args.mode == 'all':
        demo_eigenvector_continuity()
    
    print("\n" + "=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
