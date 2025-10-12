"""
Spin network mathematical utilities for LQG calculations.

This module provides the fundamental building blocks for spin network computations:
- SU(2) utilities (Wigner symbols, 6j/9j coefficients)
- Volume and area operator eigenvalues
- Spin network graph structures
- Polymer correction functions
"""

import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass
from scipy.special import factorial
import warnings

try:
    from sympy.physics.wigner import wigner_3j as sympy_wigner_3j
    from sympy.physics.wigner import wigner_6j as sympy_wigner_6j
    SYMPY_AVAILABLE = True
except ImportError:
    SYMPY_AVAILABLE = False
    warnings.warn("SymPy not available; using placeholder Wigner symbols")

from .constants import (
    L_PLANCK, HBAR, C, G, GAMMA_IMMIRZI,
    EPSILON_SMALL, J_MIN, J_MAX
)


# ============================================================================
# SU(2) Utilities and Wigner Symbols
# ============================================================================

def wigner_3j(j1: float, j2: float, j3: float, 
              m1: float, m2: float, m3: float) -> float:
    """
    Compute Wigner 3j symbol.
    
    Returns the value of:
        ⎛ j1  j2  j3 ⎞
        ⎝ m1  m2  m3 ⎠
    
    Uses SymPy's exact implementation if available, otherwise falls back to
    simplified version with limited accuracy.
    """
    if SYMPY_AVAILABLE:
        # Use SymPy's exact calculation
        result = sympy_wigner_3j(j1, j2, j3, m1, m2, m3)
        return float(result)
    
    # Fallback: basic selection rules and simple cases
    # Selection rules
    if abs(m1) > j1 or abs(m2) > j2 or abs(m3) > j3:
        return 0.0
    if m1 + m2 + m3 != 0:
        return 0.0
    if not (abs(j1 - j2) <= j3 <= j1 + j2):
        return 0.0
    
    # All j and m must be half-integer or integer
    if not all((2*x) % 1 == 0 for x in [j1, j2, j3, m1, m2, m3]):
        return 0.0
    
    # Simple special cases
    if j1 == 0.5 and j2 == 0.5 and j3 == 0:
        if m1 + m2 == 0:
            return (-1)**(0.5 - m1) / np.sqrt(2)
        return 0.0
    
    # Warn about limited accuracy
    warnings.warn("Using fallback 3j symbol - install SymPy for exact results", stacklevel=2)
    return 0.0


def wigner_6j(j1: float, j2: float, j3: float,
              j4: float, j5: float, j6: float) -> float:
    """
    Compute Wigner 6j symbol (Racah W-coefficient).
    
    Returns the value of:
        ⎧ j1  j2  j3 ⎫
        ⎩ j4  j5  j6 ⎭
    
    Critical for spin network calculations and recoupling theory.
    Uses SymPy's exact implementation if available.
    """
    if SYMPY_AVAILABLE:
        # Use SymPy's exact calculation
        result = sympy_wigner_6j(j1, j2, j3, j4, j5, j6)
        return float(result)
    
    # Fallback: basic selection rules and simple cases
    # Triangle inequalities (4 triangles must be satisfied)
    triangles = [
        (j1, j2, j3), (j1, j5, j6),
        (j4, j2, j6), (j4, j5, j3)
    ]
    
    for (a, b, c) in triangles:
        if not (abs(a - b) <= c <= a + b):
            return 0.0
    
    # Simple orthogonality case
    if all(j <= 2 for j in [j1, j2, j3, j4, j5, j6]):
        if j1 == j4 and j2 == j5 and j3 == j6:
            dim = (2*j1 + 1) * (2*j2 + 1) * (2*j3 + 1)
            return 1.0 / np.sqrt(dim) if dim > 0 else 0.0
    
    # Warn about limited accuracy
    warnings.warn("Using fallback 6j symbol - install SymPy for exact results", stacklevel=2)
    return 0.0


# ============================================================================
# Spin Network Graph Structure
# ============================================================================

@dataclass
class SpinNetworkEdge:
    """Edge in a spin network, labeled by SU(2) spin quantum number."""
    node_i: int
    node_j: int
    spin: float  # j = 0, 1/2, 1, 3/2, 2, ...
    
    def area_eigenvalue(self) -> float:
        """Area eigenvalue associated with this edge (puncture on a surface)."""
        j = self.spin
        return 8 * np.pi * GAMMA_IMMIRZI * L_PLANCK**2 * np.sqrt(j * (j + 1))


@dataclass
class SpinNetworkNode:
    """Node (vertex) in a spin network with valence and intertwiners."""
    node_id: int
    edges: List[int]  # Indices of incident edges
    intertwiner: Optional[np.ndarray] = None  # SU(2) intertwiner
    
    def valence(self) -> int:
        """Number of edges meeting at this node."""
        return len(self.edges)


class SpinNetwork:
    """
    A spin network: a graph with edges labeled by SU(2) spins and nodes by intertwiners.
    
    In LQG, spin networks are quantum states of spatial geometry.
    """
    
    def __init__(self):
        self.nodes: List[SpinNetworkNode] = []
        self.edges: List[SpinNetworkEdge] = []
    
    def add_node(self, node_id: int) -> int:
        """Add a node and return its index."""
        node = SpinNetworkNode(node_id=node_id, edges=[])
        self.nodes.append(node)
        return len(self.nodes) - 1
    
    def add_edge(self, node_i: int, node_j: int, spin: float) -> int:
        """Add an edge between two nodes with given spin label."""
        edge = SpinNetworkEdge(node_i=node_i, node_j=node_j, spin=spin)
        edge_idx = len(self.edges)
        self.edges.append(edge)
        
        # Update node adjacency
        self.nodes[node_i].edges.append(edge_idx)
        self.nodes[node_j].edges.append(edge_idx)
        
        return edge_idx
    
    def total_area(self) -> float:
        """Total area eigenvalue from all edges."""
        return sum(edge.area_eigenvalue() for edge in self.edges)
    
    def volume_eigenvalue(self, node_idx: int) -> float:
        """
        Volume eigenvalue at a node (simplified calculation).
        
        The full calculation involves summing over orientations and uses 6j symbols.
        This is a simplified version using the standard formula for tetrahedra.
        """
        node = self.nodes[node_idx]
        if node.valence() < 4:
            return 0.0  # Need at least 4 edges for non-zero volume
        
        # Get spins of incident edges
        spins = [self.edges[e].spin for e in node.edges[:4]]  # Use first 4
        j1, j2, j3, j4 = spins
        
        # Simplified volume formula (order of magnitude correct)
        # Full formula: V = (8πγ ℓ_P³/√2) * √[sum over orientations of (6j)²]
        # We use approximate scaling
        j_avg = np.mean(spins)
        volume_estimate = (8 * np.pi * GAMMA_IMMIRZI * L_PLANCK**3 / np.sqrt(2)) * j_avg**(3/2)
        
        return volume_estimate
    
    def total_volume(self) -> float:
        """Total volume eigenvalue (sum over all nodes)."""
        return sum(self.volume_eigenvalue(i) for i in range(len(self.nodes)))


# ============================================================================
# Polymer Correction Functions
# ============================================================================

def polymer_correction_sinc(mu: float, j: float) -> float:
    """
    Polymer correction to gravitational dynamics: sinc(π μ j).
    
    In the polymer representation, the classical Poisson bracket {A, E} 
    gets replaced by a discrete version, introducing sinc corrections.
    
    Args:
        mu: Polymer/Barbero-Immirzi scale parameter (dimensionless)
        j: Spin label
    
    Returns:
        sinc(π μ j) correction factor
    """
    x = np.pi * mu * j
    if abs(x) < EPSILON_SMALL:
        return 1.0
    return np.sin(x) / x


def polymer_enhancement_factor(mu: float, j: float) -> float:
    """
    Enhancement factor relative to classical for polymer-corrected dynamics.
    
    At small μj, sinc → 1 (classical limit).
    At μj ≈ 1/(2π), sinc reaches maximum ≈ 1.
    At μj = 1/2, sinc = 2/π ≈ 0.637.
    
    Returns ratio of polymer to classical coupling.
    """
    sinc_val = polymer_correction_sinc(mu, j)
    return sinc_val


def effective_planck_length(mu: float, j: float) -> float:
    """
    Effective Planck length modified by polymer corrections.
    
    In polymer LQG, the minimal length scale is shifted from ℓ_P to ℓ_eff.
    This affects the energy-curvature relationship.
    """
    correction = polymer_correction_sinc(mu, j)
    return L_PLANCK / np.sqrt(max(correction, EPSILON_SMALL))


# ============================================================================
# Volume Operator Eigenvalue (General Formula)
# ============================================================================

def volume_eigenvalue_tetrahedron(j1: float, j2: float, j3: float, j4: float,
                                   j5: float, j6: float) -> float:
    """
    Volume eigenvalue for a 4-valent node (tetrahedron) in LQG.
    
    The volume operator eigenvalue is:
        V = (8πγ ℓ_P³/√2) √[Σ_{ε} (6j-symbol)²]
    
    where the sum is over orientations ε of the tetrahedron, and the 6j symbol is:
        ⎧ j1  j2  j3 ⎫
        ⎩ j4  j5  j6 ⎭
    
    Args:
        j1, j2, j3, j4, j5, j6: Spins labeling the 6 edges of a tetrahedron
    
    Returns:
        Volume eigenvalue in m³
    """
    # Sum over orientations (there are multiple valid 6j contractions)
    # For simplicity, we compute one representative 6j
    sixj = wigner_6j(j1, j2, j3, j4, j5, j6)
    
    # Volume formula
    prefactor = 8 * np.pi * GAMMA_IMMIRZI * L_PLANCK**3 / np.sqrt(2)
    volume = prefactor * np.sqrt(sixj**2)
    
    return volume


# ============================================================================
# Coarse-Graining Utilities
# ============================================================================

def average_spin_in_region(spins: List[float], weights: Optional[List[float]] = None) -> float:
    """
    Compute effective average spin in a coarse-grained region.
    
    When coarse-graining a spin network, many fine-scale edges are replaced
    by effective macroscopic edges. The effective spin is a weighted average.
    """
    if weights is None:
        weights = np.ones(len(spins))
    
    weights = np.array(weights)
    spins = np.array(spins)
    
    return np.average(spins, weights=weights)


def coarse_grain_spin_network(network: SpinNetwork, scale: float) -> SpinNetwork:
    """
    Coarse-grain a spin network by grouping nodes within a given scale.
    
    This is a simplified placeholder. Full implementation requires:
    - Spatial embedding of nodes
    - Grouping nodes within distance < scale
    - Summing volumes and averaging spins
    - Constructing effective intertwiner
    
    Args:
        network: Fine-scale spin network
        scale: Coarse-graining length scale (in Planck lengths)
    
    Returns:
        Coarse-grained spin network
    """
    # Placeholder: return a single-node network with averaged properties
    coarse_network = SpinNetwork()
    
    # Create one coarse node
    coarse_node_id = coarse_network.add_node(node_id=0)
    
    # Average spin
    if network.edges:
        avg_spin = np.mean([e.spin for e in network.edges])
        # Add representative edge with averaged spin
        coarse_network.add_edge(0, 0, avg_spin)  # Self-loop for simplicity
    
    return coarse_network


# ============================================================================
# Utility Functions
# ============================================================================

def spin_dimension(j: float) -> int:
    """Dimension of SU(2) irrep with spin j."""
    return int(2 * j + 1)


def is_triangle(j1: float, j2: float, j3: float) -> bool:
    """Check if three spins satisfy triangle inequality (coupling rule)."""
    return abs(j1 - j2) <= j3 <= j1 + j2


def compute_6j_sum_squared(j_list: List[Tuple[float, float, float, float, float, float]]) -> float:
    """
    Compute sum of squared 6j symbols, used in volume calculations.
    
    Args:
        j_list: List of 6-tuples of spins for each 6j symbol
    
    Returns:
        Σ (6j)²
    """
    total = 0.0
    for (j1, j2, j3, j4, j5, j6) in j_list:
        sixj = wigner_6j(j1, j2, j3, j4, j5, j6)
        total += sixj**2
    return total
