"""
Portal-Induced Stress-Energy Modification

Derive δT_μν from axion-photon and axion-nucleon interactions
in a medium with finite coherence and saturation effects.

This is a conservative EFT sketch, not a complete derivation.
"""

from typing import Dict
import numpy as np


def compute_portal_delta_T(
    g_agamma: float,  # GeV⁻¹
    g_aN: float,      # dimensionless
    m_axion: float,   # GeV
    B_field: float,   # T
    E_field: float,   # V/m
    nucleon_density: float,  # m⁻³
    volume: float,    # m³
    coherence_time: float = 1e-15,  # s (timescale for coherent interactions)
    coherence_length: float = 1e-6  # m (spatial coherence)
) -> np.ndarray:
    """
    Compute portal-induced stress-energy modification δT_μν.
    
    Physical model (conservative):
    - Axion-photon mixing induces effective EM stress-energy correction
    - Axion-nucleon coupling modifies matter stress-energy
    - Finite coherence time/length suppress macroscopic effects
    - Saturation prevents runaway amplification
    
    EFT sketch:
    δT_μν ∼ g_aγ g_aN (EB) n_N (V_c τ_c / V)
    
    where V_c ~ λ_a³ is coherence volume, τ_c is coherence time.
    
    Args:
        g_agamma: Axion-photon coupling (GeV⁻¹)
        g_aN: Axion-nucleon coupling
        m_axion: Axion mass (GeV)
        B_field: Magnetic field (T)
        E_field: Electric field (V/m)
        nucleon_density: Nucleon number density (m⁻³)
        volume: Interaction volume (m³)
        coherence_time: Coherent interaction timescale (s)
        coherence_length: Spatial coherence length (m)
        
    Returns:
        δT_μν (4×4 array) in J/m³
    """
    # Physical constants
    c = 2.99792458e8  # m/s
    hbar = 1.054571817e-34  # J·s
    GEV_TO_J = 1.602176634e-10  # J
    GEV_TO_KG = GEV_TO_J / c**2
    
    # Axion Compton wavelength
    m_axion_kg = m_axion * GEV_TO_KG
    lambda_a = hbar / (m_axion_kg * c)  # m
    
    # Coherence volume
    V_coherence = coherence_length**3  # m³
    
    # Suppression factor from finite coherence
    # (Only coherent volume contributes, averaged over total volume)
    coherence_suppression = min(V_coherence / volume, 1.0)
    time_suppression = coherence_time * c / coherence_length  # dimensionless
    
    # Field energy density
    epsilon_0 = 8.854187817e-12  # F/m
    mu_0 = 4 * np.pi * 1e-7  # H/m
    
    u_E = 0.5 * epsilon_0 * E_field**2  # J/m³
    u_B = 0.5 * B_field**2 / mu_0  # J/m³
    u_field = u_E + u_B
    
    # Coupling strength (SI units)
    g_agamma_SI = g_agamma / GEV_TO_J  # J⁻¹
    
    # Effective stress-energy density from portal
    # Conservative scaling: linear in field energy and nucleon density
    # with coherence suppression
    
    delta_rho = (abs(g_agamma_SI * g_aN) * 
                 u_field * 
                 nucleon_density * 
                 lambda_a**2 *
                 coherence_suppression *
                 time_suppression)  # J/m³
    
    # Saturation: δT should not exceed field energy density
    delta_rho = min(delta_rho, 0.1 * u_field)  # At most 10% of field energy
    
    # Construct stress-energy tensor
    # Assume isotropic pressure contribution
    delta_T = np.zeros((4, 4))
    
    # Energy density (time-time component)
    delta_T[0, 0] = delta_rho
    
    # Pressure (spatial diagonal)
    # For EM-like contribution: p ~ u/3
    delta_p = delta_rho / 3.0
    delta_T[1, 1] = delta_p
    delta_T[2, 2] = delta_p
    delta_T[3, 3] = delta_p
    
    return delta_T


def apply_portal_correction(
    T_baseline: np.ndarray,
    delta_T_portal: np.ndarray,
    screening_factor: float = 1.0
) -> np.ndarray:
    """
    Apply portal-induced correction to baseline stress-energy.
    
    T_total = T_baseline + α_screen × δT_portal
    
    where α_screen accounts for medium screening effects.
    
    Args:
        T_baseline: Baseline stress-energy from metric (4×4)
        delta_T_portal: Portal contribution (4×4)
        screening_factor: Medium screening (0 = fully screened, 1 = no screening)
        
    Returns:
        T_total (4×4)
    """
    T_total = T_baseline + screening_factor * delta_T_portal
    
    return T_total


def estimate_screening_factor(
    nucleon_density: float,
    temperature: float = 300.0,  # K
    conductivity: float = 1e7  # S/m (for metals)
) -> float:
    """
    Estimate medium screening of axion-photon mixing.
    
    In conductive media, photon acquires effective mass (plasma frequency)
    which can suppress axion-photon conversion.
    
    Args:
        nucleon_density: n_N (m⁻³)
        temperature: Medium temperature (K)
        conductivity: Electrical conductivity (S/m)
        
    Returns:
        Screening factor (0 to 1)
    """
    # Plasma frequency
    e = 1.602176634e-19  # C
    epsilon_0 = 8.854187817e-12  # F/m
    m_e = 9.10938356e-31  # kg
    
    # Electron density (rough: n_e ~ n_N for neutral matter)
    n_e = nucleon_density
    
    # Plasma frequency (rad/s)
    omega_p = np.sqrt(n_e * e**2 / (epsilon_0 * m_e))
    
    # Debye length
    k_B = 1.380649e-23  # J/K
    lambda_D = np.sqrt(epsilon_0 * k_B * temperature / (n_e * e**2))
    
    # Screening factor: exponential suppression beyond Debye length
    # (Simplified - real screening depends on geometry and frequency)
    
    # For axion-photon mixing, screening is weak in insulators,
    # strong in conductors
    
    if conductivity > 1e6:  # Conductor
        screening = 0.1  # Strongly screened
    elif conductivity > 1e3:  # Semiconductor
        screening = 0.5  # Moderately screened
    else:  # Insulator
        screening = 1.0  # Weakly screened
    
    return screening


def compute_portal_stress_energy_full(
    portal_params: Dict,
    field_params: Dict,
    medium_params: Dict
) -> Dict:
    """
    Full pipeline for portal stress-energy computation.
    
    Args:
        portal_params: {g_agamma, g_aN, m_axion}
        field_params: {B_field, E_field, volume, coherence_time, coherence_length}
        medium_params: {nucleon_density, temperature, conductivity}
        
    Returns:
        Dictionary with δT_μν and diagnostics
    """
    # Compute portal contribution
    delta_T = compute_portal_delta_T(
        g_agamma=portal_params['g_agamma'],
        g_aN=portal_params['g_aN'],
        m_axion=portal_params['m_axion'],
        B_field=field_params['B_field'],
        E_field=field_params['E_field'],
        nucleon_density=medium_params['nucleon_density'],
        volume=field_params['volume'],
        coherence_time=field_params.get('coherence_time', 1e-15),
        coherence_length=field_params.get('coherence_length', 1e-6)
    )
    
    # Estimate screening
    screening = estimate_screening_factor(
        nucleon_density=medium_params['nucleon_density'],
        temperature=medium_params.get('temperature', 300.0),
        conductivity=medium_params.get('conductivity', 1e-5)  # Default: insulator
    )
    
    # Extract components
    delta_rho = delta_T[0, 0]
    delta_p = (delta_T[1, 1] + delta_T[2, 2] + delta_T[3, 3]) / 3.0
    
    return {
        'delta_T_munu': delta_T,
        'delta_rho_J_m3': delta_rho,
        'delta_p_J_m3': delta_p,
        'screening_factor': screening,
        'delta_T_screened': screening * delta_T,
        'coherence_suppression': field_params.get('coherence_length', 1e-6)**3 / field_params['volume']
    }


# TODO: Integrate with actual field theory calculations
# - Derive from QFT Lagrangian with axion-photon and axion-nucleon terms
# - Include dispersion relations and frequency matching
# - Account for quantum coherence and decoherence
# - Validate against experimental bounds on energy density modifications
