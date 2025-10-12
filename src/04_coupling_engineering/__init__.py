"""
Research Direction #4: Coupling Engineering (Impedance Matching)

Identify materials and field configurations that couple strongly to 
polymer-modified quantum geometry.
"""

from .matter_coupling import (
    MatterGeometryCoupling,
    MatterFieldType,
    compute_transition_rates,
    search_optimal_coupling,
    demonstrate_coupling_engineering,
)

__all__ = [
    'MatterGeometryCoupling',
    'MatterFieldType',
    'compute_transition_rates',
    'search_optimal_coupling',
    'demonstrate_coupling_engineering',
]
