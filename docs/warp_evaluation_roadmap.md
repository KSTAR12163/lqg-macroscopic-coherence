# Warp Evaluation Roadmap: From Placeholders to Physical Rigor

**Date**: October 14, 2025  
**Status**: Infrastructure scaffolded, physics TODOs identified  
**Goal**: Replace heuristic stress-energy boost with field-theory-derived δT_μν

---

## Current State Assessment

### ✅ What Works (Validated)

1. **Portal coupling physics** (`portal_physics.py`):
   - Conservative and optimistic models with proper SI units
   - Experimental constraint enforcement (CAST, SN1987A)
   - Nucleon density dependence
   - Dimensionless κ_eff normalization

2. **Uncertainty quantification** (`portal_uncertainty.py`):
   - Latin Hypercube Sampling for stratified coverage
   - Field parameter variation (B, E, V, n_N)
   - 95% CI robustly above threshold (1.58×10¹⁵× lower bound)
   - Exclusion reason tracking

3. **Evaluation scaffolding** (`warp_eval/`):
   - Modular structure (energy_conditions, stability, realizability, runner)
   - Clear API for metric → stress-energy → condition checks
   - Portal boost integration point identified

### ⚠️ Critical Gaps (Acknowledged Placeholders)

1. **Stress-energy from metrics** (`stress_energy.py`):
   - Created infrastructure but G_μν computation uses toy wall profile
   - Need: Proper Christoffel symbol calculation from metric
   - Need: Integration with warp-bubble-einstein-equations repo

2. **Portal-induced δT_μν** (`portal_stress_energy.py`):
   - EFT sketch provided but not derived from QFT Lagrangian
   - Coherence suppression heuristic (not calculated from wavefunction overlap)
   - Screening model qualitative (conductor vs insulator, not full plasma dispersion)
   - Need: Derive from L_int = g_aγ a F·F̃ + g_aN a N̄N with medium effects

3. **ANEC integration** (`geodesics.py`):
   - Geodesic integration scaffolded but uses Euler method with constant k^μ
   - Need: RK4 integration of geodesic equation with proper Γ^μ_νρ
   - Need: Handle coordinate singularities, adaptive stepping

4. **Energy conditions** (`energy_conditions.py`):
   - NEC/WEC use placeholder (ρ, p) pair
   - QI/QNEC bounds schematic (arbitrary τ, curvature)
   - Need: Extract (ρ, p) from actual T_μν computed from metric

5. **Stability analysis** (`stability.py`):
   - Random eigenvalue placeholders
   - Need: Linearize Einstein equations around bubble solution
   - Need: Solve perturbation spectrum numerically

6. **Realizability** (`realizability.py`):
   - Heuristic B/E field scaling (∼ velocity)
   - Arbitrary energy/power cutoffs (10⁴⁵ J, 10³⁰ W)
   - Need: Map δT_μν to actual coil/capacitor designs
   - Need: Integration with hts-coils repo for engineering limits

---

## Priority 1: Real Stress-Energy from Metrics

**Goal**: Compute T_μν = (c⁴/8πG) G_μν for Alcubierre, Natário, Van Den Broeck

### Tasks

1. **Metric library integration** (Week 13):
   ```python
   # Use existing warp-bubble-* repos
   from warp_bubble_metric_ansatz import AlcubierreMetric, NatarioMetric
   from warp_bubble_einstein_equations import compute_einstein_tensor
   
   # Load candidate with parameters
   metric = AlcubierreMetric(velocity=1.0, radius=100.0, wall_thickness=10.0)
   
   # Compute at grid points
   coords_grid = create_spatial_grid(bubble_radius * 2, resolution=100)
   T_munu_grid = [compute_einstein_tensor(metric, pt) / (8 * np.pi * G) 
                   for pt in coords_grid]
   ```

2. **Einstein tensor computation** (Week 13–14):
   - Christoffel symbols: Γ^μ_νρ = (1/2) g^μσ (∂_ν g_σρ + ∂_ρ g_νσ - ∂_σ g_νρ)
   - Riemann tensor: R^μ_νρσ = ∂_ρ Γ^μ_νσ - ∂_σ Γ^μ_νρ + Γ^μ_ρλ Γ^λ_νσ - Γ^μ_σλ Γ^λ_νρ
   - Ricci tensor: R_μν = R^ρ_μρν
   - Ricci scalar: R = g^μν R_μν
   - Einstein tensor: G_μν = R_μν - (1/2) R g_μν
   
   Implementation options:
   - **Symbolic** (SymPy): Exact but slow, good for validation
   - **Numerical** (finite differences): Fast, need careful step size
   - **Hybrid**: Symbolic derivatives, numerical evaluation

3. **Validation** (Week 14):
   - Test on Schwarzschild (known T_μν = 0 outside horizon)
   - Test on FLRW (known perfect fluid T_μν)
   - Compare to published Alcubierre stress-energy calculations

### Deliverables

- `stress_energy.py`: Real `compute_einstein_tensor()` implementation
- `examples/validate_stress_energy.py`: Test cases
- Documentation of method choice and accuracy

---

## Priority 2: Portal δT_μν from EFT

**Goal**: Derive δT_μν from axion-photon-nucleon Lagrangian with medium effects

### Tasks

1. **Effective Lagrangian** (Week 14–15):
   ```
   L_eff = L_SM + (g_aγ/4) a F_μν F̃^μν + (g_aN/f_a) a ψ̄_N ψ_N
   
   where F̃^μν = (1/2) ε^μνρσ F_ρσ is dual field strength
   ```
   
   Derive equations of motion:
   - Modified Maxwell: ∂_μ F^μν = J^ν + g_aγ ∂_μ(a F̃^μν)
   - Axion: □a + m_a² a = (g_aγ/4) F·F̃ + (g_aN/f_a) ψ̄_N ψ_N
   
   Energy-momentum tensor:
   - T^μν = T^μν_EM + T^μν_axion + T^μν_matter + T^μν_int
   
   where T^μν_int is interaction contribution

2. **Medium effects** (Week 15):
   - **Plasma screening**: ω_p = sqrt(n_e e²/ε₀ m_e)
   - **Debye shielding**: λ_D = sqrt(ε₀ k_B T / n_e e²)
   - **Coherence volume**: V_c ~ (c τ_c)³ where τ_c depends on decoherence rate
   - **Frequency matching**: Axion conversion requires ω_photon ≈ m_a c²/ℏ
   
   Modify δT_μν with suppression factors:
   - f_screen(ω_p, m_a)
   - f_coherence(V_c, V_total)
   - f_dispersion(ω, k)

3. **Saturation and perturbativity** (Week 15):
   - Check g_aγ B λ_a ≪ 1 (perturbative photon mixing)
   - Check g_aN n_N λ_a³ ≪ 1 (perturbative nucleon coupling)
   - Cap δT_μν at some fraction of field energy (e.g., 10%)

4. **Implementation** (Week 16):
   ```python
   def compute_delta_T_from_EFT(
       portal_params, field_params, medium_params
   ):
       # Solve axion EOM with sources
       a_field = solve_axion_equation(...)
       
       # Compute interaction stress-energy
       T_int = compute_interaction_stress_energy(a_field, F_munu, psi_N)
       
       # Apply medium corrections
       T_int_medium = apply_medium_effects(T_int, screening, coherence)
       
       return T_int_medium
   ```

### Deliverables

- `portal_stress_energy_eft.py`: Field-theory-derived δT_μν
- `docs/portal_eft_derivation.md`: Full derivation with references
- Validation against known limits (free space, high screening, etc.)

---

## Priority 3: Real ANEC from Geodesics

**Goal**: Integrate ∫ T_μν k^μ k^ν dλ along numerically integrated null geodesics

### Tasks

1. **Geodesic equation solver** (Week 16):
   ```python
   def integrate_geodesic_rk4(metric, x0, k0, lambda_max, n_steps):
       # System: dx^μ/dλ = k^μ
       #         dk^μ/dλ = -Γ^μ_νρ k^ν k^ρ
       
       for step in range(n_steps):
           # RK4 update
           Gamma = compute_christoffel(metric, x)
           dk_dlambda = -einsum('mnp,n,p', Gamma, k, k)
           
           k_new = rk4_step(k, dk_dlambda, dlambda)
           x_new = rk4_step(x, k, dlambda)
   ```

2. **Christoffel symbol computation** (Week 16):
   - Numerical derivatives of metric (4th order centered differences)
   - Inverse metric computation (careful near singularities)
   - Caching for repeated evaluations

3. **Multiple geodesic sampling** (Week 17):
   - Radial geodesics at various impact parameters
   - Tangential geodesics (orbit around bubble)
   - Infalling vs outgoing
   - Statistical summary across ensemble

4. **Integration** (Week 17):
   - Adaptive step size (dense sampling near wall)
   - Convergence testing (vary n_steps)
   - Handle geodesic incompleteness (coordinate singularities)

### Deliverables

- `geodesics.py`: Proper RK4 integration with Christoffel symbols
- `examples/test_geodesics_schwarzschild.py`: Validate against known orbits
- ANEC statistics for Alcubierre with/without portal δT_μν

---

## Priority 4: Integration and Testing

**Goal**: End-to-end pipeline from metric parameters to viability decision

### Tasks

1. **Warp-* repo integration** (Week 18):
   - Clone warp-bubble-metric-ansatz, warp-bubble-einstein-equations
   - Create adapter layer for our evaluation framework
   - Load diverse candidates (Alcubierre, Natário, Van Den Broeck, Lentz)

2. **Full pipeline test** (Week 18–19):
   ```python
   # Load metric
   metric = load_from_warp_repo("Alcubierre", velocity=1.0, ...)
   
   # Compute baseline T_μν
   T_baseline = compute_stress_energy_from_metric(metric, coords_grid)
   
   # Compute portal δT_μν
   delta_T = compute_delta_T_from_EFT(portal_params, field_params, medium_params)
   
   # Combine
   T_total = T_baseline + screening * delta_T
   
   # ANEC along geodesics
   anec_stats = sample_anec_multiple_geodesics(metric, T_total, bubble_radius)
   
   # Energy conditions
   nec_result = check_NEC(T_total, coords_grid)
   wec_result = check_WEC(T_total, coords_grid)
   
   # Viability decision
   viable = (anec_stats['all_passed'] and 
             nec_result['fraction_violated'] < 0.01 and
             realizability['achievable'])
   ```

3. **Sensitivity analysis** (Week 19):
   - Vary portal parameters within 95% CI
   - Vary metric parameters (velocity, radius, wall thickness)
   - Identify which parameters most impact viability

4. **Documentation** (Week 20):
   - Update portal_warp_evaluation_results.md with real physics
   - Create technical appendix with derivations
   - Prepare figures (stress-energy profiles, geodesics, ANEC distributions)

### Deliverables

- Working end-to-end pipeline
- 5+ diverse bubble candidates evaluated
- Sensitivity analysis quantifying parameter impact
- Conclusive Week 12 gate decision (with evidence)

---

## Week 12 Gate Decision (Revised)

### Current Status: **INCONCLUSIVE**

**Why**: Placeholder stress-energy and portal boost prevent definitive assessment

**What's needed**:
1. Real T_μν from at least 3 metrics (Alcubierre, Natário, Van Den Broeck)
2. Field-theory-derived δT_μν with medium effects
3. Numerically integrated ANEC along proper null geodesics
4. Realistic realizability tied to engineering constraints (hts-coils)

### Success Criteria (Week 20)

**PASS** if:
- At least 1 candidate has ANEC ≥ 0 for all sampled geodesics
- Energy density ρ ≥ -10⁻⁶ J/m³ (quantum inequality scale)
- Field requirements (B, E) within 10× of current technology
- Exotic energy ≤ 10⁴⁸ J (Jupiter mass-energy)

**FAIL** if:
- All candidates violate ANEC by >10 orders
- Minimum exotic energy > 10⁵⁵ J (galactic scale)
- Required fields > 10¹⁰ T (magnetar interior)

---

## Technical Debt Tracking

| Component | Status | ETA | Blocker |
|-----------|--------|-----|---------|
| Real G_μν computation | 🔴 TODO | Week 14 | Christoffel symbol numerics |
| Portal δT_μν from EFT | 🔴 TODO | Week 16 | Medium screening model |
| Geodesic RK4 integration | 🔴 TODO | Week 17 | Metric derivative caching |
| ANEC statistical sampling | 🔴 TODO | Week 17 | Geodesic solver |
| Warp-* repo integration | 🔴 TODO | Week 18 | Adapter layer design |
| Stability spectrum | 🔴 TODO | Week 19 | Perturbation linearization |
| Realizability engineering | 🔴 TODO | Week 19 | hts-coils integration |
| Full pipeline test | 🔴 TODO | Week 20 | All above |

---

## Honest Assessment

**Portal coupling enhancement** (g_eff = 1.47×10⁻²¹ J): 🟢 **Validated**
- Conservative model with proper physics
- 95% CI robustly above threshold
- Experimental constraints satisfied

**Portal impact on warp viability**: 🟡 **Unknown** (not red, not green)
- Current "boost" heuristic is unphysical
- Directional intuition (geometry dominates) likely correct
- But magnitude of portal contribution uncertain by orders of magnitude
- Need field-theory-derived δT_μν to quantify

**Warp bubble viability** (under GR + portal): 🔴 **Likely impossible, but unproven**
- Energy conditions are fundamental (QFT + causality)
- No known mechanism for sustained macroscopic negative energy
- Portal provides coupling, not exotic matter source
- **BUT**: Need real calculation to be certain, not placeholders

**Recommendation**:
- **Short term** (Weeks 13–20): Complete Priority 1–4 to conclusively settle viability
- **Medium term** (if failed): Pivot to quantum vacuum engineering or modified gravity
- **Long term**: Honest final FTL assessment with all avenues explored

---

**Key Principle**: "Extraordinary claims require extraordinary evidence."

We have an extraordinary claim (portal boost enables warp drives). We now need extraordinary evidence (real T_μν, real ANEC, real field requirements). Placeholders got us to scaffolding stage; now we need physics.
