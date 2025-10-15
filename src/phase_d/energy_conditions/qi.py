"""
Quantum Inequality (QI) Bounds for Negative Energy

Quantum inequalities constrain the magnitude and duration of negative
energy densities allowed by quantum field theory. They prevent macroscopic
violations of energy conditions by limiting space-time averages.

Standard form (Ford & Roman):
    ∫ ρ(τ) g(τ) dτ ≥ -C / τ₀⁴

where:
- ρ(τ): Energy density along worldline
- g(τ): Sampling function (e.g., Lorentzian, Gaussian)
- τ₀: Sampling timescale
- C: Constant depending on g and spacetime dimension

For 3+1D massless scalar field:
- Lorentzian: C_L ≈ 3/(32π²)
- Gaussian: C_G ≈ 3/(16π²)

Key implications for warp drives:
1. Negative energy must be "borrowed" and "repaid" quickly
2. Magnitude scales as 1/τ₀⁴ (shorter pulses → less negative allowed)
3. Total negative energy integral is highly constrained
4. Sustained macroscopic ANEC violations are forbidden

References:
- Ford & Roman (1996): "Quantum field theory constrains traversable wormholes"
- Ford & Roman (2000): "Restrictions on negative energy density"
- Pfenning & Ford (1997): "Scalar field QI in flat spacetime"
- Visser (2003): "Lorentzian wormholes"
"""

import numpy as np
from typing import Callable, Dict, Tuple
from scipy.integrate import quad


class QuantumInequalityChecker:
    """
    Check quantum inequality bounds for negative energy configurations.
    """
    
    # Constants for 3+1D massless scalar field
    C_LORENTZIAN = 3.0 / (32.0 * np.pi**2)  # ≈ 9.48e-3
    C_GAUSSIAN = 3.0 / (16.0 * np.pi**2)    # ≈ 1.90e-2
    
    # Speed of light and hbar (SI units)
    c = 299792458.0  # m/s
    hbar = 1.054571817e-34  # J·s
    
    def __init__(self, sampling_type: str = 'lorentzian', tau_0: float = 1e-15):
        """
        Initialize QI checker.
        
        Args:
            sampling_type: 'lorentzian' or 'gaussian'
            tau_0: Sampling timescale (s). Typical values:
                   - Planck time: ~5.4e-44 s (absolute minimum)
                   - Proton crossing: ~3e-24 s
                   - Atomic timescale: ~1e-15 s (femtosecond)
                   - Human timescale: ~1 s
        """
        self.sampling_type = sampling_type.lower()
        self.tau_0 = tau_0
        
        if self.sampling_type == 'lorentzian':
            self.C = self.C_LORENTZIAN
        elif self.sampling_type == 'gaussian':
            self.C = self.C_GAUSSIAN
        else:
            raise ValueError(f"Unknown sampling type: {sampling_type}")
        
        # Convert to SI units: C / τ₀⁴ with ħc factors
        # ρ_min = -(ħc⁴/τ₀⁴) × C
        self.rho_min_bound = -(self.hbar * self.c**4 / self.tau_0**4) * self.C
    
    def lorentzian_weight(self, tau: np.ndarray) -> np.ndarray:
        """
        Lorentzian sampling function.
        
        g(τ) = (τ₀² / π) / (τ² + τ₀²)²
        
        Normalized: ∫ g(τ) dτ = 1
        
        Args:
            tau: Proper time array (s)
            
        Returns:
            Weight array
        """
        return (self.tau_0**2 / np.pi) / (tau**2 + self.tau_0**2)**2
    
    def gaussian_weight(self, tau: np.ndarray) -> np.ndarray:
        """
        Gaussian sampling function.
        
        g(τ) = (1 / √(2π τ₀²)) exp(-τ²/(2τ₀²))
        
        Normalized: ∫ g(τ) dτ = 1
        
        Args:
            tau: Proper time array (s)
            
        Returns:
            Weight array
        """
        return (1.0 / np.sqrt(2.0 * np.pi * self.tau_0**2)) * \
               np.exp(-tau**2 / (2.0 * self.tau_0**2))
    
    def get_weight(self, tau: np.ndarray) -> np.ndarray:
        """Get sampling weight for configured type."""
        if self.sampling_type == 'lorentzian':
            return self.lorentzian_weight(tau)
        else:
            return self.gaussian_weight(tau)
    
    def compute_averaged_density(
        self,
        rho_fn: Callable[[float], float],
        tau_range: Tuple[float, float],
        n_points: int = 1000
    ) -> float:
        """
        Compute weighted average of energy density.
        
        ⟨ρ⟩ = ∫ ρ(τ) g(τ) dτ
        
        Args:
            rho_fn: Energy density function ρ(τ) in J/m³
            tau_range: (tau_min, tau_max) integration range
            n_points: Number of sampling points
            
        Returns:
            Averaged density (J/m³)
        """
        tau_min, tau_max = tau_range
        tau = np.linspace(tau_min, tau_max, n_points)
        
        rho_vals = np.array([rho_fn(t) for t in tau])
        weights = self.get_weight(tau)
        
        # Trapezoidal integration
        integrand = rho_vals * weights
        avg_rho = np.trapz(integrand, tau)
        
        return avg_rho
    
    def check_bound(
        self,
        rho_fn: Callable[[float], float],
        tau_range: Tuple[float, float],
        n_points: int = 1000
    ) -> Dict:
        """
        Check if energy density satisfies quantum inequality.
        
        Args:
            rho_fn: Energy density function
            tau_range: Integration range
            n_points: Sampling resolution
            
        Returns:
            Dictionary with:
            - 'averaged_rho': ⟨ρ⟩ (J/m³)
            - 'bound': Lower bound from QI (J/m³)
            - 'satisfies_qi': Boolean (True if ⟨ρ⟩ ≥ bound)
            - 'margin': (⟨ρ⟩ - bound) / |bound| (positive = safe)
            - 'tau_0': Sampling timescale used
            - 'sampling_type': Weight function type
        """
        avg_rho = self.compute_averaged_density(rho_fn, tau_range, n_points)
        
        satisfies = avg_rho >= self.rho_min_bound
        
        if abs(self.rho_min_bound) > 1e-100:
            margin = (avg_rho - self.rho_min_bound) / abs(self.rho_min_bound)
        else:
            margin = np.inf if avg_rho >= 0 else -np.inf
        
        return {
            'averaged_rho': avg_rho,
            'bound': self.rho_min_bound,
            'satisfies_qi': satisfies,
            'margin': margin,
            'tau_0': self.tau_0,
            'sampling_type': self.sampling_type,
            'C': self.C
        }
    
    def sweep_timescales(
        self,
        rho_fn: Callable[[float], float],
        tau_range: Tuple[float, float],
        tau_0_values: np.ndarray,
        n_points: int = 1000
    ) -> Dict:
        """
        Sweep over sampling timescales to find QI constraints.
        
        Args:
            rho_fn: Energy density function
            tau_range: Integration range
            tau_0_values: Array of timescales to test
            n_points: Sampling resolution
            
        Returns:
            Dictionary with arrays for each τ₀:
            - 'tau_0_values': Input timescales
            - 'averaged_rho': ⟨ρ⟩ for each τ₀
            - 'bounds': QI bounds for each τ₀
            - 'satisfies': Boolean array
            - 'margins': Margin array
        """
        results = {
            'tau_0_values': tau_0_values,
            'averaged_rho': [],
            'bounds': [],
            'satisfies': [],
            'margins': []
        }
        
        for tau_0 in tau_0_values:
            # Update checker timescale
            old_tau_0 = self.tau_0
            self.tau_0 = tau_0
            self.rho_min_bound = -(self.hbar * self.c**4 / tau_0**4) * self.C
            
            # Check bound
            check = self.check_bound(rho_fn, tau_range, n_points)
            
            results['averaged_rho'].append(check['averaged_rho'])
            results['bounds'].append(check['bound'])
            results['satisfies'].append(check['satisfies_qi'])
            results['margins'].append(check['margin'])
            
            # Restore
            self.tau_0 = old_tau_0
            self.rho_min_bound = -(self.hbar * self.c**4 / old_tau_0**4) * self.C
        
        # Convert to arrays
        for key in ['averaged_rho', 'bounds', 'satisfies', 'margins']:
            results[key] = np.array(results[key])
        
        return results


def estimate_qi_constrained_pulse(
    peak_rho: float,
    tau_0: float,
    sampling_type: str = 'lorentzian'
) -> Dict:
    """
    Estimate maximum negative energy pulse satisfying QI.
    
    For a simple Lorentzian pulse:
    ρ(τ) = ρ_peak × τ₀² / (τ² + τ₀²)
    
    The QI-averaged value is:
    ⟨ρ⟩ ≈ ρ_peak × (fraction depending on sampling)
    
    Args:
        peak_rho: Peak energy density (J/m³, can be negative)
        tau_0: Pulse width timescale (s)
        sampling_type: 'lorentzian' or 'gaussian'
        
    Returns:
        Dictionary with:
        - 'peak_rho': Input peak
        - 'qi_bound': QI lower bound
        - 'max_allowed_peak': Maximum ρ_peak satisfying QI
        - 'reduction_factor': max_allowed / requested
    """
    checker = QuantumInequalityChecker(sampling_type, tau_0)
    qi_bound = checker.rho_min_bound
    
    # For matching-width Lorentzian pulse and sampling:
    # ⟨ρ⟩ ≈ 0.5 × ρ_peak (approximate; exact value from integral)
    
    # Conservative estimate: ⟨ρ⟩ ≈ 0.5 ρ_peak for Lorentzian
    if sampling_type == 'lorentzian':
        avg_fraction = 0.5
    else:  # Gaussian
        avg_fraction = 0.8  # Gaussian is broader
    
    max_allowed_peak = qi_bound / avg_fraction
    
    if peak_rho < 0:
        reduction_factor = max_allowed_peak / peak_rho
    else:
        reduction_factor = np.inf  # Positive energy always allowed
    
    return {
        'peak_rho': peak_rho,
        'qi_bound': qi_bound,
        'max_allowed_peak': max_allowed_peak,
        'reduction_factor': reduction_factor,
        'tau_0': tau_0,
        'sampling_type': sampling_type
    }


if __name__ == "__main__":
    """Test quantum inequality checker."""
    
    print("="*70)
    print("Quantum Inequality Checker Test")
    print("="*70)
    
    # Test with typical warp drive scales
    # Alcubierre ANEC ~ -1e40 J over λ ~ 400 m
    # At v=c, proper time τ ~ λ/c ~ 1.3e-6 s
    
    tau_0 = 1e-6  # Microsecond sampling
    peak_rho = -1e40  # J/m³ (Alcubierre-like)
    
    print(f"\nTest configuration:")
    print(f"  Sampling timescale: τ₀ = {tau_0:.3e} s")
    print(f"  Peak energy density: ρ_peak = {peak_rho:.3e} J/m³")
    
    # Create checker
    checker = QuantumInequalityChecker('lorentzian', tau_0)
    
    print(f"\nQI bound:")
    print(f"  ⟨ρ⟩ ≥ {checker.rho_min_bound:.3e} J/m³")
    print(f"  C_Lorentzian = {checker.C:.3e}")
    
    # Test with simple Lorentzian pulse
    def rho_lorentzian(tau):
        return peak_rho * tau_0**2 / (tau**2 + tau_0**2)
    
    tau_range = (-10 * tau_0, 10 * tau_0)
    
    result = checker.check_bound(rho_lorentzian, tau_range, n_points=500)
    
    print(f"\nLorentzian pulse test:")
    print(f"  ⟨ρ⟩ = {result['averaged_rho']:.3e} J/m³")
    print(f"  Bound = {result['bound']:.3e} J/m³")
    print(f"  Satisfies QI: {result['satisfies_qi']}")
    print(f"  Margin: {result['margin']:.3e}")
    
    if not result['satisfies_qi']:
        violation_factor = abs(result['averaged_rho'] / result['bound'])
        print(f"  ⚠️  Violation by factor: {violation_factor:.3e}")
    
    # Sweep timescales
    print(f"\n{'='*70}")
    print("Timescale sweep")
    print("="*70)
    
    tau_0_sweep = np.logspace(-15, -3, 13)  # fs to ms
    
    sweep_results = checker.sweep_timescales(
        rho_lorentzian,
        tau_range,
        tau_0_sweep,
        n_points=300
    )
    
    print(f"\n{'τ₀ (s)':<12} {'⟨ρ⟩ (J/m³)':<15} {'Bound (J/m³)':<15} {'Satisfies':<10}")
    print("-"*70)
    
    for i, tau_0_val in enumerate(tau_0_sweep):
        avg = sweep_results['averaged_rho'][i]
        bound = sweep_results['bounds'][i]
        satisfies = sweep_results['satisfies'][i]
        
        status = "✅" if satisfies else "❌"
        print(f"{tau_0_val:<12.3e} {avg:<15.3e} {bound:<15.3e} {status:<10}")
    
    # Estimate max allowed
    print(f"\n{'='*70}")
    print("Maximum allowed pulse estimate")
    print("="*70)
    
    estimate = estimate_qi_constrained_pulse(peak_rho, tau_0, 'lorentzian')
    
    print(f"\nRequested: ρ_peak = {estimate['peak_rho']:.3e} J/m³")
    print(f"QI bound: ⟨ρ⟩ ≥ {estimate['qi_bound']:.3e} J/m³")
    print(f"Max allowed peak: {estimate['max_allowed_peak']:.3e} J/m³")
    print(f"Reduction needed: {estimate['reduction_factor']:.3e}×")
    
    if estimate['reduction_factor'] > 1:
        print(f"\n✅ Pulse satisfies QI")
    else:
        print(f"\n❌ Pulse violates QI by {1/estimate['reduction_factor']:.3e}×")
    
    print("\n" + "="*70)
    print("Key takeaway:")
    print("="*70)
    print(f"For τ₀ = {tau_0:.3e} s:")
    print(f"  QI allows: ⟨ρ⟩ ≥ {checker.rho_min_bound:.3e} J/m³")
    print(f"  Alcubierre needs: ρ ~ {peak_rho:.3e} J/m³")
    print(f"  Gap: {abs(peak_rho / checker.rho_min_bound):.3e}×")
    print(f"\n➡️  Quantum inequalities forbid macroscopic negative energy!")
