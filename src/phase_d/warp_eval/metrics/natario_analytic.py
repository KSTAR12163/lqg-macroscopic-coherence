"""
Natário Warp Drive Metric (Analytic Implementation)

The Natário metric (1999, 2002) uses a "flow" approach where space flows
around the bubble rather than expanding/contracting ahead/behind.

Key differences from Alcubierre:
- No expansion scalar (∇·v = 0) in proper formulation
- Lower peak energy densities for same velocity
- More complex stress-energy distribution

Metric (3+1 ADM form):
    ds² = -dt² + (dx^i + v^i dt)(dx_i + v_i dt)
    
where the shift vector is:
    v^i = -v_s f(r_s) ∇^i r_s / |∇r_s|
    
and f(r_s) is the shape function (same as Alcubierre).

Coordinate system: (t, x, y, z) with bubble center at origin in comoving frame.

References:
- Natário (1999): "Warp drive with zero expansion"
- Natário (2002): "Relativity and Singularities"
- Lobo & Visser (2004): "Energy conditions in warp drives"
"""

import numpy as np
from typing import Tuple


def natario_shape_function(
    r_s: float,
    R: float,
    sigma: float
) -> Tuple[float, float]:
    """
    Smooth shape function for Natário metric.
    
    Same functional form as Alcubierre for consistency:
    f(r_s) = 0.5 * [tanh((R+σ-r_s)/σ) - tanh((R-σ-r_s)/σ)]
    
    Args:
        r_s: Radial distance from bubble center
        R: Bubble radius (transition at R)
        sigma: Wall thickness (smaller = sharper)
        
    Returns:
        (f, df/dr_s): Shape function and derivative
    """
    arg_outer = (R + sigma - r_s) / sigma
    arg_inner = (R - sigma - r_s) / sigma
    
    tanh_outer = np.tanh(arg_outer)
    tanh_inner = np.tanh(arg_inner)
    
    f = 0.5 * (tanh_outer - tanh_inner)
    
    # Derivatives: d/dr_s tanh((a-r_s)/σ) = -sech²((a-r_s)/σ)/σ
    sech2_outer = 1.0 / np.cosh(arg_outer)**2
    sech2_inner = 1.0 / np.cosh(arg_inner)**2
    
    df_drs = -0.5 * (sech2_outer - sech2_inner) / sigma
    
    return f, df_drs


def natario_metric(
    t: float,
    x: float,
    y: float,
    z: float,
    v_s: float = 1.0,
    R: float = 100.0,
    sigma: float = 10.0,
    x_c: float = 0.0
) -> np.ndarray:
    """
    Natário warp metric in (t,x,y,z) coordinates.
    
    Metric form:
        ds² = -dt² + (dx - v_x dt)(dx - v_x dt)
                   + (dy - v_y dt)(dy - v_y dt)
                   + (dz - v_z dt)(dz - v_z dt)
    
    where v^i = -v_s f(r_s) n^i with n^i = ∇^i r_s / |∇r_s| (unit radial).
    
    Args:
        t, x, y, z: Spacetime coordinates
        v_s: Bubble velocity (dimensionless, c=1)
        R: Bubble radius
        sigma: Wall thickness
        x_c: Bubble center x-position (for moving bubble; default 0)
        
    Returns:
        g_μν (4×4 metric tensor)
    """
    # Position relative to bubble center
    x_rel = x - x_c
    r_s = np.sqrt(x_rel**2 + y**2 + z**2)
    
    # Shape function
    f, _ = natario_shape_function(r_s, R, sigma)
    
    # Handle r_s = 0 (bubble center)
    if r_s < 1e-10:
        # At center: no shift (v^i = 0)
        g = np.diag([-1.0, 1.0, 1.0, 1.0])
        return g
    
    # Unit radial vector: n^i = (x_rel, y, z) / r_s
    n_x = x_rel / r_s
    n_y = y / r_s
    n_z = z / r_s
    
    # Shift vector: v^i = -v_s f n^i
    v_x = -v_s * f * n_x
    v_y = -v_s * f * n_y
    v_z = -v_s * f * n_z
    
    # Metric components (ADM form: g_tt = -1, g_ti = v_i, g_ij = δ_ij)
    g = np.zeros((4, 4))
    
    # Time-time: g_tt = -1 + v_i v^i = -1 + |v|²
    v_squared = v_x**2 + v_y**2 + v_z**2
    g[0, 0] = -1.0 + v_squared
    
    # Time-space: g_ti = v_i
    g[0, 1] = g[1, 0] = v_x
    g[0, 2] = g[2, 0] = v_y
    g[0, 3] = g[3, 0] = v_z
    
    # Space-space: g_ij = δ_ij
    g[1, 1] = 1.0
    g[2, 2] = 1.0
    g[3, 3] = 1.0
    
    return g


def natario_inverse_metric(
    t: float,
    x: float,
    y: float,
    z: float,
    v_s: float = 1.0,
    R: float = 100.0,
    sigma: float = 10.0,
    x_c: float = 0.0
) -> np.ndarray:
    """
    Analytic inverse of Natário metric.
    
    For ADM form with lapse α=1, shift β^i = -v^i, spatial metric γ_ij = δ_ij:
    
    g^tt = -1
    g^ti = v^i
    g^ij = δ^ij - v^i v^j
    
    Args:
        Same as natario_metric
        
    Returns:
        g^μν (4×4 inverse metric)
    """
    # Position relative to bubble center
    x_rel = x - x_c
    r_s = np.sqrt(x_rel**2 + y**2 + z**2)
    
    # Shape function
    f, _ = natario_shape_function(r_s, R, sigma)
    
    # Handle r_s = 0
    if r_s < 1e-10:
        g_inv = np.diag([-1.0, 1.0, 1.0, 1.0])
        return g_inv
    
    # Unit radial vector
    n_x = x_rel / r_s
    n_y = y / r_s
    n_z = z / r_s
    
    # Shift vector: v^i = -v_s f n^i
    v_x = -v_s * f * n_x
    v_y = -v_s * f * n_y
    v_z = -v_s * f * n_z
    
    # Inverse metric
    g_inv = np.zeros((4, 4))
    
    # Time-time: g^tt = -1
    g_inv[0, 0] = -1.0
    
    # Time-space: g^ti = v^i
    g_inv[0, 1] = g_inv[1, 0] = v_x
    g_inv[0, 2] = g_inv[2, 0] = v_y
    g_inv[0, 3] = g_inv[3, 0] = v_z
    
    # Space-space: g^ij = δ^ij - v^i v^j
    g_inv[1, 1] = 1.0 - v_x * v_x
    g_inv[2, 2] = 1.0 - v_y * v_y
    g_inv[3, 3] = 1.0 - v_z * v_z
    
    g_inv[1, 2] = g_inv[2, 1] = -v_x * v_y
    g_inv[1, 3] = g_inv[3, 1] = -v_x * v_z
    g_inv[2, 3] = g_inv[3, 2] = -v_y * v_z
    
    return g_inv


def natario_christoffel(
    t: float,
    x: float,
    y: float,
    z: float,
    v_s: float = 1.0,
    R: float = 100.0,
    sigma: float = 10.0,
    x_c: float = 0.0
) -> np.ndarray:
    """
    Analytic Christoffel symbols for Natário metric.
    
    Computed from: Γ^λ_μν = (1/2) g^λσ (∂_μ g_σν + ∂_ν g_μσ - ∂_σ g_μν)
    
    Key derivatives:
    - ∂_i f = (df/dr_s) (∂_i r_s) = (df/dr_s) (x^i / r_s)
    - ∂_i n^j = (δ^ij - n^i n^j) / r_s
    - ∂_i v^j = -v_s [(df/dr_s) n^i n^j + f (∂_i n^j)]
    
    Args:
        Same as natario_metric
        
    Returns:
        Γ^λ_μν (4×4×4 array)
    """
    # Position relative to bubble center
    x_rel = x - x_c
    r_s = np.sqrt(x_rel**2 + y**2 + z**2)
    
    # Shape function and derivative
    f, df_drs = natario_shape_function(r_s, R, sigma)
    
    Gamma = np.zeros((4, 4, 4))
    
    # Handle r_s = 0 (all Γ = 0 by symmetry)
    if r_s < 1e-10:
        return Gamma
    
    # Unit radial vector and components
    n_x = x_rel / r_s
    n_y = y / r_s
    n_z = z / r_s
    n = np.array([n_x, n_y, n_z])
    
    # Shift vector: v^i = -v_s f n^i
    v = -v_s * f * n
    
    # Derivatives of n^j: ∂_i n^j = (δ_ij - n_i n_j) / r_s
    dn = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            delta_ij = 1.0 if i == j else 0.0
            dn[i, j] = (delta_ij - n[i] * n[j]) / r_s
    
    # Derivatives of v^j: ∂_i v^j = -v_s [df/dr_s * n_i n_j + f * dn_ij]
    dv = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            dv[i, j] = -v_s * (df_drs * n[i] * n[j] + f * dn[i, j])
    
    # Metric derivatives (only spatial components vary)
    # ∂_k g_tt = ∂_k (v_i v^i) = 2 v^i ∂_k v_i
    # ∂_k g_ti = ∂_k v_i
    # ∂_k g_ij = 0 (spatial metric is flat)
    
    # Inverse metric
    g_inv = natario_inverse_metric(t, x, y, z, v_s, R, sigma, x_c)
    
    # Compute Christoffel symbols
    # Γ^λ_μν = (1/2) g^λσ (∂_μ g_σν + ∂_ν g_μσ - ∂_σ g_μν)
    
    for lam in range(4):
        for mu in range(4):
            for nu in range(4):
                sum_val = 0.0
                
                for sig in range(4):
                    # Need ∂_μ g_σν
                    if mu == 0:
                        dg_mu_sig_nu = 0.0  # Time derivative = 0 (stationary)
                    else:
                        i_mu = mu - 1
                        
                        if sig == 0 and nu == 0:
                            # ∂_i g_tt = 2 v^j ∂_i v_j
                            dg_mu_sig_nu = 2.0 * np.sum(v * dv[i_mu])
                        elif sig == 0 and nu > 0:
                            # ∂_i g_t,j = ∂_i v_j
                            j_nu = nu - 1
                            dg_mu_sig_nu = dv[i_mu, j_nu]
                        elif sig > 0 and nu == 0:
                            # ∂_i g_j,t = ∂_i v_j
                            j_sig = sig - 1
                            dg_mu_sig_nu = dv[i_mu, j_sig]
                        else:
                            # ∂_i g_jk = 0 (flat spatial metric)
                            dg_mu_sig_nu = 0.0
                    
                    # ∂_ν g_μσ (same logic)
                    if nu == 0:
                        dg_nu_mu_sig = 0.0
                    else:
                        i_nu = nu - 1
                        
                        if mu == 0 and sig == 0:
                            dg_nu_mu_sig = 2.0 * np.sum(v * dv[i_nu])
                        elif mu == 0 and sig > 0:
                            j_sig = sig - 1
                            dg_nu_mu_sig = dv[i_nu, j_sig]
                        elif mu > 0 and sig == 0:
                            j_mu = mu - 1
                            dg_nu_mu_sig = dv[i_nu, j_mu]
                        else:
                            dg_nu_mu_sig = 0.0
                    
                    # ∂_σ g_μν
                    if sig == 0:
                        dg_sig_mu_nu = 0.0
                    else:
                        i_sig = sig - 1
                        
                        if mu == 0 and nu == 0:
                            dg_sig_mu_nu = 2.0 * np.sum(v * dv[i_sig])
                        elif mu == 0 and nu > 0:
                            j_nu = nu - 1
                            dg_sig_mu_nu = dv[i_sig, j_nu]
                        elif mu > 0 and nu == 0:
                            j_mu = mu - 1
                            dg_sig_mu_nu = dv[i_sig, j_mu]
                        else:
                            dg_sig_mu_nu = 0.0
                    
                    sum_val += g_inv[lam, sig] * (dg_mu_sig_nu + dg_nu_mu_sig - dg_sig_mu_nu)
                
                Gamma[lam, mu, nu] = 0.5 * sum_val
    
    return Gamma


if __name__ == "__main__":
    """Test Natário metric implementation."""
    
    print("="*70)
    print("Natário Metric Test")
    print("="*70)
    
    # Test point: on x-axis at bubble wall
    t, x, y, z = 0.0, 100.0, 0.0, 0.0
    v_s, R, sigma = 1.0, 100.0, 10.0
    
    print(f"\nTest point: (t={t}, x={x}, y={y}, z={z})")
    print(f"Parameters: v_s={v_s}, R={R}m, σ={sigma}m")
    
    # Metric
    g = natario_metric(t, x, y, z, v_s, R, sigma)
    print(f"\nMetric g_μν:")
    print(g)
    
    # Inverse
    g_inv = natario_inverse_metric(t, x, y, z, v_s, R, sigma)
    print(f"\nInverse g^μν:")
    print(g_inv)
    
    # Check g g^-1 = I
    product = g @ g_inv
    print(f"\ng·g^-1 (should be identity):")
    print(product)
    print(f"Max error: {np.max(np.abs(product - np.eye(4))):.3e}")
    
    # Christoffel at center (should be 0 by symmetry)
    Gamma_center = natario_christoffel(0.0, 0.0, 0.0, 0.0, v_s, R, sigma)
    print(f"\nΓ at center: max component = {np.max(np.abs(Gamma_center)):.3e}")
    
    # Christoffel at wall
    Gamma_wall = natario_christoffel(t, x, y, z, v_s, R, sigma)
    print(f"Γ at wall: max component = {np.max(np.abs(Gamma_wall)):.3e}")
    
    # Compare to numerical Christoffel
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
    from phase_d.warp_eval.stress_energy import (
        compute_metric_derivatives,
        compute_christoffel_symbols
    )
    
    def metric_fn(t2, x2, y2, z2):
        return natario_metric(t2, x2, y2, z2, v_s, R, sigma)
    
    coords = np.array([t, x, y, z])
    dx = 1e-6
    
    dg_num = compute_metric_derivatives(metric_fn, coords, dx)
    g_at_point = metric_fn(*coords)
    Gamma_num = compute_christoffel_symbols(g_at_point, dg_num)
    
    diff = Gamma_wall - Gamma_num
    print(f"\nAnalytic vs numerical Γ:")
    print(f"  Max difference: {np.max(np.abs(diff)):.3e}")
    print(f"  Relative error: {np.max(np.abs(diff)) / np.max(np.abs(Gamma_num)):.3e}")
    
    print("\n✅ Natário metric implementation complete")
