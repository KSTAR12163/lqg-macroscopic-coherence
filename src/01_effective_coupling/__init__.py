"""LQG Macroscopic Coherence Framework - Effective coupling derivation."""

from .derive_effective_coupling import (
    EffectiveCouplingCalculator,
    EffectiveCouplingResult,
    demonstrate_effective_coupling,
    parameter_space_scan
)

__all__ = [
    'EffectiveCouplingCalculator',
    'EffectiveCouplingResult',
    'demonstrate_effective_coupling',
    'parameter_space_scan'
]
