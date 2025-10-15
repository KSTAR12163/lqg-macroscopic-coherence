"""
Analytic Alcubierre Metric and Christoffel Symbols

Provides analytic expressions for the Alcubierre warp bubble metric
and its Christoffel symbols to avoid numerical differentiation errors.

Metric:
    ds² = -c²dt² + [dx - v_s f(r_s) dt]² + dy² + dz²
    
where:
    r_s = √[(x - x_s(t))² + y² + z²]
    x_s(t) = v_s t (bubble center trajectory)
    f(r_s) = shape function (smooth top-hat)
"""

import numpy as np
from typing import Tuple


def alcubierre_shape_function(
    r_s: float,
    R: float,
    sigma: float
) -> Tuple[float, float, float]:
    """
    Compute Alcubierre shape function and its derivatives.
    
    f(r_s) = 0.5 * [tanh((R + σ - r_s)/σ) - tanh((R - σ - r_s)/σ)]
    
    This matches the parameterization in stress_energy.py:load_alcubierre_metric.
    
    Args:
        r_s: Distance from bubble center
        R: Bubble radius
        sigma: Wall thickness parameter
        
    Returns:
        (f, df/dr_s, d²f/dr_s²)
    """
    # Arguments for tanh
    arg_p = (R + sigma - r_s) / sigma
    arg_m = (R - sigma - r_s) / sigma
    
    # f(r_s)
    tanh_p = np.tanh(arg_p)
    tanh_m = np.tanh(arg_m)
    f = 0.5 * (tanh_p - tanh_m)
    
    # df/dr_s = 0.5 * [d/dr_s tanh(arg_p) - d/dr_s tanh(arg_m)]
    #          = 0.5 * [sech²(arg_p) * (-1/σ) - sech²(arg_m) * (-1/σ)]
    #          = (-1/2σ) * [sech²(arg_p) - sech²(arg_m)]
    sech2_p = 1.0 - tanh_p**2
    sech2_m = 1.0 - tanh_m**2
    df = (-1.0 / (2.0 * sigma)) * (sech2_p - sech2_m)
    
    # d²f/dr_s² = d/dr_s[(-1/2σ)(sech²(arg_p) - sech²(arg_m))]
    #           = (-1/2σ) * [d/dr_s sech²(arg_p) - d/dr_s sech²(arg_m)]
    # d/dx sech²(x) = -2 sech²(x) tanh(x)
    # d/dr_s sech²(arg) = -2 sech²(arg) tanh(arg) * d(arg)/dr_s
    #                   = -2 sech²(arg) tanh(arg) * (-1/σ)
    #                   = (2/σ) sech²(arg) tanh(arg)
    dsech2_p_drs = (2.0 / sigma) * sech2_p * tanh_p
    dsech2_m_drs = (2.0 / sigma) * sech2_m * tanh_m
    d2f = (-1.0 / (2.0 * sigma)) * (dsech2_p_drs - dsech2_m_drs)
    
    return f, df, d2f


def alcubierre_metric_analytic(
    t: float,
    x: float,
    y: float,
    z: float,
    v_s: float = 1.0,
    R: float = 100.0,
    sigma: float = 10.0
) -> np.ndarray:
    """
    Alcubierre metric tensor g_μν (analytic).
    
    Args:
        t, x, y, z: Spacetime coordinates
        v_s: Bubble velocity (dimensionless, in units of c)
        R: Bubble radius (m)
        sigma: Wall sharpness (1/m)
        
    Returns:
        g_μν (4×4 array)
    """
    # Bubble center position (stationary at origin for now)
    x_s = 0.0
    
    # Distance from center
    r_s = np.sqrt((x - x_s)**2 + y**2 + z**2)
    
    # Shape function
    f, _, _ = alcubierre_shape_function(r_s, R, sigma)
    
    # Metric components
    v_f = v_s * f  # Dimensionless
    
    g = np.eye(4)
    g[0, 0] = -1.0 + v_f**2
    g[0, 1] = g[1, 0] = -v_f
    g[1, 1] = 1.0
    g[2, 2] = 1.0
    g[3, 3] = 1.0
    
    return g


def alcubierre_christoffel_analytic(
    t: float,
    x: float,
    y: float,
    z: float,
    v_s: float = 1.0,
    R: float = 100.0,
    sigma: float = 10.0
) -> np.ndarray:
    """
    Christoffel symbols Γ^λ_μν for Alcubierre metric (analytic).
    
    Computed from:
        Γ^λ_μν = (1/2) g^λσ (∂_μ g_σν + ∂_ν g_μσ - ∂_σ g_μν)
        
    Args:
        t, x, y, z: Spacetime coordinates
        v_s: Bubble velocity (dimensionless, in units of c)
        R: Bubble radius (m)
        sigma: Wall sharpness (1/m)
        
    Returns:
        Γ^λ_μν (4×4×4 array)
    """
    # Bubble center (stationary at origin)
    x_s = 0.0
    dx = x - x_s
    r_s = np.sqrt(dx**2 + y**2 + z**2)
    
    # Avoid singularity at r_s = 0
    if r_s < 1e-10:
        return np.zeros((4, 4, 4))
    
    # Shape function and derivatives
    f, df, d2f = alcubierre_shape_function(r_s, R, sigma)
    
    # Partial derivatives of r_s (bubble stationary, so dr/dt = 0)
    dr_dx = dx / r_s
    dr_dy = y / r_s
    dr_dz = z / r_s
    dr_dt = 0.0  # Stationary bubble
    
    # Partial derivatives of f
    df_dt = df * dr_dt
    df_dx = df * dr_dx
    df_dy = df * dr_dy
    df_dz = df * dr_dz
    
    # Metric and inverse
    v_f = v_s * f
    v_df_dt = v_s * df_dt
    v_df_dx = v_s * df_dx
    v_df_dy = v_s * df_dy
    v_df_dz = v_s * df_dz
    
    # Inverse metric (2×2 block for t-x subspace)
    # det([[g_00, g_01], [g_10, g_11]]) = g_00 * g_11 - g_01² = -1
    # Inverse should be:
    #   g^00 = -1,
    #   g^01 = g^10 = -v_f,
    #   g^11 = 1 - v_f^2
    det_tx = -1.0
    g_inv = np.zeros((4, 4))
    g_inv[0, 0] = -1.0
    g_inv[0, 1] = g_inv[1, 0] = -v_f
    g_inv[1, 1] = 1.0 - v_f**2
    g_inv[2, 2] = 1.0
    g_inv[3, 3] = 1.0
    
    # Metric derivatives (only non-zero for t-x components)
    # g_00 = -1 + (v_s f)²
    dg_00_dt = 2 * v_s**2 * f * df_dt
    dg_00_dx = 2 * v_s**2 * f * df_dx
    dg_00_dy = 2 * v_s**2 * f * df_dy
    dg_00_dz = 2 * v_s**2 * f * df_dz
    
    # g_01 = g_10 = -v_s f
    dg_01_dt = -v_s * df_dt
    dg_01_dx = -v_s * df_dx
    dg_01_dy = -v_s * df_dy
    dg_01_dz = -v_s * df_dz
    
    # g_11 = g_22 = g_33 = 1 (constant)
    
    # Christoffel symbols
    Gamma = np.zeros((4, 4, 4))
    
    # Non-zero components (only involving t-x subspace)
    # Γ^0_00
    Gamma[0, 0, 0] = 0.5 * g_inv[0, 0] * dg_00_dt + 0.5 * g_inv[0, 1] * 2 * dg_01_dt
    
    # Γ^0_01 = Γ^0_10
    Gamma[0, 0, 1] = Gamma[0, 1, 0] = (
        0.5 * g_inv[0, 0] * dg_00_dx + 
        0.5 * g_inv[0, 1] * (dg_01_dt + dg_01_dx)
    )
    
    # Γ^0_02 = Γ^0_20
    Gamma[0, 0, 2] = Gamma[0, 2, 0] = (
        0.5 * g_inv[0, 0] * dg_00_dy + 
        0.5 * g_inv[0, 1] * dg_01_dy
    )
    
    # Γ^0_03 = Γ^0_30
    Gamma[0, 0, 3] = Gamma[0, 3, 0] = (
        0.5 * g_inv[0, 0] * dg_00_dz + 
        0.5 * g_inv[0, 1] * dg_01_dz
    )
    
    # Γ^0_11
    Gamma[0, 1, 1] = 0.5 * g_inv[0, 1] * 2 * dg_01_dx
    
    # Γ^0_12 = Γ^0_21
    Gamma[0, 1, 2] = Gamma[0, 2, 1] = 0.5 * g_inv[0, 1] * dg_01_dy
    
    # Γ^0_13 = Γ^0_31
    Gamma[0, 1, 3] = Gamma[0, 3, 1] = 0.5 * g_inv[0, 1] * dg_01_dz
    
    # Γ^1_00
    Gamma[1, 0, 0] = 0.5 * g_inv[1, 0] * dg_00_dt + 0.5 * g_inv[1, 1] * 2 * dg_01_dt
    
    # Γ^1_01 = Γ^1_10
    Gamma[1, 0, 1] = Gamma[1, 1, 0] = (
        0.5 * g_inv[1, 0] * dg_00_dx +
        0.5 * g_inv[1, 1] * (dg_01_dt + dg_01_dx)
    )
    
    # Γ^1_02 = Γ^1_20
    Gamma[1, 0, 2] = Gamma[1, 2, 0] = (
        0.5 * g_inv[1, 0] * dg_00_dy +
        0.5 * g_inv[1, 1] * dg_01_dy
    )
    
    # Γ^1_03 = Γ^1_30
    Gamma[1, 0, 3] = Gamma[1, 3, 0] = (
        0.5 * g_inv[1, 0] * dg_00_dz +
        0.5 * g_inv[1, 1] * dg_01_dz
    )
    
    # Γ^1_11
    Gamma[1, 1, 1] = 0.5 * g_inv[1, 1] * 2 * dg_01_dx
    
    # Γ^1_12 = Γ^1_21
    Gamma[1, 1, 2] = Gamma[1, 2, 1] = 0.5 * g_inv[1, 1] * dg_01_dy
    
    # Γ^1_13 = Γ^1_31
    Gamma[1, 1, 3] = Gamma[1, 3, 1] = 0.5 * g_inv[1, 1] * dg_01_dz
    
    # Γ^2_μν components (coupling to y-direction)
    # Γ^2_02 = Γ^2_20
    Gamma[2, 0, 2] = Gamma[2, 2, 0] = 0.5 * g_inv[2, 2] * dg_01_dy
    
    # Γ^2_12 = Γ^2_21
    Gamma[2, 1, 2] = Gamma[2, 2, 1] = 0.5 * g_inv[2, 2] * dg_01_dy
    
    # Γ^3_μν components (coupling to z-direction)
    # Γ^3_03 = Γ^3_30
    Gamma[3, 0, 3] = Gamma[3, 3, 0] = 0.5 * g_inv[3, 3] * dg_01_dz
    
    # Γ^3_13 = Γ^3_31
    Gamma[3, 1, 3] = Gamma[3, 3, 1] = 0.5 * g_inv[3, 3] * dg_01_dz
    
    return Gamma


def test_analytic_christoffel():
    """Test analytic Christoffel symbols against numerical."""
    from stress_energy import load_alcubierre_metric
    from geodesics import compute_christoffel_at_point
    
    # Parameters
    v_s = 1.0
    R = 100.0
    sigma = 10.0
    c = 299792458.0
    
    # Test point (near wall)
    coords = np.array([0.0, 100.0, 0.0, 0.0])
    
    # Analytic
    Gamma_analytic = alcubierre_christoffel_analytic(
        *coords, v_s=v_s, R=R, sigma=sigma
    )
    
    # Numerical
    metric_fn = load_alcubierre_metric(v_s, R, sigma)
    Gamma_numeric = compute_christoffel_at_point(metric_fn, coords, dx=1e-5)
    
    # Compare
    diff = np.abs(Gamma_analytic - Gamma_numeric)
    max_diff = np.max(diff)
    rel_diff = max_diff / (np.max(np.abs(Gamma_analytic)) + 1e-10)
    
    print("Analytic vs Numerical Christoffel Symbols:")
    print(f"  Max absolute difference: {max_diff:.3e}")
    print(f"  Max relative difference: {rel_diff:.3e}")
    print(f"  Max |Γ_analytic|: {np.max(np.abs(Gamma_analytic)):.3e}")
    print(f"  Max |Γ_numeric|: {np.max(np.abs(Gamma_numeric)):.3e}")
    
    if rel_diff < 0.01:
        print("  ✅ Agreement within 1%")
    else:
        print("  ⚠️  Significant discrepancy")
        print("\nLargest differences:")
        idx = np.unravel_index(np.argmax(diff), diff.shape)
        print(f"  Γ^{idx[0]}_{idx[1]}{idx[2]}: analytic={Gamma_analytic[idx]:.3e}, numeric={Gamma_numeric[idx]:.3e}")


if __name__ == "__main__":
    test_analytic_christoffel()
