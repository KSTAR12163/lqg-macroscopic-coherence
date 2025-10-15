"""
Quick ANEC sweep for f(R) = R + alpha R^2 using precomputed geometry.
Saves JSON with ANEC for GR and f(R) across alpha values and optional multi-ray.
"""

import json
from pathlib import Path
import numpy as np

from phase_d.warp_eval.alcubierre_analytic import alcubierre_metric_analytic
from phase_d.warp_eval.geodesics_alcubierre import integrate_alcubierre_geodesic, compute_anec_alcubierre
from phase_d.warp_eval.stress_energy import compute_einstein_tensor, einstein_to_stress_energy
from phase_d.modified_gravity.f_R_gravity import FRGravity


def main():
    v_s = 1.0
    R = 100.0
    sigma = 10.0
    lambda_max = 400.0
    n_steps = 180
    alpha_values = [1e-10, 1e-8, 1e-6]

    # One central ray; extendable to multiple
    initial_coords = np.array([0.0, -200.0, 0.0, 0.0])
    direction = np.array([1.0, 0.0, 0.0])

    # Integrate geodesic once
    positions, tangents, diag = integrate_alcubierre_geodesic(
        initial_coords, direction, lambda_max, v_s, R, sigma,
        n_steps=n_steps, project_null=True, rtol=1e-8, atol=1e-10
    )
    if not diag['success']:
        raise RuntimeError(f"Geodesic integration failed: {diag['message']}")

    def metric_fn(t, x, y, z):
        return alcubierre_metric_analytic(t, x, y, z, v_s, R, sigma)

    # Precompute geometry along geodesic for reuse
    fr = FRGravity(alpha=0.0)
    pre_list = []
    for p in positions:
        pre = fr.precompute_geometry_terms(metric_fn, p, dx=1e-5)
        pre_list.append(pre)

    # GR ANEC
    def T_GR_fn(t, x, y, z):
        coords = np.array([t, x, y, z])
        G = compute_einstein_tensor(metric_fn, coords)
        return einstein_to_stress_energy(G)

    anec_GR, stats_GR = compute_anec_alcubierre(T_GR_fn, positions, tangents, lambda_max)

    results = {
        'params': {'v_s': v_s, 'R': R, 'sigma': sigma, 'lambda_max': lambda_max, 'n_steps': n_steps},
        'geodesic_diag': diag,
        'anec_GR': anec_GR,
        'alpha_results': []
    }

    for alpha in alpha_values:
        fr = FRGravity(alpha=alpha)
        # Define T_fn using precomputed geometry
        def T_fR_fn(t, x, y, z, _alpha=alpha):
            # Find closest point index (simple nearest, same sampling)
            # For this pipeline positions are used directly in loop below; not used here
            return None

        # Compute ANEC using precomputed tensors directly
        Tkk_vals = []
        for pre, (pos, k) in zip(pre_list, zip(positions, tangents)):
            G_mod = fr.modified_einstein_from_precompute(pre)
            T_eff = (fr.c**4 / (8 * np.pi * fr.G_Newton)) * G_mod
            Tkk_vals.append(float(k @ (T_eff @ k)))
        lambda_vals = np.linspace(0.0, lambda_max, len(Tkk_vals))
        anec_fR = float(np.trapz(Tkk_vals, lambda_vals))

        results['alpha_results'].append({
            'alpha': alpha,
            'anec_fR': anec_fR,
            'rel_change': float(abs((anec_fR - anec_GR) / anec_GR)) if abs(anec_GR) > 0 else None
        })

    out_path = Path(__file__).parent / 'fR_anec_sweep.json'
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Saved results to {out_path}")


if __name__ == '__main__':
    main()
