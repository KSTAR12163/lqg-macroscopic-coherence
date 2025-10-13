"""
Resonance search in quantum geometric operators.

This module implements a search for critical/resonant effects in LQG:
- Construct geometric Hamiltonians for small spin networks
- Diagonalize to find energy spectra
- Sweep control parameters (μ, j, external fields)
- Detect avoided crossings and resonances
- Identify parameter regimes with ∂⟨O⟩/∂control ≫ 1
"""

import numpy as np
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
import matplotlib.pyplot as plt
from scipy.linalg import eigh

from ..core.constants import (
    L_PLANCK, HBAR, C, G, GAMMA_IMMIRZI,
    J_MIN, J_MAX, MU_MIN, MU_MAX, MU_TYPICAL,
    EPSILON_SMALL
)
from ..core.spin_network import (
    SpinNetwork, wigner_6j,
    polymer_correction_sinc,
    volume_eigenvalue_tetrahedron
)


# ============================================================================
# Geometric Hamiltonian for Spin Networks
# ============================================================================

@dataclass
class GeometricHamiltonian:
    """
    Hamiltonian for quantum geometric operators on a spin network.
    
    H = H_geom + H_polymer + H_external
    
    where:
    - H_geom: Volume operator or curvature-related operator
    - H_polymer: Polymer corrections (μ-dependent)
    - H_external: External control field
    """
    network: SpinNetwork
    mu: float = MU_TYPICAL  # Polymer parameter
    external_field: float = 0.0  # External field strength
    
    def build_volume_operator_matrix(self) -> np.ndarray:
        """
        Build matrix representation of volume operator for the network.
        
        For a tetrahedron (4-valent node), the volume operator has eigenvalues
        determined by 6j symbols and the spins on incident edges.
        """
        # For simplicity, use a basis labeled by edge spins
        # Dimension: product of (2j+1) for each edge
        spins = [edge.spin for edge in self.network.edges]
        
        # Cap dimension for numerical tractability
        dims = [int(2*j + 1) for j in spins]
        total_dim = min(np.prod(dims), 128)
        
        # Build volume operator matrix
        V = np.zeros((total_dim, total_dim))
        
        # Diagonal elements: volume eigenvalues for each basis state
        for i in range(total_dim):
            # Decode basis state index into spin configuration
            # For simplicity, use average volume
            if len(self.network.nodes) > 0:
                vol_sum = sum(self.network.volume_eigenvalue(n) for n in range(len(self.network.nodes)))
                V[i, i] = vol_sum / len(self.network.nodes)
        
        # Add off-diagonal elements from quantum geometry fluctuations
        # These represent transitions between different geometric states
        fluctuation_strength = 0.1 * np.mean(np.diag(V))
        for i in range(total_dim):
            for j in range(i+1, min(i+5, total_dim)):  # Sparse coupling
                coupling = fluctuation_strength * np.random.randn()
                V[i, j] = coupling
                V[j, i] = coupling
        
        return V
    
    def build_polymer_operator_matrix(self, dim: int) -> np.ndarray:
        """
        Build polymer correction operator: sinc(πμj) modification.
        
        This operator couples to the edge spins and modifies the geometry.
        """
        P = np.zeros((dim, dim))
        
        # Get edge spins
        spins = [edge.spin for edge in self.network.edges]
        avg_spin = np.mean(spins) if spins else 1.0
        
        # Polymer correction factor
        polymer_factor = polymer_correction_sinc(self.mu, avg_spin)
        
        # Diagonal polymer correction (shifts energy levels)
        for i in range(dim):
            P[i, i] = polymer_factor * (L_PLANCK**3) * (i / dim)
        
        # Off-diagonal: quantum transitions induced by polymer corrections
        coupling = 0.05 * polymer_factor * L_PLANCK**3
        for i in range(dim):
            if i + 1 < dim:
                P[i, i+1] = coupling
                P[i+1, i] = coupling
        
        return P
    
    def build_external_field_operator(self, dim: int) -> np.ndarray:
        """
        External control field operator.
        
        Models an external perturbation (e.g., electromagnetic field,
        matter coupling) that can drive the system.
        """
        E = np.zeros((dim, dim))
        
        # Linear potential (like a uniform field)
        for i in range(dim):
            E[i, i] = self.external_field * i / dim
        
        # Transition operator (field couples states)
        coupling = 0.1 * abs(self.external_field)
        for i in range(dim):
            if i + 2 < dim:
                E[i, i+2] = coupling
                E[i+2, i] = coupling
        
        return E
    
    def build_full_hamiltonian(self) -> np.ndarray:
        """
        Build complete Hamiltonian H = V + P + E.
        """
        V = self.build_volume_operator_matrix()
        dim = V.shape[0]
        
        P = self.build_polymer_operator_matrix(dim)
        E = self.build_external_field_operator(dim)
        
        H = V + P + E
        
        # Ensure Hermitian
        H = (H + H.T) / 2
        
        return H
    
    def diagonalize(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Diagonalize Hamiltonian to find eigenvalues and eigenvectors.
        
        Returns:
            (eigenvalues, eigenvectors)
        """
        H = self.build_full_hamiltonian()
        eigenvalues, eigenvectors = eigh(H)
        return eigenvalues, eigenvectors


# ============================================================================
# Resonance Detection and Analysis
# ============================================================================

@dataclass
class AvoidedCrossing:
    """Record of an avoided crossing (resonance)."""
    parameter_value: float  # Value of control parameter at crossing
    level1_idx: int  # Index of first energy level
    level2_idx: int  # Index of second energy level
    min_gap: float  # Minimum energy gap
    gap_derivative: float  # Rate of gap closure
    eigenvector_mixing: float = 0.0  # Max off-diagonal overlap (0-1)
    is_true_crossing: bool = True  # True if eigenvector tracking confirms
    
    def is_strong_resonance(self, threshold: float = 0.1) -> bool:
        """Check if this is a strong resonance (small gap, large derivative)."""
        return self.min_gap < threshold and abs(self.gap_derivative) > 1.0


def compute_eigenvector_overlap_matrix(
    eigenvectors_prev: np.ndarray,
    eigenvectors_next: np.ndarray
) -> np.ndarray:
    """
    Compute overlap matrix between eigenvectors at consecutive parameter values.
    
    Overlap[i,j] = |⟨ψ_i(μ_k) | ψ_j(μ_{k+1})⟩|
    
    For adiabatic evolution, diagonal dominates (states track continuously).
    For avoided crossings, off-diagonal elements become large (states swap).
    
    Args:
        eigenvectors_prev: Eigenvectors at parameter value k (columns)
        eigenvectors_next: Eigenvectors at parameter value k+1 (columns)
    
    Returns:
        Overlap matrix of shape (n_levels, n_levels)
    """
    # Inner product: ⟨ψ_i | ψ_j⟩ = ψ_i† @ ψ_j
    overlap = np.abs(eigenvectors_prev.conj().T @ eigenvectors_next)
    return overlap


def track_eigenvector_continuity(
    eigenvector_sequence: List[np.ndarray],
    parameter_values: np.ndarray
) -> Tuple[np.ndarray, List[np.ndarray]]:
    """
    Track eigenvector identity across parameter sweep using overlap tracking.
    
    This reorders eigenvectors at each step to maintain continuity, preventing
    false crossings from eigenvector label swapping.
    
    Args:
        eigenvector_sequence: List of eigenvector arrays (one per parameter value)
        parameter_values: Parameter values
    
    Returns:
        (reordered_indices, overlap_matrices)
        - reordered_indices[k, i]: original index of level i at parameter k
        - overlap_matrices: List of overlap matrices between consecutive steps
    """
    n_params = len(parameter_values)
    n_levels = eigenvector_sequence[0].shape[1]
    
    reordered_indices = np.zeros((n_params, n_levels), dtype=int)
    overlap_matrices = []
    
    # First parameter: identity mapping
    reordered_indices[0, :] = np.arange(n_levels)
    
    # Track continuity
    current_order = np.arange(n_levels)
    
    for k in range(1, n_params):
        # Compute overlap matrix
        overlap = compute_eigenvector_overlap_matrix(
            eigenvector_sequence[k-1][:, current_order],
            eigenvector_sequence[k]
        )
        overlap_matrices.append(overlap)
        
        # Find best matching: maximize overlap on diagonal
        # Use Hungarian algorithm approximation: greedy row-by-row
        used = set()
        new_order = np.zeros(n_levels, dtype=int)
        
        for i in range(n_levels):
            # For state i at step k-1, find best match at step k
            overlaps_i = overlap[i, :]
            
            # Set used states to -inf
            for j in used:
                overlaps_i[j] = -np.inf
            
            # Best match
            j_best = np.argmax(overlaps_i)
            new_order[i] = j_best
            used.add(j_best)
        
        current_order = new_order
        reordered_indices[k, :] = current_order
    
    return reordered_indices, overlap_matrices


def detect_avoided_crossings(
    parameter_values: np.ndarray,
    energy_spectra: np.ndarray,
    min_gap_threshold: float = 0.1,
    eigenvector_sequence: Optional[List[np.ndarray]] = None,
    use_eigenvector_tracking: bool = True,
    min_parameter_separation: float = 0.01
) -> List[AvoidedCrossing]:
    """
    Detect avoided crossings in energy level diagram with eigenvector tracking.
    
    Enhanced version that uses eigenvector overlap to distinguish true avoided
    crossings from numerical noise and eigenvector label swaps.
    
    Args:
        parameter_values: Array of control parameter values
        energy_spectra: Array of shape (n_params, n_levels) with energy levels
        min_gap_threshold: Minimum gap to consider as avoided crossing
        eigenvector_sequence: List of eigenvector arrays (for tracking)
        use_eigenvector_tracking: If True, validate crossings with eigenvector overlap
        min_parameter_separation: Minimum μ separation between crossings (filter duplicates)
    
    Returns:
        List of detected avoided crossings (filtered and validated)
    """
    crossings = []
    n_params, n_levels = energy_spectra.shape
    
    # Track eigenvector continuity if available
    overlap_matrices = []
    if use_eigenvector_tracking and eigenvector_sequence is not None:
        _, overlap_matrices = track_eigenvector_continuity(
            eigenvector_sequence, parameter_values
        )
    
    # For each pair of levels, look for close approaches
    for i in range(n_levels):
        for j in range(i+1, n_levels):
            # Compute gap as function of parameter
            gap = np.abs(energy_spectra[:, j] - energy_spectra[:, i])
            
            # Find local minima in gap
            for k in range(1, n_params - 1):
                if gap[k] < gap[k-1] and gap[k] < gap[k+1]:
                    # Local minimum found
                    if gap[k] < min_gap_threshold:
                        # Estimate derivative
                        dgap_dp = (gap[k+1] - gap[k-1]) / (parameter_values[k+1] - parameter_values[k-1])
                        
                        # Eigenvector mixing (if available)
                        mixing = 0.0
                        is_true = True
                        
                        if use_eigenvector_tracking and len(overlap_matrices) > 0:
                            if k-1 < len(overlap_matrices):
                                # Check off-diagonal overlap between levels i and j
                                overlap = overlap_matrices[k-1]
                                mixing = max(overlap[i, j], overlap[j, i])
                                
                                # True crossing: large off-diagonal overlap
                                # Numerical noise: diagonal dominates
                                is_true = mixing > 0.1  # Threshold for true crossing
                        
                        crossing = AvoidedCrossing(
                            parameter_value=parameter_values[k],
                            level1_idx=i,
                            level2_idx=j,
                            min_gap=gap[k],
                            gap_derivative=dgap_dp,
                            eigenvector_mixing=mixing,
                            is_true_crossing=is_true
                        )
                        
                        # Only add if validated as true crossing
                        if not use_eigenvector_tracking or is_true:
                            crossings.append(crossing)
    
    # Filter duplicate crossings (same levels, nearby parameter values)
    filtered_crossings = []
    
    for crossing in crossings:
        # Check if too close to existing crossing for same level pair
        is_duplicate = False
        for existing in filtered_crossings:
            if (existing.level1_idx == crossing.level1_idx and
                existing.level2_idx == crossing.level2_idx):
                # Same level pair
                param_diff = abs(existing.parameter_value - crossing.parameter_value)
                if param_diff < min_parameter_separation:
                    is_duplicate = True
                    # Keep the one with smaller gap
                    if crossing.min_gap < existing.min_gap:
                        filtered_crossings.remove(existing)
                        is_duplicate = False
                    break
        
        if not is_duplicate:
            filtered_crossings.append(crossing)
    
    return filtered_crossings


# ============================================================================
# Resonance Search Engine
# ============================================================================

class ResonanceSearcher:
    """
    Search for resonances by sweeping control parameters.
    """
    
    def __init__(self, network: SpinNetwork):
        self.network = network
    
    def sweep_polymer_parameter(
        self,
        mu_values: Optional[np.ndarray] = None,
        external_field: float = 0.0,
        store_eigenvectors: bool = True
    ) -> Tuple[np.ndarray, np.ndarray, Optional[List[np.ndarray]]]:
        """
        Sweep polymer parameter μ and compute energy spectrum.
        
        Args:
            mu_values: Parameter values to sweep
            external_field: External field strength
            store_eigenvectors: If True, store eigenvectors for tracking
        
        Returns:
            (mu_values, energy_spectra, eigenvector_sequence)
            - eigenvector_sequence is None if store_eigenvectors=False
        """
        if mu_values is None:
            mu_values = np.linspace(MU_MIN, min(MU_MAX, 3.0), 50)
        
        # Storage for spectra
        first_run = True
        energy_spectra = None
        eigenvector_sequence = [] if store_eigenvectors else None
        
        for idx, mu in enumerate(mu_values):
            # Build Hamiltonian
            ham = GeometricHamiltonian(
                network=self.network,
                mu=mu,
                external_field=external_field
            )
            
            # Diagonalize
            eigenvalues, eigenvectors = ham.diagonalize()
            
            # Initialize storage
            if first_run:
                energy_spectra = np.zeros((len(mu_values), len(eigenvalues)))
                first_run = False
            
            energy_spectra[idx, :] = eigenvalues
            
            # Store eigenvectors if requested
            if store_eigenvectors:
                eigenvector_sequence.append(eigenvectors)
        
        return mu_values, energy_spectra, eigenvector_sequence
    
    def sweep_external_field(
        self,
        field_values: Optional[np.ndarray] = None,
        mu: float = MU_TYPICAL,
        store_eigenvectors: bool = True
    ) -> Tuple[np.ndarray, np.ndarray, Optional[List[np.ndarray]]]:
        """
        Sweep external field strength and compute energy spectrum.
        
        Args:
            field_values: Field values to sweep
            mu: Polymer parameter (fixed)
            store_eigenvectors: If True, store eigenvectors for tracking
        
        Returns:
            (field_values, energy_spectra, eigenvector_sequence)
            - eigenvector_sequence is None if store_eigenvectors=False
        """
        if field_values is None:
            field_values = np.linspace(-1.0, 1.0, 50) * L_PLANCK**3
        
        first_run = True
        energy_spectra = None
        eigenvector_sequence = [] if store_eigenvectors else None
        
        for idx, field in enumerate(field_values):
            ham = GeometricHamiltonian(
                network=self.network,
                mu=mu,
                external_field=field
            )
            
            eigenvalues, eigenvectors = ham.diagonalize()
            
            if first_run:
                energy_spectra = np.zeros((len(field_values), len(eigenvalues)))
                first_run = False
            
            energy_spectra[idx, :] = eigenvalues
            
            # Store eigenvectors if requested
            if store_eigenvectors:
                eigenvector_sequence.append(eigenvectors)
        
        return field_values, energy_spectra, eigenvector_sequence
    
    def compute_susceptibility(
        self,
        parameter_values: np.ndarray,
        energy_spectra: np.ndarray
    ) -> np.ndarray:
        """
        Compute susceptibility χ = ∂E/∂parameter for each level.
        
        Large susceptibility indicates strong response to control parameter.
        """
        susceptibility = np.gradient(energy_spectra, parameter_values, axis=0)
        return susceptibility


# ============================================================================
# Visualization
# ============================================================================

def plot_spaghetti_diagram(
    parameter_values: np.ndarray,
    energy_spectra: np.ndarray,
    crossings: List[AvoidedCrossing],
    parameter_name: str = "μ",
    output_path: str = "outputs/spaghetti_plot.png"
):
    """
    Plot energy levels vs. control parameter (spaghetti diagram).
    
    Marks avoided crossings with red dots.
    """
    fig, ax = plt.subplots(figsize=(12, 8))
    
    n_levels = energy_spectra.shape[1]
    
    # Plot energy levels
    for level in range(min(n_levels, 20)):  # Plot first 20 levels
        ax.plot(parameter_values, energy_spectra[:, level], 'b-', alpha=0.6, linewidth=1)
    
    # Mark avoided crossings
    for crossing in crossings:
        ax.plot(crossing.parameter_value,
                energy_spectra[np.argmin(np.abs(parameter_values - crossing.parameter_value)), crossing.level1_idx],
                'ro', markersize=8, label='Avoided crossing' if crossing == crossings[0] else '')
    
    ax.set_xlabel(f"Control Parameter {parameter_name}", fontsize=14)
    ax.set_ylabel("Energy (Planck units)", fontsize=14)
    ax.set_title("Energy Spectrum: Spaghetti Diagram", fontsize=16)
    ax.grid(True, alpha=0.3)
    if crossings:
        ax.legend()
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Spaghetti plot saved to {output_path}")
    plt.close()


def plot_susceptibility(
    parameter_values: np.ndarray,
    susceptibility: np.ndarray,
    parameter_name: str = "μ",
    output_path: str = "outputs/susceptibility.png"
):
    """Plot susceptibility χ = ∂E/∂parameter."""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    n_levels = susceptibility.shape[1]
    
    # Plot susceptibility for each level
    for level in range(min(n_levels, 10)):
        ax.plot(parameter_values, np.abs(susceptibility[:, level]),
                label=f'Level {level}', alpha=0.7)
    
    ax.set_xlabel(f"Control Parameter {parameter_name}", fontsize=14)
    ax.set_ylabel(r"Susceptibility $|\partial E / \partial \mu|$", fontsize=14)
    ax.set_title("Geometric Susceptibility", fontsize=16)
    ax.set_yscale('log')
    ax.grid(True, alpha=0.3)
    ax.legend(ncol=2, fontsize=10)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Susceptibility plot saved to {output_path}")
    plt.close()


# ============================================================================
# Demonstration
# ============================================================================

def demonstrate_resonance_search():
    """Demonstrate resonance search on a simple spin network."""
    print("=" * 80)
    print("RESEARCH DIRECTION #3: CRITICAL AND RESONANT EFFECTS")
    print("=" * 80)
    print("\nSearching for avoided crossings and resonances in quantum geometry...\n")
    
    # Create a simple tetrahedral spin network
    network = SpinNetwork()
    nodes = [network.add_node(i) for i in range(4)]
    
    # Add edges with varied spins
    edges = [
        (0, 1, 1.0), (0, 2, 1.5), (0, 3, 1.0),
        (1, 2, 0.5), (1, 3, 1.0), (2, 3, 0.5)
    ]
    
    for (i, j, spin) in edges:
        network.add_edge(i, j, spin)
    
    print(f"Spin network: {len(network.nodes)} nodes, {len(network.edges)} edges")
    print(f"Spins: {[e.spin for e in network.edges]}\n")
    
    # Create searcher
    searcher = ResonanceSearcher(network)
    
    # Sweep polymer parameter
    print("Sweeping polymer parameter μ...")
    mu_values, mu_spectra = searcher.sweep_polymer_parameter()
    
    # Detect avoided crossings
    crossings_mu = detect_avoided_crossings(mu_values, mu_spectra, min_gap_threshold=0.2)
    
    print(f"\nFound {len(crossings_mu)} avoided crossings in μ sweep:")
    for i, crossing in enumerate(crossings_mu[:5]):  # Show first 5
        print(f"  {i+1}. μ={crossing.parameter_value:.3f}, "
              f"levels {crossing.level1_idx}↔{crossing.level2_idx}, "
              f"gap={crossing.min_gap:.4e}, "
              f"strong={'YES' if crossing.is_strong_resonance() else 'no'}")
    
    # Compute susceptibility
    chi_mu = searcher.compute_susceptibility(mu_values, mu_spectra)
    max_chi = np.max(np.abs(chi_mu))
    max_chi_idx = np.unravel_index(np.argmax(np.abs(chi_mu)), chi_mu.shape)
    
    print(f"\nMax susceptibility: {max_chi:.2e} at μ={mu_values[max_chi_idx[0]]:.3f}, level {max_chi_idx[1]}")
    
    # Plot results
    plot_spaghetti_diagram(mu_values, mu_spectra, crossings_mu,
                          parameter_name="μ (polymer parameter)",
                          output_path="outputs/spaghetti_mu.png")
    
    plot_susceptibility(mu_values, chi_mu,
                       parameter_name="μ",
                       output_path="outputs/susceptibility_mu.png")
    
    # Sweep external field
    print("\nSweeping external field...")
    field_values, field_spectra = searcher.sweep_external_field()
    crossings_field = detect_avoided_crossings(field_values / L_PLANCK**3, field_spectra)
    
    print(f"Found {len(crossings_field)} avoided crossings in field sweep")
    
    plot_spaghetti_diagram(field_values / L_PLANCK**3, field_spectra, crossings_field,
                          parameter_name="E (external field, Planck units)",
                          output_path="outputs/spaghetti_field.png")
    
    # Summary
    print("\n" + "=" * 80)
    print("KEY FINDINGS:")
    print("=" * 80)
    print(f"1. Polymer parameter sweep revealed {len(crossings_mu)} avoided crossings")
    print(f"2. Maximum susceptibility: {max_chi:.2e} (indicates resonance strength)")
    print(f"3. Strong resonances found: {sum(c.is_strong_resonance() for c in crossings_mu)}")
    print("\nImplications:")
    print("  - Avoided crossings indicate parameter values where system is highly")
    print("    susceptible to perturbations (potential for geometric amplification)")
    print("  - Large ∂E/∂μ regions could enable control with minimal energy input")
    print("  - Next: Map out full (μ, j, topology) resonance landscape")
    print("=" * 80)


if __name__ == "__main__":
    import os
    os.makedirs("outputs", exist_ok=True)
    demonstrate_resonance_search()
