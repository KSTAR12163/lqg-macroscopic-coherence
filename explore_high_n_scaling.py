#!/usr/bin/env python3
"""
High-N Scaling Exploration

Push beyond N=500 to see if quadratic scaling holds
and identify computational limits.

Questions:
1. Does α stay ~2.0 at very large N?
2. What's the practical computational limit?
3. Can we reach 10¹⁰× or even 10¹⁵× with pure Tier 1?
"""

import numpy as np
import time
import matplotlib.pyplot as plt

from src.phase_d.tier1_collective.network_construction import create_complete_network
from src.phase_d.tier1_collective.collective_hamiltonian import (
    build_collective_hamiltonian
)
from run_week1_day3 import modify_edge_spins


def test_high_n_scaling(N_values, j=2.0, lambda_opt=5.0, E_opt=1e-13, dim=16):
    """Test scaling at high N."""
    
    print("="*70)
    print("HIGH-N SCALING EXPLORATION")
    print("="*70)
    print(f"\nTesting N = {N_values}")
    print(f"Configuration: j={j}, λ={lambda_opt}, E={E_opt:.2e} J, dim={dim}")
    
    results = []
    
    for N in N_values:
        print(f"\n{'='*70}")
        print(f"N = {N}")
        print(f"{'='*70}")
        
        t0 = time.time()
        
        # Create network
        print(f"Creating network...", end=" ", flush=True)
        network, _ = create_complete_network(N)
        network = modify_edge_spins(network, j)
        n_edges = len(network.edges)
        t1 = time.time()
        print(f"✅ {n_edges:,} edges ({t1-t0:.2f}s)")
        
        # Build Hamiltonian
        print(f"Building Hamiltonian...", end=" ", flush=True)
        ham = build_collective_hamiltonian(
            network,
            dim=dim,
            lambda_coupling=lambda_opt,
            matter_energy=E_opt
        )
        t2 = time.time()
        print(f"✅ ({t2-t1:.2f}s)")
        
        # Diagonalize
        print(f"Diagonalizing (dim={dim})...", end=" ", flush=True)
        eigvals, eigvecs = np.linalg.eigh(ham.H_total)
        t3 = time.time()
        print(f"✅ ({t3-t2:.2f}s)")
        
        # Extract coupling
        psi0 = eigvecs[:, 0]
        psi1 = eigvecs[:, 1]
        g_coll = abs(np.dot(np.conj(psi1), ham.H_int @ psi0))
        gap = eigvals[1] - eigvals[0]
        
        g_single = 3.96e-121
        enh = g_coll / g_single
        
        t_total = t3 - t0
        
        results.append({
            'N': N,
            'edges': n_edges,
            'g': g_coll,
            'enh': enh,
            'gap': gap,
            'time_network': t1 - t0,
            'time_hamiltonian': t2 - t1,
            'time_diag': t3 - t2,
            'time_total': t_total
        })
        
        print(f"\nResults:")
        print(f"  g = {g_coll:.4e} J")
        print(f"  Enhancement = {enh:.4e}×")
        print(f"  Gap = {gap:.4e} J")
        print(f"  Total time = {t_total:.2f}s")
        
        # Check targets
        tier1_target = 1e6
        tier2_target = 1e36  # Aspirational
        warp_target = 1e71
        
        tier1_ratio = enh / tier1_target
        tier2_ratio = enh / tier2_target
        warp_ratio = enh / warp_target
        
        print(f"\nVs Targets:")
        print(f"  Tier 1 (10⁶×): {tier1_ratio:.2e}× {'✅' if tier1_ratio >= 1 else '❌'}")
        print(f"  Tier 2 (10³⁶×): {tier2_ratio:.2e}× {'✅' if tier2_ratio >= 1 else '❌'}")
        print(f"  Warp (10⁷¹×): {warp_ratio:.2e}× {'✅' if warp_ratio >= 1 else '❌'}")
    
    return results


def analyze_high_n_results(results):
    """Analyze scaling and extrapolate."""
    
    print("\n" + "="*70)
    print("SCALING ANALYSIS")
    print("="*70)
    
    # Fit power law
    N_vals = np.array([r['N'] for r in results])
    g_vals = np.array([r['g'] for r in results])
    
    log_N = np.log(N_vals)
    log_g = np.log(g_vals)
    
    fit = np.polyfit(log_N, log_g, 1)
    alpha = fit[0]
    log_g0 = fit[1]
    g0 = np.exp(log_g0)
    
    # Residuals
    log_g_fit = alpha * log_N + log_g0
    residuals = log_g - log_g_fit
    rms = np.sqrt(np.mean(residuals**2))
    
    print(f"\nPower Law Fit: g = g₀ × N^α")
    print(f"  α = {alpha:.4f}")
    print(f"  g₀ = {g0:.4e} J")
    print(f"  RMS residual = {rms:.4f}")
    
    # Compare to theory
    alpha_theory = 2.0
    deviation = abs(alpha - alpha_theory)
    print(f"\nComparison to Theory:")
    print(f"  Theory: α = {alpha_theory}")
    print(f"  Measured: α = {alpha:.4f}")
    print(f"  Deviation: {deviation:.4f} ({deviation/alpha_theory*100:.2f}%)")
    
    if deviation < 0.05:
        print(f"  ✅ Excellent agreement!")
    elif deviation < 0.1:
        print(f"  ✅ Good agreement")
    else:
        print(f"  ⚠️  Significant deviation")
    
    # Extrapolation
    print("\n" + "="*70)
    print("EXTRAPOLATION")
    print("="*70)
    
    N_extrap = [1000, 5000, 10000, 50000, 100000]
    
    print(f"\nAssuming α = {alpha:.4f} holds...")
    print(f"\n{'N':>10s} {'Enhancement':>15s} {'vs 10⁶×':>12s} {'vs 10⁷¹×':>12s}")
    print("-"*60)
    
    for N in N_extrap:
        g_pred = g0 * N**alpha
        enh_pred = g_pred / 3.96e-121
        
        tier1_ratio = enh_pred / 1e6
        warp_ratio = enh_pred / 1e71
        
        print(f"{N:10,d} {enh_pred:15.3e} {tier1_ratio:12.2e} {warp_ratio:12.2e}")
    
    # Find N for specific targets
    print("\n" + "="*70)
    print("N REQUIREMENTS")
    print("="*70)
    
    targets = [
        ("Tier 1", 1e6),
        ("10¹⁰×", 1e10),
        ("10¹⁵×", 1e15),
        ("10²⁰×", 1e20),
        ("Tier 2", 1e36),
        ("Warp", 1e71)
    ]
    
    print(f"\n{'Target':>15s} {'Required N':>15s} {'Feasible?':>15s}")
    print("-"*50)
    
    for name, target in targets:
        g_target = target * 3.96e-121
        N_req = (g_target / g0)**(1/alpha)
        
        if N_req < 1000:
            feasible = "✅ Easy"
        elif N_req < 10000:
            feasible = "✅ Tractable"
        elif N_req < 100000:
            feasible = "⚠️ Challenging"
        elif N_req < 1e10:
            feasible = "❌ Impractical"
        else:
            feasible = "❌ Impossible"
        
        print(f"{name:>15s} {N_req:15.2e} {feasible:>15s}")
    
    # Computational scaling
    print("\n" + "="*70)
    print("COMPUTATIONAL SCALING")
    print("="*70)
    
    times = np.array([r['time_total'] for r in results])
    
    # Fit time vs N
    log_t = np.log(times)
    t_fit = np.polyfit(log_N, log_t, 1)
    beta = t_fit[0]
    
    print(f"\nTime Scaling: t ∝ N^β")
    print(f"  β = {beta:.3f}")
    
    if beta < 2.5:
        print(f"  ✅ Better than N³ (expected for diagonalization)")
    elif beta < 3.5:
        print(f"  ✅ Close to N³")
    else:
        print(f"  ⚠️  Worse than N³ - may have overhead")
    
    # Time projections
    print(f"\nTime Projections:")
    for N in [1000, 5000, 10000]:
        t_pred = np.exp(beta * np.log(N) + t_fit[1])
        print(f"  N={N:5,d}: {t_pred:6.1f}s ({t_pred/60:.1f}min)")


def create_high_n_plots(results):
    """Visualize high-N results."""
    
    fig = plt.figure(figsize=(15, 10))
    
    N_vals = [r['N'] for r in results]
    g_vals = [r['g'] for r in results]
    enh_vals = [r['enh'] for r in results]
    times = [r['time_total'] for r in results]
    
    # Plot 1: Enhancement vs N
    ax1 = plt.subplot(2, 3, 1)
    ax1.loglog(N_vals, enh_vals, 'bo-', linewidth=2, markersize=10, label='Measured')
    
    # Add target lines
    ax1.axhline(1e6, color='green', linestyle='--', linewidth=2, label='Tier 1 (10⁶×)')
    ax1.axhline(1e71, color='red', linestyle='--', linewidth=2, label='Warp (10⁷¹×)')
    
    ax1.set_xlabel('Network Size N', fontsize=13)
    ax1.set_ylabel('Enhancement', fontsize=13)
    ax1.set_title('High-N Scaling', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Scaling fit
    ax2 = plt.subplot(2, 3, 2)
    log_N = np.log(N_vals)
    log_g = np.log(g_vals)
    fit = np.polyfit(log_N, log_g, 1)
    alpha = fit[0]
    
    ax2.plot(log_N, log_g, 'bo', markersize=10, label='Data')
    ax2.plot(log_N, alpha*log_N + fit[1], 'r-', linewidth=2, label=f'Fit: α={alpha:.3f}')
    ax2.set_xlabel('ln(N)', fontsize=13)
    ax2.set_ylabel('ln(g)', fontsize=13)
    ax2.set_title(f'Power Law Fit (α={alpha:.3f})', fontsize=14, fontweight='bold')
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Computational time
    ax3 = plt.subplot(2, 3, 3)
    ax3.loglog(N_vals, times, 'mo-', linewidth=2, markersize=10)
    ax3.set_xlabel('Network Size N', fontsize=13)
    ax3.set_ylabel('Computation Time (s)', fontsize=13)
    ax3.set_title('Computational Scaling', fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Time breakdown
    ax4 = plt.subplot(2, 3, 4)
    t_net = [r['time_network'] for r in results]
    t_ham = [r['time_hamiltonian'] for r in results]
    t_diag = [r['time_diag'] for r in results]
    
    x = range(len(N_vals))
    ax4.bar(x, t_net, label='Network', alpha=0.7)
    ax4.bar(x, t_ham, bottom=t_net, label='Hamiltonian', alpha=0.7)
    ax4.bar(x, t_diag, bottom=np.array(t_net)+np.array(t_ham), label='Diagonalization', alpha=0.7)
    
    ax4.set_xticks(x)
    ax4.set_xticklabels([str(n) for n in N_vals])
    ax4.set_xlabel('Network Size N', fontsize=13)
    ax4.set_ylabel('Time (s)', fontsize=13)
    ax4.set_title('Time Breakdown', fontsize=14, fontweight='bold')
    ax4.legend(fontsize=10)
    ax4.grid(True, alpha=0.3, axis='y')
    
    # Plot 5: Enhancement rate
    ax5 = plt.subplot(2, 3, 5)
    if len(N_vals) > 1:
        enh_rate = [enh_vals[i+1]/enh_vals[i] for i in range(len(enh_vals)-1)]
        N_mid = [(N_vals[i] + N_vals[i+1])/2 for i in range(len(N_vals)-1)]
        ax5.semilogx(N_mid, enh_rate, 'go-', linewidth=2, markersize=10)
        ax5.set_xlabel('Network Size N', fontsize=13)
        ax5.set_ylabel('Enhancement Ratio (N_i+1 / N_i)', fontsize=13)
        ax5.set_title('Incremental Boost', fontsize=14, fontweight='bold')
        ax5.grid(True, alpha=0.3)
    
    # Plot 6: Efficiency (enh per second)
    ax6 = plt.subplot(2, 3, 6)
    efficiency = np.array(enh_vals) / np.array(times)
    ax6.loglog(N_vals, efficiency, 'co-', linewidth=2, markersize=10)
    ax6.set_xlabel('Network Size N', fontsize=13)
    ax6.set_ylabel('Enhancement per Second', fontsize=13)
    ax6.set_title('Computational Efficiency', fontsize=14, fontweight='bold')
    ax6.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('high_n_scaling.png', dpi=150, bbox_inches='tight')
    print("\n✅ Plot saved: high_n_scaling.png")


def main():
    """Run high-N exploration."""
    
    print("="*70)
    print("HIGH-N SCALING EXPLORATION")
    print("="*70)
    print("\nGoal: Push Tier 1 to its limits")
    print("Test: N = [100, 238, 500, 1000, 2000]")
    print("Config: Optimized (λ=5, E=10⁻¹³ J, j=2, dim=16)")
    
    # Warning
    print("\n⚠️  WARNING: N=2000 has ~2 million edges!")
    print("   Computation may take several minutes")
    print("   Hamiltonian size: 16×16 (manageable)")
    
    input("\nPress Enter to continue...")
    
    # Test range
    N_values = [100, 238, 500, 1000, 2000]
    
    results = test_high_n_scaling(N_values, j=2.0, lambda_opt=5.0, E_opt=1e-13, dim=16)
    
    # Analysis
    analyze_high_n_results(results)
    
    # Plots
    create_high_n_plots(results)
    
    print("\n" + "="*70)
    print("✅ HIGH-N EXPLORATION COMPLETE")
    print("="*70)
    
    return results


if __name__ == "__main__":
    results = main()
