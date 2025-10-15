"""
Time-pulsed metric profiles for warp metrics.

Provides a pulsed Alcubierre-style metric wrapper with a smooth time envelope.
"""

import numpy as np
from typing import Callable
from .alcubierre_analytic import alcubierre_metric_analytic


def smooth_envelope(t: float, t0: float, t1: float, k: float = 4.0) -> float:
    """
    Smooth step envelope in time from 0 to 1 between t0 and t1.
    Uses a logistic-based blend for C^1 smoothness.
    """
    if t <= t0:
        return 0.0
    if t >= t1:
        return 1.0
    # scaled logistic blend
    s = (t - t0) / max(t1 - t0, 1e-9)
    return 1.0 / (1.0 + np.exp(-k * (s - 0.5)))


def pulsed_alcubierre_metric(v_s: float, R: float, sigma: float, t0: float, t1: float, k: float = 4.0) -> Callable:
    """
    Return a metric_fn(t,x,y,z) that applies a smooth time envelope to v_s: v_eff(t) = v_s * envelope(t).
    """
    def metric_fn(t: float, x: float, y: float, z: float):
        v_eff = v_s * smooth_envelope(t, t0, t1, k)
        return alcubierre_metric_analytic(t, x, y, z, v_eff, R, sigma)
    return metric_fn
