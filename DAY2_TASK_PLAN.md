# Week 1 Day 2 Task Plan - Network Construction

**Date**: October 14, 2025  
**Objective**: Implement network construction functions for N-scaling measurements  
**Estimated time**: 4-6 hours

---

## Tasks Overview

### 1. Review Existing Code ✅ (30 min)
**Status**: Research complete

**Found**:
- Phase B example (`examples/phase_b_network_mapping.py`) shows tetrahedral network construction
- Matter-Geometry coupling in `src.04_coupling_engineering.matter_coupling`
- SpinNetwork class in `src/core/spin_network.py`

**Key pattern**:
```python
# Create network
network = SpinNetwork()
nodes = [network.add_node(i) for i in range(N)]

# Add edges
for i, j in edge_list:
    network.add_edge(i, j, spin=0.5)

# Compute coupling
coupling = MatterGeometryCoupling(network, matter_field, lambda_val, mu=mu_val)
energies, eigvec = coupling.compute_energy_spectrum(dim)
```

---

## 2. Implement Complete Graph Constructor ⏳ (2 hours)

### Function Signature
```python
def create_complete_network(N: int, 
                           lambda_val: float = 1.0,
                           mu: float = 0.1) -> Tuple[SpinNetwork, MatterGeometryCoupling]:
    """
    Create complete graph K_N (all-to-all connectivity).
    
    Args:
        N: Number of nodes
        lambda_val: Polymer parameter
        mu: Matter field scale
        
    Returns:
        (network, coupling) tuple
        
    Properties:
        - N nodes
        - N(N-1)/2 edges (every pair connected)
        - Uniform edge weights (spin = 0.5)
    """
```

### Implementation Steps
1. [ ] Create SpinNetwork instance
2. [ ] Add N nodes
3. [ ] Generate all pairs: `itertools.combinations(range(N), 2)`
4. [ ] Add edges with spin = 0.5
5. [ ] Create MatterFieldProperties (same as Phase B)
6. [ ] Instantiate MatterGeometryCoupling
7. [ ] Return (network, coupling)

### Test Cases
- N=4 (tetrahedral): 6 edges, verify against Phase B
- N=10: 45 edges, check construction time
- N=50: 1225 edges, verify memory usage

---

## 3. Measure Collective Coupling ⏳ (1 hour)

### Function Signature
```python
def measure_collective_coupling(N: int,
                               topology: str = "complete",
                               lambda_val: float = 1.0,
                               mu: float = 0.1,
                               dim: int = 32) -> CollectiveResult:
    """
    Measure effective coupling for N-node network.
    
    Returns:
        CollectiveResult with:
            - N (number of nodes)
            - g_single (baseline single-node coupling)
            - g_coll (collective coupling)
            - enhancement (g_coll / g_single)
            - topology
    """
```

### Implementation Steps
1. [ ] Call network constructor (complete or lattice)
2. [ ] Compute energy spectrum
3. [ ] Extract gap: Δ = E₁ - E₀
4. [ ] Compute interaction matrix element: g = |⟨1|H_int|0⟩|
5. [ ] Compare to g_single baseline
6. [ ] Validate with guardrails (expect warning for g < 10⁻⁵⁰)
7. [ ] Return CollectiveResult

### Expected Results
For N=10 complete graph:
- g_coll ≈ g_single × √10 ≈ 3.2× (if incoherent)
- g_coll ≈ g_single × 10 (if coherent)
- g_coll ≈ g_single × 100 (if superradiant - unlikely!)

---

## 4. Test and Validate ⏳ (1 hour)

### Test Script: `test_network_construction.py`

```python
"""Test network construction for Week 1."""

from src.phase_d.tier1_collective.network_construction import (
    create_complete_network,
    measure_collective_coupling
)
from src.numerical_guardrails import validate_coupling

# Test 1: Small network (N=4)
print("Test 1: N=4 (tetrahedral)")
result = measure_collective_coupling(4, topology="complete")
print(f"  g_single: {result.g_single:.2e} J")
print(f"  g_coll:   {result.g_coll:.2e} J")
print(f"  Enhancement: {result.enhancement:.2f}×")

# Test 2: Medium network (N=10)
print("\nTest 2: N=10")
result = measure_collective_coupling(10, topology="complete")
print(f"  g_single: {result.g_single:.2e} J")
print(f"  g_coll:   {result.g_coll:.2e} J")
print(f"  Enhancement: {result.enhancement:.2f}×")

# Test 3: Guardrail validation
print("\nTest 3: Guardrail validation")
valid = validate_coupling(result.g_coll, name="g_coll")
if not valid.is_valid:
    print(f"  ⚠️ WARNING: {valid.message}")
    print("  (Expected - coupling below viability threshold)")
else:
    print("  ✅ Coupling above threshold")
```

### Expected Output
```
Test 1: N=4 (tetrahedral)
  g_single: 3.96e-121 J
  g_coll:   7.92e-121 J
  Enhancement: 2.00×

Test 2: N=10
  g_single: 3.96e-121 J
  g_coll:   1.25e-120 J
  Enhancement: 3.16×

Test 3: Guardrail validation
  ⚠️ WARNING: Coupling g_coll = 1.25e-120 J is below threshold 1.00e-50 J
  (Expected - coupling below viability threshold)
```

---

## 5. Document and Commit ⏳ (30 min)

### Files to Create
- [ ] `src/phase_d/tier1_collective/network_construction.py`
- [ ] `test_network_construction.py`
- [ ] Update `WEEK1_PROGRESS.md` with Day 2 results

### Commit Message
```
Week 1 Day 2: Implement network construction

- Add create_complete_network() for K_N graphs
- Add measure_collective_coupling() function
- Test with N=4, N=10
- Validate with guardrails (expect warnings)

Status: Network construction ready for scaling study
Next: Days 4-5 full N-scan [10, 50, 100, 500, 1000]
```

---

## Known Challenges & Solutions

### Challenge 1: MatterGeometryCoupling Import
**Problem**: Module path `src.04_coupling_engineering.matter_coupling`  
**Solution**: Use importlib.import_module() like Phase B example

### Challenge 2: Coupling Below Threshold
**Problem**: All couplings will be < 10⁻⁵⁰ J → guardrail warnings  
**Solution**: Expected! Document in comments, proceed with measurement

### Challenge 3: Matrix Size for Large N
**Problem**: N=1000 → 1M×1M Hamiltonian (impossible!)  
**Solution**: 
- Use sparse matrices (scipy.sparse)
- Or reduce dim parameter (dim=16 instead of 32)
- Or limit N to ≤ 100 for full eigensolve

---

## Success Criteria (Day 2)

- [x] Review existing code ✅ (Done during planning)
- [ ] Implement `create_complete_network()` ⏳
- [ ] Implement `measure_collective_coupling()` ⏳
- [ ] Test with N=4, N=10 ⏳
- [ ] Verify coupling calculation works ⏳
- [ ] Document implementation ⏳

**Definition of Done**: 
- Test script runs without errors
- Produces coupling values (even if below threshold)
- Ready for Day 4-5 full scaling study

---

## Timeline

| Time | Task | Duration |
|------|------|----------|
| 00:00 | Review existing code | ✅ 30 min |
| 00:30 | Implement complete network | ⏳ 2 hours |
| 02:30 | Implement measurement | ⏳ 1 hour |
| 03:30 | Test and validate | ⏳ 1 hour |
| 04:30 | Document and commit | ⏳ 30 min |
| **05:00** | **Day 2 Complete** | **5 hours** |

---

## Day 3 Preview

If Day 2 completes successfully:
- [ ] Add lattice network constructor
- [ ] Test topology comparison (complete vs. lattice)
- [ ] Prepare for Days 4-5 full scan
- [ ] Update progress documentation

If Day 2 encounters issues:
- Debug network construction
- Simplify implementation if needed
- Focus on getting N=10 working reliably

---

## Notes for Implementation

### Matter Field Properties (from Phase B)
```python
from src.core.constants import L_PLANCK

matter_field = MatterFieldProperties(
    field_type=MatterFieldType.SCALAR,
    characteristic_energy=1e-15,  # Joules
    characteristic_length=L_PLANCK * 1e10,
    impedance=1.0
)
```

### Baseline Single-Node Coupling
From Phase B-C analysis: g_single = 3.96×10⁻¹²¹ J

This is the reference for computing enhancement:
```python
g_single = 3.96e-121  # J (known from Phase B)
enhancement = g_coll / g_single
```

### Edge Weights
All edges use spin j = 0.5 (fundamental representation):
```python
network.add_edge(i, j, spin=0.5)
```

---

**Ready to begin Day 2 implementation!** 🚀

**Start time**: When you're ready  
**Expected completion**: 4-6 hours of focused work  
**Next milestone**: Week 1 Days 4-5 (full scaling study)
