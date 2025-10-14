# FTL Warp Capability – Focused Action Plan (Alpha Centauri)

This plan is strictly outcome-driven: pursue only paths that can plausibly lead to >c effective motion. Publishing is out-of-scope until we have a credible route.

## Current ground truth (validated)

- Passive and Hermitian non-equilibrium mechanisms: null (Phase 1 + A)
- Active gain: exponential growth mathematically possible but useless at g0 ≈ 1e-121 J
- Purcell scan (corrected): requires F_p ~ 1e141 to even enter numeric regime → not physically achievable
- Sensitivity analysis: cannot find g0 in [1e-60, 1e-10] J that achieves 1-year target under realistic gains/F_p
- Conclusion: Present LQG coupling is orders-of-magnitude too small; FTL warp needs a fundamentally different coupling or mechanism

## Objectives (with hard gates)

1) Identify any mechanism that lifts effective coupling toward g0 ≥ 1e-50 J
2) Produce a warp-bubble candidate that satisfies field equations, stability, and energy-condition constraints with a realizable source model
3) If neither is achieved under the gates below, declare FTL not achievable under current physics assumptions

### Gates and stop-rules
- 4 weeks: If no mechanism exceeds g0 ≥ 1e-60 J (credible, not numeric artifact), pause coupling search and pivot to field-engineering only
- 12 weeks: If no bubble candidate passes QI/ANEC/QNEC screens with a realizable source model, pause field-engineering and reassess assumptions
- 24 weeks: Final verdict on FTL viability under current model space

## Track 1 — Coupling mechanisms (Tier 3 focus)

High-risk, high-reward mechanisms to push g0 upward. All runs must import and pass `src/numerical_guardrails.validate_coupling`.

- Hidden-sector/portal couplings
  - Add axion/ALP and dark photon portals; compute induced mixing terms and net g0
  - Scan portal strengths within current experimental bounds
  - Acceptance: max(g0_scan) ≥ 1e-60 J (GO); else stop branch

- Nonlocal/holographic-inspired terms
  - Introduce controlled nonlocal kernels in effective action; regularize and test causality
  - Acceptance: numeric stability + demonstrable growth without violating guardrails

- Phase-transition/critical amplification
  - Near-critical lattice models coupled to geometry degrees; test diverging susceptibility scenarios
  - Acceptance: clear pre/post-critical scaling with guardrails intact

- Measurement-based/feedback-driven gain
  - Lindblad with inversion + feedback; confirm growth per time in a network (not just two-level toy)
  - Acceptance: growth tied to nonzero transition matrix elements (not diagonal gain)

Deliverables (rolling, weekly): JSON summaries of g0 upper bounds per mechanism; plots; a single `phase_d/tier3_exotic/scorecard.md` updated weekly.

## Track 2 — Field-engineered warp bubble candidates

Build and evaluate warp-bubble solutions with cross-repo tools. Goal: minimize negative energy and satisfy constraints.

- Cross-repo integration (scripts only, no heavy refactors):
  - Pull metric ansätze from `warp-bubble-metric-ansatz/`
  - Compute Einstein tensor and T_{μν} via `warp-bubble-einstein-equations/`
  - Use shape controls from `warp-bubble-shape-catalog/` and `warp-bubble-optimizer/`
  - Evaluate curvature, stability from `warp-curvature-analysis/`
  - Check energy conditions (ANEC/QI/QNEC) using `lqg-anec-framework/`

- Acceptance functions to add here (stubs under `src/phase_d/warp_eval/`):
  - `passes_energy_conditions(candidate) -> bool, diagnostics`
  - `stability_ok(candidate) -> bool, modes`
  - `source_realizable(candidate) -> bool, BOM` (maps to coils, materials, power via `warp-field-coils/`)

- Optimization target: minimize spacetime-integrated negative energy subject to constraints while achieving target bubble velocity profile

Gates:
- 6 weeks: At least one candidate that passes basic stability and weak/QNEC checks (even if not ANEC) → else pause Track 2
- 12 weeks: Candidate that passes ANEC along all relevant null geodesics OR a clear impossibility proof under chosen ansatz class

## Immediate 10-day sprint

- Day 1–2: Wire guardrails into all growth/drive scripts; add smoke tests (done for Purcell scan)
- Day 3–5: Implement `src/phase_d/warp_eval/` with the three acceptance APIs and a tiny runner that orchestrates the cross-repo calls
- Day 6–7: Assemble 3–5 metric candidates (top hat, smooth dome, asymmetric lens) and run the evaluation pipeline end-to-end
- Day 8–10: Prototype Tier-3 portal coupling; scan axion/dark photon parameter space; produce g0 upper-bound table

## How we measure progress

- Coupling scorecard: best g0 found vs time (log plot); guardrail status
- Warp candidate scorecard: pass/fail per acceptance API; energy budget vs target; stability spectra
- Kill-switch: any sign of artifact (e.g., growth with zero off-diagonal coupling) immediately halts and patches guardrails

## Practical reality check

- Known quantum inequalities severely constrain negative energy; classical GR plus standard QFT disfavors FTL bubbles with realizable sources
- This plan targets the only two levers we have: (1) change the coupling via beyond-standard mechanisms within bounds, and (2) minimize energy-condition violations by aggressive field/shape engineering
- If both levers fail the gates above, we stop and declare FTL non-viable under current assumptions and technology

## Minimal commands (optional)

These commands will exist once `warp_eval` runner is added.

```bash
# Evaluate a set of metric candidates (placeholder example)
python -m src.phase_d.warp_eval.run --candidates configs/warp_candidates.yaml --out results/warp_eval_summary.json

# Run a Tier-3 portal scan (placeholder)
python -m src.phase_d.tier3_exotic.portal_scan --bounds conservative --out results/portal_g0_bounds.json
```

---

If you want me to prioritize Track 2 (warp candidate evaluator) right now, I’ll create `src/phase_d/warp_eval/` with the three acceptance functions and a tiny orchestrator so we can start evaluating candidates from your existing warp-* repos in the next session.