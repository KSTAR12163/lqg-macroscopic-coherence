#!/usr/bin/env python3
"""
Phase A Completion: Metric Expansion + QI Analysis

This script runs the complete Phase A workflow:
1. Test all three analytic metrics (Alcubierre, Natário, Van Den Broeck)
2. Multi-ray ANEC sweeps for each
3. QI-aware pulse optimization
4. Generate consolidated summary JSON

Execute from lqg-macroscopic-coherence directory:
    cd src/phase_d/warp_eval
    python run_phase_a_complete.py
"""

import sys
import os
from pathlib import Path
import subprocess

# Ensure we're in the right directory
script_dir = Path(__file__).parent
os.chdir(script_dir)

def run_command(cmd: str, description: str):
    """Run command and report status."""
    print(f"\n{'='*70}")
    print(f"{description}")
    print(f"{'='*70}")
    print(f"Command: {cmd}\n")
    
    result = subprocess.run(cmd, shell=True, capture_output=False, text=True)
    
    if result.returncode == 0:
        print(f"\n✅ {description} completed successfully")
    else:
        print(f"\n❌ {description} failed with code {result.returncode}")
        return False
    
    return True

def main():
    """Run complete Phase A analysis."""
    
    print("="*70)
    print("PHASE A: COMPREHENSIVE METRIC EXPANSION + QI ANALYSIS")
    print("="*70)
    print()
    print("This will:")
    print("  1. Test Natário metric implementation")
    print("  2. Test Van Den Broeck metric implementation")
    print("  3. Test Quantum Inequality checker")
    print("  4. Run multi-metric ANEC comparison (all 3 metrics)")
    print("  5. Run QI-aware pulse optimization")
    print()
    print("Expected runtime: ~5-10 minutes")
    print("Output: Multiple JSON files in current directory")
    print()
    
    input("Press Enter to start...")
    
    # Step 1: Test Natário metric
    if not run_command(
        "python metrics/natario_analytic.py",
        "Step 1/5: Testing Natário Metric"
    ):
        return
    
    # Step 2: Test Van Den Broeck metric
    if not run_command(
        "python metrics/vdb_analytic.py",
        "Step 2/5: Testing Van Den Broeck Metric"
    ):
        return
    
    # Step 3: Test QI checker
    qi_test = "python -c \"import sys; sys.path.insert(0,'../../..'); from phase_d.energy_conditions.qi import QuantumInequalityChecker; print('QI module imported successfully')\""
    
    if not run_command(
        qi_test,
        "Step 3/5: Testing Quantum Inequality Module"
    ):
        return
    
    # Step 4: Multi-metric ANEC comparison
    if not run_command(
        "python run_multimetric_anec.py",
        "Step 4/5: Multi-Metric ANEC Comparison (⏱️  may take several minutes)"
    ):
        return
    
    # Step 5: QI pulse optimization
    if not run_command(
        "python run_qi_pulse_optimization.py",
        "Step 5/5: QI-Aware Pulse Optimization"
    ):
        return
    
    # Summary
    print("\n" + "="*70)
    print("PHASE A COMPLETE ✅")
    print("="*70)
    print("\nGenerated files:")
    
    output_files = [
        "multimetric_anec_comparison.json",
        "qi_pulse_optimization.json"
    ]
    
    for fname in output_files:
        fpath = Path(fname)
        if fpath.exists():
            size_kb = fpath.stat().st_size / 1024
            print(f"  ✅ {fname} ({size_kb:.1f} KB)")
        else:
            print(f"  ❌ {fname} (not found)")
    
    print("\nNext steps:")
    print("  1. Review JSON files for detailed results")
    print("  2. Decide: Continue to Phase B (scalar-tensor)?")
    print("  3.         Or: Document closure (modified gravity fails)?")
    print("  4.         Or: Pivot to Phase C (wormholes)?")
    print()
    print("To visualize results (requires matplotlib):")
    print("  python plot_multimetric_summary.py")
    print()

if __name__ == "__main__":
    main()
