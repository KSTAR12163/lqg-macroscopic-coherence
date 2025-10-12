"""
Example: Demonstrate coarse-graining from Planck scale to macroscopic scale.

This script shows how polymer corrections and coherence combine to give
the effective coupling f_eff at different length scales.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Note: Import using importlib to handle numeric directory names
import importlib
coarse_graining_module = importlib.import_module('src.01_effective_coupling.coarse_graining')

from src.core.constants import L_PLANCK, print_fundamental_scales

# Extract functions from the imported module
demonstrate_coarse_graining = coarse_graining_module.demonstrate_coarse_graining
compute_f_eff_first_principles = coarse_graining_module.compute_f_eff_first_principles
RenormalizationGroup = coarse_graining_module.RenormalizationGroup


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("EXAMPLE: Coarse-Graining and f_eff Derivation")
    print("=" * 80)
    print("\nThis demonstrates Research Direction #1: deriving f_eff from first principles")
    print("by coarse-graining polymer corrections from Planck scale to macroscopic scale.\n")
    
    print_fundamental_scales()
    print()
    
    # Run full demonstration
    demonstrate_coarse_graining()
    
    print("\n" + "=" * 80)
    print("INTERPRETATION:")
    print("=" * 80)
    print("""
The key insight:
    
At Planck scale, polymer corrections give sinc(πμj) ≈ 0.6-0.9 modification.
But at macroscopic scales, we must average over ~(L/ℓ_P)³ quantum DOF.

Without macroscopic coherence:
    f_eff ≈ (polymer correction) / √N_DOF
    → f_eff ~ 10^-60 at 1 meter scale
    → Energy reduction ~ 10^60 (INSUFFICIENT for warp drive!)

With full macroscopic coherence:
    f_eff ≈ (polymer correction) × 1
    → f_eff ~ 0.6-0.9
    → Energy reduction ~ 1.1-1.7× (still classical-scale)

CONCLUSION:
    Coherence is necessary but not sufficient. We need:
    1. Macroscopic coherence to avoid 1/√N suppression
    2. PLUS additional enhancement mechanism (resonance, critical effects)
       to push f_eff down by many orders of magnitude
    
The RG flow plots show how f_eff evolves across scales. The challenge is
to find parameter regimes where f_eff << 1 at macroscopic scales.
""")
    print("=" * 80)
