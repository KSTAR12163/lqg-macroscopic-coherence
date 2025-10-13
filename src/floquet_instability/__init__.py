"""
Floquet instability scanning utilities.

This package provides tools to scan for non-perturbative amplification under
strong periodic driving, with optional PT-symmetric gain/loss exploration.

Note: For strictly Hermitian, closed-system Hamiltonians H(t), the Floquet
monodromy is unitary and does not yield |eigenvalue| != 1. Exponential growth
requires effective non-Hermitian terms (gain/loss) or open-system pumping.
"""

__all__ = [
    "floquet_scan_two_level",
]
