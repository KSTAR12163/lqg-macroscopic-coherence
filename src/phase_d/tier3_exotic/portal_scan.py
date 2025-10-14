#!/usr/bin/env python3
"""
Portal Coupling Scanner

Scan axion and dark photon portal parameter spaces to find
maximum achievable g_eff within experimental bounds.

Usage:
    python -m src.phase_d.tier3_exotic.portal_scan --bounds conservative --out results/portal_g0_bounds.json
"""

import argparse
import json
from pathlib import Path

from src.phase_d.tier3_exotic.portal_couplings import find_best_portal_coupling


def main():
    """Main entry point."""
    
    parser = argparse.ArgumentParser(
        description="Scan portal coupling parameter space for maximum g_eff"
    )
    parser.add_argument(
        '--bounds',
        choices=['conservative', 'aggressive', 'theoretical'],
        default='conservative',
        help='Parameter space bounds (conservative = well within experimental limits)'
    )
    parser.add_argument(
        '--out',
        type=Path,
        default=Path('results/portal_g0_bounds.json'),
        help='Output JSON path'
    )
    
    args = parser.parse_args()
    
    # Run scan
    results = find_best_portal_coupling(bounds=args.bounds)
    
    # Save results
    args.out.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to JSON-serializable
    output = {
        'bounds': results['bounds'],
        'n_axion_configs': results['n_axion_configs'],
        'n_dark_photon_configs': results['n_dark_photon_configs'],
        'best_axion': results['best_axion'],
        'best_dark_photon': results['best_dark_photon'],
        'best_overall': results['best_overall'],
        'top_10': results['all_results']
    }
    
    with open(args.out, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Results saved: {args.out}")
    
    print(f"\n{'='*70}")
    print("✅ PORTAL SCAN COMPLETE")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
