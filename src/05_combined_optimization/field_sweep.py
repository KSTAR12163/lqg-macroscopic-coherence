"""
2D (μ, external field) parameter sweep for combined optimization (GPT-5 Priority #1).

Extends the combined resonance-coupling search to include external field
perturbation, which breaks degeneracies and induces mixing between levels.

Includes parallel execution for 10-20× speedup on multi-core systems.
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
import matplotlib.pyplot as plt
from multiprocessing import Pool, cpu_count
from functools import partial

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.spin_network import SpinNetwork
from src.core.constants import HBAR, L_PLANCK

import importlib
resonance_module = importlib.import_module('src.03_critical_effects.resonance_search')
coupling_module = importlib.import_module('src.04_coupling_engineering.matter_coupling')
combined_module = importlib.import_module('src.05_combined_optimization.resonant_coupling_search')

MatterFieldProperties = coupling_module.MatterFieldProperties
MatterGeometryCoupling = coupling_module.MatterGeometryCoupling
ResonantCouplingPoint = combined_module.ResonantCouplingPoint
detect_avoided_crossings = resonance_module.detect_avoided_crossings


@dataclass
class FieldSweepPoint:
    """Extended resonant coupling point with external field."""
    mu: float
    external_field: float
    lambda_opt: float
    field_type: str
    level1_idx: int
    level2_idx: int
    energy_gap: float
    coupling_strength: float
    driven_rate: float
    susceptibility: float
    figure_of_merit: float


def compute_coupling_with_field(
    network: SpinNetwork,
    mu: float,
    external_field: float,
    matter_field: MatterFieldProperties,
    lambda_val: float,
    level1: int,
    level2: int,
    dim: int = 32,
    rho_exponent: float = 1.0
) -> Tuple[float, float]:
    """
    Compute coupling at resonance WITH external field perturbation.
    
    Args:
        network: Spin network
        mu: Polymer parameter
        external_field: External field strength h
        matter_field: Matter field properties
        lambda_val: Coupling constant
        level1, level2: Resonant levels
        dim: Hilbert space dimension
        rho_exponent: Density of states exponent (α)
    
    Returns:
        (coupling_strength, driven_rate)
    """
    # Build coupling with external field
    coupling = MatterGeometryCoupling(
        network=network,
        matter_field=matter_field,
        coupling_constant=lambda_val,
        mu=mu,
        external_field=external_field
    )
    
    # Get eigenstates (now modified by field)
    eigenvalues, eigenvectors = coupling.compute_energy_spectrum(dim)
    
    # Build interaction Hamiltonian
    H_int = coupling.build_interaction_hamiltonian(dim)
    
    # Compute matrix element
    matrix_element = eigenvectors[:, level2].conj() @ H_int @ eigenvectors[:, level1]
    coupling_strength = abs(matrix_element)
    
    # Driven rate with configurable ρ ~ 1/gap^α
    energy_gap = abs(eigenvalues[level2] - eigenvalues[level1])
    if energy_gap > 0:
        rho_states = 1.0 / energy_gap**rho_exponent
    else:
        rho_states = 0.0
    
    driven_rate = (2 * np.pi / HBAR) * coupling_strength**2 * rho_states
    
    return coupling_strength, driven_rate


def compute_hamiltonian_energy_scale(
    network: SpinNetwork,
    matter_field: MatterFieldProperties,
    lambda_val: float,
    mu: float,
    dim: int = 32
) -> float:
    """
    Compute characteristic energy scale of the Hamiltonian.
    
    Returns mean absolute value of H_geom matrix elements.
    This sets the scale for meaningful external field perturbations.
    
    Args:
        network: Spin network
        matter_field: Matter field properties
        lambda_val: Coupling constant
        mu: Polymer parameter
        dim: Hilbert space dimension
    
    Returns:
        H_scale: Mean |H_geom| (J)
    """
    coupling = MatterGeometryCoupling(
        network=network,
        matter_field=matter_field,
        coupling_constant=lambda_val,
        mu=mu,
        external_field=0.0  # No field for baseline
    )
    
    # Build geometry operator (acts as Hamiltonian for geometric degrees of freedom)
    H_geom = coupling.build_geometry_operator(dim)
    
    # Compute mean absolute value of off-diagonal elements
    # (diagonal represents energy levels, off-diagonal represents mixing)
    H_offdiag = H_geom - np.diag(np.diag(H_geom))
    H_scale = np.mean(np.abs(H_offdiag)) if np.any(H_offdiag) else np.mean(np.abs(np.diag(H_geom)))
    
    # Fallback: if still zero, use full Hamiltonian
    if H_scale == 0:
        H_full = coupling.build_full_hamiltonian(dim)
        eigenvalues, _ = coupling.compute_energy_spectrum(dim)
        H_scale = np.mean(np.abs(np.diff(eigenvalues)))  # Mean level spacing
    
    return H_scale


def auto_optimize_field_range(
    network: SpinNetwork,
    matter_field: MatterFieldProperties,
    lambda_val: float,
    mu: float,
    dim: int = 32,
    perturbation_fraction: float = 0.1,
    num_field_points: int = 20
) -> np.ndarray:
    """
    Automatically determine optimal external field range.
    
    Strategy: Set h_max ~ perturbation_fraction × H_scale
    This ensures field is strong enough to mix levels but not dominate.
    
    Args:
        network: Spin network
        matter_field: Matter field properties
        lambda_val: Coupling constant for scale estimation
        mu: Polymer parameter for scale estimation
        dim: Hilbert space dimension
        perturbation_fraction: Field strength as fraction of H_scale (default 10%)
        num_field_points: Number of field values to sweep
    
    Returns:
        field_values: Optimized field array
    """
    # Compute Hamiltonian energy scale
    H_scale = compute_hamiltonian_energy_scale(network, matter_field, lambda_val, mu, dim)
    
    # Set h_max as fraction of H_scale
    h_max = perturbation_fraction * H_scale
    
    print(f"\nAuto-optimized external field range:")
    print(f"  H_scale (mean |H_geom|) = {H_scale:.3e} J")
    print(f"  Perturbation fraction = {perturbation_fraction:.1%}")
    print(f"  h_max = {h_max:.3e} J ({perturbation_fraction:.1%} of H_scale)")
    print(f"  Field range: [0, {h_max:.3e}] J")
    
    # Create field array (include zero)
    field_values = np.linspace(0, h_max, num_field_points)
    
    return field_values


def field_enhanced_search(
    network: SpinNetwork,
    mu_values: np.ndarray,
    field_values: np.ndarray,
    matter_fields: Dict[str, MatterFieldProperties],
    lambda_range: Tuple[float, float] = (1e-8, 1e-4),
    n_lambda: int = 10,
    min_gap_threshold: float = 1e-37,
    dim: int = 32,
    rho_exponent: float = 1.0,
    auto_optimize_field: bool = False
) -> List[FieldSweepPoint]:
    """
    2D sweep over (μ, external field) to find enhanced coupling regions.
    
    This implements GPT-5's Priority #1: external field perturbation can break
    degeneracies and induce mixing, potentially increasing |⟨f|H_int|i⟩| by
    many orders of magnitude.
    
    Args:
        network: Spin network
        mu_values: Polymer parameter grid (~200 points)
        field_values: External field grid (~20 points) OR None if auto_optimize_field=True
        matter_fields: Matter field types to test
        lambda_range: Coupling constant range
        n_lambda: Number of λ samples
        min_gap_threshold: Resonance detection threshold
        dim: Hilbert space dimension
        rho_exponent: Density of states exponent (α=1 physical)
        auto_optimize_field: If True, automatically compute optimal field range
    
    Returns:
        List of FieldSweepPoint objects ranked by FOM
    """
    print("=" * 80)
    print("2D (μ, EXTERNAL FIELD) SWEEP WITH COMBINED OPTIMIZATION")
    print("=" * 80)
    
    # Auto-optimize field range if requested
    if auto_optimize_field:
        # Use first matter field and middle μ for scaling estimate
        first_field = list(matter_fields.values())[0]
        mu_mid = mu_values[len(mu_values) // 2]
        lambda_mid = np.sqrt(lambda_range[0] * lambda_range[1])  # Geometric mean
        
        field_values = auto_optimize_field_range(
            network, first_field, lambda_mid, mu_mid, dim,
            perturbation_fraction=0.1,  # 10% of H_scale
            num_field_points=20
        )
    
    print(f"\nParameter grid:")
    print(f"  μ: {len(mu_values)} points in [{mu_values.min():.3e}, {mu_values.max():.3e}]")
    print(f"  External field: {len(field_values)} points in [{field_values.min():.3e}, {field_values.max():.3e}]")
    print(f"  Total grid points: {len(mu_values) * len(field_values)}")
    print(f"\nDensity of states: ρ ~ 1/gap^{rho_exponent}\n")
    
    results = []
    lambda_values = np.logspace(np.log10(lambda_range[0]), np.log10(lambda_range[1]), n_lambda)
    
    ResonanceSearcher = resonance_module.ResonanceSearcher
    
    # Loop over external field values
    for field_idx, field in enumerate(field_values, 1):
        print(f"Field {field_idx}/{len(field_values)}: h = {field:.3e}")
        
        # Step 1: Resonance search at this field value
        searcher = ResonanceSearcher(network)
        mu_vals, energy_spectra, _ = searcher.sweep_polymer_parameter(mu_values, external_field=field)
        
        # Detect avoided crossings
        avoided_crossings = detect_avoided_crossings(mu_vals, energy_spectra, min_gap_threshold)
        print(f"  → Found {len(avoided_crossings)} resonances")
        
        if len(avoided_crossings) == 0:
            continue
        
        # Compute susceptibility
        susceptibility = searcher.compute_susceptibility(mu_vals, energy_spectra)
        
        # Step 2: Optimize coupling at each resonance
        for crossing in avoided_crossings[:15]:  # Limit to top 15 per field
            mu_res = crossing.parameter_value
            level1 = crossing.level1_idx
            level2 = crossing.level2_idx
            gap = crossing.min_gap
            
            # Get susceptibility
            mu_idx = np.argmin(np.abs(mu_vals - mu_res))
            chi = np.mean([abs(susceptibility[mu_idx, level1]), abs(susceptibility[mu_idx, level2])])
            
            # Test each matter field
            for field_name, matter_field in matter_fields.items():
                best_lambda = lambda_values[0]
                best_coupling = 0.0
                best_rate = 0.0
                
                # Optimize λ
                for lambda_val in lambda_values:
                    coupling_strength, driven_rate = compute_coupling_with_field(
                        network, mu_res, field, matter_field, lambda_val,
                        level1, level2, dim, rho_exponent
                    )
                    
                    if coupling_strength > best_coupling:
                        best_coupling = coupling_strength
                        best_lambda = lambda_val
                        best_rate = driven_rate
                
                # Calculate figure of merit
                if gap > 0:
                    fom = best_rate * chi / gap
                else:
                    fom = 0.0
                
                # Store result
                results.append(FieldSweepPoint(
                    mu=mu_res,
                    external_field=field,
                    lambda_opt=best_lambda,
                    field_type=field_name,
                    level1_idx=level1,
                    level2_idx=level2,
                    energy_gap=gap,
                    coupling_strength=best_coupling,
                    driven_rate=best_rate,
                    susceptibility=chi,
                    figure_of_merit=fom
                ))
    
    # Sort by figure of merit
    results.sort(key=lambda x: x.figure_of_merit, reverse=True)
    
    print(f"\n✓ Completed 2D sweep: {len(results)} total candidates")
    
    return results


def _process_single_field_value(
    field: float,
    network: SpinNetwork,
    mu_values: np.ndarray,
    matter_fields: Dict[str, MatterFieldProperties],
    lambda_range: Tuple[float, float],
    n_lambda: int,
    min_gap_threshold: float,
    dim: int,
    rho_exponent: float,
    field_idx: int,
    total_fields: int
) -> List[FieldSweepPoint]:
    """
    Process a single field value in the 2D sweep.
    
    This function is designed to be called in parallel via multiprocessing.Pool.
    
    Args:
        field: External field strength for this iteration
        network: Spin network (must be picklable)
        mu_values: Polymer parameter grid
        matter_fields: Matter field types to test
        lambda_range: Coupling constant range
        n_lambda: Number of λ samples
        min_gap_threshold: Resonance detection threshold
        dim: Hilbert space dimension
        rho_exponent: Density of states exponent
        field_idx: Index of this field value (for progress reporting)
        total_fields: Total number of field values
    
    Returns:
        List of FieldSweepPoint objects for this field value
    """
    results = []
    lambda_values = np.logspace(np.log10(lambda_range[0]), np.log10(lambda_range[1]), n_lambda)
    
    ResonanceSearcher = resonance_module.ResonanceSearcher
    
    print(f"Field {field_idx}/{total_fields}: h = {field:.3e}")
    
    # Step 1: Resonance search at this field value
    searcher = ResonanceSearcher(network)
    mu_vals, energy_spectra, _ = searcher.sweep_polymer_parameter(mu_values, external_field=field)
    
    # Detect avoided crossings
    avoided_crossings = detect_avoided_crossings(mu_vals, energy_spectra, min_gap_threshold)
    print(f"  → Found {len(avoided_crossings)} resonances")
    
    if len(avoided_crossings) == 0:
        return results
    
    # Compute susceptibility
    susceptibility = searcher.compute_susceptibility(mu_vals, energy_spectra)
    
    # Step 2: Optimize coupling at each resonance
    for crossing in avoided_crossings[:15]:  # Limit to top 15 per field
        mu_res = crossing.parameter_value
        level1 = crossing.level1_idx
        level2 = crossing.level2_idx
        gap = crossing.min_gap
        
        # Get susceptibility
        mu_idx = np.argmin(np.abs(mu_vals - mu_res))
        chi = np.mean([abs(susceptibility[mu_idx, level1]), abs(susceptibility[mu_idx, level2])])
        
        # Test each matter field
        for field_name, matter_field in matter_fields.items():
            best_lambda = lambda_values[0]
            best_coupling = 0.0
            best_rate = 0.0
            
            # Optimize λ
            for lambda_val in lambda_values:
                coupling_strength, driven_rate = compute_coupling_with_field(
                    network, mu_res, field, matter_field, lambda_val,
                    level1, level2, dim, rho_exponent
                )
                
                if driven_rate > best_rate:
                    best_rate = driven_rate
                    best_coupling = coupling_strength
                    best_lambda = lambda_val
            
            # FOM: balance coupling and susceptibility
            fom = best_coupling * chi
            
            results.append(FieldSweepPoint(
                mu=mu_res,
                external_field=field,
                lambda_opt=best_lambda,
                field_type=field_name,
                level1_idx=level1,
                level2_idx=level2,
                energy_gap=gap,
                coupling_strength=best_coupling,
                driven_rate=best_rate,
                susceptibility=chi,
                figure_of_merit=fom
            ))
    
    return results


def field_enhanced_search_parallel(
    network: SpinNetwork,
    mu_values: np.ndarray,
    field_values: np.ndarray,
    matter_fields: Dict[str, MatterFieldProperties],
    lambda_range: Tuple[float, float] = (1e-8, 1e-4),
    n_lambda: int = 10,
    min_gap_threshold: float = 1e-37,
    dim: int = 32,
    rho_exponent: float = 1.0,
    auto_optimize_field: bool = False,
    n_processes: Optional[int] = None
) -> List[FieldSweepPoint]:
    """
    PARALLEL version of 2D (μ, external field) sweep.
    
    Distributes field values across multiple CPU cores for ~10-20× speedup.
    Each field value is processed independently in parallel.
    
    Args:
        network: Spin network
        mu_values: Polymer parameter grid (~200 points)
        field_values: External field grid (~20 points) OR None if auto_optimize_field=True
        matter_fields: Matter field types to test
        lambda_range: Coupling constant range
        n_lambda: Number of λ samples
        min_gap_threshold: Resonance detection threshold
        dim: Hilbert space dimension
        rho_exponent: Density of states exponent (α=1 physical)
        auto_optimize_field: If True, automatically compute optimal field range
        n_processes: Number of parallel processes (None = use all cores)
    
    Returns:
        List of FieldSweepPoint objects ranked by FOM
    """
    print("=" * 80)
    print("PARALLEL 2D (μ, EXTERNAL FIELD) SWEEP")
    print("=" * 80)
    
    # Auto-optimize field range if requested
    if auto_optimize_field:
        first_field = list(matter_fields.values())[0]
        mu_mid = mu_values[len(mu_values) // 2]
        lambda_mid = np.sqrt(lambda_range[0] * lambda_range[1])
        
        field_values = auto_optimize_field_range(
            network, first_field, lambda_mid, mu_mid, dim,
            perturbation_fraction=0.1,
            num_field_points=20
        )
    
    # Determine number of processes
    if n_processes is None:
        n_processes = min(cpu_count(), len(field_values))
    
    print(f"\nParallel execution:")
    print(f"  CPU cores available: {cpu_count()}")
    print(f"  Processes to use: {n_processes}")
    print(f"  Expected speedup: ~{min(n_processes, len(field_values))}× vs sequential\n")
    
    print(f"Parameter grid:")
    print(f"  μ: {len(mu_values)} points in [{mu_values.min():.3e}, {mu_values.max():.3e}]")
    print(f"  External field: {len(field_values)} points in [{field_values.min():.3e}, {field_values.max():.3e}]")
    print(f"  Total grid points: {len(mu_values) * len(field_values)}")
    print(f"\nDensity of states: ρ ~ 1/gap^{rho_exponent}\n")
    
    # Parallel execution over field values
    print("Starting parallel sweep...")
    with Pool(processes=n_processes) as pool:
        # Create argument tuples for starmap
        args_list = [
            (field, network, mu_values, matter_fields, lambda_range, n_lambda,
             min_gap_threshold, dim, rho_exponent, idx+1, len(field_values))
            for idx, field in enumerate(field_values)
        ]
        results_per_field = pool.starmap(_process_single_field_value, args_list)
    
    # Combine results from all field values
    all_results = []
    for field_results in results_per_field:
        all_results.extend(field_results)
    
    # Sort by figure of merit
    all_results.sort(key=lambda x: x.figure_of_merit, reverse=True)
    
    print(f"\n✓ Completed parallel 2D sweep: {len(all_results)} total candidates")
    
    return all_results


def plot_field_landscape(
    results: List[FieldSweepPoint],
    decoherence_rate: float = 0.01,
    output_path: str = "outputs/field_landscape.png"
):
    """
    Visualize 2D (μ, h) landscape showing coupling enhancement from field.
    
    Creates a scatter plot with color indicating Γ_driven/γ ratio.
    """
    if not results:
        print("No results to plot.")
        return
    
    mu_vals = np.array([r.mu for r in results])
    field_vals = np.array([r.external_field for r in results])
    rates = np.array([r.driven_rate for r in results])
    
    # SNR: Γ_driven/γ
    snr = rates / decoherence_rate
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Log scale for SNR coloring
    scatter = ax.scatter(
        mu_vals, field_vals,
        c=np.log10(snr + 1e-300),  # Avoid log(0)
        s=50,
        cmap='viridis',
        alpha=0.6
    )
    
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('log₁₀(Γ_driven/γ)', fontsize=12)
    
    ax.set_xlabel('Polymer parameter μ', fontsize=12)
    ax.set_ylabel('External field h', fontsize=12)
    ax.set_title('2D Field Sweep: Coupling Enhancement Landscape', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    # Mark observability threshold (Γ_driven = 10γ)
    threshold_snr = np.log10(10)
    ax.axhline(y=0, color='red', linestyle='--', linewidth=1, alpha=0.5, label='h = 0 (no field)')
    
    ax.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n✓ Saved field landscape to {output_path}")
    plt.close()


def analyze_field_enhancement(
    results: List[FieldSweepPoint],
    decoherence_rate: float = 0.01,
    top_n: int = 10
):
    """
    Analyze how external field enhances coupling and driven rates.
    
    Reports progress toward Γ_driven/γ ≥ 10 milestone.
    """
    print("\n" + "=" * 80)
    print("FIELD ENHANCEMENT ANALYSIS")
    print("=" * 80)
    
    if not results:
        print("No candidates to analyze.")
        return
    
    # Categorize by observability
    promising = [r for r in results if r.driven_rate >= 10 * decoherence_rate]
    marginal = [r for r in results if decoherence_rate / 10 <= r.driven_rate < 10 * decoherence_rate]
    unfeasible = [r for r in results if r.driven_rate < decoherence_rate / 10]
    
    print(f"\nTotal candidates: {len(results)}")
    print(f"  ✓ Promising (Γ ≥ 10γ): {len(promising)} ({100*len(promising)/len(results):.1f}%)")
    print(f"  ⚠️  Marginal (γ/10 ≤ Γ < 10γ): {len(marginal)} ({100*len(marginal)/len(results):.1f}%)")
    print(f"  ✗ Unfeasible (Γ < γ/10): {len(unfeasible)} ({100*len(unfeasible)/len(results):.1f}%)")
    
    # Top candidates
    print(f"\nTop {min(top_n, len(results))} candidates:")
    for idx, point in enumerate(results[:top_n], 1):
        snr = point.driven_rate / decoherence_rate
        print(f"\n{idx}. Matter: {point.field_type}, μ={point.mu:.3f}, h={point.external_field:.3e}")
        print(f"   λ*={point.lambda_opt:.3e}, gap={point.energy_gap:.3e} J")
        print(f"   |⟨f|H_int|i⟩|={point.coupling_strength:.3e} J")
        print(f"   Γ_driven={point.driven_rate:.3e} Hz (SNR={snr:.3e})")
        if snr >= 10:
            print(f"   ✓ OBSERVABLE (Γ/γ ≥ 10)")
        elif snr >= 0.1:
            print(f"   ⚠️  MARGINAL")
        else:
            print(f"   ✗ UNFEASIBLE")
    
    # Field effect summary
    h_zero_results = [r for r in results if abs(r.external_field) < 1e-30]
    h_nonzero_results = [r for r in results if abs(r.external_field) >= 1e-30]
    
    if h_zero_results and h_nonzero_results:
        avg_rate_zero = np.mean([r.driven_rate for r in h_zero_results])
        avg_rate_nonzero = np.mean([r.driven_rate for r in h_nonzero_results])
        enhancement = avg_rate_nonzero / avg_rate_zero if avg_rate_zero > 0 else float('inf')
        
        print(f"\nField effect:")
        print(f"  Average Γ (h=0): {avg_rate_zero:.3e} Hz")
        print(f"  Average Γ (h≠0): {avg_rate_nonzero:.3e} Hz")
        print(f"  Enhancement factor: {enhancement:.3e}×")
