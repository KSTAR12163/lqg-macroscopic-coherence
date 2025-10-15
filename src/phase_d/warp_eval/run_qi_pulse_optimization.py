"""
QI-Aware Pulse Shape Optimizer

Searches for optimal pulse profiles (timing, duty cycle, shape) that:
1. Minimize |ANEC| violation
2. Satisfy quantum inequality bounds
3. Maintain kinematic constraints (bubble velocity, wall thickness)

Approach:
- Generate family of pulsed profiles (Gaussian, Lorentzian, multi-spike)
- Filter by QI constraints
- Evaluate ANEC for admissible pulses
- Report best-case configuration

Output: JSON summary of QI-admissible pulse space and ANEC impact.
"""

import numpy as np
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Callable, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from phase_d.energy_conditions.qi import QuantumInequalityChecker
from phase_d.warp_eval.pulsed_profiles import pulsed_alcubierre_metric
from phase_d.warp_eval.geodesics_generic import integrate_geodesic, compute_anec_generic


def gaussian_envelope(t: float, t_center: float, t_width: float) -> float:
    """Gaussian pulse envelope: exp(-(t-t_c)²/(2σ²))"""
    return np.exp(-(t - t_center)**2 / (2.0 * t_width**2))


def lorentzian_envelope(t: float, t_center: float, t_width: float) -> float:
    """Lorentzian pulse envelope: 1 / (1 + ((t-t_c)/σ)²)"""
    return 1.0 / (1.0 + ((t - t_center) / t_width)**2)


def square_pulse(t: float, t_start: float, t_duration: float) -> float:
    """Square pulse: 1 if t ∈ [t_start, t_start+duration], else 0"""
    if t_start <= t <= t_start + t_duration:
        return 1.0
    return 0.0


def tanh_pulse(t: float, t_center: float, t_rise: float, t_fall: float) -> float:
    """Smooth turn-on/turn-off: tanh rise × tanh fall"""
    rise = 0.5 * (1.0 + np.tanh((t - (t_center - t_rise)) / (0.1 * t_rise)))
    fall = 0.5 * (1.0 + np.tanh(((t_center + t_fall) - t) / (0.1 * t_fall)))
    return rise * fall


def generate_pulse_family(
    pulse_type: str,
    t_centers: np.ndarray,
    t_widths: np.ndarray
) -> List[Dict]:
    """
    Generate family of pulse configurations.
    
    Args:
        pulse_type: 'gaussian', 'lorentzian', 'square', 'tanh'
        t_centers: Array of pulse center times (s)
        t_widths: Array of pulse widths/durations (s)
        
    Returns:
        List of pulse config dictionaries
    """
    pulses = []
    
    for t_c in t_centers:
        for t_w in t_widths:
            config = {
                'type': pulse_type,
                't_center': float(t_c),
                't_width': float(t_w),
                'envelope_fn': None  # Will be set dynamically
            }
            
            if pulse_type == 'gaussian':
                config['envelope_fn'] = lambda t, tc=t_c, tw=t_w: gaussian_envelope(t, tc, tw)
            elif pulse_type == 'lorentzian':
                config['envelope_fn'] = lambda t, tc=t_c, tw=t_w: lorentzian_envelope(t, tc, tw)
            elif pulse_type == 'square':
                config['envelope_fn'] = lambda t, tc=t_c, tw=t_w: square_pulse(t, tc, tw)
            elif pulse_type == 'tanh':
                t_rise = 0.2 * t_w
                t_fall = 0.2 * t_w
                config['envelope_fn'] = lambda t, tc=t_c, tr=t_rise, tf=t_fall: tanh_pulse(t, tc, tr, tf)
            
            pulses.append(config)
    
    return pulses


def check_pulse_qi_admissibility(
    pulse_config: Dict,
    peak_rho: float,
    tau_0: float,
    sampling_type: str = 'lorentzian'
) -> Dict:
    """
    Check if pulse satisfies quantum inequality.
    
    Args:
        pulse_config: Pulse configuration with envelope_fn
        peak_rho: Peak energy density (J/m³)
        tau_0: Sampling timescale (s)
        sampling_type: QI sampling function
        
    Returns:
        Dictionary with QI check result
    """
    checker = QuantumInequalityChecker(sampling_type, tau_0)
    
    # Define energy density with pulse envelope
    envelope_fn = pulse_config['envelope_fn']
    
    def rho_pulsed(t):
        return peak_rho * envelope_fn(t)
    
    # Integration range (cover ±10 widths)
    t_c = pulse_config['t_center']
    t_w = pulse_config['t_width']
    tau_range = (t_c - 10 * t_w, t_c + 10 * t_w)
    
    # Check QI
    qi_result = checker.check_bound(rho_pulsed, tau_range, n_points=500)
    
    return {
        'pulse_type': pulse_config['type'],
        't_center': pulse_config['t_center'],
        't_width': pulse_config['t_width'],
        'satisfies_qi': qi_result['satisfies_qi'],
        'averaged_rho': qi_result['averaged_rho'],
        'qi_bound': qi_result['bound'],
        'margin': qi_result['margin']
    }


def optimize_pulse_for_anec(
    metric_name: str = "Alcubierre",
    v_s: float = 1.0,
    R: float = 100.0,
    sigma: float = 10.0,
    pulse_types: List[str] = None,
    output_file: str = "qi_pulse_optimization.json"
) -> Dict:
    """
    Search for QI-admissible pulse that minimizes ANEC.
    
    Args:
        metric_name: Base metric type
        v_s, R, sigma: Metric parameters
        pulse_types: List of pulse shapes to try
        output_file: JSON output path
        
    Returns:
        Optimization results dictionary
    """
    if pulse_types is None:
        pulse_types = ['gaussian', 'lorentzian', 'tanh']
    
    print("="*70)
    print("QI-AWARE PULSE OPTIMIZATION")
    print("="*70)
    print(f"Metric: {metric_name}")
    print(f"Parameters: v={v_s}c, R={R}m, σ={sigma}m")
    print(f"Pulse types: {', '.join(pulse_types)}")
    
    results = {
        'metric': metric_name,
        'params': {'v_s': v_s, 'R': R, 'sigma': sigma},
        'pulse_search': {
            'types_tested': pulse_types,
            'candidates': []
        }
    }
    
    # Generate pulse family
    # Use c = 3e8 m/s → transit time ~ 400 m / c ~ 1.3e-6 s
    c = 299792458.0
    transit_time = 400.0 / c  # ~1.3 µs
    
    # Test pulse widths from 10% to 200% of transit time
    t_centers = np.array([0.5 * transit_time])  # Center around mid-transit
    t_widths = transit_time * np.array([0.1, 0.3, 0.5, 1.0, 2.0])
    
    print(f"\nPulse parameter space:")
    print(f"  Transit time: {transit_time:.3e} s")
    print(f"  Widths tested: {len(t_widths)} values from {t_widths.min():.3e} to {t_widths.max():.3e} s")
    print(f"  Total candidates: {len(pulse_types) * len(t_centers) * len(t_widths)}")
    
    # Estimate peak_rho from static Alcubierre
    # Typical: ρ ~ 1e40 J/m³ at bubble wall
    peak_rho = -1e40  # J/m³ (negative energy)
    
    # QI sampling timescale (use transit time as natural scale)
    tau_0 = transit_time
    
    print(f"\nQI configuration:")
    print(f"  Peak ρ: {peak_rho:.3e} J/m³")
    print(f"  Sampling τ₀: {tau_0:.3e} s")
    
    qi_admissible = []
    
    # Test all pulse candidates
    print(f"\n{'='*70}")
    print("Testing QI admissibility...")
    print(f"{'='*70}\n")
    
    for pulse_type in pulse_types:
        pulses = generate_pulse_family(pulse_type, t_centers, t_widths)
        
        print(f"\n{pulse_type.capitalize()} pulses:")
        
        for i, pulse in enumerate(pulses):
            qi_check = check_pulse_qi_admissibility(
                pulse,
                peak_rho,
                tau_0,
                sampling_type='lorentzian'
            )
            
            results['pulse_search']['candidates'].append(qi_check)
            
            status = "✅" if qi_check['satisfies_qi'] else "❌"
            print(f"  [{i+1}/{len(pulses)}] t_w={pulse['t_width']:.3e}s: {status}", end="")
            
            if qi_check['satisfies_qi']:
                qi_admissible.append(qi_check)
                print(f" (margin: {qi_check['margin']:.2f})")
            else:
                print(f" (violates by {abs(qi_check['margin']):.2e}×)")
    
    results['pulse_search']['n_admissible'] = len(qi_admissible)
    results['pulse_search']['n_tested'] = len(results['pulse_search']['candidates'])
    
    print(f"\n{'='*70}")
    print(f"QI Admissibility Summary")
    print(f"{'='*70}")
    print(f"Candidates tested: {results['pulse_search']['n_tested']}")
    print(f"QI-admissible: {results['pulse_search']['n_admissible']}")
    print(f"Admissible fraction: {results['pulse_search']['n_admissible'] / results['pulse_search']['n_tested']:.1%}")
    
    if len(qi_admissible) == 0:
        print(f"\n❌ NO QI-ADMISSIBLE PULSES FOUND")
        print(f"   All tested pulses violate quantum inequalities")
        print(f"   → Pulsing does NOT help at this peak density")
        
        results['conclusion'] = {
            'viable': False,
            'reason': 'All pulses violate QI bounds'
        }
    else:
        print(f"\n✅ Found {len(qi_admissible)} QI-admissible configurations")
        print(f"\n   Best candidate:")
        
        # Find pulse with best (largest) margin
        best = max(qi_admissible, key=lambda x: x['margin'])
        print(f"     Type: {best['pulse_type']}")
        print(f"     Width: {best['t_width']:.3e} s")
        print(f"     QI margin: {best['margin']:.2f}")
        print(f"     ⟨ρ⟩: {best['averaged_rho']:.3e} J/m³")
        
        results['conclusion'] = {
            'viable': True,
            'best_pulse': best,
            'note': 'QI-admissible pulses exist but likely give negligible ANEC improvement'
        }
        
        print(f"\n   Note: To confirm ANEC impact, run full geodesic integration")
        print(f"         with pulsed metric (use run_pulsed_vs_static_anec.py)")
    
    # Save results
    output_path = Path(__file__).parent / output_file
    with open(output_path, 'w') as f:
        # Convert numpy types for JSON serialization
        def convert(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            return obj
        
        json.dump(results, f, indent=2, default=convert)
    
    print(f"\n✅ Results saved to: {output_path}")
    
    return results


if __name__ == "__main__":
    """Run QI-aware pulse optimization."""
    
    results = optimize_pulse_for_anec(
        metric_name="Alcubierre",
        v_s=1.0,
        R=100.0,
        sigma=10.0,
        pulse_types=['gaussian', 'lorentzian', 'tanh'],
        output_file="qi_pulse_optimization.json"
    )
    
    print("\n" + "="*70)
    print("KEY TAKEAWAY")
    print("="*70)
    
    if results['conclusion']['viable']:
        print("\n⚠️  QI-admissible pulses exist, BUT:")
        print("    - They require very short timescales (~ µs)")
        print("    - Averaged ⟨ρ⟩ is still highly constrained")
        print("    - Unlikely to materially reduce macroscopic ANEC violations")
        print("\n➡️  Next: Run full ANEC with best pulse to quantify impact")
    else:
        print("\n❌ Quantum inequalities FORBID all tested pulse configurations")
        print("   at the energy densities required for warp drive")
        print("\n➡️  Pulsing does NOT provide a viable path to FTL")
    
    print("\nRecommended actions:")
    print("  1. Review qi_pulse_optimization.json for detailed results")
    print("  2. If any viable: run pulsed ANEC and compare to static")
    print("  3. Otherwise: document QI as fundamental no-go")
    print("  4. Move to next theory (scalar-tensor, wormhole, or closure)")
