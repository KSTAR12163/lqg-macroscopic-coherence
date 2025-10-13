#!/usr/bin/env python3
"""
Phase B: Aggressive Floquet Instability Search (Warp-first)

Goal: Find any non-perturbative amplification via strong periodic drive.

Approach:
- Model a representative two-level sector near a small gap (Δ) with coupling g0.
- Apply periodic modulation g(t) = g0 (1 + A cos ωt), scanning A, ω.
- Optionally include PT-symmetric gain/loss (γ_gain) to probe threshold behavior.

Outputs:
- Reports maximal growth per period: max log |λ_F|, where λ_F are Floquet multipliers.
- If growth > 0, exponential amplification is present.

Notes:
- For closed Hermitian systems (γ_gain=0), we expect growth=0.
- Positive growth requires effective gain/loss or open-system pumping.
"""

import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.floquet_instability.floquet_scan import floquet_scan_two_level


def main():
    print("=" * 80)
    print("PHASE B: FLOQUET INSTABILITY SCAN (WARP-FIRST)")
    print("=" * 80)

    # Set a representative small gap and base coupling (energy units)
    # These are abstracted; we scan relative scales rather than physical Hz here.
    delta_grid = np.geomspace(1e-6, 1e-2, 9)
    omega_grid = np.geomspace(1e-6, 1e-1, 13)
    amplitude_grid = np.linspace(0.1, 1.0, 10)  # strong drive up to 100%
    g0 = 1e-6  # small static coupling

    print("- Hermitian scan (no gain) ...")
    res_herm = floquet_scan_two_level(
        delta_grid=delta_grid,
        omega_grid=omega_grid,
        amplitude_grid=amplitude_grid,
        g0=g0,
        gamma_gain=0.0,
        steps_per_period=200,
        periods=20,
    )
    best_h = res_herm["best"]
    print(f"  Best hermitian growth: {best_h['growth']:.3e} per period (expected 0)")

    print("\n- PT-symmetric gain scan ...")
    res_gain = floquet_scan_two_level(
        delta_grid=delta_grid,
        omega_grid=omega_grid,
        amplitude_grid=amplitude_grid,
        g0=g0,
        gamma_gain=1e-6,  # probe tiny gain threshold
        steps_per_period=200,
        periods=20,
    )
    best_g = res_gain["best"]
    print(
        "  Best gain-assisted growth: "
        f"{best_g['growth']:.3e} per period at (Δ={best_g['delta']:.2e}, ω={best_g['omega']:.2e}, A={best_g['amplitude']:.2f})"
    )

    print("\nSummary:")
    if best_g["growth"] > 0:
        print("  → Non-Hermitian threshold crossed: exponential amplification possible.")
        print("  Next: Couple this sector back to full network; design active reservoir.")
    else:
        print("  → No exponential growth detected in this scan.")
        print("  Next: Increase gamma_gain, test multi-tone drive, and cavity Purcell boost.")


if __name__ == "__main__":
    main()
