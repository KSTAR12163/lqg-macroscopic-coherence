"""Topology exploration module exports."""

from .topology_generator import (
    generate_topology,
    generate_topology_suite,
    print_topology_summary,
    TopologyInfo,
    # Edge generators
    tetrahedral_edges,
    cubic_edges,
    octahedral_edges,
    icosahedral_edges,
    random_triangulation_edges,
    # Spin assignment strategies
    uniform_spins,
    peaked_spins,
    random_spins,
    geometric_spins,
)

__all__ = [
    'generate_topology',
    'generate_topology_suite',
    'print_topology_summary',
    'TopologyInfo',
    'tetrahedral_edges',
    'cubic_edges',
    'octahedral_edges',
    'icosahedral_edges',
    'random_triangulation_edges',
    'uniform_spins',
    'peaked_spins',
    'random_spins',
    'geometric_spins',
]
