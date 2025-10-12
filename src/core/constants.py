"""
Physical Constants and Fundamental Scales
==========================================

Defines fundamental constants for LQG macroscopic coherence calculations.
All values in SI units unless otherwise specified.

Author: LQG Macroscopic Coherence Research Team
Date: October 2025
Status: Research prototype
"""

import numpy as np
import scipy.constants as const

# ============================================================================
# Fundamental Physical Constants
# ============================================================================

# Speed of light
C = const.c  # m/s

# Gravitational constant
G = const.G  # m^3 kg^-1 s^-2

# Reduced Planck constant
HBAR = const.hbar  # J·s

# Boltzmann constant
K_B = const.k  # J/K

# Planck length
L_PLANCK = np.sqrt(HBAR * G / C**3)  # m ≈ 1.616 × 10^-35 m

# Planck mass
M_PLANCK = np.sqrt(HBAR * C / G)  # kg ≈ 2.176 × 10^-8 kg

# Planck time
T_PLANCK = L_PLANCK / C  # s ≈ 5.391 × 10^-44 s

# Planck energy
E_PLANCK = M_PLANCK * C**2  # J ≈ 1.956 × 10^9 J

# ============================================================================
# Einstein Field Equation Scale
# ============================================================================

# Critical energy density per unit curvature (J/m³ per 1/m²)
# From G_μν = (8πG/c⁴) T_μν
EINSTEIN_COUPLING = 8 * np.pi * G / C**4  # s²/kg·m ≈ 2.075 × 10^-43

# Energy density per unit curvature (inverse of Einstein coupling)
RHO_PER_CURVATURE = C**4 / (8 * np.pi * G)  # J/m³ per (1/m²) ≈ 4.82 × 10^42

# For reference: 1 megaton TNT
MEGATON_TNT = 4.184e15  # J

# ============================================================================
# LQG-Specific Constants
# ============================================================================

# Barbero-Immirzi parameter (from LQG black hole entropy)
GAMMA_IMMIRZI = 0.2375  # dimensionless

# Polymer parameter typical scale
MU_TYPICAL = 0.7  # dimensionless (phenomenological optimum)

# Area quantum (minimum area eigenvalue for j=1/2)
# A_min = 4π√3 γ ℓ_P²
AREA_QUANTUM = 4 * np.pi * np.sqrt(3) * GAMMA_IMMIRZI * L_PLANCK**2  # m²

# Volume quantum (minimum volume eigenvalue)
# V_min ≈ 0.365 γ³/² ℓ_P³ (approximate, depends on triangulation)
VOLUME_QUANTUM = 0.365 * GAMMA_IMMIRZI**(3/2) * L_PLANCK**3  # m³

# ============================================================================
# Coherence Scales (exploratory estimates)
# ============================================================================

# Decoherence time scale for quantum geometry (highly speculative)
# Order of magnitude: could range from Planck time to macroscopic times
TAU_DECOHERENCE_LOWER = T_PLANCK  # s (absolute minimum)
TAU_DECOHERENCE_UPPER = 1e-6  # s (optimistic upper bound for protected states)

# Coherence length scale (similarly speculative)
LAMBDA_COHERENCE_LOWER = L_PLANCK  # m (minimum)
LAMBDA_COHERENCE_UPPER = 1e-9  # m (nanoscale, very optimistic)

# ============================================================================
# Energy Comparison Scales
# ============================================================================

# Characteristic energy scales for context
ENERGY_SCALES = {
    'household_electricity_day': 10e6,  # J (10 kWh)
    'car_fuel_tank': 1.5e9,  # J (gasoline, ~10 gallons)
    'large_power_plant_day': 8.64e13,  # J (1 GW × 24 hours)
    'hiroshima_bomb': 6.3e13,  # J (15 kilotons TNT)
    'tsar_bomba': 2.1e17,  # J (50 megatons TNT)
    'global_annual_energy': 6e20,  # J (≈600 EJ/year, 2020 estimate)
}

# ============================================================================
# Numerical Precision Parameters
# ============================================================================

# Machine epsilon safety margin
EPSILON = np.finfo(float).eps

# Small and large epsilon for numerical stability
EPSILON_SMALL = 1e-100  # Small value to avoid division by zero
EPSILON_LARGE = 1e100  # Large value for capping

# Numerical tolerance for comparisons
TOL_ABSOLUTE = 1e-15
TOL_RELATIVE = 1e-12

# Maximum iterations for iterative algorithms
MAX_ITERATIONS = 10000

# Convergence criterion
CONVERGENCE_THRESHOLD = 1e-10

# ============================================================================
# Physical Bounds for Validation
# ============================================================================

# Minimum and maximum polymer parameter for numerical stability
MU_MIN = 1e-6  # Below this: classical limit, sinc(πμ) → 1
MU_MAX = 10.0  # Above this: strong quantum regime, may be unphysical

# SU(2) quantum number bounds
J_MIN = 0.5  # Minimum spin (fundamental representation)
J_MAX = 1000  # Practical upper bound for numerics
J_TYPICAL = 1.0  # Typical spin for phenomenological estimates

# Curvature scale bounds (1/m²)
R_MIN = 1 / (1e6)**2  # Very gentle curvature (1 km scale)
R_MAX = 1 / L_PLANCK**2  # Planck-scale curvature (maximum physical)

# Energy density bounds (J/m³)
RHO_MIN = 1e3  # Water-like density (~1000 kg/m³ × c²/geometric factor)
RHO_MAX = 1e17  # Nuclear density limit

# ============================================================================
# Utility Functions
# ============================================================================

def print_fundamental_scales():
    """Print fundamental scales for reference."""
    print("=" * 70)
    print("FUNDAMENTAL SCALES")
    print("=" * 70)
    print(f"Planck length:     {L_PLANCK:.3e} m")
    print(f"Planck mass:       {M_PLANCK:.3e} kg")
    print(f"Planck time:       {T_PLANCK:.3e} s")
    print(f"Planck energy:     {E_PLANCK:.3e} J")
    print()
    print(f"Einstein coupling: {EINSTEIN_COUPLING:.3e} s²/(kg·m)")
    print(f"ρ per unit R:      {RHO_PER_CURVATURE:.3e} J/m³ per (1/m²)")
    print()
    print(f"Area quantum:      {AREA_QUANTUM:.3e} m²")
    print(f"Volume quantum:    {VOLUME_QUANTUM:.3e} m³")
    print("=" * 70)

def energy_in_context(energy_joules: float) -> str:
    """
    Express energy in human-scale contexts.
    
    Parameters:
    -----------
    energy_joules : float
        Energy in joules
        
    Returns:
    --------
    str : Human-readable comparison
    """
    if energy_joules < 1e3:
        return f"{energy_joules:.2e} J (sub-kilojoule)"
    elif energy_joules < ENERGY_SCALES['household_electricity_day']:
        kj = energy_joules / 1e3
        return f"{kj:.2f} kJ"
    elif energy_joules < ENERGY_SCALES['car_fuel_tank']:
        kwh = energy_joules / 3.6e6
        return f"{kwh:.2f} kWh"
    elif energy_joules < ENERGY_SCALES['hiroshima_bomb']:
        car_tanks = energy_joules / ENERGY_SCALES['car_fuel_tank']
        return f"{car_tanks:.2f} car fuel tanks"
    elif energy_joules < ENERGY_SCALES['tsar_bomba']:
        megatons = energy_joules / MEGATON_TNT / 1e6
        kilotons = megatons * 1000
        return f"{kilotons:.2f} kilotons TNT"
    elif energy_joules < ENERGY_SCALES['global_annual_energy']:
        megatons = energy_joules / MEGATON_TNT / 1e6
        return f"{megatons:.2f} megatons TNT"
    else:
        years_global = energy_joules / ENERGY_SCALES['global_annual_energy']
        return f"{years_global:.2f} years of global energy consumption"

if __name__ == "__main__":
    # Print fundamental scales when run as script
    print_fundamental_scales()
    
    # Example energy comparisons
    print("\nENERGY SCALE EXAMPLES:")
    print("-" * 70)
    for scale_name, scale_energy in ENERGY_SCALES.items():
        print(f"{scale_name:30s}: {energy_in_context(scale_energy)}")
    print("-" * 70)
    
    # Warp bubble energy examples
    print("\nWARP BUBBLE ENERGY ESTIMATES:")
    print("-" * 70)
    radii = [1, 10, 100, 1000]  # meters
    for r in radii:
        # Crude estimate: E ~ (c⁴/8πG) × (1/r²) × (4πr³/3) ~ r × (c⁴/8πG)
        E_classical = r * C**4 / (8 * np.pi * G)
        print(f"r = {r:4d} m: {energy_in_context(E_classical)}")
    print("-" * 70)
