"""
Research Direction #3: Critical and Resonant Effects

Search for quantum geometric phase transitions, resonances, and parameter regimes
where small control inputs produce large macroscopic geometric responses.
"""

from .resonance_search import (
    GeometricHamiltonian,
    ResonanceSearcher,
    detect_avoided_crossings,
    demonstrate_resonance_search,
)

__all__ = [
    'GeometricHamiltonian',
    'ResonanceSearcher',
    'detect_avoided_crossings',
    'demonstrate_resonance_search',
]
