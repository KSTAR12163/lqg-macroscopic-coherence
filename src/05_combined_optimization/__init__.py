"""
Combined optimization module (Direction #5 foundation).

Implements Gemini 2.5 Pro's key recommendation: find parameter "sweet spots"
where geometric resonances enhance matter-geometry coupling strength.
"""

from .resonant_coupling_search import (
    ResonantCouplingPoint,
    compute_coupling_at_resonance,
    combined_resonance_coupling_search,
    plot_resonant_coupling_map,
    analyze_top_candidates,
    demonstrate_combined_optimization
)

__all__ = [
    'ResonantCouplingPoint',
    'compute_coupling_at_resonance',
    'combined_resonance_coupling_search',
    'plot_resonant_coupling_map',
    'analyze_top_candidates',
    'demonstrate_combined_optimization',
]
