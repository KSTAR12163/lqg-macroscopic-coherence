r"""
Generic geodesic integration for arbitrary metric functions using numerical Christoffels.

Provides:
- project_to_null_cone: exact solve for k^t given spatial k and metric g
- null_tangent: build initial null tangent for a given direction
- integrate_geodesic: solve geodesic ODEs with solve_ivp
- compute_anec_generic: integrate T_{\mu\nu} k^\mu k^\nu along path
"""

import numpy as np
from typing import Callable, Tuple, Dict
from scipy.integrate import solve_ivp

from .stress_energy import (
    compute_metric_derivatives,
    compute_christoffel_symbols,
    compute_einstein_tensor,
    einstein_to_stress_energy,
)


def project_to_null_cone(k: np.ndarray, g: np.ndarray) -> np.ndarray:
    r"""
    Enforce null condition by solving for k^t from g_{\mu\nu} k^\mu k^\nu = 0.
    a (k^t)^2 + b k^t + c = 0, where a=g_00, b=2 g_0i k^i, c=g_ij k^i k^j.
    """
    a = g[0, 0]
    b = 2.0 * float(np.dot(g[0, 1:], k[1:]))
    c = float(np.dot(k[1:], np.dot(g[1:, 1:], k[1:])))
    k_proj = k.copy()
    eps = 1e-12
    if abs(a) < eps:
        if abs(b) > eps:
            k_proj[0] = -c / b
        return k_proj
    disc = b * b - 4.0 * a * c
    if disc < 0:
        return k_proj
    sqrt_disc = np.sqrt(disc)
    k_t1 = (-b + sqrt_disc) / (2.0 * a)
    k_t2 = (-b - sqrt_disc) / (2.0 * a)
    k_proj[0] = k_t1 if k_t1 >= k_t2 else k_t2
    return k_proj


def null_tangent(coords: np.ndarray, direction: np.ndarray, metric_fn: Callable) -> np.ndarray:
    r"""
    Build an initial null tangent vector k given a spatial direction and metric.
    """
    n_spatial = direction / np.linalg.norm(direction)
    g = metric_fn(*coords)
    k = np.array([0.0, n_spatial[0], n_spatial[1], n_spatial[2]])
    return project_to_null_cone(k, g)


def geodesic_rhs(lambda_param: float, state: np.ndarray, metric_fn: Callable, dx: float) -> np.ndarray:
    """RHS for geodesic ODE using numerical Christoffels."""
    coords = state[0:4]
    k = state[4:8]
    g = metric_fn(*coords)
    dg = compute_metric_derivatives(metric_fn, coords, dx)
    Gamma = compute_christoffel_symbols(g, dg)
    # dx^mu/dlambda = k^mu
    dcoords = k
    # dk^mu/dlambda = -Gamma^mu_{alpha beta} k^alpha k^beta
    dk = np.zeros(4)
    for mu in range(4):
        for a in range(4):
            for b in range(4):
                dk[mu] -= Gamma[mu, a, b] * k[a] * k[b]
    return np.concatenate([dcoords, dk])


def integrate_geodesic(
    metric_fn: Callable,
    initial_coords: np.ndarray,
    initial_direction: np.ndarray,
    lambda_max: float,
    n_steps: int = 150,
    dx: float = 1e-5,
    method: str = 'RK45',
    project_null: bool = True,
    rtol: float = 1e-8,
    atol: float = 1e-10,
) -> Tuple[np.ndarray, np.ndarray, Dict]:
    """Integrate a null geodesic using numerical Christoffels."""
    k0 = null_tangent(initial_coords, initial_direction, metric_fn)
    state0 = np.concatenate([initial_coords, k0])

    def rhs(lam, state):
        coords = state[0:4]
        k = state[4:8]
        if project_null:
            g = metric_fn(*coords)
            k = project_to_null_cone(k, g)
            state = np.concatenate([coords, k])
        return geodesic_rhs(lam, state, metric_fn, dx)

    lam_eval = np.linspace(0.0, lambda_max, n_steps)
    sol = solve_ivp(rhs, (0.0, lambda_max), state0, method=method, t_eval=lam_eval, rtol=rtol, atol=atol)
    if not sol.success:
        positions = np.zeros((n_steps, 4))
        tangents = np.zeros((n_steps, 4))
        diagnostics = {
            'success': False,
            'message': sol.message,
            'n_eval': sol.nfev,
            'null_violation_max': np.nan,
            'null_violation_mean': np.nan,
            'null_violation_std': np.nan,
        }
        return positions, tangents, diagnostics

    positions = sol.y[0:4, :].T
    tangents_raw = sol.y[4:8, :].T

    # Post-project to null cone
    tangents = np.zeros_like(tangents_raw)
    null_violations = []
    for i in range(len(positions)):
        g = metric_fn(*positions[i])
        k_proj = project_to_null_cone(tangents_raw[i], g)
        tangents[i] = k_proj
        null_norm = float(k_proj @ (g @ k_proj))
        null_violations.append(abs(null_norm))

    diagnostics = {
        'success': True,
        'message': sol.message,
        'n_eval': sol.nfev,
        'null_violation_max': float(np.max(null_violations)),
        'null_violation_mean': float(np.mean(null_violations)),
        'null_violation_std': float(np.std(null_violations)),
    }
    return positions, tangents, diagnostics


def compute_anec_generic(metric_fn: Callable, positions: np.ndarray, tangents: np.ndarray, lambda_max: float) -> Tuple[float, Dict]:
    """Compute ANEC by numerically obtaining T_{mu nu} from Einstein tensor at each point."""
    n_steps = len(positions)
    Tkk_vals = np.zeros(n_steps)
    for i in range(n_steps):
        coords = positions[i]
        G = compute_einstein_tensor(metric_fn, coords)
        T = einstein_to_stress_energy(G)
        k = tangents[i]
        Tkk_vals[i] = float(k @ (T @ k))
    lam_vals = np.linspace(0.0, lambda_max, n_steps)
    anec = float(np.trapz(Tkk_vals, lam_vals))
    stats = {
        'T_kk_min': float(np.min(Tkk_vals)),
        'T_kk_max': float(np.max(Tkk_vals)),
        'T_kk_mean': float(np.mean(Tkk_vals)),
        'T_kk_std': float(np.std(Tkk_vals)),
        'negative_fraction': float(np.mean(Tkk_vals < 0.0)),
    }
    return anec, stats
