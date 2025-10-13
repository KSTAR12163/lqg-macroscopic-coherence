#!/usr/bin/env python3
"""
Debug and fix icosahedral topology generator.

Issue: Current implementation produces 0 edges (threshold too strict).
Goal: Generate proper 12-node, 30-edge icosahedron.
"""

import numpy as np
import itertools

print("=" * 80)
print("DEBUGGING ICOSAHEDRAL TOPOLOGY GENERATOR")
print("=" * 80)

# Current implementation
phi = (1 + np.sqrt(5)) / 2

vertices_old = []
for signs in itertools.product([1, -1], repeat=2):
    vertices_old.append([0, signs[0], signs[1] * phi])
    vertices_old.append([signs[0], signs[1] * phi, 0])
    vertices_old.append([signs[0] * phi, 0, signs[1]])

vertices_old = np.array(vertices_old)

print(f"\nOLD implementation:")
print(f"  Number of vertices generated: {len(vertices_old)}")
print(f"  Unique vertices: {len(np.unique(vertices_old, axis=0))}")
print(f"\n  First few vertices:")
for i in range(min(6, len(vertices_old))):
    print(f"    {i}: {vertices_old[i]}")

# Count edges with different thresholds
for threshold in [2.0, 2.1, 2.2, 2.5, 3.0]:
    edges = []
    for i in range(len(vertices_old)):
        for j in range(i + 1, len(vertices_old)):
            dist = np.linalg.norm(vertices_old[i] - vertices_old[j])
            if dist < threshold:
                edges.append((i, j))
    print(f"\n  Threshold {threshold}: {len(edges)} edges")

print("\n" + "=" * 80)
print("FIXED IMPLEMENTATION")
print("=" * 80)

# Correct icosahedral vertices
# 12 vertices: permutations of (0, ±1, ±φ) with proper uniqueness
vertices_new = []

# Group 1: (0, ±1, ±φ)
for s1, s2 in itertools.product([1, -1], repeat=2):
    vertices_new.append([0, s1 * 1, s2 * phi])

# Group 2: (±1, ±φ, 0)
for s1, s2 in itertools.product([1, -1], repeat=2):
    vertices_new.append([s1 * 1, s2 * phi, 0])

# Group 3: (±φ, 0, ±1)
for s1, s2 in itertools.product([1, -1], repeat=2):
    vertices_new.append([s1 * phi, 0, s2 * 1])

vertices_new = np.array(vertices_new)

print(f"\nNEW implementation:")
print(f"  Number of vertices generated: {len(vertices_new)}")
print(f"  Unique vertices: {len(np.unique(vertices_new, axis=0))}")
print(f"\n  All vertices:")
for i in range(len(vertices_new)):
    print(f"    {i}: {vertices_new[i]}")

# Compute pairwise distances
distances = []
for i in range(len(vertices_new)):
    for j in range(i + 1, len(vertices_new)):
        dist = np.linalg.norm(vertices_new[i] - vertices_new[j])
        distances.append(dist)

distances = np.array(distances)
print(f"\n  Distance statistics:")
print(f"    Min distance: {distances.min():.4f}")
print(f"    Max distance: {distances.max():.4f}")
print(f"    Unique distances: {len(np.unique(np.round(distances, 3)))}")

# Histogram of distances
unique_dists = np.unique(np.round(distances, 3))
print(f"\n  Distance distribution:")
for d in sorted(unique_dists):
    count = np.sum(np.abs(distances - d) < 0.01)
    print(f"    {d:.3f}: {count} edges")

# Expected: icosahedron has edge length ~2.0
# Should have 30 edges at shortest distance
shortest_dist = distances.min()
threshold = shortest_dist * 1.01  # 1% tolerance

edges_correct = []
for i in range(len(vertices_new)):
    for j in range(i + 1, len(vertices_new)):
        dist = np.linalg.norm(vertices_new[i] - vertices_new[j])
        if dist < threshold:
            edges_correct.append((i, j))

print(f"\n  Using threshold {threshold:.4f} (shortest distance + 1%):")
print(f"    Number of edges: {len(edges_correct)}")
print(f"    Expected: 30 edges")

if len(edges_correct) == 30:
    print("\n    ✓ CORRECT! Found 30 edges for icosahedron")
else:
    print(f"\n    ✗ INCORRECT! Expected 30, got {len(edges_correct)}")

# Verify coordination number
coord_nums = {}
for i in range(len(vertices_new)):
    coord_nums[i] = 0

for i, j in edges_correct:
    coord_nums[i] += 1
    coord_nums[j] += 1

print(f"\n  Coordination numbers:")
for i in range(len(vertices_new)):
    print(f"    Node {i}: {coord_nums[i]} neighbors")

avg_coord = np.mean(list(coord_nums.values()))
print(f"\n  Average coordination: {avg_coord:.1f}")
print(f"  Expected: 5.0 (regular icosahedron)")

if abs(avg_coord - 5.0) < 0.1:
    print("    ✓ CORRECT!")
else:
    print(f"    ✗ INCORRECT! Expected 5.0, got {avg_coord:.1f}")

print("\n" + "=" * 80)
print("RECOMMENDED FIX")
print("=" * 80)

print(f"""
Replace icosahedral_edges() with:

def icosahedral_edges() -> List[Tuple[int, int]]:
    \"\"\"
    Icosahedral graph: 12 nodes, 30 edges.
    Regular icosahedron connectivity.
    \"\"\"
    phi = (1 + np.sqrt(5)) / 2
    
    # 12 vertices: permutations of (0, ±1, ±φ)
    vertices = []
    
    # Group 1: (0, ±1, ±φ)
    for s1, s2 in itertools.product([1, -1], repeat=2):
        vertices.append([0, s1 * 1, s2 * phi])
    
    # Group 2: (±1, ±φ, 0)
    for s1, s2 in itertools.product([1, -1], repeat=2):
        vertices.append([s1 * 1, s2 * phi, 0])
    
    # Group 3: (±φ, 0, ±1)
    for s1, s2 in itertools.product([1, -1], repeat=2):
        vertices.append([s1 * phi, 0, s2 * 1])
    
    vertices = np.array(vertices)
    
    # Edges: connect nearest neighbors
    distances = []
    for i in range(12):
        for j in range(i + 1, 12):
            dist = np.linalg.norm(vertices[i] - vertices[j])
            distances.append(dist)
    
    threshold = np.min(distances) * 1.01  # Shortest distance + 1%
    
    edges = []
    for i in range(12):
        for j in range(i + 1, 12):
            dist = np.linalg.norm(vertices[i] - vertices[j])
            if dist < threshold:
                edges.append((i, j))
    
    return edges
""")

print("=" * 80)
