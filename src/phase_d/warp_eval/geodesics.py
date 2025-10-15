"""
Null Geodesic Integration and ANEC Computation

Compute ANEC = ∫ T_μν k^μ k^ν dλ along null geodesics
for warp bubble metrics using RK4 integration with Christoffel symbols.
"""

from typing import Callable, Tuple, List, Dict
import numpy as np
from scipy.integrate import solve_ivp


def compute_metric_derivatives_local(
    metric_fn: Callable,
    coords: np.ndarray,
    dx: float = 1e-5
) -> np.ndarray:
    """
    Compute metric derivatives ∂_μ g_αβ using central differences.
    
    Args:
        metric_fn: Function(t, x, y, z) → g_μν
        coords: (t, x, y, z) evaluation point
        dx: Finite difference step
        
    Returns:
        dg[μ][α][β] = ∂_μ g_αβ (4×4×4 array)
    """
    dg = np.zeros((4, 4, 4))
    
    coord_shifts = [
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1],
    ]
    
    for mu, shift in enumerate(coord_shifts):
        c_p1 = coords + dx * np.array(shift)
        c_m1 = coords - dx * np.array(shift)
        
        g_p1 = metric_fn(*c_p1)
        g_m1 = metric_fn(*c_m1)
        
        dg[mu] = (g_p1 - g_m1) / (2 * dx)
    
    return dg


def compute_christoffel_at_point(
    metric_fn: Callable,
    coords: np.ndarray,
    dx: float = 1e-5
) -> np.ndarray:
    """
    Compute Christoffel symbols Γ^λ_μν at a point.
    
    Args:
        metric_fn: Metric function(t, x, y, z) → g_μν
        coords: Point (t, x, y, z)
        dx: Finite difference step
        
    Returns:
        Γ^λ_μν (4×4×4 array)
    """
    g = metric_fn(*coords)
    dg = compute_metric_derivatives_local(metric_fn, coords, dx)
    
    try:
        g_inv = np.linalg.inv(g)
    except np.linalg.LinAlgError:
        return np.zeros((4, 4, 4))
    
    Gamma = np.zeros((4, 4, 4))
    
    for lam in range(4):
        for mu in range(4):
            for nu in range(4):
                for sigma in range(4):
                    Gamma[lam, mu, nu] += 0.5 * g_inv[lam, sigma] * (
                        dg[mu, sigma, nu] + dg[nu, mu, sigma] - dg[sigma, mu, nu]
                    )
    
    return Gamma


def null_tangent(
    metric_fn: Callable,
    coords: np.ndarray,
    direction: np.ndarray
) -> np.ndarray:
    """
    Compute null 4-vector k^μ satisfying g_μν k^μ k^ν = 0.
    
    Given a spatial direction, construct a normalized null vector.
    
    Args:
        metric_fn: Metric function(t, x, y, z) → g_μν
        coords: Position (t, x, y, z)
        direction: Spatial direction (3-vector)
        
    Returns:
        k^μ (4-vector) with g_μν k^μ k^ν = 0
    """
    g = metric_fn(*coords)
    
    # Normalize spatial direction
    dir_norm = np.linalg.norm(direction)
    if dir_norm > 0:
        s = direction / dir_norm
    else:
        s = np.array([1.0, 0.0, 0.0])  # Default to x-direction
    
    # For null vector: g_μν k^μ k^ν = 0
    # Let k = (k^t, k^x, k^y, k^z) = (k^t, k^t * s)
    # Then: g_tt (k^t)² + 2 g_ti k^t k^i + g_ij k^i k^j = 0
    
    # Spatial metric components
    g_spatial = g[1:4, 1:4]
    g_time_spatial = g[0, 1:4]
    
    # Solve quadratic: g_tt (k^t)² + 2 g_ti s_i k^t + g_ij s_i s_j = 0
    a = g[0, 0]
    b = 2 * np.dot(g_time_spatial, s)
    c = np.dot(s, np.dot(g_spatial, s))
    
    discriminant = b**2 - 4*a*c
    
    if discriminant < 0:
        # No real null vector - use approximate
        k_t = 1.0
    else:
        # Take positive root (future-directed)
        k_t = (-b + np.sqrt(discriminant)) / (2*a)
    
    k = np.zeros(4)
    k[0] = k_t
    k[1:4] = k_t * s
    
    return k


def geodesic_equation_rhs(
    lambda_param: float,
    state: np.ndarray,
    metric_fn: Callable,
    dx: float = 1e-5
) -> np.ndarray:
    """
    RHS of geodesic equation for ODE integration.
    
    d²x^μ/dλ² = -Γ^μ_αβ dx^α/dλ dx^β/dλ
    
    Rewritten as first-order system:
    dx^μ/dλ = k^μ
    dk^μ/dλ = -Γ^μ_αβ k^α k^β
    
    Args:
        lambda_param: Affine parameter (not used in autonomous system)
        state: [x^μ, k^μ] (8-vector)
        metric_fn: Metric function(t, x, y, z) → g_μν
        dx: Finite difference step for Christoffel computation
        
    Returns:
        d(state)/dλ = [k^μ, -Γ^μ_αβ k^α k^β]
    """
    coords = state[0:4]  # x^μ = (t, x, y, z)
    k = state[4:8]       # k^μ = dx^μ/dλ
    
    # Compute Christoffel symbols at current position
    Gamma = compute_christoffel_at_point(metric_fn, coords, dx)
    
    # Geodesic equation: dk^μ/dλ = -Γ^μ_αβ k^α k^β
    dk_dlambda = np.zeros(4)
    for mu in range(4):
        for alpha in range(4):
            for beta in range(4):
                dk_dlambda[mu] -= Gamma[mu, alpha, beta] * k[alpha] * k[beta]
    
    # Return [dx/dλ, dk/dλ]
    return np.concatenate([k, dk_dlambda])


def compute_null_vector(
    metric: Callable,
    coords: np.ndarray,
    direction: np.ndarray
) -> np.ndarray:
    """Alias for null_tangent."""
    return null_tangent(metric, coords, direction)


def integrate_null_geodesic(
    metric_fn: Callable,
    initial_coords: np.ndarray,
    initial_direction: np.ndarray,
    lambda_max: float,
    n_steps: int = 1000,
    dx_christoffel: float = 1e-5,
    method: str = 'RK45'
) -> Tuple[np.ndarray, np.ndarray, Dict]:
    """
    Integrate null geodesic using adaptive RK45 or fixed RK4.
    
    Args:
        metric_fn: Metric function(t, x, y, z) → g_μν
        initial_coords: Starting position (t, x, y, z)
        initial_direction: Initial spatial direction (3-vector)
        lambda_max: Maximum affine parameter
        n_steps: Number of output points
        dx_christoffel: Step for Christoffel symbol computation
        method: Integration method ('RK45' or 'RK4')
        
    Returns:
        (positions, tangents, diagnostics)
    """
    # Initial null tangent
    k0 = null_tangent(metric_fn, initial_coords, initial_direction)
    
    # Initial state: [x^μ, k^μ]
    state0 = np.concatenate([initial_coords, k0])
    
    # Define RHS for scipy
    def rhs(lam, state):
        return geodesic_equation_rhs(lam, state, metric_fn, dx_christoffel)
    
    # Integrate using scipy.integrate.solve_ivp
    lambda_eval = np.linspace(0, lambda_max, n_steps)
    
    sol = solve_ivp(
        rhs,
        (0, lambda_max),
        state0,
        method=method,
        t_eval=lambda_eval,
        dense_output=False,
        rtol=1e-6,
        atol=1e-9
    )
    
    if not sol.success:
        # Fallback: return straight line
        positions = np.zeros((n_steps, 4))
        tangents = np.zeros((n_steps, 4))
        for i, lam in enumerate(lambda_eval):
            positions[i] = initial_coords + lam * k0
            tangents[i] = k0
        
        diagnostics = {
            'success': False,
            'message': sol.message,
            'n_eval': 0
        }
    else:
        # Extract positions and tangents
        positions = sol.y[0:4, :].T  # (n_steps, 4)
        tangents = sol.y[4:8, :].T  # (n_steps, 4)
        
        # Check null condition: g_μν k^μ k^ν ≈ 0
        null_violations = []
        for i in range(positions.shape[0]):
            g = metric_fn(*positions[i])
            k = tangents[i]
            null_norm = np.dot(k, np.dot(g, k))
            null_violations.append(abs(null_norm))
        
        diagnostics = {
            'success': True,
            'message': sol.message,
            'n_eval': sol.nfev,
            'null_violation_max': float(np.max(null_violations)),
            'null_violation_mean': float(np.mean(null_violations))
        }
    
    return positions, tangents, diagnostics


def compute_T_kk_along_geodesic(
    T_fn: Callable,  # Stress-energy function(t, x, y, z) → T_μν
    coords: np.ndarray,  # Geodesic coordinates (n_steps, 4)
    k_vectors: np.ndarray  # Null vectors (n_steps, 4)
) -> np.ndarray:
    """
    Compute T_μν k^μ k^ν along a null geodesic.
    
    Args:
        T_fn: Stress-energy tensor function
        coords: Coordinates along geodesic
        k_vectors: Null vectors along geodesic
        
    Returns:
        T_kk values (n_steps,)
    """
    n_steps = len(coords)
    T_kk = np.zeros(n_steps)
    
    for i in range(n_steps):
        # Evaluate stress-energy at this point
        T = T_fn(*coords[i])
        
        # Contract: T_μν k^μ k^ν
        k = k_vectors[i]
        T_kk[i] = np.einsum('ij,i,j', T, k, k)
    
    return T_kk


def compute_anec_along_geodesic(
    T_fn: Callable,
    metric_fn: Callable,
    geodesic_positions: np.ndarray,
    geodesic_tangents: np.ndarray
) -> Tuple[float, Dict]:
    """
    Compute ANEC = ∫ T_μν k^μ k^ν dλ along a geodesic.
    
    Uses trapezoidal rule for integration.
    
    Args:
        T_fn: Stress-energy function T_μν(t, x, y, z) → 4×4 array
        metric_fn: Metric function g_μν(t, x, y, z) → 4×4 array
        geodesic_positions: Array of positions (n, 4)
        geodesic_tangents: Array of tangents k^μ (n, 4)
        
    Returns:
        (anec_value, diagnostics)
    """
    n_points = geodesic_positions.shape[0]
    
    # Compute T_μν k^μ k^ν at each point
    T_kk = np.zeros(n_points)
    null_violations = np.zeros(n_points)
    
    for i in range(n_points):
        coords = geodesic_positions[i]
        k = geodesic_tangents[i]
        
        # Get stress-energy tensor
        T = T_fn(*coords)
        
        # Contract: T_μν k^μ k^ν
        T_kk[i] = np.dot(k, np.dot(T, k))
        
        # Check null condition: g_μν k^μ k^ν should be ≈ 0
        g = metric_fn(*coords)
        null_violations[i] = abs(np.dot(k, np.dot(g, k)))
    
    # Integrate using trapezoidal rule
    # ANEC = ∫ T_μν k^μ k^ν dλ
    
    # Approximate dλ from coordinate separations
    dlambda = np.zeros(n_points - 1)
    for i in range(n_points - 1):
        dx = geodesic_positions[i+1] - geodesic_positions[i]
        dlambda[i] = np.linalg.norm(dx)
    
    # Integrate
    lambda_vals = np.zeros(n_points)
    lambda_vals[1:] = np.cumsum(dlambda)
    anec_value = float(np.trapz(T_kk, lambda_vals))
    
    # Diagnostics
    diagnostics = {
        'anec_integral': anec_value,
        'T_kk_min': float(np.min(T_kk)),
        'T_kk_max': float(np.max(T_kk)),
        'T_kk_mean': float(np.mean(T_kk)),
        'T_kk_std': float(np.std(T_kk)),
        'negative_region_fraction': float(np.sum(T_kk < 0) / len(T_kk)),
        'geodesic_length': float(lambda_vals[-1]),
        'n_steps': int(n_points),
        'start_point': geodesic_positions[0].tolist(),
        'end_point': geodesic_positions[-1].tolist(),
        'null_violation_max': float(np.max(null_violations)),
        'null_violation_mean': float(np.mean(null_violations))
    }
    
    return anec_value, diagnostics


def sample_anec_multiple_geodesics(
    metric_fn: Callable,
    T_fn: Callable,
    bubble_radius: float = 100.0,
    n_rays: int = 20,
    lambda_max: float = None,
    n_steps: int = 500
) -> Dict:
    """
    Sample ANEC along multiple null geodesics through bubble.
    
    Samples rays at various impact parameters crossing the bubble wall.
    
    Args:
        metric_fn: Metric function(t, x, y, z) → g_μν
        T_fn: Stress-energy function(t, x, y, z) → T_μν
        bubble_radius: Bubble radius (m)
        n_rays: Number of geodesics to sample
        lambda_max: Maximum affine parameter (default: 4 * radius)
        n_steps: Integration steps per geodesic
        
    Returns:
        Dictionary with ANEC statistics across all rays
    """
    if lambda_max is None:
        lambda_max = 4 * bubble_radius
    
    anec_values = []
    all_diagnostics = []
    violation_count = 0
    
    # Sample impact parameters from 0 to 1.5 * radius
    # (to capture center, wall, and exterior)
    impact_params = np.linspace(0, 1.5 * bubble_radius, n_rays)
    
    for b in impact_params:
        # Initial position: far behind bubble, offset by impact parameter
        t0 = 0.0
        x0 = -2 * bubble_radius
        y0 = b
        z0 = 0.0
        initial_coords = np.array([t0, x0, y0, z0])
        
        # Direction: toward +x (through bubble)
        initial_direction = np.array([1.0, 0.0, 0.0])
        
        try:
            # Integrate geodesic
            positions, tangents, geo_diag = integrate_null_geodesic(
                metric_fn,
                initial_coords,
                initial_direction,
                lambda_max,
                n_steps
            )
            
            if not geo_diag['success']:
                continue
            
            # Compute ANEC along this geodesic
            anec, anec_diag = compute_anec_along_geodesic(
                T_fn,
                metric_fn,
                positions,
                tangents
            )
            
            anec_values.append(anec)
            
            # Store diagnostics
            combined_diag = {
                'impact_parameter': float(b),
                'anec': anec,
                'geodesic': geo_diag,
                'anec_details': anec_diag
            }
            all_diagnostics.append(combined_diag)
            
            # Count violations (ANEC < 0)
            if anec < -1e-12:  # Small tolerance for numerical errors
                violation_count += 1
                
        except Exception as e:
            # Skip failed geodesics
            continue
    
    if len(anec_values) == 0:
        return {
            'success': False,
            'error': 'No geodesics integrated successfully',
            'n_rays_attempted': n_rays
        }
    
    anec_array = np.array(anec_values)
    
    return {
        'success': True,
        'n_rays': len(anec_values),
        'min_anec': float(np.min(anec_array)),
        'max_anec': float(np.max(anec_array)),
        'median_anec': float(np.median(anec_array)),
        'mean_anec': float(np.mean(anec_array)),
        'std_anec': float(np.std(anec_array)),
        'violation_count': int(violation_count),
        'violation_fraction': float(violation_count / len(anec_values)),
        'all_anec_values': anec_array.tolist(),
        'impact_parameters': [d['impact_parameter'] for d in all_diagnostics],
        'diagnostics': all_diagnostics
    }

