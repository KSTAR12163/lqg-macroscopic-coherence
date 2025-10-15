"""
Multi-ray ANEC sweep for f(R) = R + alpha R^2 using precomputed geometry.
Samples several impact parameters (y offsets) through an Alcubierre bubble.
Outputs a JSON summary of ANEC for GR and f(R) across alpha values for each ray.
"""

import json
from pathlib import Path
import numpy as np

from phase_d.warp_eval.alcubierre_analytic import alcubierre_metric_analytic
from phase_d.warp_eval.geodesics_alcubierre import integrate_alcubierre_geodesic
from phase_d.warp_eval.stress_energy import compute_einstein_tensor, einstein_to_stress_energy
from phase_d.modified_gravity.f_R_gravity import FRGravity


def integrate_and_precompute(metric_fn, initial_coords, direction, lambda_max, v_s, R, sigma, n_steps=180):
    positions, tangents, diag = integrate_alcubierre_geodesic(
        initial_coords, direction, lambda_max, v_s, R, sigma,
        n_steps=n_steps, project_null=True, rtol=1e-8, atol=1e-10
    )
    if not diag['success']:
        return None, None, diag

    # Precompute geometry along the ray for reuse across alphas
    fr_tmp = FRGravity(alpha=0.0)
    pre_list = []
    for p in positions:
        pre = fr_tmp.precompute_geometry_terms(metric_fn, p, dx=1e-5)
        pre_list.append(pre)
    return positions, tangents, {'diag': diag, 'pre_list': pre_list}


def compute_anec_from_precompute(metric_fn, pre_list, positions, tangents, lambda_max, fr: FRGravity):
    # Compute ANEC for GR baseline
    # Note: We recompute GR via Einstein tensor rather than precomputed G_GR to stay consistent with pipeline
    def T_GR_fn(t, x, y, z):
        coords = np.array([t, x, y, z])
        G = compute_einstein_tensor(metric_fn, coords)
        return einstein_to_stress_energy(G)

    # Using precomputed GR would be faster; here we compute directly to avoid any subtle mismatch
    Tkk_vals_gr = []
    for pos, k in zip(positions, tangents):
        T = T_GR_fn(*pos)
        Tkk_vals_gr.append(float(k @ (T @ k)))
    lambda_vals = np.linspace(0.0, lambda_max, len(Tkk_vals_gr))
    anec_gr = float(np.trapz(Tkk_vals_gr, lambda_vals))

    # f(R) ANEC using precomputed geometry
    Tkk_vals_fr = []
    for pre, (pos, k) in zip(pre_list, zip(positions, tangents)):
        G_mod = fr.modified_einstein_from_precompute(pre)
        T_eff = (fr.c**4 / (8 * np.pi * fr.G_Newton)) * G_mod
        Tkk_vals_fr.append(float(k @ (T_eff @ k)))
    anec_fr = float(np.trapz(Tkk_vals_fr, lambda_vals))

    return anec_gr, anec_fr


def main():
    # Bubble and integration parameters
    v_s = 1.0
    R = 100.0
    sigma = 10.0
    lambda_max = 400.0
    n_steps = 160
    alpha_values = [1e-10, 1e-8, 1e-6]

    # Rays: y offsets (impact parameters), +x direction
    impact_params_y = [-20.0, -10.0, 0.0, 10.0, 20.0]
    direction = np.array([1.0, 0.0, 0.0])

    def metric_fn(t, x, y, z):
        return alcubierre_metric_analytic(t, x, y, z, v_s, R, sigma)

    rays_results = []

    for y0 in impact_params_y:
        initial_coords = np.array([0.0, -200.0, y0, 0.0])
        positions, tangents, data = integrate_and_precompute(metric_fn, initial_coords, direction, lambda_max, v_s, R, sigma, n_steps=n_steps)
        if positions is None:
            rays_results.append({
                'y0': y0,
                'success': False,
                'message': data['message'] if isinstance(data, dict) and 'message' in data else 'geodesic failure'
            })
            continue

        diag = data['diag']
        pre_list = data['pre_list']

        # Baseline GR ANEC
        # Compute once; we’ll reuse it across alphas

        # Compute and store per-alpha results
        alpha_entries = []
        anec_gr_cached = None
        for alpha in alpha_values:
            fr = FRGravity(alpha=alpha)
            anec_gr, anec_fr = compute_anec_from_precompute(metric_fn, pre_list, positions, tangents, lambda_max, fr)
            if anec_gr_cached is None:
                anec_gr_cached = anec_gr
            rel_change = float(abs((anec_fr - anec_gr_cached) / anec_gr_cached)) if abs(anec_gr_cached) > 0 else None
            alpha_entries.append({
                'alpha': alpha,
                'anec_fR': anec_fr,
                'rel_change': rel_change
            })

        rays_results.append({
            'y0': y0,
            'success': True,
            'diag': diag,
            'anec_GR': anec_gr_cached,
            'alpha_results': alpha_entries,
        })

    out_path = Path(__file__).parent / 'fR_anec_multiray.json'
    with open(out_path, 'w') as f:
        json.dump({
            'params': {'v_s': v_s, 'R': R, 'sigma': sigma, 'lambda_max': lambda_max, 'n_steps': n_steps},
            'impact_params_y': impact_params_y,
            'rays': rays_results
        }, f, indent=2)
    print(f"Saved multi-ray results to {out_path}")


if __name__ == '__main__':
    main()
