"""
Tier 3 Exotic Coupling: Portal Mechanisms

Explore beyond-standard-model portal couplings that could enhance
effective matter-geometry coupling g_eff.

Mechanisms:
1. Axion/ALP portal: Light pseudoscalar coupled to photons and geometry
2. Dark photon portal: Hidden U(1) sector mixing with SM photon
3. Combined portals: Synergistic effects

All calculations respect experimental bounds and numerical guardrails.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional
import numpy as np

# Import numerical guardrails
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.numerical_guardrails import validate_coupling, G_EFF_THRESHOLD


@dataclass
class PortalCoupling:
    """
    Portal coupling specification.
    
    Attributes:
        name: Portal mechanism identifier
        coupling_constant: Dimensionless coupling strength
        mass_scale: Mass scale of new particle (GeV)
        mixing_angle: Kinetic mixing angle (if applicable)
        experimental_bound: Current experimental constraint
    """
    name: str
    coupling_constant: float
    mass_scale: float  # GeV
    mixing_angle: Optional[float] = None
    experimental_bound: Optional[Dict[str, float]] = None


class AxionPortal:
    """
    Axion-like particle (ALP) portal coupling.
    
    Physics:
    - Pseudoscalar field a(x) coupled to photons: ℒ ⊃ (g_aγγ/4) a F F̃
    - Can also couple to matter: ℒ ⊃ (g_aN/Λ) a N̄N
    - Induces effective matter-geometry coupling via photon-geometry interaction
    
    Enhancement mechanism:
    - Axion mediates long-range force between matter and curvature
    - Effective coupling: g_eff ~ g_aγγ × g_aN × (photon density)
    
    Constraints:
    - Solar axion searches: g_aγγ < 6.6e-11 GeV⁻¹ (CAST)
    - Astrophysical: g_aN < 1e-10 (supernova cooling)
    - Mass: m_a < 1 eV typically
    """
    
    def __init__(self):
        self.hbar_c = 0.1973  # GeV·fm
        self.G_N = 6.674e-11  # m³/kg/s²
        
    def compute_effective_coupling(
        self,
        g_agamma: float,  # GeV⁻¹
        g_aN: float,      # Dimensionless
        m_axion: float,   # GeV
        photon_density: float = 1e15  # photons/m³ (typical lab)
    ) -> Tuple[float, Dict[str, float]]:
        """
        Compute effective matter-geometry coupling induced by axion portal.
        
        Args:
            g_agamma: Axion-photon coupling (GeV⁻¹)
            g_aN: Axion-nucleon coupling (dimensionless)
            m_axion: Axion mass (GeV)
            photon_density: Photon number density (m⁻³)
            
        Returns:
            (g_eff, diagnostics) tuple
        """
        # Convert to SI units
        m_axion_kg = m_axion * 1.783e-27  # GeV to kg
        
        # Axion propagator at low momentum: ~ 1/m_a²
        # Effective coupling through axion exchange
        
        # Photon field energy density (rough estimate)
        # E_photon ~ hbar * omega, typical optical omega ~ 1 eV
        E_photon_per_particle = 1.6e-19  # Joules (1 eV)
        rho_photon = photon_density * E_photon_per_particle  # J/m³
        
        # Effective 4-point vertex: matter - axion - photon - gravity
        # Dimensional analysis: [g_eff] = J
        # g_eff ~ g_agamma * g_aN * rho_photon * (hbar*c / m_a)² * G_N * M_planck²
        
        # Planck mass
        M_planck_kg = np.sqrt(self.hbar_c * 1e15 / (self.G_N * 3e8))  # kg
        
        # Length scale
        lambda_axion = self.hbar_c * 1e-15 / m_axion  # meters
        
        # Effective coupling (very rough estimate)
        g_eff = (abs(g_agamma) * 1e9) * abs(g_aN) * rho_photon * (lambda_axion**2)
        
        # Apply guardrails
        validation = validate_coupling(
            g_eff,
            name=f"Axion portal: g_aγ={g_agamma:.2e}, g_aN={g_aN:.2e}, m_a={m_axion:.2e} GeV"
        )
        is_valid = validation.is_valid
        messages = [validation.message] if validation.message else []
        
        diagnostics = {
            'g_agamma': g_agamma,
            'g_aN': g_aN,
            'm_axion_GeV': m_axion,
            'm_axion_kg': m_axion_kg,
            'photon_density': photon_density,
            'lambda_axion_m': lambda_axion,
            'g_eff_J': g_eff,
            'passes_guardrails': is_valid,
            'is_warning': validation.is_warning,
            'guardrail_messages': messages,
            'vs_threshold': g_eff / G_EFF_THRESHOLD if G_EFF_THRESHOLD > 0 else float('inf')
        }
        
        return g_eff, diagnostics
    
    def scan_parameter_space(
        self,
        bounds: str = 'conservative'
    ) -> List[Dict[str, float]]:
        """
        Scan portal parameter space within experimental bounds.
        
        Args:
            bounds: 'conservative', 'aggressive', or 'theoretical'
            
        Returns:
            List of (parameters, g_eff, diagnostics) dictionaries
        """
        if bounds == 'conservative':
            # Well within current bounds
            g_agamma_values = np.logspace(-12, -11, 5)  # GeV⁻¹
            g_aN_values = np.logspace(-12, -10, 5)
            m_axion_values = np.logspace(-6, -3, 5)  # 1 μeV to 1 meV
        elif bounds == 'aggressive':
            # Push to experimental limits
            g_agamma_values = np.logspace(-11, -10, 10)
            g_aN_values = np.logspace(-10, -9, 10)
            m_axion_values = np.logspace(-4, -1, 10)  # 0.1 meV to 0.1 GeV
        else:  # theoretical
            # No experimental constraints, explore full range
            g_agamma_values = np.logspace(-10, -8, 15)
            g_aN_values = np.logspace(-8, -6, 15)
            m_axion_values = np.logspace(-3, 0, 15)  # 1 meV to 1 GeV
        
        results = []
        
        for g_ag in g_agamma_values:
            for g_aN in g_aN_values:
                for m_a in m_axion_values:
                    g_eff, diag = self.compute_effective_coupling(g_ag, g_aN, m_a)
                    
                    results.append({
                        'g_agamma': g_ag,
                        'g_aN': g_aN,
                        'm_axion': m_a,
                        'g_eff': g_eff,
                        'passes_guardrails': diag['passes_guardrails'],
                        'vs_threshold': diag['vs_threshold']
                    })
        
        # Sort by g_eff
        results.sort(key=lambda x: x['g_eff'], reverse=True)
        
        return results


class DarkPhotonPortal:
    """
    Dark photon (hidden U(1)) portal coupling.
    
    Physics:
    - Hidden photon A' coupled to SM photon via kinetic mixing: ℒ ⊃ (ε/2) F_μν F'^μν
    - Can modify effective charge seen by gravity
    - Mass m_A' sets range of interaction
    
    Enhancement mechanism:
    - Dark sector fields can have different coupling to curvature
    - Mixing allows matter in SM to "see" enhanced gravity coupling through dark sector
    
    Constraints:
    - Beam dump experiments: ε < 1e-3 for m_A' ~ MeV
    - Cosmology: ε < 1e-6 - 1e-10 depending on m_A'
    """
    
    def __init__(self):
        self.G_N = 6.674e-11  # m³/kg/s²
        
    def compute_effective_coupling(
        self,
        epsilon: float,     # Kinetic mixing parameter
        m_dark_photon: float,  # GeV
        enhancement_factor: float = 1.0  # Dark sector coupling enhancement
    ) -> Tuple[float, Dict[str, float]]:
        """
        Compute effective coupling through dark photon mixing.
        
        Args:
            epsilon: Kinetic mixing angle
            m_dark_photon: Dark photon mass (GeV)
            enhancement_factor: Ratio of dark/visible gravity coupling
            
        Returns:
            (g_eff, diagnostics) tuple
        """
        # Effective coupling modification: g_eff ~ epsilon² * enhancement_factor * g_base
        # where g_base is baseline matter-geometry coupling
        
        g_base = 1e-121  # Baseline from LQG (Joules)
        
        # Mixing allows fraction epsilon² of matter to couple with enhancement
        g_eff = g_base * (1 + (epsilon**2) * (enhancement_factor - 1))
        
        # Apply guardrails
        validation = validate_coupling(
            g_eff,
            name=f"Dark photon: ε={epsilon:.2e}, m_A'={m_dark_photon:.2e} GeV, η={enhancement_factor:.2e}"
        )
        is_valid = validation.is_valid
        messages = [validation.message] if validation.message else []
        
        diagnostics = {
            'epsilon': epsilon,
            'm_dark_photon_GeV': m_dark_photon,
            'enhancement_factor': enhancement_factor,
            'g_base_J': g_base,
            'g_eff_J': g_eff,
            'boost': g_eff / g_base,
            'passes_guardrails': is_valid,
            'is_warning': validation.is_warning,
            'guardrail_messages': messages,
            'vs_threshold': g_eff / G_EFF_THRESHOLD if G_EFF_THRESHOLD > 0 else float('inf')
        }
        
        return g_eff, diagnostics
    
    def scan_parameter_space(
        self,
        bounds: str = 'conservative'
    ) -> List[Dict[str, float]]:
        """
        Scan dark photon parameter space.
        
        Returns:
            List of (parameters, g_eff, diagnostics) dictionaries
        """
        if bounds == 'conservative':
            epsilon_values = np.logspace(-8, -6, 5)
            m_values = np.logspace(-3, -1, 5)  # 1 MeV to 0.1 GeV
            enhancement_values = np.logspace(0, 2, 5)  # 1 to 100
        elif bounds == 'aggressive':
            epsilon_values = np.logspace(-6, -4, 10)
            m_values = np.logspace(-2, 0, 10)
            enhancement_values = np.logspace(0, 4, 10)  # 1 to 10,000
        else:  # theoretical
            epsilon_values = np.logspace(-4, -2, 15)
            m_values = np.logspace(-1, 1, 15)
            enhancement_values = np.logspace(0, 6, 15)  # 1 to 1,000,000
        
        results = []
        
        for eps in epsilon_values:
            for m_dp in m_values:
                for eta in enhancement_values:
                    g_eff, diag = self.compute_effective_coupling(eps, m_dp, eta)
                    
                    results.append({
                        'epsilon': eps,
                        'm_dark_photon': m_dp,
                        'enhancement_factor': eta,
                        'g_eff': g_eff,
                        'boost': diag['boost'],
                        'passes_guardrails': diag['passes_guardrails'],
                        'vs_threshold': diag['vs_threshold']
                    })
        
        results.sort(key=lambda x: x['g_eff'], reverse=True)
        
        return results


def find_best_portal_coupling(bounds: str = 'conservative') -> Dict[str, Any]:
    """
    Search for best portal coupling configuration.
    
    Args:
        bounds: Parameter space bounds
        
    Returns:
        Summary with best configurations
    """
    print(f"{'='*70}")
    print(f"PORTAL COUPLING SCAN ({bounds.upper()} BOUNDS)")
    print(f"{'='*70}")
    
    # Axion portal
    print("\n1. AXION PORTAL SCAN")
    axion = AxionPortal()
    axion_results = axion.scan_parameter_space(bounds)
    
    print(f"   Scanned {len(axion_results)} configurations")
    best_axion = None
    if axion_results:
        best_axion = axion_results[0]
        print(f"   Best g_eff: {best_axion['g_eff']:.4e} J")
        print(f"   Parameters: g_aγ={best_axion['g_agamma']:.2e}, "
              f"g_aN={best_axion['g_aN']:.2e}, m_a={best_axion['m_axion']:.2e} GeV")
        print(f"   vs threshold: {best_axion['vs_threshold']:.2e}×")
    
    # Dark photon portal
    print("\n2. DARK PHOTON PORTAL SCAN")
    dark_photon = DarkPhotonPortal()
    dp_results = dark_photon.scan_parameter_space(bounds)
    
    print(f"   Scanned {len(dp_results)} configurations")
    best_dp = None
    if dp_results:
        best_dp = dp_results[0]
        print(f"   Best g_eff: {best_dp['g_eff']:.4e} J")
        print(f"   Parameters: ε={best_dp['epsilon']:.2e}, "
              f"m_A'={best_dp['m_dark_photon']:.2e} GeV, η={best_dp['enhancement_factor']:.2e}")
        print(f"   Boost: {best_dp['boost']:.2e}×")
        print(f"   vs threshold: {best_dp['vs_threshold']:.2e}×")
    
    # Overall best
    all_results = axion_results + dp_results
    all_results.sort(key=lambda x: x['g_eff'], reverse=True)
    
    best_overall = all_results[0] if all_results else None
    
    print(f"\n{'='*70}")
    print("BEST OVERALL PORTAL CONFIGURATION")
    print(f"{'='*70}")
    
    if best_overall:
        portal_type = "Axion" if 'g_agamma' in best_overall else "Dark Photon"
        print(f"\nType: {portal_type}")
        print(f"g_eff: {best_overall['g_eff']:.4e} J")
        print(f"vs baseline (1e-121 J): {best_overall['g_eff']/1e-121:.2e}×")
        print(f"vs threshold (1e-50 J): {best_overall['vs_threshold']:.2e}×")
        
        if best_overall['vs_threshold'] >= 1.0:
            print(f"\n✅ EXCEEDS THRESHOLD!")
        elif best_overall['vs_threshold'] >= 0.1:
            print(f"\n⚠️  Within 10× of threshold")
        else:
            print(f"\n❌ Still {1/best_overall['vs_threshold']:.0f}× below threshold")
    
    return {
        'bounds': bounds,
        'n_axion_configs': len(axion_results),
        'n_dark_photon_configs': len(dp_results),
        'best_axion': best_axion if axion_results else None,
        'best_dark_photon': best_dp if dp_results else None,
        'best_overall': best_overall,
        'all_results': all_results[:10]  # Top 10
    }
