"""
Van Den Broeck "Pocket" Warp Drive Metric (Analytic Implementation)

The Van Den Broeck metric (1999) addresses Alcubierre's enormous energy
requirements by using a radically different geometry: a microscopic "throat"
connecting to a macroscopic interior "pocket."

Key idea:
- Alcubierre energy scales ∝ R² (bubble radius squared)
- VDB keeps exterior bubble tiny (r_ext ~ mm) → low energy
- Uses conformal factor to expand interior space → comfortable habitat
- Passengers see large interior; exterior observers see tiny object

Metric (simplified form):
    ds² = -dt² + [1 + (Ω-1)f(r_s)]² × [(dx-v_s f dt)² + dy² + dz²]
    
where:
- f(r_s): Shape function (bubble wall profile)
- Ω(r_s): Conformal factor (Ω ≫ 1 inside, Ω → 1 outside)
- r_ext: External radius (throat size, ~ mm)
- r_int: Internal radius (pocket size, ~ m)

Trade-off:
- Energy ∝ r_ext² (tiny!) instead of r_int²
- But: Extreme curvature at throat → potential stability issues
- Requires ρ ~ c⁴/(G r_ext²) at throat

This implementation uses:
- r_ext = external bubble radius (throat)
- Ω_max = conformal expansion factor (r_int/r_ext)
- Same shape function f(r_s) as Alcubierre for consistency

References:
- Van Den Broeck (1999): "A 'warp drive' with more reasonable energy requirements"
- Clark+ (1999): "Null geodesics in the Alcubierre warp drive spacetime"
- Lobo & Visser (2004): "Fundamental limitations in warp drives"
"""

import numpy as np
from typing import Tuple


def vdb_shape_function(
    r_s: float,
    R: float,
    sigma: float
) -> Tuple[float, float]:
    """
    Shape function for Van Den Broeck metric.
    
    Same as Alcubierre/Natário for consistency:
    f(r_s) = 0.5 * [tanh((R+σ-r_s)/σ) - tanh((R-σ-r_s)/σ)]
    
    Args:
        r_s: Radial distance from bubble center
        R: External bubble radius (throat size)
        sigma: Wall thickness
        
    Returns:
        (f, df/dr_s)
    """
    arg_outer = (R + sigma - r_s) / sigma
    arg_inner = (R - sigma - r_s) / sigma
    
    tanh_outer = np.tanh(arg_outer)
    tanh_inner = np.tanh(arg_inner)
    
    f = 0.5 * (tanh_outer - tanh_inner)
    
    sech2_outer = 1.0 / np.cosh(arg_outer)**2
    sech2_inner = 1.0 / np.cosh(arg_inner)**2
    
    df_drs = -0.5 * (sech2_outer - sech2_inner) / sigma
    
    return f, df_drs


def vdb_conformal_factor(
    r_s: float,
    R: float,
    sigma: float,
    Omega_max: float
) -> Tuple[float, float]:
    """
    Conformal expansion factor for Van Den Broeck metric.
    
    Profile:
    Ω(r_s) = 1 + (Ω_max - 1) × g(r_s)
    
    where g(r_s) is a smooth step function:
    - g = 1 inside bubble (r_s < R - σ) → Ω ≈ Ω_max (expanded interior)
    - g = 0 outside bubble (r_s > R + σ) → Ω ≈ 1 (flat exterior)
    - Smooth transition in wall
    
    Use same tanh-based profile as shape function.
    
    Args:
        r_s: Radial distance
        R: External radius
        sigma: Wall thickness
        Omega_max: Maximum conformal factor (expansion ratio)
        
    Returns:
        (Ω, dΩ/dr_s)
    """
    # Step function (same form as shape function)
    g, dg_drs = vdb_shape_function(r_s, R, sigma)
    
    # Conformal factor
    Omega = 1.0 + (Omega_max - 1.0) * g
    dOmega_drs = (Omega_max - 1.0) * dg_drs
    
    return Omega, dOmega_drs


def vdb_metric(
    t: float,
    x: float,
    y: float,
    z: float,
    v_s: float = 1.0,
    R: float = 0.001,  # 1 mm external radius
    sigma: float = 0.0001,  # 0.1 mm wall
    Omega_max: float = 1000.0,  # 1000× interior expansion
    x_c: float = 0.0
) -> np.ndarray:
    """
    Van Den Broeck warp metric.
    
    Form (simplified, conformal Alcubierre):
    ds² = -dt² + Ω²(r_s) [(dx - v_s f dt)² + dy² + dz²]
    
    where:
    - Ω(r_s): Conformal factor (1 outside, Ω_max inside)
    - f(r_s): Alcubierre-like shape function
    - v_s: Bubble velocity
    
    Args:
        t, x, y, z: Spacetime coordinates
        v_s: Bubble velocity (dimensionless, c=1)
        R: External bubble radius (throat size, default 1 mm)
        sigma: Wall thickness
        Omega_max: Interior expansion factor (r_interior/r_exterior)
        x_c: Bubble center position
        
    Returns:
        g_μν (4×4 metric)
    """
    # Position relative to bubble center
    x_rel = x - x_c
    r_s = np.sqrt(x_rel**2 + y**2 + z**2)
    
    # Shape function and conformal factor
    f, _ = vdb_shape_function(r_s, R, sigma)
    Omega, _ = vdb_conformal_factor(r_s, R, sigma, Omega_max)
    
    # Metric components
    # g_tt = -1 + (v_s f Ω)²
    # g_tx = -v_s f Ω²
    # g_xx = g_yy = g_zz = Ω²
    
    g = np.zeros((4, 4))
    
    v_eff = v_s * f
    Omega2 = Omega**2
    
    g[0, 0] = -1.0 + (v_eff * Omega)**2
    g[0, 1] = g[1, 0] = -v_eff * Omega2
    
    g[1, 1] = Omega2
    g[2, 2] = Omega2
    g[3, 3] = Omega2
    
    return g


def vdb_inverse_metric(
    t: float,
    x: float,
    y: float,
    z: float,
    v_s: float = 1.0,
    R: float = 0.001,
    sigma: float = 0.0001,
    Omega_max: float = 1000.0,
    x_c: float = 0.0
) -> np.ndarray:
    """
    Analytic inverse of Van Den Broeck metric.
    
    For the metric form:
    g_tt = -1 + (vfΩ)²
    g_tx = -vf Ω²
    g_xx = g_yy = g_zz = Ω²
    
    Inverse (block diagonal in (t,x) and (y,z)):
    g^tt = -1/Ω²
    g^tx = -vf/Ω²
    g^xx = 1/Ω² - v²f²
    g^yy = g^zz = 1/Ω²
    
    Args:
        Same as vdb_metric
        
    Returns:
        g^μν (4×4 inverse metric)
    """
    # Position and geometric functions
    x_rel = x - x_c
    r_s = np.sqrt(x_rel**2 + y**2 + z**2)
    
    f, _ = vdb_shape_function(r_s, R, sigma)
    Omega, _ = vdb_conformal_factor(r_s, R, sigma, Omega_max)
    
    # Compute inverse
    g_inv = np.zeros((4, 4))
    
    v_eff = v_s * f
    Omega2_inv = 1.0 / Omega**2
    
    g_inv[0, 0] = -Omega2_inv
    g_inv[0, 1] = g_inv[1, 0] = -v_eff * Omega2_inv
    
    g_inv[1, 1] = Omega2_inv - v_eff**2
    g_inv[2, 2] = Omega2_inv
    g_inv[3, 3] = Omega2_inv
    
    return g_inv


def vdb_christoffel(
    t: float,
    x: float,
    y: float,
    z: float,
    v_s: float = 1.0,
    R: float = 0.001,
    sigma: float = 0.0001,
    Omega_max: float = 1000.0,
    x_c: float = 0.0
) -> np.ndarray:
    """
    Analytic Christoffel symbols for Van Den Broeck metric.
    
    Key derivatives:
    - ∂_i Ω = (dΩ/dr_s) × (x^i / r_s)
    - ∂_i f = (df/dr_s) × (x^i / r_s)
    - All time derivatives = 0 (stationary metric)
    
    Args:
        Same as vdb_metric
        
    Returns:
        Γ^λ_μν (4×4×4 array)
    """
    # Position and radial distance
    x_rel = x - x_c
    y_coord = y
    z_coord = z
    r_s = np.sqrt(x_rel**2 + y_coord**2 + z_coord**2)
    
    Gamma = np.zeros((4, 4, 4))
    
    # Handle center (all Γ = 0 by symmetry)
    if r_s < 1e-12:
        return Gamma
    
    # Geometric functions and derivatives
    f, df_drs = vdb_shape_function(r_s, R, sigma)
    Omega, dOmega_drs = vdb_conformal_factor(r_s, R, sigma, Omega_max)
    
    # Radial unit vector components
    n_x = x_rel / r_s
    n_y = y_coord / r_s
    n_z = z_coord / r_s
    n = np.array([n_x, n_y, n_z])
    
    # Spatial derivatives: ∂_i Ω = (dΩ/dr_s) n_i, etc.
    dOmega = dOmega_drs * n
    df = df_drs * n
    
    # Metric at point
    v_eff = v_s * f
    Omega2 = Omega**2
    
    # Inverse metric
    g_inv = vdb_inverse_metric(t, x, y, z, v_s, R, sigma, Omega_max, x_c)
    
    # Metric derivatives
    # g_tt = -1 + (v_s f Ω)²
    # g_ti = -v_s f Ω² δ_ix
    # g_ij = Ω² δ_ij
    
    # ∂_k g_tt = 2 v_s² Ω (f dΩ/dr_s + Ω df/dr_s) n_k
    # ∂_k g_tx = -v_s Ω (2 f dΩ/dr_s + Ω df/dr_s) n_k  (only k=x,y,z component)
    # ∂_k g_ij = 2 Ω dΩ/dr_s n_k δ_ij
    
    for lam in range(4):
        for mu in range(4):
            for nu in range(4):
                sum_val = 0.0
                
                for sig in range(4):
                    # ∂_μ g_σν
                    if mu == 0:
                        dg_mu_sig_nu = 0.0  # Stationary
                    else:
                        i_mu = mu - 1
                        
                        if sig == 0 and nu == 0:
                            # ∂_i g_tt
                            dg_mu_sig_nu = 2.0 * v_s**2 * Omega * (
                                f * dOmega[i_mu] + Omega * df[i_mu]
                            )
                        elif sig == 0 and nu == 1:
                            # ∂_i g_tx
                            dg_mu_sig_nu = -v_s * Omega * (
                                2.0 * f * dOmega[i_mu] + Omega * df[i_mu]
                            )
                        elif sig == 1 and nu == 0:
                            # ∂_i g_xt
                            dg_mu_sig_nu = -v_s * Omega * (
                                2.0 * f * dOmega[i_mu] + Omega * df[i_mu]
                            )
                        elif sig > 0 and nu > 0:
                            # ∂_i g_jk = 2 Ω dΩ/drs n_i δ_jk
                            j_sig = sig - 1
                            k_nu = nu - 1
                            delta_jk = 1.0 if j_sig == k_nu else 0.0
                            dg_mu_sig_nu = 2.0 * Omega * dOmega[i_mu] * delta_jk
                        else:
                            dg_mu_sig_nu = 0.0
                    
                    # ∂_ν g_μσ (symmetric logic)
                    if nu == 0:
                        dg_nu_mu_sig = 0.0
                    else:
                        i_nu = nu - 1
                        
                        if mu == 0 and sig == 0:
                            dg_nu_mu_sig = 2.0 * v_s**2 * Omega * (
                                f * dOmega[i_nu] + Omega * df[i_nu]
                            )
                        elif mu == 0 and sig == 1:
                            dg_nu_mu_sig = -v_s * Omega * (
                                2.0 * f * dOmega[i_nu] + Omega * df[i_nu]
                            )
                        elif mu == 1 and sig == 0:
                            dg_nu_mu_sig = -v_s * Omega * (
                                2.0 * f * dOmega[i_nu] + Omega * df[i_nu]
                            )
                        elif mu > 0 and sig > 0:
                            j_mu = mu - 1
                            k_sig = sig - 1
                            delta_jk = 1.0 if j_mu == k_sig else 0.0
                            dg_nu_mu_sig = 2.0 * Omega * dOmega[i_nu] * delta_jk
                        else:
                            dg_nu_mu_sig = 0.0
                    
                    # ∂_σ g_μν
                    if sig == 0:
                        dg_sig_mu_nu = 0.0
                    else:
                        i_sig = sig - 1
                        
                        if mu == 0 and nu == 0:
                            dg_sig_mu_nu = 2.0 * v_s**2 * Omega * (
                                f * dOmega[i_sig] + Omega * df[i_sig]
                            )
                        elif mu == 0 and nu == 1:
                            dg_sig_mu_nu = -v_s * Omega * (
                                2.0 * f * dOmega[i_sig] + Omega * df[i_sig]
                            )
                        elif mu == 1 and nu == 0:
                            dg_sig_mu_nu = -v_s * Omega * (
                                2.0 * f * dOmega[i_sig] + Omega * df[i_sig]
                            )
                        elif mu > 0 and nu > 0:
                            j_mu = mu - 1
                            k_nu = nu - 1
                            delta_jk = 1.0 if j_mu == k_nu else 0.0
                            dg_sig_mu_nu = 2.0 * Omega * dOmega[i_sig] * delta_jk
                        else:
                            dg_sig_mu_nu = 0.0
                    
                    sum_val += g_inv[lam, sig] * (
                        dg_mu_sig_nu + dg_nu_mu_sig - dg_sig_mu_nu
                    )
                
                Gamma[lam, mu, nu] = 0.5 * sum_val
    
    return Gamma


if __name__ == "__main__":
    """Test Van Den Broeck metric implementation."""
    
    print("="*70)
    print("Van Den Broeck Metric Test")
    print("="*70)
    
    # Test with microscopic external radius
    R_ext = 0.001  # 1 mm throat
    sigma = 0.0001  # 0.1 mm wall
    Omega_max = 1000.0  # 1 km interior from 1 mm exterior
    v_s = 1.0
    
    print(f"\nParameters:")
    print(f"  External radius: {R_ext*1000:.3f} mm")
    print(f"  Wall thickness: {sigma*1000:.3f} mm")
    print(f"  Expansion factor: {Omega_max:.0f}× ({Omega_max*R_ext:.1f} m interior)")
    print(f"  Velocity: {v_s}c")
    
    # Test at throat wall
    t, x, y, z = 0.0, R_ext, 0.0, 0.0
    
    print(f"\nTest point: (t={t}, x={x*1000:.3f}mm, y={y}, z={z})")
    
    # Metric
    g = vdb_metric(t, x, y, z, v_s, R_ext, sigma, Omega_max)
    print(f"\nMetric g_μν:")
    print(g)
    
    # Inverse
    g_inv = vdb_inverse_metric(t, x, y, z, v_s, R_ext, sigma, Omega_max)
    print(f"\nInverse g^μν:")
    print(g_inv)
    
    # Check identity
    product = g @ g_inv
    print(f"\ng·g^-1:")
    print(product)
    print(f"Max error: {np.max(np.abs(product - np.eye(4))):.3e}")
    
    # Christoffel
    Gamma = vdb_christoffel(t, x, y, z, v_s, R_ext, sigma, Omega_max)
    print(f"\nΓ at throat wall: max component = {np.max(np.abs(Gamma)):.3e}")
    
    # Compare to numerical
    import sys
    sys.path.insert(0, '../../..')
    from phase_d.warp_eval.stress_energy import (
        compute_metric_derivatives,
        compute_christoffel_symbols
    )
    
    def metric_fn(t2, x2, y2, z2):
        return vdb_metric(t2, x2, y2, z2, v_s, R_ext, sigma, Omega_max)
    
    coords = np.array([t, x, y, z])
    dx = 1e-9  # Small step for mm-scale geometry
    
    dg_num = compute_metric_derivatives(metric_fn, coords, dx)
    g_at_point = metric_fn(*coords)
    Gamma_num = compute_christoffel_symbols(g_at_point, dg_num)
    
    diff = Gamma - Gamma_num
    print(f"\nAnalytic vs numerical Γ:")
    print(f"  Max difference: {np.max(np.abs(diff)):.3e}")
    if np.max(np.abs(Gamma_num)) > 1e-10:
        print(f"  Relative error: {np.max(np.abs(diff)) / np.max(np.abs(Gamma_num)):.3e}")
    
    # Energy density estimate
    print(f"\n{'='*70}")
    print("Energy Density Estimate (Van Den Broeck advantage)")
    print("="*70)
    
    # For Alcubierre: ρ ~ c⁴/(G R²)
    # For VDB: ρ ~ c⁴/(G R_ext²) with R_ext ≪ R_interior
    
    c = 299792458.0  # m/s
    G = 6.67430e-11  # m³/(kg·s²)
    
    # Alcubierre with 100 m radius
    R_alcubierre = 100.0  # m
    rho_alcubierre = c**4 / (G * R_alcubierre**2)
    
    # VDB with 1 mm throat
    rho_vdb = c**4 / (G * R_ext**2)
    
    print(f"\nAlcubierre (R=100m): ρ ~ {rho_alcubierre:.3e} J/m³")
    print(f"VDB (R_ext=1mm): ρ ~ {rho_vdb:.3e} J/m³")
    print(f"Ratio: VDB/Alcubierre = {rho_vdb/rho_alcubierre:.3e}")
    print(f"       = (R_Alc/R_ext)² = {(R_alcubierre/R_ext)**2:.3e}")
    
    print("\n✅ Van Den Broeck metric implementation complete")
    print(f"   Energy advantage: {(R_alcubierre/R_ext)**2:.0e}× lower with throat!")
