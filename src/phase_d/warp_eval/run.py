#!/usr/bin/env python3
"""
Warp Candidate Evaluation Runner

Orchestrates evaluation of warp bubble candidates from configuration files.
Interfaces with existing warp-* repositories to screen candidates against
energy, stability, and realizability constraints.

Usage:
    python -m src.phase_d.warp_eval.run --candidates configs/warp_candidates.yaml --out results/warp_eval_summary.json
"""

import argparse
import json
import yaml
from pathlib import Path
from typing import List, Dict, Any

from src.phase_d.warp_eval import (
    WarpCandidate,
    WarpCandidateEvaluator,
    EnergyCondition,
    create_test_candidates
)


def load_candidates_from_yaml(yaml_path: Path) -> List[WarpCandidate]:
    """Load candidate specifications from YAML file."""
    
    if not yaml_path.exists():
        print(f"⚠️  Config file not found: {yaml_path}")
        print("Using test candidates instead...")
        return create_test_candidates()
    
    with open(yaml_path, 'r') as f:
        config = yaml.safe_load(f)
    
    candidates = []
    for c in config.get('candidates', []):
        candidates.append(WarpCandidate(
            name=c['name'],
            shape_type=c['shape_type'],
            parameters=c['parameters'],
            velocity=c['velocity'],
            bubble_radius=c['bubble_radius'],
            wall_thickness=c['wall_thickness']
        ))
    
    return candidates


def evaluate_candidates(
    candidates: List[WarpCandidate],
    strict_mode: bool = True
) -> List[Dict[str, Any]]:
    """
    Evaluate all candidates and return results.
    
    Args:
        candidates: List of warp candidates to evaluate
        strict_mode: Apply stringent acceptance criteria
        
    Returns:
        List of evaluation result dictionaries
    """
    evaluator = WarpCandidateEvaluator(strict_mode=strict_mode)
    
    results = []
    
    print("="*70)
    print("WARP CANDIDATE EVALUATION")
    print("="*70)
    print(f"\nEvaluating {len(candidates)} candidates...")
    print(f"Strict mode: {'ENABLED' if strict_mode else 'DISABLED'}")
    
    for i, candidate in enumerate(candidates, 1):
        print(f"\n{'='*70}")
        print(f"CANDIDATE {i}/{len(candidates)}: {candidate.name}")
        print(f"{'='*70}")
        print(f"Shape: {candidate.shape_type}")
        print(f"Velocity: {candidate.velocity:.1f}c")
        print(f"Bubble radius: {candidate.bubble_radius:.1f} m")
        print(f"Wall thickness: {candidate.wall_thickness:.1f} m")
        
        # Evaluate
        result = evaluator.evaluate(candidate)
        
        # Print summary
        print(f"\n--- RESULTS ---")
        print(f"Overall score: {result.overall_score:.1f}/100")
        print(f"Viable: {'✅ YES' if result.viable else '❌ NO'}")
        print(f"Recommendation: {result.recommendation}")
        
        # Energy conditions
        print(f"\nEnergy Conditions:")
        for ec in result.energy_conditions:
            status = "✅" if ec.satisfied else "❌"
            print(f"  {status} {ec.condition.value:15s}: "
                  f"{'PASS' if ec.satisfied else f'VIOLATE ({ec.violation_magnitude:.2e})'}")
        
        # Stability
        print(f"\nStability:")
        if result.stability.stable:
            print(f"  ✅ STABLE")
        else:
            print(f"  ❌ UNSTABLE ({len(result.stability.unstable_modes)} modes)")
            if result.stability.characteristic_timescale:
                print(f"     Timescale: {result.stability.characteristic_timescale:.2e} s")
        
        # Realizability
        print(f"\nSource Realizability:")
        if result.source_realizability.realizable:
            print(f"  ✅ REALIZABLE (TRL {result.source_realizability.technological_readiness_level})")
        else:
            print(f"  ❌ NOT REALIZABLE")
        print(f"  Energy budget: {result.source_realizability.required_energy:.2e} J")
        print(f"  Negative energy: {result.source_realizability.required_negative_energy:.2e} J")
        print(f"  Power: {result.source_realizability.required_power:.2e} W")
        
        # Convert to dict for JSON serialization
        result_dict = {
            'candidate': {
                'name': candidate.name,
                'shape_type': candidate.shape_type,
                'parameters': candidate.parameters,
                'velocity': candidate.velocity,
                'bubble_radius': candidate.bubble_radius,
                'wall_thickness': candidate.wall_thickness
            },
            'energy_conditions': [
                {
                    'condition': ec.condition.value,
                    'satisfied': ec.satisfied,
                    'violation_magnitude': ec.violation_magnitude,
                    'notes': ec.notes
                }
                for ec in result.energy_conditions
            ],
            'stability': {
                'stable': result.stability.stable,
                'n_unstable_modes': len(result.stability.unstable_modes),
                'characteristic_timescale': result.stability.characteristic_timescale,
                'notes': result.stability.notes
            },
            'source_realizability': {
                'realizable': result.source_realizability.realizable,
                'required_energy': result.source_realizability.required_energy,
                'required_negative_energy': result.source_realizability.required_negative_energy,
                'required_power': result.source_realizability.required_power,
                'materials': result.source_realizability.materials_needed,
                'TRL': result.source_realizability.technological_readiness_level,
                'notes': result.source_realizability.notes
            },
            'overall_score': result.overall_score,
            'viable': result.viable,
            'recommendation': result.recommendation
        }
        
        results.append(result_dict)
    
    return results


def print_summary(results: List[Dict[str, Any]]):
    """Print summary of all evaluations."""
    
    print(f"\n{'='*70}")
    print("EVALUATION SUMMARY")
    print(f"{'='*70}")
    
    viable_count = sum(1 for r in results if r['viable'])
    
    print(f"\nTotal candidates: {len(results)}")
    print(f"Viable: {viable_count}")
    print(f"Not viable: {len(results) - viable_count}")
    
    if viable_count > 0:
        print(f"\n✅ VIABLE CANDIDATES:")
        for r in results:
            if r['viable']:
                print(f"  • {r['candidate']['name']} (score: {r['overall_score']:.1f}/100)")
    
    # Best candidate (by score)
    best = max(results, key=lambda r: r['overall_score'])
    print(f"\n🏆 BEST CANDIDATE: {best['candidate']['name']}")
    print(f"   Score: {best['overall_score']:.1f}/100")
    print(f"   Viable: {'YES' if best['viable'] else 'NO'}")
    
    # Energy condition pass rates
    conditions = ['QI', 'QNEC', 'ANEC', 'NEC', 'WEC']
    print(f"\nEnergy Condition Pass Rates:")
    for cond in conditions:
        passed = sum(1 for r in results 
                    for ec in r['energy_conditions'] 
                    if ec['condition'] == cond and ec['satisfied'])
        total = len(results)
        print(f"  {cond:6s}: {passed}/{total} ({passed/total*100:.0f}%)")


def save_results(results: List[Dict[str, Any]], output_path: Path):
    """Save results to JSON file."""
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump({
            'n_candidates': len(results),
            'n_viable': sum(1 for r in results if r['viable']),
            'results': results
        }, f, indent=2)
    
    print(f"\n✅ Results saved: {output_path}")


def main():
    """Main entry point."""
    
    parser = argparse.ArgumentParser(
        description="Evaluate warp bubble candidates against energy/stability/realizability constraints"
    )
    parser.add_argument(
        '--candidates',
        type=Path,
        default=Path('configs/warp_candidates.yaml'),
        help='Path to candidates YAML file'
    )
    parser.add_argument(
        '--out',
        type=Path,
        default=Path('results/warp_eval_summary.json'),
        help='Output JSON path'
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        default=True,
        help='Use strict acceptance criteria (default: True)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Use built-in test candidates instead of config file'
    )
    
    args = parser.parse_args()
    
    # Load candidates
    if args.test or not args.candidates.exists():
        print("Using test candidates...")
        candidates = create_test_candidates()
    else:
        candidates = load_candidates_from_yaml(args.candidates)
    
    # Evaluate
    results = evaluate_candidates(candidates, strict_mode=args.strict)
    
    # Summary
    print_summary(results)
    
    # Save
    save_results(results, args.out)
    
    print(f"\n{'='*70}")
    print("✅ WARP EVALUATION COMPLETE")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
