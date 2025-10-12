"""
Core mathematical and physical constants for LQG coherence research.
"""

from .constants import (
    # Physical constants
    C, G, HBAR, K_B,
    
    # Planck scales
    L_PLANCK, M_PLANCK, T_PLANCK, E_PLANCK,
    
    # LQG parameters
    GAMMA_IMMIRZI,
    
    # Energy-curvature relation
    EINSTEIN_COUPLING,
    RHO_PER_CURVATURE,
    
    # Parameter ranges
    MU_MIN, MU_MAX, MU_TYPICAL,
    J_MIN, J_MAX, J_TYPICAL,
    
    # Numerical tolerances
    EPSILON_SMALL, EPSILON_LARGE,
    
    # Utility functions
    print_fundamental_scales,
    energy_in_context,
)

from .spin_network import (
    # SU(2) utilities
    wigner_3j, wigner_6j,
    spin_dimension, is_triangle,
    
    # Spin network classes
    SpinNetwork, SpinNetworkNode, SpinNetworkEdge,
    
    # Polymer corrections
    polymer_correction_sinc,
    polymer_enhancement_factor,
    effective_planck_length,
    
    # Volume/area operators
    volume_eigenvalue_tetrahedron,
    
    # Coarse-graining
    average_spin_in_region,
    coarse_grain_spin_network,
)

__all__ = [
    'C', 'G', 'HBAR', 'K_B',
    'L_PLANCK', 'M_PLANCK', 'T_PLANCK', 'E_PLANCK',
    'GAMMA_IMMIRZI',
    'EINSTEIN_COUPLING', 'RHO_PER_CURVATURE',
    'MU_MIN', 'MU_MAX', 'MU_TYPICAL',
    'J_MIN', 'J_MAX', 'J_TYPICAL',
    'EPSILON_SMALL', 'EPSILON_LARGE',
    'print_fundamental_scales', 'energy_in_context',
    # Spin network exports
    'wigner_3j', 'wigner_6j', 'spin_dimension', 'is_triangle',
    'SpinNetwork', 'SpinNetworkNode', 'SpinNetworkEdge',
    'polymer_correction_sinc', 'polymer_enhancement_factor', 'effective_planck_length',
    'volume_eigenvalue_tetrahedron',
    'average_spin_in_region', 'coarse_grain_spin_network',
]
