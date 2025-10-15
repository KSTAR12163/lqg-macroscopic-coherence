"""
Compare ANEC for static vs time-pulsed Alcubierre metric using the generic integrator.
Saves JSON with ANEC values and Tkk stats for both cases.
"""

import json
from pathlib import Path
import numpy as np

from phase_d.warp_eval.alcubierre_analytic import alcubierre_metric_analytic
from phase_d.warp_eval.geodesics_generic import integrate_geodesic, compute_anec_generic
from phase_d.warp_eval.pulsed_profiles import pulsed_alcubierre_metric


def main():
    # Baseline bubble
    v_s = 1.0
    R = 100.0
    sigma = 10.0

    # Geodesic params
    initial_coords = np.array([0.0, -200.0, 0.0, 0.0])
    direction = np.array([1.0, 0.0, 0.0])
    lambda_max = 400.0
    n_steps = 180

    # Static metric function
    def metric_static(t, x, y, z):
        return alcubierre_metric_analytic(t, x, y, z, v_s, R, sigma)

    # Pulsed metric function (turn on between t0 and t1)
    t0, t1 = 0.0, 50.0  # switch-on over 50 units of coordinate time (dimensionless here)
    metric_pulsed = pulsed_alcubierre_metric(v_s, R, sigma, t0, t1, k=5.0)

    # Integrate static
    pos_s, tan_s, diag_s = integrate_geodesic(metric_static, initial_coords, direction, lambda_max, n_steps=n_steps)
    anec_s, stats_s = compute_anec_generic(metric_static, pos_s, tan_s, lambda_max)

    # Integrate pulsed
    pos_p, tan_p, diag_p = integrate_geodesic(metric_pulsed, initial_coords, direction, lambda_max, n_steps=n_steps)
    anec_p, stats_p = compute_anec_generic(metric_pulsed, pos_p, tan_p, lambda_max)

    out = {
        'params': {'v_s': v_s, 'R': R, 'sigma': sigma, 'lambda_max': lambda_max, 'n_steps': n_steps, 't0': t0, 't1': t1},
        'static': {'diag': diag_s, 'anec': anec_s, 'stats': stats_s},
        'pulsed': {'diag': diag_p, 'anec': anec_p, 'stats': stats_p},
        'delta_anec': anec_p - anec_s,
        'rel_change': float(abs((anec_p - anec_s) / anec_s)) if abs(anec_s) > 0 else None,
    }

    out_path = Path(__file__).parent / 'pulsed_vs_static_anec.json'
    with open(out_path, 'w') as f:
        json.dump(out, f, indent=2)
    print(f"Saved results to {out_path}")


if __name__ == '__main__':
    main()
