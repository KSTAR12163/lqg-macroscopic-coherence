"""
Stress-Energy Tensor Computation from Warp Metrics

Compute T_μν from warp bubble metric solutions via Einstein equations:
T_μν = (c⁴/8πG) G_μν

where G_μν is the Einstein tensor.
"""

from typing import Dict, Callable, Tuple
import numpy as np


def compute_metric_derivatives(
    metric_fn: Callable,
    coords: np.ndarray,
    dx: float = 1e-6
) -> np.ndarray:
    """
    Compute first derivatives ∂_μ g_αβ using 4th-order central differences.
    
    Args:
        metric_fn: Function(t, x, y, z) → g_μν
        coords: (t, x, y, z) evaluation point
        dx: Finite difference step
        
    Returns:
        dg[μ][α][β] = ∂_μ g_αβ (4×4×4 array)
    """
    dg = np.zeros((4, 4, 4))
    t, x, y, z = coords
    
    # 4th order central difference: f'(x) ≈ [−f(x+2h) + 8f(x+h) − 8f(x−h) + f(x−2h)] / 12h
    coord_shifts = [
        [1, 0, 0, 0],  # ∂_t
        [0, 1, 0, 0],  # ∂_x
        [0, 0, 1, 0],  # ∂_y
        [0, 0, 0, 1],  # ∂_z
    ]
    
    for mu, shift in enumerate(coord_shifts):
        c_p2 = coords + 2 * dx * np.array(shift)
        c_p1 = coords + dx * np.array(shift)
        c_m1 = coords - dx * np.array(shift)
        c_m2 = coords - 2 * dx * np.array(shift)
        
        g_p2 = metric_fn(*c_p2)
        g_p1 = metric_fn(*c_p1)
        g_m1 = metric_fn(*c_m1)
        g_m2 = metric_fn(*c_m2)
        
        dg[mu] = (-g_p2 + 8*g_p1 - 8*g_m1 + g_m2) / (12 * dx)
    
    return dg


def compute_christoffel_symbols(
    g: np.ndarray,
    dg: np.ndarray
) -> np.ndarray:
    """
    Compute Christoffel symbols Γ^λ_μν = (1/2) g^λσ (∂_μ g_σν + ∂_ν g_μσ - ∂_σ g_μν).
    
    Args:
        g: Metric tensor g_μν (4×4)
        dg: Metric derivatives ∂_μ g_αβ (4×4×4)
        
    Returns:
        Γ^λ_μν (4×4×4 array)
    """
    try:
        g_inv = np.linalg.inv(g)
    except np.linalg.LinAlgError:
        # Singular metric - return zeros
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


def compute_riemann_tensor(
    Gamma: np.ndarray,
    dGamma: np.ndarray
) -> np.ndarray:
    """
    Compute Riemann tensor R^ρ_σμν = ∂_μ Γ^ρ_νσ - ∂_ν Γ^ρ_μσ + Γ^ρ_μλ Γ^λ_νσ - Γ^ρ_νλ Γ^λ_μσ.
    
    Args:
        Gamma: Christoffel symbols Γ^λ_μν (4×4×4)
        dGamma: Derivatives ∂_μ Γ^λ_αβ (4×4×4×4)
        
    Returns:
        R^ρ_σμν (4×4×4×4 array)
    """
    R = np.zeros((4, 4, 4, 4))
    
    for rho in range(4):
        for sigma in range(4):
            for mu in range(4):
                for nu in range(4):
                    # Derivative terms
                    R[rho, sigma, mu, nu] = dGamma[mu, rho, nu, sigma] - dGamma[nu, rho, mu, sigma]
                    
                    # Quadratic terms
                    for lam in range(4):
                        R[rho, sigma, mu, nu] += (
                            Gamma[rho, mu, lam] * Gamma[lam, nu, sigma] -
                            Gamma[rho, nu, lam] * Gamma[lam, mu, sigma]
                        )
    
    return R


def compute_ricci_tensor(
    R: np.ndarray
) -> np.ndarray:
    """
    Compute Ricci tensor R_μν = R^λ_μλν (contraction of Riemann tensor).
    
    Args:
        R: Riemann tensor R^ρ_σμν (4×4×4×4)
        
    Returns:
        R_μν (4×4 array)
    """
    Ric = np.zeros((4, 4))
    
    for mu in range(4):
        for nu in range(4):
            for lam in range(4):
                Ric[mu, nu] += R[lam, mu, lam, nu]
    
    return Ric


def compute_ricci_scalar(
    g_inv: np.ndarray,
    Ric: np.ndarray
) -> float:
    """
    Compute Ricci scalar R = g^μν R_μν.
    
    Args:
        g_inv: Inverse metric g^μν (4×4)
        Ric: Ricci tensor R_μν (4×4)
        
    Returns:
        R (scalar)
    """
    R_scalar = 0.0
    for mu in range(4):
        for nu in range(4):
            R_scalar += g_inv[mu, nu] * Ric[mu, nu]
    
    return R_scalar


def compute_einstein_tensor(
    metric_fn: Callable,
    coords: np.ndarray,
    dx: float = 1e-5
) -> np.ndarray:
    """
    Compute Einstein tensor G_μν = R_μν - (1/2) R g_μν numerically.
    
    Uses 4th-order finite differences for derivatives.
    
    Args:
        metric_fn: Function(t, x, y, z) → g_μν (4×4 array)
        coords: Coordinates (t, x, y, z) at evaluation point
        dx: Finite difference step (default 1e-5 m for stability)
        
    Returns:
        G_μν as 4×4 array
    """
    # Metric at evaluation point
    g = metric_fn(*coords)
    
    # Inverse metric
    try:
        g_inv = np.linalg.inv(g)
    except np.linalg.LinAlgError:
        # Singular metric - return zeros
        return np.zeros((4, 4))
    
    # First derivatives of metric
    dg = compute_metric_derivatives(metric_fn, coords, dx)
    
    # Christoffel symbols
    Gamma = compute_christoffel_symbols(g, dg)
    
    # Derivatives of Christoffel symbols (for Riemann tensor)
    dGamma = np.zeros((4, 4, 4, 4))
    coord_shifts = [
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1],
    ]
    
    for mu, shift in enumerate(coord_shifts):
        c_p2 = coords + 2 * dx * np.array(shift)
        c_p1 = coords + dx * np.array(shift)
        c_m1 = coords - dx * np.array(shift)
        c_m2 = coords - 2 * dx * np.array(shift)
        
        # Compute Gamma at shifted points
        g_p2 = metric_fn(*c_p2)
        dg_p2 = compute_metric_derivatives(metric_fn, c_p2, dx)
        Gamma_p2 = compute_christoffel_symbols(g_p2, dg_p2)
        
        g_p1 = metric_fn(*c_p1)
        dg_p1 = compute_metric_derivatives(metric_fn, c_p1, dx)
        Gamma_p1 = compute_christoffel_symbols(g_p1, dg_p1)
        
        g_m1 = metric_fn(*c_m1)
        dg_m1 = compute_metric_derivatives(metric_fn, c_m1, dx)
        Gamma_m1 = compute_christoffel_symbols(g_m1, dg_m1)
        
        g_m2 = metric_fn(*c_m2)
        dg_m2 = compute_metric_derivatives(metric_fn, c_m2, dx)
        Gamma_m2 = compute_christoffel_symbols(g_m2, dg_m2)
        
        # 4th order derivative
        dGamma[mu] = (-Gamma_p2 + 8*Gamma_p1 - 8*Gamma_m1 + Gamma_m2) / (12 * dx)
    
    # Riemann tensor
    R = compute_riemann_tensor(Gamma, dGamma)
    
    # Ricci tensor
    Ric = compute_ricci_tensor(R)
    
    # Ricci scalar
    R_scalar = compute_ricci_scalar(g_inv, Ric)
    
    # Einstein tensor: G_μν = R_μν - (1/2) R g_μν
    G = Ric - 0.5 * R_scalar * g
    
    return G


def einstein_to_stress_energy(G_munu: np.ndarray) -> np.ndarray:
    """
    Convert Einstein tensor to stress-energy tensor.
    
    T_μν = (c⁴/8πG) G_μν
    
    Args:
        G_munu: Einstein tensor (4×4)
        
    Returns:
        T_μν (4×4) in J/m³ (energy density units)
    """
    c = 2.99792458e8  # m/s
    G_newton = 6.67430e-11  # m³/(kg·s²)
    
    prefactor = c**4 / (8 * np.pi * G_newton)
    
    T_munu = prefactor * G_munu
    
    return T_munu


def load_alcubierre_metric(
    velocity: float,  # units of c
    radius: float,    # m
    wall_thickness: float  # m
) -> Callable:
    """
    Load Alcubierre metric function.
    
    ds² = -dt² + (dx - v_s f(r_s) dt)² + dy² + dz²
    
    where f(r_s) is the shape function and r_s = sqrt((x-x_s)²+y²+z²)
    
    Args:
        velocity: Bubble velocity (units of c)
        radius: Bubble radius (m)
        wall_thickness: Wall thickness (m)
        
    Returns:
        Metric function(t, x, y, z) → g_μν
    """
    c = 2.99792458e8  # m/s
    v = velocity * c
    
    def shape_function(r_s: float) -> float:
        """Top-hat shape function with smoothing."""
        sigma = wall_thickness
        return 0.5 * (np.tanh((radius + sigma - r_s) / sigma) - 
                     np.tanh((radius - sigma - r_s) / sigma))
    
    def metric(t: float, x: float, y: float, z: float) -> np.ndarray:
        """Alcubierre metric at point (t, x, y, z)."""
        
        # Shift frame (bubble at origin)
        x_s = 0.0  # Bubble center x-position
        r_s = np.sqrt((x - x_s)**2 + y**2 + z**2)
        
        f = shape_function(r_s)
        
        g = np.zeros((4, 4))
        
        # Metric components (signature -+++)
        g[0, 0] = -1.0 + v**2 * f**2  # g_tt
        g[0, 1] = -v * f              # g_tx
        g[1, 0] = -v * f              # g_xt
        g[1, 1] = 1.0                 # g_xx
        g[2, 2] = 1.0                 # g_yy
        g[3, 3] = 1.0                 # g_zz
        
        return g
    
    return metric


def compute_stress_energy_from_metric(
    metric_fn: Callable,
    coords: np.ndarray
) -> np.ndarray:
    """
    Full pipeline: metric → Einstein tensor → stress-energy.
    
    Args:
        metric_fn: Metric function(t, x, y, z) → g_μν
        coords: Evaluation point [t, x, y, z]
        
    Returns:
        T_μν (4×4) in SI units
    """
    # Compute Einstein tensor
    G_munu = compute_einstein_tensor(metric_fn, coords)
    
    # Convert to stress-energy
    T_munu = einstein_to_stress_energy(G_munu)
    
    return T_munu


def extract_energy_density_and_pressure(T_munu: np.ndarray) -> Tuple[float, float]:
    """
    Extract energy density and pressure from stress-energy tensor.
    
    For perfect fluid: T_μν = (ρ + p) u_μ u_ν + p g_μν
    In local rest frame: T_00 = ρ, T_ii = p
    
    Args:
        T_munu: Stress-energy tensor (4×4)
        
    Returns:
        (rho, p) in J/m³
    """
    rho = T_munu[0, 0]  # Energy density
    
    # Assume isotropic pressure (average spatial diagonal)
    p = (T_munu[1, 1] + T_munu[2, 2] + T_munu[3, 3]) / 3.0
    
    return rho, p


# TODO: Integrate with existing warp-* repos
# from warp_bubble_metric_ansatz import AlcubierreMetric
# from warp_bubble_einstein_equations import compute_ricci_tensor
