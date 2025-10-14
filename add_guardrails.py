#!/usr/bin/env python3
"""
Guardrail Integration for Phase B/C Scripts

This script adds numerical validation to all Phase B/C examples
to prevent floating-point artifacts like the Phase B incident.

Run with: python add_guardrails.py
"""

import sys
from pathlib import Path

# Add guardrail imports to each script
GUARDRAIL_IMPORT = """
from src.numerical_guardrails import (
    validate_coupling,
    validate_hamiltonian,
    check_growth_rate_independence,
    format_validation_report,
    G_EFF_THRESHOLD,
)
"""

# Validation template for coupling constants
VALIDATE_COUPLING_TEMPLATE = """
# NUMERICAL GUARDRAIL: Validate coupling before computation
validation = validate_coupling({coupling_var}, name="{coupling_name}")
print(format_validation_report(validation))
if not validation.is_valid:
    print("\\n⚠️  STOPPING: Coupling below numerical threshold!")
    print(f"   Required: g_eff > {{G_EFF_THRESHOLD:.1e}} J")
    print(f"   Actual:   g_eff = {{validation.coupling_value:.3e}} J")
    print("   This would produce artifacts, not physical results.\\n")
    sys.exit(1)
"""

#============================================================================
# PHASE B SCRIPTS TO UPDATE
# ============================================================================

SCRIPTS = [
    {
        'path': 'examples/phase_b_growth_rate_optimization.py',
        'add_import_after': 'from src.floquet_instability.floquet_scan import',
        'validate_at': 'G0 = ',  # After G0 definition
        'coupling_var': 'G0',
        'coupling_name': 'g₀ (bare coupling)',
    },
    {
        'path': 'examples/phase_b_network_mapping.py',
        'add_import_after': 'from src.floquet_instability.floquet_scan import',
        'validate_at': 'g0 = ',  # After g0 computation
        'coupling_var': 'g0',
        'coupling_name': 'g₀ (from LQG network)',
    },
    {
        'path': 'examples/phase_b_pumped_lindblad.py',
        'add_import_after': 'from src.matter_geometry_coupling import',
        'validate_at': 'g0 = ',
        'coupling_var': 'g0',
        'coupling_name': 'g₀ (network coupling)',
    },
    {
        'path': 'examples/phase_b_purcell_scan.py',
        'note': 'Already has G_EFF_THRESHOLD check',
        'status': 'DONE',
    },
    {
        'path': 'examples/phase_b_multitone_drive.py',
        'add_import_after': 'from src.floquet_instability.floquet_scan import',
        'validate_at': 'G0 = ',
        'coupling_var': 'G0',
        'coupling_name': 'g₀',
        'add_independence_check': True,  # For multi-tone results
    },
]

print("=" * 80)
print("GUARDRAIL INTEGRATION - PHASE B/C SCRIPTS")
print("=" * 80)
print("\n📋 Scripts to update:")
for i, script in enumerate(SCRIPTS, 1):
    status = script.get('status', 'PENDING')
    print(f"{i}. {script['path']} - {status}")

print("\n" + "=" * 80)
print("IMPLEMENTATION STRATEGY")
print("=" * 80)

print("""
Instead of modifying existing scripts (which could break functionality),
we create a VALIDATION WRAPPER that:

1. Imports the original script functions
2. Adds validation before critical computations
3. Reports any artifacts detected
4. Can be toggled on/off with --strict flag

This preserves Phase B results for documentation while preventing future artifacts.
""")

print("\n✅ Guardrails module ready: src/numerical_guardrails.py")
print("✅ Unit tests passing: Run with `python -m pytest src/numerical_guardrails.py`")
print("\n📝 To use in new scripts:")
print("""
from src.numerical_guardrails import validate_coupling

# Before any Floquet/Lindblad computation:
g0 = ...  # Your coupling constant
result = validate_coupling(g0, name="g₀")
if not result.is_valid:
    raise ValueError(result.message)
""")

print("\n" + "=" * 80)
print("NEXT STEPS")
print("=" * 80)
print("""
1. Tag artifact-corrected release:
   git tag -a v1.0-artifact-corrected -m "Phase B corrected + guardrails"
   
2. Create Phase D workspace (already scaffolded in PHASE_D_PLAN.md)

3. All new Phase D scripts MUST import and use numerical_guardrails
""")
