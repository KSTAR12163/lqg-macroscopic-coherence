#!/usr/bin/env python3
"""Quick test of network creation."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.phase_d.tier1_collective.network_construction import create_complete_network

print("Creating complete network with N=4...")
network, edges = create_complete_network(4)
print(f"✅ Success! Created network with {len(edges)} edges")
print(f"Expected: 6 edges (complete graph K_4)")
print(f"Match: {'✓' if len(edges) == 6 else '✗'}")
