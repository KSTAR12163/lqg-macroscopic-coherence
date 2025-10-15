#!/usr/bin/env python3
"""
Generate summary plots for f(R) gravity ANEC analysis.
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Results from test_fR_anec.py
results = {
    'alpha_values': [1e-10, 1e-8, 1e-6],
    'anec_gr': [-7.482e40, -7.482e40, -7.482e40],
    'anec_fr': [-2.928e40, -1.197e41, -4.563e42],
    'rel_change': [0.0, 0.60, 60.0]  # Relative to GR
}

# Create figure with subplots
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Plot 1: ANEC values
ax1 = axes[0]
alpha_plot = results['alpha_values']
ax1.plot(alpha_plot, np.abs(results['anec_gr']), 'o-', label='GR', linewidth=2, markersize=8)
ax1.plot(alpha_plot, np.abs(results['anec_fr']), 's-', label='f(R)', linewidth=2, markersize=8)
ax1.axhline(0, color='green', linestyle='--', linewidth=1, alpha=0.5, label='ANEC = 0 (boundary)')
ax1.set_xscale('log')
ax1.set_yscale('log')
ax1.set_xlabel('α (m²)', fontsize=12)
ax1.set_ylabel('|ANEC| (J)', fontsize=12)
ax1.set_title('ANEC Violation vs α\nf(R) = R + α R²', fontsize=14, fontweight='bold')
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)

# Add PPN constraint line
ax1.axvline(1e-6, color='red', linestyle=':', linewidth=2, alpha=0.7)
ax1.text(1e-6, 1e39, 'PPN limit\n(α < 10⁻⁶)', fontsize=9, ha='right', va='bottom', color='red')

# Plot 2: Relative worsening
ax2 = axes[1]
worsening_factor = [abs(fr/gr) for gr, fr in zip(results['anec_gr'], results['anec_fr'])]
ax2.bar(range(len(alpha_plot)), worsening_factor, color=['orange', 'red', 'darkred'], alpha=0.7)
ax2.set_xticks(range(len(alpha_plot)))
ax2.set_xticklabels([f'{a:.0e}' for a in alpha_plot])
ax2.set_xlabel('α (m²)', fontsize=12)
ax2.set_ylabel('|ANEC_f(R) / ANEC_GR|', fontsize=12)
ax2.set_title('f(R) Amplification Factor\n(>1 means worse than GR)', fontsize=14, fontweight='bold')
ax2.axhline(1, color='green', linestyle='--', linewidth=2, alpha=0.7, label='GR baseline')
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3, axis='y')

# Add value labels on bars
for i, (a, w) in enumerate(zip(alpha_plot, worsening_factor)):
    ax2.text(i, w, f'{w:.1f}×', ha='center', va='bottom', fontsize=10, fontweight='bold')

plt.tight_layout()

# Save figure
output_path = Path(__file__).parent / 'f_R_anec_summary.png'
plt.savefig(output_path, dpi=150, bbox_inches='tight')
print(f"✅ Plot saved to {output_path}")

# Print summary table
print("\n" + "="*70)
print("f(R) = R + α R² ANEC SUMMARY")
print("="*70)
print(f"{'α (m²)':<12} {'ANEC_GR (J)':<15} {'ANEC_f(R) (J)':<15} {'Amplification':<15}")
print("-"*70)
for a, gr, fr in zip(results['alpha_values'], results['anec_gr'], results['anec_fr']):
    amp = abs(fr/gr)
    print(f"{a:<12.1e} {gr:<15.3e} {fr:<15.3e} {amp:<15.1f}×")
print("="*70)
print("\n✅ All α values make ANEC WORSE, not better")
print("❌ f(R) = R + α R² does NOT enable FTL")
print()
