"""
Geodesic Integration for Alcubierre Metric with Analytic Christoffels

Optimized version using analytic Christoffel symbols to:
1. Reduce numerical errors (no finite differencing)
2. Improve performance (no repeated metric evaluations)
3. Tighten null constraint preservation
"""

import numpy as np
from typing import Callable, Tuple, Dict
from scipy.integrate import solve_ivp
from .alcubierre_analytic import (
    alcubierre_metric_analytic,
    alcubierre_christoffel_analytic
)


def project_to_null_cone(
    k: np.ndarray,
    g: np.ndarray,
    u: np.ndarray = None
) -> np.ndarray:
    """
    Project 4-vector k onto the null cone by solving g_{\mu\nu} k^\mu k^\nu = 0
    exactly for k^t given the spatial components.

    This replaces the previous linear projection, which could leave noticeable
    nullness drift when g_{\mu 0} k^\mu ≈ 0. We solve the quadratic (or linear
    if a ≈ 0) equation in k^t:

        a (k^t)^2 + b k^t + c = 0

    where a = g_{00}, b = 2 g_{0i} k^i, c = g_{ij} k^i k^j.
    """
    # Coefficients for k^t equation
    a = g[0, 0]
    b = 2.0 * np.dot(g[0, 1:], k[1:])
    c = float(np.dot(k[1:], np.dot(g[1:, 1:], k[1:])))

    k_proj = k.copy()

    # Handle near-degenerate quadratic (|a| ~ 0) with linear solve
    eps = 1e-12
    if abs(a) < eps:
        if abs(b) > eps:
            k_t = -c / b
            k_proj[0] = k_t
        # else leave k unchanged (cannot determine k^t)
        return k_proj

    # Solve quadratic for k^t, choose future-directed root (larger k^t)
    disc = b * b - 4.0 * a * c
    if disc < 0:
        # Numerical issue: keep original k
        return k_proj

    sqrt_disc = np.sqrt(disc)
    k_t1 = (-b + sqrt_disc) / (2.0 * a)
    k_t2 = (-b - sqrt_disc) / (2.0 * a)

    # Pick root with larger coordinate time component (future-directed)
    k_t = k_t1 if k_t1 >= k_t2 else k_t2
    k_proj[0] = k_t
    return k_proj


def null_tangent_alcubierre(
    coords: np.ndarray,
    direction: np.ndarray,
    v_s: float = 1.0,
    R: float = 100.0,
    sigma: float = 10.0
) -> np.ndarray:
    """
    Compute initial null tangent for Alcubierre metric.
    
    Args:
        coords: Initial position (t, x, y, z)
        direction: Spatial direction (3-vector, will be normalized)
        v_s, R, sigma, c: Alcubierre parameters
        
    Returns:
        k^μ satisfying g_μν k^μ k^ν = 0
    """
    # Normalize spatial direction
    n_spatial = direction / np.linalg.norm(direction)
    
    # Get metric
    g = alcubierre_metric_analytic(*coords, v_s, R, sigma)
    
    # Solve g_μν k^μ k^ν = 0 for k^t given k^i = n^i
    k = np.array([0.0, n_spatial[0], n_spatial[1], n_spatial[2]])
    k = project_to_null_cone(k, g)
    return k


def geodesic_rhs_alcubierre(
    lambda_param: float,
    state: np.ndarray,
    v_s: float,
    R: float,
    sigma: float,
    project_null: bool = True
) -> np.ndarray:
    """
    RHS for Alcubierre geodesic equation using analytic Christoffels.
    
    Args:
        lambda_param: Affine parameter
        state: [x^μ, k^μ] (8-vector)
        v_s, R, sigma, c: Alcubierre parameters
        project_null: Whether to project k to null cone
        
    Returns:
        d(state)/dλ
    """
    coords = state[0:4]
    k = state[4:8]
    
    # Get metric and Christoffel (analytic - fast!)
    g = alcubierre_metric_analytic(*coords, v_s, R, sigma)
    Gamma = alcubierre_christoffel_analytic(*coords, v_s, R, sigma)
    
    # Project k to null cone (exact k^t solve)
    if project_null:
        k = project_to_null_cone(k, g)
    
    # dx^μ/dλ = k^μ
    dcoords = k
    
    # dk^μ/dλ = -Γ^μ_αβ k^α k^β
    dk = np.zeros(4)
    for mu in range(4):
        for alpha in range(4):
            for beta in range(4):
                dk[mu] -= Gamma[mu, alpha, beta] * k[alpha] * k[beta]
    
    return np.concatenate([dcoords, dk])


def integrate_alcubierre_geodesic(
    initial_coords: np.ndarray,
    initial_direction: np.ndarray,
    lambda_max: float,
    v_s: float = 1.0,
    R: float = 100.0,
    sigma: float = 10.0,
    n_steps: int = 500,
    method: str = 'RK45',
    project_null: bool = True,
    rtol: float = 1e-8,
    atol: float = 1e-10
) -> Tuple[np.ndarray, np.ndarray, Dict]:
    """
    Integrate null geodesic for Alcubierre metric using analytic Christoffels.
    
    Args:
        initial_coords: Starting (t, x, y, z)
        initial_direction: Spatial direction (3-vector)
        lambda_max: Integration range
        v_s, R, sigma, c: Alcubierre parameters
        n_steps: Number of output points
        method: 'RK45', 'RK23', 'DOP853'
        project_null: Enforce null constraint at each step
        rtol: Relative tolerance
        atol: Absolute tolerance
        
    Returns:
        (positions, tangents, diagnostics)
    """
    # Initial null vector
    k0 = null_tangent_alcubierre(initial_coords, initial_direction, v_s, R, sigma)
    
    # Initial state
    state0 = np.concatenate([initial_coords, k0])
    
    # RHS wrapper
    def rhs(lam, state):
        return geodesic_rhs_alcubierre(lam, state, v_s, R, sigma, project_null)
    
    # Integration points
    lambda_eval = np.linspace(0, lambda_max, n_steps)
    
    # Solve
    sol = solve_ivp(
        rhs,
        (0, lambda_max),
        state0,
        method=method,
        t_eval=lambda_eval,
        rtol=rtol,
        atol=atol,
        dense_output=False
    )
    
    if not sol.success:
        # Fallback
        positions = np.zeros((n_steps, 4))
        tangents = np.zeros((n_steps, 4))
        for i, lam in enumerate(lambda_eval):
            positions[i] = initial_coords + lam * k0
            tangents[i] = k0
        
        diagnostics = {
            'success': False,
            'message': sol.message,
            'n_eval': 0,
            'null_violation_max': np.nan,
            'null_violation_mean': np.nan
        }
    else:
        positions = sol.y[0:4, :].T
        tangents_raw = sol.y[4:8, :].T
        
        # Project tangents onto null cone at each point (enforce constraint)
        tangents = np.zeros_like(tangents_raw)
        null_violations = []
        for i in range(len(positions)):
            g = alcubierre_metric_analytic(*positions[i], v_s, R, sigma)
            k_proj = project_to_null_cone(tangents_raw[i], g)
            tangents[i] = k_proj
            null_norm = np.dot(k_proj, np.dot(g, k_proj))
            null_violations.append(abs(null_norm))
        
        diagnostics = {
            'success': True,
            'message': sol.message,
            'n_eval': sol.nfev,
            'null_violation_max': float(np.max(null_violations)),
            'null_violation_mean': float(np.mean(null_violations)),
            'null_violation_std': float(np.std(null_violations))
        }
    
    return positions, tangents, diagnostics


def compute_anec_alcubierre(
    T_fn: Callable,
    positions: np.ndarray,
    tangents: np.ndarray,
    lambda_max: float
) -> Tuple[float, Dict]:
    """
    Compute ANEC = ∫ T_μν k^μ k^ν dλ along geodesic.
    
    Args:
        T_fn: Stress-energy function(t, x, y, z) → T_μν
        positions: Geodesic positions (n_steps, 4)
        tangents: Null tangents (n_steps, 4)
        lambda_max: Affine parameter range
        
    Returns:
        (ANEC value, statistics)
    """
    n_steps = len(positions)
    T_kk_values = np.zeros(n_steps)
    
    for i in range(n_steps):
        T = T_fn(*positions[i])
        k = tangents[i]
        T_kk_values[i] = np.dot(k, np.dot(T, k))
    
    # Trapezoidal integration
    lambda_values = np.linspace(0, lambda_max, n_steps)
    anec = np.trapz(T_kk_values, lambda_values)
    
    stats = {
        'anec': float(anec),
        'T_kk_min': float(np.min(T_kk_values)),
        'T_kk_max': float(np.max(T_kk_values)),
        'T_kk_mean': float(np.mean(T_kk_values)),
        'T_kk_std': float(np.std(T_kk_values)),
        'negative_fraction': float(np.sum(T_kk_values < 0) / n_steps)
    }
    
    return anec, stats


if __name__ == "__main__":
    """Quick test of analytic geodesic integration."""
    from stress_energy import compute_einstein_tensor, einstein_to_stress_energy
    
    # Parameters
    v_s = 1.0
    R = 100.0
    sigma = 10.0
    
    # Initial conditions (ray through center)
    initial_coords = np.array([0.0, -200.0, 0.0, 0.0])
    direction = np.array([1.0, 0.0, 0.0])  # +x
    lambda_max = 400.0
    
    print("Testing Alcubierre geodesic with analytic Christoffels...")
    print(f"  Bubble: v={v_s}c, R={R}m, σ={sigma}/m")
    print(f"  Ray: x={initial_coords[1]}m → +x direction")
    print(f"  Integration: λ∈[0, {lambda_max}], project_null=True")
    print()
    
    # Integrate
    positions, tangents, diag = integrate_alcubierre_geodesic(
        initial_coords,
        direction,
        lambda_max,
        v_s, R, sigma,
        n_steps=300,
        project_null=True,
        rtol=1e-8,
        atol=1e-10
    )
    
    if diag['success']:
        print(f"✅ Integration successful")
        print(f"   Function evaluations: {diag['n_eval']}")
        print(f"   Null violation (max): {diag['null_violation_max']:.3e}")
        print(f"   Null violation (mean): {diag['null_violation_mean']:.3e}")
        print(f"   Null violation (std): {diag['null_violation_std']:.3e}")
        print()
        
        # Compute ANEC using corrected stress-energy
        def T_fn(t, x, y, z):
            # Use analytic metric (no c² bug)
            def metric_fn_local(t2, x2, y2, z2):
                return alcubierre_metric_analytic(t2, x2, y2, z2, v_s, R, sigma)
            
            coords_local = np.array([t, x, y, z])
            G = compute_einstein_tensor(metric_fn_local, coords_local)
            T = einstein_to_stress_energy(G)
            return T
        
        anec, stats = compute_anec_alcubierre(T_fn, positions, tangents, lambda_max)
        
        print("ANEC Result:")
        print(f"  ∫ T_μν k^μ k^ν dλ = {anec:.3e}")
        print(f"  T_kk min = {stats['T_kk_min']:.3e}")
        print(f"  T_kk max = {stats['T_kk_max']:.3e}")
        print(f"  T_kk mean = {stats['T_kk_mean']:.3e}")
        print(f"  Negative fraction: {stats['negative_fraction']*100:.2f}%")
        
        if anec < 0:
            print("  ⚠️  ANEC VIOLATED (integral < 0)")
        else:
            print("  ✅ ANEC satisfied")
    else:
        print(f"❌ Integration failed: {diag['message']}")
