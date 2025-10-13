"""
Topology generator for systematic spin network exploration (GPT-5 Priority #1).

This module generates spin networks with different topologies and spin assignments
to test whether network structure determines coupling strength.

Goal: Find topologies that support |⟨f|H_int|i⟩| ≥ 10^20 × tetrahedral baseline.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import itertools

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.spin_network import SpinNetwork


@dataclass
class TopologyInfo:
    """Metadata about a generated topology."""
    name: str
    num_nodes: int
    num_edges: int
    edge_list: List[Tuple[int, int]]
    spin_assignment: str  # 'uniform', 'peaked', 'random'
    spin_values: List[float]


# ============================================================================
# Platonic Solid Topologies
# ============================================================================

def tetrahedral_edges() -> List[Tuple[int, int]]:
    """
    Tetrahedral graph: 4 nodes, 6 edges.
    Complete graph K4.
    """
    edges = []
    for i in range(4):
        for j in range(i + 1, 4):
            edges.append((i, j))
    return edges


def cubic_edges() -> List[Tuple[int, int]]:
    """
    Cubic graph: 8 nodes, 12 edges.
    Vertices and edges of a cube.
    """
    # Label vertices as binary: 000, 001, 010, ..., 111
    # Edge if Hamming distance = 1
    edges = []
    for i in range(8):
        for j in range(i + 1, 8):
            # Check Hamming distance
            xor = i ^ j
            if bin(xor).count('1') == 1:  # Differs in exactly 1 bit
                edges.append((i, j))
    return edges


def octahedral_edges() -> List[Tuple[int, int]]:
    """
    Octahedral graph: 6 nodes, 12 edges.
    Dual of cube, vertices at ±x, ±y, ±z axes.
    """
    # Label: 0=+x, 1=-x, 2=+y, 3=-y, 4=+z, 5=-z
    # Edge if not opposite (not same axis)
    edges = []
    opposites = {0: 1, 1: 0, 2: 3, 3: 2, 4: 5, 5: 4}
    
    for i in range(6):
        for j in range(i + 1, 6):
            if j != opposites[i]:
                edges.append((i, j))
    
    return edges


def icosahedral_edges() -> List[Tuple[int, int]]:
    """
    Icosahedral graph: 12 nodes, 30 edges.
    Regular icosahedron connectivity.
    
    Using golden ratio construction.
    """
    # Golden ratio
    phi = (1 + np.sqrt(5)) / 2
    
    # 12 vertices: permutations of (0, ±1, ±φ)
    vertices = []
    for signs in itertools.product([1, -1], repeat=2):
        vertices.append([0, signs[0], signs[1] * phi])
        vertices.append([signs[0], signs[1] * phi, 0])
        vertices.append([signs[0] * phi, 0, signs[1]])
    
    vertices = np.array(vertices)
    
    # Edges: connect vertices at distance ~2.0 (nearest neighbors in icosahedron)
    edges = []
    edge_threshold = 2.1  # Adjusted threshold
    
    for i in range(12):
        for j in range(i + 1, 12):
            dist = np.linalg.norm(vertices[i] - vertices[j])
            if dist < edge_threshold:
                edges.append((i, j))
    
    return edges


def random_triangulation_edges(num_nodes: int, seed: Optional[int] = None) -> List[Tuple[int, int]]:
    """
    Random triangulated graph: num_nodes nodes, ~3*num_nodes edges.
    
    Start with triangle, iteratively add nodes and triangulate.
    """
    if seed is not None:
        np.random.seed(seed)
    
    if num_nodes < 3:
        raise ValueError("Need at least 3 nodes for triangulation")
    
    edges = [(0, 1), (1, 2), (2, 0)]  # Initial triangle
    
    for new_node in range(3, num_nodes):
        # Pick random existing edge to subdivide
        if len(edges) == 0:
            break
        
        edge_idx = np.random.randint(len(edges))
        i, j = edges[edge_idx]
        
        # Add new node connected to both endpoints
        edges.append((i, new_node))
        edges.append((j, new_node))
        
        # Optionally connect to a few other random nodes for richness
        num_extra = min(2, len(range(new_node)))
        if num_extra > 0:
            extra_nodes = np.random.choice(new_node, size=num_extra, replace=False)
            for k in extra_nodes:
                if (k, new_node) not in edges and (new_node, k) not in edges:
                    edges.append((k, new_node))
    
    return edges


# ============================================================================
# Spin Assignment Strategies
# ============================================================================

def uniform_spins(num_edges: int, spin_value: float = 1.0) -> List[float]:
    """
    All edges have the same spin j.
    
    Args:
        num_edges: Number of edges
        spin_value: Spin quantum number (default j=1)
    
    Returns:
        List of spin values
    """
    return [spin_value] * num_edges


def peaked_spins(num_edges: int, peak_spin: float = 10.0, base_spin: float = 0.5) -> List[float]:
    """
    One edge has large spin, rest have small spin.
    
    Tests if localized high-spin edge enhances coupling.
    
    Args:
        num_edges: Number of edges
        peak_spin: Large spin for one edge
        base_spin: Small spin for other edges
    
    Returns:
        List of spin values
    """
    spins = [base_spin] * num_edges
    spins[0] = peak_spin  # First edge gets large spin
    return spins


def random_spins(num_edges: int, min_spin: float = 0.5, max_spin: float = 5.0, 
                 seed: Optional[int] = None) -> List[float]:
    """
    Random spins drawn from uniform distribution.
    
    Args:
        num_edges: Number of edges
        min_spin: Minimum spin value
        max_spin: Maximum spin value
        seed: Random seed for reproducibility
    
    Returns:
        List of spin values
    """
    if seed is not None:
        np.random.seed(seed)
    
    return list(np.random.uniform(min_spin, max_spin, num_edges))


def geometric_spins(num_edges: int, base: float = 2.0, start_spin: float = 0.5) -> List[float]:
    """
    Geometric progression: j_n = start_spin × base^n.
    
    Tests if gradual spin increase affects coupling.
    """
    return [start_spin * base**n for n in range(num_edges)]


# ============================================================================
# Topology Generator
# ============================================================================

def generate_topology(
    topology_type: str,
    spin_mode: str = 'uniform',
    spin_params: Optional[Dict] = None,
    num_nodes: Optional[int] = None,
    seed: Optional[int] = None
) -> Tuple[SpinNetwork, TopologyInfo]:
    """
    Generate a spin network with specified topology and spin assignment.
    
    Args:
        topology_type: Type of topology
            - 'tetrahedral': 4 nodes, 6 edges (K4)
            - 'cubic': 8 nodes, 12 edges (cube)
            - 'octahedral': 6 nodes, 12 edges (octahedron)
            - 'icosahedral': 12 nodes, 30 edges (icosahedron)
            - 'random': Random triangulation (specify num_nodes)
        
        spin_mode: Spin assignment strategy
            - 'uniform': All spins equal (default j=1.0)
            - 'peaked': One large spin, rest small
            - 'random': Uniform distribution [min, max]
            - 'geometric': Geometric progression
        
        spin_params: Parameters for spin assignment
            - uniform: {'spin_value': 1.0}
            - peaked: {'peak_spin': 10.0, 'base_spin': 0.5}
            - random: {'min_spin': 0.5, 'max_spin': 5.0, 'seed': 42}
            - geometric: {'base': 2.0, 'start_spin': 0.5}
        
        num_nodes: Number of nodes (required for 'random' topology)
        seed: Random seed (for random topology generation)
    
    Returns:
        (SpinNetwork, TopologyInfo) tuple
    
    Example:
        >>> network, info = generate_topology('cubic', spin_mode='uniform')
        >>> print(f"{info.name}: {info.num_nodes} nodes, {info.num_edges} edges")
        cubic: 8 nodes, 12 edges
    """
    # Get edge list based on topology
    if topology_type == 'tetrahedral':
        edge_list = tetrahedral_edges()
        num_nodes_actual = 4
    elif topology_type == 'cubic':
        edge_list = cubic_edges()
        num_nodes_actual = 8
    elif topology_type == 'octahedral':
        edge_list = octahedral_edges()
        num_nodes_actual = 6
    elif topology_type == 'icosahedral':
        edge_list = icosahedral_edges()
        num_nodes_actual = 12
    elif topology_type == 'random':
        if num_nodes is None:
            raise ValueError("num_nodes required for random topology")
        edge_list = random_triangulation_edges(num_nodes, seed=seed)
        num_nodes_actual = num_nodes
    else:
        raise ValueError(f"Unknown topology type: {topology_type}")
    
    num_edges = len(edge_list)
    
    # Generate spin assignments
    if spin_params is None:
        spin_params = {}
    
    if spin_mode == 'uniform':
        spin_values = uniform_spins(num_edges, **spin_params)
    elif spin_mode == 'peaked':
        spin_values = peaked_spins(num_edges, **spin_params)
    elif spin_mode == 'random':
        spin_values = random_spins(num_edges, **spin_params)
    elif spin_mode == 'geometric':
        spin_values = geometric_spins(num_edges, **spin_params)
    else:
        raise ValueError(f"Unknown spin mode: {spin_mode}")
    
    # Build SpinNetwork
    network = SpinNetwork()
    
    # Add nodes
    for i in range(num_nodes_actual):
        network.add_node(i)
    
    # Add edges with spins
    for (i, j), spin in zip(edge_list, spin_values):
        network.add_edge(i, j, spin)
    
    # Create topology info
    info = TopologyInfo(
        name=f"{topology_type}_{spin_mode}",
        num_nodes=num_nodes_actual,
        num_edges=num_edges,
        edge_list=edge_list,
        spin_assignment=spin_mode,
        spin_values=spin_values
    )
    
    return network, info


# ============================================================================
# Topology Comparison Utilities
# ============================================================================

def generate_topology_suite() -> Dict[str, Tuple[SpinNetwork, TopologyInfo]]:
    """
    Generate a comprehensive suite of topologies for comparison.
    
    Returns:
        Dictionary mapping name → (network, info)
    """
    suite = {}
    
    # Platonic solids with uniform spins
    for topo in ['tetrahedral', 'cubic', 'octahedral', 'icosahedral']:
        network, info = generate_topology(topo, spin_mode='uniform', spin_params={'spin_value': 1.0})
        suite[info.name] = (network, info)
    
    # Test peaked assignment on cubic
    network, info = generate_topology('cubic', spin_mode='peaked', 
                                      spin_params={'peak_spin': 10.0, 'base_spin': 0.5})
    suite[info.name] = (network, info)
    
    # Test random spins on octahedral
    network, info = generate_topology('octahedral', spin_mode='random',
                                      spin_params={'min_spin': 0.5, 'max_spin': 3.0, 'seed': 42})
    suite[info.name] = (network, info)
    
    # Random triangulations
    for n_nodes in [6, 10]:
        network, info = generate_topology('random', spin_mode='uniform',
                                          num_nodes=n_nodes, seed=42,
                                          spin_params={'spin_value': 1.0})
        suite[f"random_{n_nodes}nodes_uniform"] = (network, info)
    
    return suite


def print_topology_summary(info: TopologyInfo):
    """Print summary of topology properties."""
    print(f"\nTopology: {info.name}")
    print(f"  Nodes: {info.num_nodes}")
    print(f"  Edges: {info.num_edges}")
    print(f"  Spin assignment: {info.spin_assignment}")
    if info.spin_values:
        print(f"  Spin range: [{min(info.spin_values):.2f}, {max(info.spin_values):.2f}]")
        print(f"  Average spin: {np.mean(info.spin_values):.2f}")
    else:
        print(f"  ⚠️  No edges/spins assigned!")
