"""
Coarse-graining algorithms for spin networks to derive f_eff from first principles.

This module implements the core calculation for Research Direction #1:
deriving the effective coupling f_eff by coarse-graining polymer corrections
from the Planck scale to macroscopic scales.

The key idea:
    - At Planck scale: polymer corrections modify Einstein equation by sinc(πμj)
    - At macroscopic scale: average over ~(L/ℓ_P)³ quantum degrees of freedom
    - Effective coupling: f_eff = ⟨polymer corrections⟩ / ⟨coherence⟩
"""

import numpy as np
from typing import List, Tuple, Optional, Callable
from dataclasses import dataclass
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from scipy.integrate import quad

from ..core.constants import (
    L_PLANCK, C, G, HBAR, GAMMA_IMMIRZI,
    MU_MIN, MU_MAX, MU_TYPICAL,
    J_MIN, J_MAX, J_TYPICAL,
    EPSILON_SMALL, RHO_PER_CURVATURE
)
from ..core.spin_network import (
    SpinNetwork, polymer_correction_sinc,
    average_spin_in_region
)


# ============================================================================
# Coarse-Graining Scale Hierarchy
# ============================================================================

@dataclass
class CoarseGrainingScale:
    """A scale in the hierarchy from Planck to macroscopic."""
    length_scale: float  # in meters
    num_planck_volumes: float  # (L/ℓ_P)³
    effective_j: float  # Effective spin at this scale
    effective_mu: float  # Effective polymer parameter
    
    def planck_units(self) -> float:
        """Length scale in Planck units."""
        return self.length_scale / L_PLANCK
    
    def num_degrees_of_freedom(self) -> float:
        """Number of quantum DOF at this scale."""
        return self.num_planck_volumes


def build_scale_hierarchy(L_min: float, L_max: float, num_scales: int) -> List[CoarseGrainingScale]:
    """
    Build a logarithmic hierarchy of scales from Planck to macroscopic.
    
    Args:
        L_min: Minimum scale (typically ℓ_P)
        L_max: Maximum scale (macroscopic, e.g., 1 meter)
        num_scales: Number of intermediate scales
    
    Returns:
        List of coarse-graining scales
    """
    scales = []
    length_scales = np.logspace(np.log10(L_min), np.log10(L_max), num_scales)
    
    for L in length_scales:
        num_volumes = (L / L_PLANCK)**3
        
        # Effective j decreases as we coarse-grain (averaging)
        # Start at J_TYPICAL and decrease logarithmically
        effective_j = J_TYPICAL * np.sqrt(L_PLANCK / L)
        effective_j = max(effective_j, J_MIN)
        
        # Effective mu also modified by coarse-graining
        effective_mu = MU_TYPICAL * (L_PLANCK / L)**(1/3)
        effective_mu = max(effective_mu, MU_MIN)
        
        scale = CoarseGrainingScale(
            length_scale=L,
            num_planck_volumes=num_volumes,
            effective_j=effective_j,
            effective_mu=effective_mu
        )
        scales.append(scale)
    
    return scales


# ============================================================================
# Polymer Correction Averaging
# ============================================================================

def average_polymer_correction(j_distribution: Callable[[float], float],
                                mu: float,
                                j_min: float = J_MIN,
                                j_max: float = J_MAX) -> float:
    """
    Average polymer correction over a distribution of spins.
    
    ⟨sinc(πμj)⟩ = ∫ P(j) sinc(πμj) dj
    
    Args:
        j_distribution: Probability density P(j) for spin distribution
        mu: Polymer parameter
        j_min, j_max: Integration range
    
    Returns:
        Averaged polymer correction factor
    """
    def integrand(j):
        return j_distribution(j) * polymer_correction_sinc(mu, j)
    
    result, error = quad(integrand, j_min, j_max)
    return result


def spin_distribution_thermal(j: float, temperature: float) -> float:
    """
    Thermal distribution of spins (Boltzmann-like).
    
    P(j) ∝ (2j+1) exp(-E_j / kT)
    
    where E_j is the energy scale associated with spin j.
    """
    # Energy scale: E_j ~ ℓ_P² j (area energy)
    beta = 1.0 / max(temperature, EPSILON_SMALL)
    energy = L_PLANCK**2 * j
    
    degeneracy = 2 * j + 1
    weight = degeneracy * np.exp(-beta * energy)
    
    # Normalize approximately (should integrate to 1)
    norm = 1.0  # Placeholder - proper normalization needs integration
    return weight / norm


def spin_distribution_uniform(j: float) -> float:
    """Uniform distribution over allowed spins."""
    if J_MIN <= j <= J_MAX:
        return 1.0 / (J_MAX - J_MIN)
    return 0.0


# ============================================================================
# Renormalization Group Flow for f_eff
# ============================================================================

@dataclass
class RenormalizationFlowResult:
    """Result of RG flow from Planck to macroscopic scale."""
    scales: List[CoarseGrainingScale]
    f_eff_values: List[float]
    polymer_corrections: List[float]
    coherence_factors: List[float]
    
    def final_f_eff(self) -> float:
        """Effective coupling at the largest (macroscopic) scale."""
        return self.f_eff_values[-1] if self.f_eff_values else 1.0


class RenormalizationGroup:
    """
    Renormalization group flow for effective gravitational coupling.
    
    Starting from Planck scale with polymer corrections, flow to macroscopic
    scale and compute how f_eff evolves.
    """
    
    def __init__(self, mu_initial: float = MU_TYPICAL, j_initial: float = J_TYPICAL):
        self.mu_initial = mu_initial
        self.j_initial = j_initial
    
    def flow_to_scale(self, L_target: float, coherence_model: str = "none") -> RenormalizationFlowResult:
        """
        Flow from Planck scale to target scale L_target.
        
        Args:
            L_target: Target coarse-graining scale (meters)
            coherence_model: Model for coherence ("none", "partial", "full")
        
        Returns:
            RenormalizationFlowResult with f_eff evolution
        """
        # Build scale hierarchy
        scales = build_scale_hierarchy(L_PLANCK, L_target, num_scales=50)
        
        f_eff_values = []
        polymer_corrections = []
        coherence_factors = []
        
        for scale in scales:
            # Polymer correction at this scale
            pc = polymer_correction_sinc(scale.effective_mu, scale.effective_j)
            
            # Coherence factor (what fraction of DOF are coherent?)
            if coherence_model == "none":
                # No coherence: each DOF independent
                coherence = 1.0 / np.sqrt(scale.num_degrees_of_freedom())
            elif coherence_model == "partial":
                # Partial coherence: √N coherent DOF
                coherence = 1.0 / (scale.num_degrees_of_freedom())**(1/4)
            elif coherence_model == "full":
                # Full coherence: all DOF phase-locked
                coherence = 1.0
            else:
                coherence = 1.0
            
            # Effective coupling
            f_eff = pc * coherence
            
            f_eff_values.append(f_eff)
            polymer_corrections.append(pc)
            coherence_factors.append(coherence)
        
        return RenormalizationFlowResult(
            scales=scales,
            f_eff_values=f_eff_values,
            polymer_corrections=polymer_corrections,
            coherence_factors=coherence_factors
        )
    
    def compare_coherence_models(self, L_target: float) -> dict:
        """
        Compare f_eff for different coherence models.
        
        Returns:
            Dictionary with model names as keys and final f_eff as values
        """
        models = ["none", "partial", "full"]
        results = {}
        
        for model in models:
            flow = self.flow_to_scale(L_target, coherence_model=model)
            results[model] = flow.final_f_eff()
        
        return results


# ============================================================================
# First-Principles f_eff Calculation
# ============================================================================

def compute_f_eff_first_principles(
    L_macro: float,
    mu: float = MU_TYPICAL,
    j_dist: str = "uniform",
    coherence_model: str = "none"
) -> Tuple[float, dict]:
    """
    Compute f_eff from first principles using coarse-graining.
    
    This is the main function for Research Direction #1.
    
    Args:
        L_macro: Macroscopic scale (meters)
        mu: Polymer parameter
        j_dist: Spin distribution ("uniform", "thermal")
        coherence_model: Coherence model ("none", "partial", "full")
    
    Returns:
        (f_eff, diagnostics_dict)
    """
    # Step 1: Choose spin distribution
    if j_dist == "uniform":
        dist_fn = spin_distribution_uniform
    elif j_dist == "thermal":
        dist_fn = lambda j: spin_distribution_thermal(j, temperature=1.0)
    else:
        dist_fn = spin_distribution_uniform
    
    # Step 2: Average polymer correction
    avg_polymer = average_polymer_correction(dist_fn, mu)
    
    # Step 3: Compute number of DOF at macroscopic scale
    N_dof = (L_macro / L_PLANCK)**3
    
    # Step 4: Apply coherence model
    if coherence_model == "none":
        coherence_factor = 1.0 / np.sqrt(N_dof)
    elif coherence_model == "partial":
        coherence_factor = 1.0 / N_dof**(1/4)
    elif coherence_model == "full":
        coherence_factor = 1.0
    else:
        coherence_factor = 1.0 / np.sqrt(N_dof)
    
    # Step 5: Effective coupling
    f_eff = avg_polymer * coherence_factor
    
    # Diagnostics
    diagnostics = {
        "L_macro": L_macro,
        "N_dof": N_dof,
        "mu": mu,
        "avg_polymer_correction": avg_polymer,
        "coherence_factor": coherence_factor,
        "f_eff": f_eff,
        "reduction_factor": 1.0 / f_eff if f_eff > 0 else np.inf
    }
    
    return f_eff, diagnostics


# ============================================================================
# Visualization and Analysis
# ============================================================================

def plot_renormalization_flow(result: RenormalizationFlowResult, 
                               output_path: str = "outputs/rg_flow.png"):
    """Plot the RG flow of f_eff across scales."""
    scales_m = [s.length_scale for s in result.scales]
    scales_planck = [s.planck_units() for s in result.scales]
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # f_eff vs scale
    ax = axes[0, 0]
    ax.loglog(scales_m, result.f_eff_values, 'b-', linewidth=2, label='f_eff')
    ax.axhline(1.0, color='k', linestyle='--', alpha=0.5, label='Classical (f=1)')
    ax.set_xlabel("Coarse-Graining Scale (m)")
    ax.set_ylabel("Effective Coupling f_eff")
    ax.set_title("Renormalization Flow of f_eff")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Polymer correction vs scale
    ax = axes[0, 1]
    ax.semilogx(scales_m, result.polymer_corrections, 'r-', linewidth=2)
    ax.set_xlabel("Scale (m)")
    ax.set_ylabel("Polymer Correction sinc(πμj)")
    ax.set_title("Polymer Correction Across Scales")
    ax.grid(True, alpha=0.3)
    
    # Coherence factor vs scale
    ax = axes[1, 0]
    ax.loglog(scales_m, result.coherence_factors, 'g-', linewidth=2)
    ax.set_xlabel("Scale (m)")
    ax.set_ylabel("Coherence Factor")
    ax.set_title("Coherence Factor Across Scales")
    ax.grid(True, alpha=0.3)
    
    # Reduction factor (1/f_eff) vs scale
    ax = axes[1, 1]
    reduction = [1.0/f if f > EPSILON_SMALL else 1e20 for f in result.f_eff_values]
    ax.loglog(scales_m, reduction, 'purple', linewidth=2)
    ax.set_xlabel("Scale (m)")
    ax.set_ylabel("Energy Reduction Factor (1/f_eff)")
    ax.set_title("Energy Reduction Across Scales")
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"RG flow plot saved to {output_path}")
    plt.close()


def demonstrate_coarse_graining():
    """Demonstration of coarse-graining calculation."""
    print("=" * 80)
    print("COARSE-GRAINING DEMONSTRATION: Deriving f_eff from First Principles")
    print("=" * 80)
    
    # Target scales
    scales_to_test = [1e-6, 1e-3, 1e-1, 1.0, 10.0]  # micrometers to meters
    
    print("\nComputing f_eff at various macroscopic scales:\n")
    print(f"{'Scale (m)':<12} {'N_DOF':<15} {'f_eff (none)':<15} {'f_eff (full)':<15} {'Reduction':<15}")
    print("-" * 80)
    
    for L in scales_to_test:
        f_none, diag_none = compute_f_eff_first_principles(L, coherence_model="none")
        f_full, diag_full = compute_f_eff_first_principles(L, coherence_model="full")
        
        print(f"{L:<12.2e} {diag_none['N_dof']:<15.2e} {f_none:<15.2e} {f_full:<15.2e} {1/f_none:<15.2e}")
    
    # RG flow analysis
    print("\n" + "=" * 80)
    print("RENORMALIZATION GROUP FLOW ANALYSIS")
    print("=" * 80)
    
    rg = RenormalizationGroup(mu_initial=MU_TYPICAL, j_initial=J_TYPICAL)
    
    # Flow to 1 meter with different coherence models
    L_target = 1.0
    flow_none = rg.flow_to_scale(L_target, coherence_model="none")
    flow_partial = rg.flow_to_scale(L_target, coherence_model="partial")
    flow_full = rg.flow_to_scale(L_target, coherence_model="full")
    
    print(f"\nRG flow to L = {L_target} m:")
    print(f"  No coherence:      f_eff = {flow_none.final_f_eff():.6e}")
    print(f"  Partial coherence: f_eff = {flow_partial.final_f_eff():.6e}")
    print(f"  Full coherence:    f_eff = {flow_full.final_f_eff():.6e}")
    
    # Plot
    plot_renormalization_flow(flow_none, "outputs/rg_flow_no_coherence.png")
    plot_renormalization_flow(flow_full, "outputs/rg_flow_full_coherence.png")
    
    print("\n" + "=" * 80)
    print("KEY FINDING:")
    print("=" * 80)
    print(f"At 1 meter scale:")
    print(f"  • Without coherence: f_eff ≈ {flow_none.final_f_eff():.2e}")
    print(f"    → Energy reduction: {1/flow_none.final_f_eff():.2e}×")
    print(f"  • With full coherence: f_eff ≈ {flow_full.final_f_eff():.2e}")
    print(f"    → Energy reduction: {1/flow_full.final_f_eff():.2e}×")
    print("\nConclusion: Macroscopic coherence is ESSENTIAL for significant energy reduction.")
    print("=" * 80)


if __name__ == "__main__":
    import os
    os.makedirs("outputs", exist_ok=True)
    demonstrate_coarse_graining()
