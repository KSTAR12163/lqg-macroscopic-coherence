#!/usr/bin/env python3
"""
Plot summary for multi-ray f(R) ANEC sweep.
Reads fR_anec_multiray.json and generates plots:
- ANEC_GR and ANEC_fR vs impact parameter y0 for each alpha
- Relative change |ANEC_fR/ANEC_GR| vs y0
"""

import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt


def main():
    data_path = Path(__file__).parent / 'fR_anec_multiray.json'
    if not data_path.exists():
        raise FileNotFoundError(f"Results JSON not found: {data_path}")

    with open(data_path, 'r') as f:
        data = json.load(f)

    rays = data['rays']
    y0s = [r['y0'] for r in rays if r.get('success')]
    anec_gr = np.array([r['anec_GR'] for r in rays if r.get('success')])

    # Collect f(R) ANEC for each alpha over rays
    # Assume all rays share the same alpha set
    alphas = [entry['alpha'] for entry in rays[0]['alpha_results']]
    anec_fr_by_alpha = {alpha: [] for alpha in alphas}
    rel_change_by_alpha = {alpha: [] for alpha in alphas}

    for r in rays:
        if not r.get('success'):
            continue
        gr_val = r['anec_GR']
        for entry in r['alpha_results']:
            alpha = entry['alpha']
            fr_val = entry['anec_fR']
            anec_fr_by_alpha[alpha].append(fr_val)
            rc = abs((fr_val - gr_val) / gr_val) if abs(gr_val) > 0 else np.nan
            rel_change_by_alpha[alpha].append(rc)

    # Plot ANEC vs y0
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    ax1 = axes[0]
    ax1.plot(y0s, np.abs(anec_gr), 'k-o', label='GR', linewidth=2)
    colors = ['C1', 'C2', 'C3', 'C4']
    for i, alpha in enumerate(alphas):
        ax1.plot(y0s, np.abs(anec_fr_by_alpha[alpha]), '-s', color=colors[i % len(colors)], label=f'f(R), α={alpha:.0e}', linewidth=2)
    ax1.set_xlabel('Impact parameter y0 (m)')
    ax1.set_ylabel('|ANEC| (J)')
    ax1.set_yscale('log')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    ax1.set_title('ANEC vs impact parameter (|.| log-scale)')

    # Plot relative change vs y0
    ax2 = axes[1]
    for i, alpha in enumerate(alphas):
        ax2.plot(y0s, rel_change_by_alpha[alpha], '-o', color=colors[i % len(colors)], label=f'α={alpha:.0e}')
    ax2.set_xlabel('Impact parameter y0 (m)')
    ax2.set_ylabel('|ANEC_f(R) - ANEC_GR| / |ANEC_GR|')
    ax2.set_yscale('log')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    ax2.set_title('Relative ANEC change by f(R)')

    plt.tight_layout()
    out_path = Path(__file__).parent / 'fR_anec_multiray.png'
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    print(f"Saved plot to {out_path}")


if __name__ == '__main__':
    main()
