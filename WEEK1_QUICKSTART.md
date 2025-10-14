# Phase D Week 1 Quick-Start Guide

**Date**: October 14, 2025  
**Objective**: Establish analytical bounds and begin N-scaling measurements  
**Decision Point**: End of Week 1 - Continue to full study or flag issues early

---

## Day 1: Analytical Bounds ← START HERE

### Run the Predictions

```bash
cd /home/sherri3/Code/asciimath/lqg-macroscopic-coherence
python -c "
from src.phase_d.tier1_collective.n_scaling import week1_analytical_bounds
week1_analytical_bounds()
"
```

**Expected Output**:
```
TIER 1 - WEEK 1: ANALYTICAL BOUNDS
==================================================

Current single-node coupling:
  g_single = 3.96e-121 J

Target for viability:
  g₀_target = 1.00e-50 J

Required enhancement:
  Factor = 2.53e+71×

SCALING SCENARIOS:
--------------------------------------------------

1. Incoherent (√N) scaling:
   g_eff ∝ √N
   Required N: 6.37e+142
   Assessment: PHYSICALLY IMPOSSIBLE
   
2. Coherent (N) scaling:
   g_eff ∝ N
   Required N: 2.53e+71
   Assessment: UNPHYSICAL (exceeds cosmological particle count)
   
3. Superradiant (N²) scaling:
   g_eff ∝ N²
   Required N: 1.59e+36
   Assessment: HIGHLY SPECULATIVE (exceeds Avogadro's number)

VERDICT: Collective enhancement alone CANNOT close gap
Recommend: Proceed with measurement to quantify actual α, then SKIP to Tier 3
```

### Interpretation

- **Incoherent (√N)**: Standard non-interacting ensemble → Need N ~ 10¹⁴² (impossible)
- **Coherent (N)**: Dicke superradiance analogy → Need N ~ 10⁷¹ (exceeds atoms in universe)
- **Superradiant (N²)**: Hypothetical cooperative enhancement → Need N ~ 10³⁶ (speculative)

**Key Insight**: Even N² scaling requires unphysical N. Tier 1 alone won't solve it.

**Why Continue?**: Empirical measurement of α is valuable for establishing benchmarks.

---

## Days 2-3: Network Construction

### Implement Topology Functions

Edit `src/phase_d/tier1_collective/n_scaling.py`, complete TODOs in:

```python
def create_complete_network(N, lambda_val, mu):
    """
    All-to-all connected network (N nodes, N(N-1)/2 edges)
    
    TODO:
    1. Create N spin network nodes at random positions
    2. Connect every pair with Klein-Gordon propagator
    3. Calculate effective coupling matrix H_int
    4. Compute collective eigenvalues
    """
    pass  # IMPLEMENT THIS
```

```python
def create_lattice_network(N, lambda_val, mu):
    """
    Cubic lattice network (N = L³ nodes)
    
    TODO:
    1. Create L×L×L cubic lattice
    2. Connect nearest neighbors only
    3. Calculate coupling with distance decay
    4. Compute collective spectrum
    """
    pass  # IMPLEMENT THIS
```

### Test Small Networks

```python
# Test N=10 complete network
from src.phase_d.tier1_collective.n_scaling import measure_collective_coupling
from src.numerical_guardrails import validate_coupling

N = 10
lambda_val = 1.0
mu = 0.3

g_eff, H_int = measure_collective_coupling(N, 'complete', lambda_val, mu)

# Validate (will likely fail - too weak!)
result = validate_coupling(g_eff, name=f"g_eff(N={N})")
if not result.is_valid:
    print(f"⚠️ WARNING: {result.message}")
    print(f"Continuing to measure scaling law despite weak coupling...")
```

**Expected**: Coupling still below 10⁻⁵⁰ J for small N (as predicted)

---

## Days 4-5: Initial Measurements

### Run Small-N Scan

```python
# Measure scaling for N = 10, 50, 100
from src.phase_d.tier1_collective.n_scaling import run_scaling_study

N_values = [10, 50, 100]
results = run_scaling_study(N_values, topology='complete')

# results['scaling_exponent'] ≈ α
print(f"Measured α = {results['scaling_exponent']:.3f}")

# Compare to predictions
if abs(results['scaling_exponent'] - 0.5) < 0.1:
    print("Scaling consistent with √N (incoherent)")
elif abs(results['scaling_exponent'] - 1.0) < 0.1:
    print("Scaling consistent with N (coherent) - SURPRISING!")
elif abs(results['scaling_exponent'] - 2.0) < 0.1:
    print("Scaling consistent with N² (superradiant) - EXTRAORDINARY!")
else:
    print(f"Novel scaling detected: α = {results['scaling_exponent']}")
```

### Generate Preliminary Plot

```python
import matplotlib.pyplot as plt
import numpy as np

N = results['N_values']
g_eff = results['g_eff_values']
alpha = results['scaling_exponent']

plt.figure(figsize=(10, 6))
plt.loglog(N, g_eff, 'o-', label=f'Measured (α={alpha:.2f})')
plt.loglog(N, g_eff[0] * (N/N[0])**0.5, '--', label='√N prediction')
plt.loglog(N, g_eff[0] * (N/N[0])**1.0, '--', label='N prediction')
plt.loglog(N, g_eff[0] * (N/N[0])**2.0, '--', label='N² prediction')
plt.axhline(1e-50, color='r', linestyle=':', label='Viability threshold')
plt.xlabel('N (number of nodes)')
plt.ylabel('g_eff (J)')
plt.title('Collective Coupling Scaling (Preliminary)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('week1_preliminary_scaling.png', dpi=150)
print("Saved: week1_preliminary_scaling.png")
```

---

## Days 6-7: Week 1 Report

### Analysis Questions

1. **What α did we measure?**
   - Compare to theoretical predictions (0.5, 1.0, 2.0)
   - Is there evidence for cooperative enhancement?

2. **Does the trend extrapolate?**
   - Calculate required N for g₀ = 10⁻⁵⁰ J using measured α
   - Is it physically plausible? (Compare to 10²³, 10⁵⁷, 10⁸⁰)

3. **Should we continue to Weeks 2-3?**
   - If α ≈ 0.5: NO (incoherent, skip to Tier 3)
   - If α ≈ 1.0: MAYBE (coherent but needs N ~ 10⁷¹)
   - If α ≈ 2.0: YES (superradiant, worth investigating)
   - If α > 2.0: EXTRAORDINARY (unexpected physics!)

### Create Week 1 Report

```markdown
# Tier 1 Week 1 Report

## Analytical Predictions
- Incoherent (√N): Required N ~ 10¹⁴²
- Coherent (N): Required N ~ 10⁷¹
- Superradiant (N²): Required N ~ 10³⁶

## Empirical Measurements
- N tested: [10, 50, 100]
- Measured α: [YOUR VALUE]
- Best-fit: g_eff = g₀ × N^α

## Extrapolation
- Required N for viability: [CALCULATED FROM α]
- Assessment: [FEASIBLE / MARGINAL / INFEASIBLE]

## Decision
- [ ] Continue to full study (Weeks 2-3)
- [ ] Skip to Tier 3 (collective alone insufficient)

## Attachments
- week1_preliminary_scaling.png
```

---

## Week 1 Success Criteria

**Minimum Viable**:
- ✅ Analytical bounds calculated
- ✅ Small-N measurements complete (N = 10, 50, 100)
- ✅ Scaling exponent α estimated (±0.2 accuracy)
- ✅ Extrapolation to viability performed
- ✅ GO/NO-GO decision documented

**Stretch Goals**:
- Additional topologies (lattice, tetrahedral)
- Higher-spin states (j = 3/2 comparison)
- Sensitivity to λ parameter

---

## Decision Tree

```
Week 1 Complete
    │
    ├─→ α < 0.7 (sub-linear)
    │   └─→ SKIP to Tier 3 (collective insufficient)
    │
    ├─→ 0.7 ≤ α ≤ 1.3 (linear)
    │   └─→ DOCUMENT & MAYBE Weeks 2-3 (marginal)
    │
    ├─→ 1.3 < α < 2.3 (super-linear)
    │   └─→ GO to Weeks 2-3 (worth investigating)
    │
    └─→ α ≥ 2.3 (novel)
        └─→ GO to Weeks 2-3 + ALERT (unexpected physics!)
```

---

## Common Issues & Solutions

### Issue: Coupling still below 10⁻⁵⁰ J for all N

**Expected**: Yes, for small N this is normal. We're measuring the *scaling law*, not reaching viability yet.

**Action**: Continue measurements, extract α, then extrapolate.

### Issue: All g_eff values identical (parameter independence)

**Problem**: Numerical artifact! (Same as Phase B)

**Action**: 
```python
from src.numerical_guardrails import check_growth_rate_independence
passed, msg = check_growth_rate_independence(results, 'N')
if not passed:
    print(f"🚨 ARTIFACT DETECTED: {msg}")
    # Increase precision, check implementation
```

### Issue: Negative or NaN couplings

**Problem**: Matrix diagonalization failure (Hamiltonian ill-conditioned)

**Action**:
```python
from src.numerical_guardrails import validate_hamiltonian
valid, msg = validate_hamiltonian(H_total, H_int, check_hermitian=True)
if not valid:
    print(f"🚨 INVALID HAMILTONIAN: {msg}")
    # Check: Off-diagonal elements, numerical stability
```

### Issue: Computational cost too high

**Problem**: N² scaling for complete graph eigenvalue problem

**Action**: 
- Use sparse matrices (scipy.sparse)
- Reduce N range (test N = 10, 30, 100 instead of 10, 50, 100)
- Parallel computing (if cluster available)
- Approximate methods (perturbation theory for large N)

---

## Next Steps After Week 1

### If GO to Weeks 2-3:
- Expand N range: [10, 20, 50, 100, 200, 500, 1000]
- Test all topologies (complete, lattice, tetrahedral)
- Generate high-quality figures
- Write `TIER1_WEEKS2-3_REPORT.md`

### If SKIP to Tier 3:
- Document null result: "Collective enhancement insufficient"
- Establish benchmark: "Maximum enhancement f(N) ~ N^α"
- Begin Tier 3 planning: Exotic mechanisms search
- Update `PHASE_D_STATUS.md`

---

## Resources

**Implemented Code**:
- `src/phase_d/tier1_collective/n_scaling.py` (main functions)
- `src/numerical_guardrails.py` (validation)
- `src/phase_d/acceptance_tests.py` (go/no-go criteria)

**Documentation**:
- `PHASE_D_PLAN.md` (overall 6-month plan)
- `PHASE_D_STATUS.md` (Day 1 implementation summary)
- `docs/PHASE_B_CORRECTED_ANALYSIS.md` (artifact background)

**References**:
- Dicke superradiance: Phys. Rev. 93, 99 (1954)
- LQG spin networks: Rovelli & Smolin, Nucl. Phys. B 442, 593 (1995)
- Matter coupling: Klein-Gordon on curved background

---

## Contact & Collaboration

If you observe:
- **α > 2.0**: Unexpected! Investigate thoroughly before proceeding.
- **Parameter artifacts**: Stop immediately, debug with guardrails.
- **Computational bottlenecks**: Consider requesting HPC resources.

**Week 1 Target Completion**: October 20, 2025 (7 days from Day 1)

---

**Good luck! The 6-month countdown begins now.** 🚀
