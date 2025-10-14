#!/usr/bin/env python3
"""
Warp Bubble Evaluation Runner

Orchestrates energy condition, stability, and realizability checks
for warp bubble candidates with optional portal coupling enhancement.

Usage:
    python -m src.phase_d.warp_eval.runner \
        --candidate configs/warp_candidates.yaml \
        --portal-g-eff 9.12e-13 \
        --out results/warp_eval.json
"""

import argparse
import json
from pathlib import Path
from typing import Dict, Optional
import yaml

from src.phase_d.warp_eval.energy_conditions import evaluate_all_energy_conditions
from src.phase_d.warp_eval.stability import evaluate_stability
from src.phase_d.warp_eval.realizability import evaluate_realizability


def load_candidate(path: Path) -> Dict:
    """Load candidate from YAML."""
    with open(path) as f:
        data = yaml.safe_load(f)
    return data


def compute_portal_boost(g_eff: float, g_baseline: float = 1e-121) -> float:
    """
    Compute portal coupling boost factor.
    
    HYPOTHESIS: Stress-energy scales as T_eff = T_geom / (1 + α × g_eff/g_baseline)
    where α is calibration parameter.
    
    For now, use simple ratio: boost = g_eff / g_baseline
    
    Args:
        g_eff: Effective coupling from portal (J)
        g_baseline: Baseline LQG coupling (J)
        
    Returns:
        Boost factor (dimensionless)
    """
    if g_baseline <= 0:
        return 1.0
    
    boost = g_eff / g_baseline
    
    # Cap boost to avoid numerical issues
    boost = min(boost, 1e10)
    boost = max(boost, 1.0)
    
    return boost


def evaluate_candidate(
    candidate: Dict,
    portal_g_eff: Optional[float] = None
) -> Dict:
    """
    Full evaluation of warp bubble candidate.
    
    Args:
        candidate: Bubble specification
        portal_g_eff: Portal-enhanced coupling (J), or None for no portal
        
    Returns:
        Complete evaluation results
    """
    # Compute portal boost
    if portal_g_eff is not None:
        portal_boost = compute_portal_boost(portal_g_eff)
    else:
        portal_boost = 1.0
    
    print(f"\nEvaluating candidate: {candidate.get('name', 'unnamed')}")
    print(f"  Shape: {candidate.get('shape', 'unknown')}")
    print(f"  Velocity: {candidate.get('velocity', '?')} c")
    print(f"  Portal boost: {portal_boost:.2e}×")
    
    # Energy conditions
    print("  Checking energy conditions...")
    energy_results = evaluate_all_energy_conditions(candidate, portal_boost)
    
    # Stability
    print("  Analyzing stability...")
    stability_results = evaluate_stability(candidate, portal_boost)
    
    # Realizability
    print("  Assessing realizability...")
    realizability_results = evaluate_realizability(candidate, portal_boost)
    
    # Overall viability score
    energy_score = sum(1 for k in ['NEC', 'WEC', 'ANEC', 'QI', 'QNEC'] 
                       if energy_results.get(k, {}).get('passed', False))
    stability_score = 1 if stability_results.get('overall_stable', False) else 0
    realizability_score = 1 if realizability_results.get('realizable', False) else 0
    
    total_score = (energy_score * 10) + (stability_score * 20) + (realizability_score * 20)
    max_score = 100
    
    viable = total_score >= 80  # Need 80/100 to be viable
    
    results = {
        'candidate': {
            'name': candidate.get('name', 'unnamed'),
            'shape': candidate.get('shape', 'unknown'),
            'velocity': candidate.get('velocity', 0.0),
            'radius': candidate.get('bubble_radius', 0.0),
            'wall_thickness': candidate.get('wall_thickness', 0.0)
        },
        'portal': {
            'g_eff_J': portal_g_eff if portal_g_eff else 0.0,
            'boost_factor': portal_boost
        },
        'energy_conditions': energy_results,
        'stability': stability_results,
        'realizability': realizability_results,
        'scoring': {
            'energy_conditions': f"{energy_score}/5",
            'stability': f"{stability_score}/1",
            'realizability': f"{realizability_score}/1",
            'total': f"{total_score}/{max_score}",
            'viable': viable
        }
    }
    
    print(f"  Score: {total_score}/{max_score} - {'VIABLE' if viable else 'NOT VIABLE'}")
    
    return results


def main():
    """Main entry point."""
    
    parser = argparse.ArgumentParser(
        description="Evaluate warp bubble candidates"
    )
    parser.add_argument(
        '--candidate',
        type=Path,
        required=True,
        help='Path to candidate YAML file'
    )
    parser.add_argument(
        '--portal-g-eff',
        type=float,
        default=None,
        help='Portal-enhanced coupling g_eff (J)'
    )
    parser.add_argument(
        '--out',
        type=Path,
        default=Path('results/warp_eval.json'),
        help='Output JSON path'
    )
    
    args = parser.parse_args()
    
    print(f"{'='*70}")
    print(f"WARP BUBBLE EVALUATION")
    print(f"{'='*70}\n")
    
    # Load candidate(s)
    data = load_candidate(args.candidate)
    
    if 'candidates' in data:
        candidates = data['candidates']
    else:
        candidates = [data]
    
    print(f"Loaded {len(candidates)} candidate(s)")
    
    if args.portal_g_eff:
        print(f"Portal coupling: g_eff = {args.portal_g_eff:.4e} J")
    else:
        print(f"No portal coupling applied")
    
    # Evaluate each candidate
    all_results = []
    
    for candidate in candidates:
        result = evaluate_candidate(candidate, args.portal_g_eff)
        all_results.append(result)
    
    # Summary
    viable_count = sum(1 for r in all_results if r['scoring']['viable'])
    
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}\n")
    print(f"Total candidates: {len(candidates)}")
    print(f"Viable: {viable_count}")
    print(f"Not viable: {len(candidates) - viable_count}")
    
    if viable_count > 0:
        print(f"\n✅ WEEK 12 GATE: PASSED ({viable_count} viable candidate(s) found)")
    else:
        print(f"\n❌ WEEK 12 GATE: FAILED (no viable candidates)")
    
    # Save results
    args.out.parent.mkdir(parents=True, exist_ok=True)
    
    output = {
        'configuration': {
            'candidate_file': str(args.candidate),
            'portal_g_eff_J': args.portal_g_eff,
            'n_candidates': len(candidates)
        },
        'summary': {
            'total': len(candidates),
            'viable': viable_count,
            'not_viable': len(candidates) - viable_count,
            'week_12_gate_passed': viable_count > 0
        },
        'results': all_results
    }
    
    with open(args.out, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Results saved: {args.out}")
    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    main()
