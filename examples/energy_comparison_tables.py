"""
Energy vs. Curvature Scaling Tables
====================================

Reproduces the fundamental energy-curvature relationship from Einstein's equations
and demonstrates required energy for different reduction factors.

This script generates the tables referenced in the research proposal showing
how even massive reduction factors (10²⁴) still leave enormous energy requirements.

Author: LQG Macroscopic Coherence Research Team
Date: October 2025
Status: Research prototype
"""

import numpy as np
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from core.constants import (
    C, G, RHO_PER_CURVATURE, MEGATON_TNT,
    energy_in_context
)

def energy_for_bubble(radius_m: float, reduction_factor: float = 1.0) -> float:
    """
    Calculate energy required for warp bubble of given radius.
    
    Uses crude order-of-magnitude model:
    - Curvature scale R ~ 1/r²
    - Energy density ρ ~ (c⁴/8πG) × R
    - Total energy E ~ ρ × Volume ~ ρ × r³ ~ (c⁴/8πG) × r
    
    Parameters:
    -----------
    radius_m : float
        Bubble radius in meters
    reduction_factor : float
        Reduction in effective energy density (1.0 = no reduction)
        
    Returns:
    --------
    float : Required energy in joules
    """
    # Fundamental constant
    fundamental_scale = C**4 / (8 * np.pi * G)  # J/m
    
    # Crude estimate (within order of magnitude)
    # More precise: E ~ (4π/3) × r × (c⁴/8πG) = (r/6) × (c⁴/G)
    energy_classical = (4 * np.pi / 3) * radius_m * fundamental_scale
    
    # Apply reduction factor
    energy_effective = energy_classical / reduction_factor
    
    return energy_effective

def print_energy_table():
    """Print table of energies for different radii and reduction factors."""
    
    print("=" * 100)
    print("ENERGY REQUIRED FOR WARP BUBBLE (JOULES)")
    print("=" * 100)
    print("\nFrom Einstein equation: E ~ r × (c⁴/8πG) / f_reduction")
    print()
    
    # Radii to test
    radii_m = [1, 10, 100, 1000]
    
    # Reduction factors to test
    reduction_factors = {
        'No reduction': 1.0,
        '×10⁻⁶ reduction': 1e6,
        '×10⁻¹² reduction': 1e12,
        '×10⁻²⁴ reduction': 1e24,
    }
    
    # Header
    header = f"{'Radius':<15s} | "
    for name in reduction_factors.keys():
        header += f"{name:<20s} | "
    print(header)
    print("-" * 100)
    
    # Rows
    for r in radii_m:
        row = f"{r:6.0f} m       | "
        for reduction in reduction_factors.values():
            E = energy_for_bubble(r, reduction)
            row += f"{E:18.2e} J | "
        print(row)
    
    print("=" * 100)
    print()
    
    # Context examples
    print("CONTEXT:")
    print("-" * 100)
    print(f"1 megaton TNT                = {MEGATON_TNT:.2e} J")
    E10 = energy_for_bubble(10, 1e24)
    print(f"10m bubble, 10²⁴ reduction   = {E10:.2e} J")
    megatons = E10 / MEGATON_TNT
    print(f"                              ≈ {megatons:.0f} megatons TNT")
    print("-" * 100)
    print()

def print_detailed_analysis():
    """More detailed breakdown for specific scenarios."""
    
    print("=" * 100)
    print("DETAILED ENERGY ANALYSIS")
    print("=" * 100)
    print()
    
    # Spacecraft-scale bubble
    r_spacecraft = 10  # meters (small spacecraft)
    
    print(f"Scenario: Small spacecraft warp bubble (r = {r_spacecraft} m)")
    print("-" * 100)
    
    reductions = [1.0, 1e6, 1e12, 1e18, 1e24, 1e30]
    
    for f_red in reductions:
        E = energy_for_bubble(r_spacecraft, f_red)
        context = energy_in_context(E)
        
        if f_red == 1.0:
            print(f"Classical (no reduction):        {E:.2e} J = {context}")
        else:
            print(f"With ×{f_red:.0e} reduction:   {E:.2e} J = {context}")
    
    print("=" * 100)
    print()
    
    # What reduction is needed for practical energy?
    print("REQUIRED REDUCTION FACTORS FOR PRACTICAL ENERGIES")
    print("-" * 100)
    
    E_classical = energy_for_bubble(r_spacecraft, 1.0)
    
    practical_energies = {
        'Power plant (1 day)': 8.64e13,  # 1 GW × 24 hr
        'Large rocket': 1e12,  # ~Starship fuel equivalent
        'Car fuel tank': 1.5e9,
        'Household daily': 10e6,  # 10 kWh
    }
    
    for scenario, E_target in practical_energies.items():
        f_needed = E_classical / E_target
        print(f"{scenario:25s}: needs ×{f_needed:.2e} reduction")
    
    print("=" * 100)
    print()

def compare_to_known_physics():
    """Compare polymer LQG to other physics reductions."""
    
    print("=" * 100)
    print("COMPARISON TO KNOWN ENERGY REDUCTIONS IN PHYSICS")
    print("=" * 100)
    print()
    
    reductions = {
        'Superconductivity (electrical resistance)': 'infinite (R → 0)',
        'Superfluidity (viscosity)': 'infinite (η → 0)',
        'Bose-Einstein condensate (temperature)': '~10⁶ (from room temp to nK)',
        'Laser (photon coherence length)': '~10⁶ (compared to LED)',
        'Required for practical warp (10m)': '~10³⁰ (very rough estimate)',
    }
    
    for phenomenon, reduction in reductions.items():
        print(f"{phenomenon:45s}: {reduction}")
    
    print()
    print("Key observation:")
    print("  - Physics has precedent for large (10⁶) reductions via coherence/phase transitions")
    print("  - But warp drive needs ~10³⁰ reduction - vastly larger than any known effect")
    print("  - This is the fundamental challenge polymer LQG must solve")
    print("=" * 100)
    print()

def scaling_law_derivation():
    """Show derivation of E ~ r scaling."""
    
    print("=" * 100)
    print("DERIVATION OF ENERGY-RADIUS SCALING")
    print("=" * 100)
    print()
    
    print("From Einstein equation: G_μν = (8πG/c⁴) T_μν")
    print()
    print("Order of magnitude:")
    print("  - Curvature scale:      R ~ 1/r²")
    print("  - Energy density:       ρ ~ (c⁴/8πG) × R ~ (c⁴/8πG) × (1/r²)")
    print("  - Volume:               V ~ r³")
    print("  - Total energy:         E ~ ρ × V ~ (c⁴/8πG) × (1/r²) × r³ ~ r × (c⁴/8πG)")
    print()
    print("Result: E ∝ r (energy scales linearly with bubble radius)")
    print()
    print("Implications:")
    print("  - Larger bubbles require proportionally more energy")
    print("  - No 'economy of scale' from classical GR")
    print("  - Reduction factor f must be enormous (10³⁰⁺) for any practical r")
    print("=" * 100)
    print()

def main():
    """Run all analyses."""
    
    print("\n")
    print("╔" + "═" * 98 + "╗")
    print("║" + " " * 25 + "ENERGY-CURVATURE SCALING ANALYSIS" + " " * 40 + "║")
    print("║" + " " * 24 + "LQG Macroscopic Coherence Framework" + " " * 39 + "║")
    print("╚" + "═" * 98 + "╝")
    print()
    
    # Main energy table
    print_energy_table()
    
    # Detailed spacecraft analysis
    print_detailed_analysis()
    
    # Comparison to known physics
    compare_to_known_physics()
    
    # Scaling law derivation
    scaling_law_derivation()
    
    print("\n" + "=" * 100)
    print("CONCLUSIONS")
    print("=" * 100)
    print()
    print("1. Classical GR requires ENORMOUS energies for macroscopic curvature")
    print("2. Even 10²⁴ reduction leaves 10m bubble needing ~50,000 megatons")
    print("3. Practical warp drive needs ~10³⁰ reduction - unprecedented in physics")
    print("4. Polymer LQG must provide mechanism for this reduction")
    print("5. This repository aims to derive whether such reduction is possible")
    print()
    print("=" * 100)
    print()

if __name__ == "__main__":
    main()
