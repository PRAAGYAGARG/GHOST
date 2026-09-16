import json
import math
import os
import random

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SEED = 42
NUM_NODES = 200
NUM_DEVICES = 80
NUM_SNAPSHOTS = 5

# City center: Beijing (approx)
CENTER_LAT = 39.915
CENTER_LON = 116.404

# Roughly 5km x 5km area
SPREAD_LAT = 0.025   # ~2.8 km in each direction
SPREAD_LON = 0.032   # ~2.8 km in each direction (adjusted for latitude)

# Edge generation: connect nodes within this distance (metres)
MAX_EDGE_DIST_M = 600
MIN_EDGE_DIST_M = 50


def haversine_m(lon1, lat1, lon2, lat2):
    """Great-circle distance in metres between two (lon, lat) points."""
    R = 6_371_000  # Earth radius in metres
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def generate_graph(seed=SEED):
    """
    Generate a connected road-network-like graph.

    Strategy: place nodes on a perturbed grid, then connect nearby nodes
    (Delaunay-like proximity graph). Ensures the graph is connected by
    adding edges to isolated components.
    """
    rng = random.Random(seed)

    # --- Generate nodes on a perturbed grid ---
    grid_side = int(math.ceil(math.sqrt(NUM_NODES)))
    nodes = []
    node_id = 0

    for row in range(grid_side):
        for col in range(grid_side):
            if node_id >= NUM_NODES:
                break
            # Base grid position
            base_lat = CENTER_LAT - SPREAD_LAT + (2 * SPREAD_LAT) * (row / max(grid_side - 1, 1))
            base_lon = CENTER_LON - SPREAD_LON + (2 * SPREAD_LON) * (col / max(grid_side - 1, 1))

            # Add jitter to make it look like real intersections
            jitter_lat = rng.gauss(0, SPREAD_LAT * 0.04)
            jitter_lon = rng.gauss(0, SPREAD_LON * 0.04)

            nodes.append({
                "id": f"n{node_id:03d}",
                "x": round(base_lon + jitter_lon, 6),
                "y": round(base_lat + jitter_lat, 6),
            })
            node_id += 1

    # --- Generate edges: connect nearby nodes ---
    edges = []
    edge_set = set()
    coords = {n["id"]: (n["x"], n["y"]) for n in nodes}

    for i, n1 in enumerate(nodes):
        for j, n2 in enumerate(nodes):
            if j <= i:
                continue
            d = haversine_m(n1["x"], n1["y"], n2["x"], n2["y"])
            if MIN_EDGE_DIST_M <= d <= MAX_EDGE_DIST_M:
                key = (n1["id"], n2["id"])
                if key not in edge_set:
                    edge_set.add(key)
                    edges.append({
                        "source": n1["id"],
                        "target": n2["id"],
                        "distance": round(d, 1),
                    })

    # --- Ensure connectivity via union-find ---
    parent = {n["id"]: n["id"] for n in nodes}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for e in edges:
        union(e["source"], e["target"])

    # Find all components and connect them
    components = {}
    for n in nodes:
        root = find(n["id"])
        components.setdefault(root, []).append(n)

    comp_list = list(components.values())
    for ci in range(1, len(comp_list)):
        # Connect component ci to component 0 via closest pair
        best_d = float("inf")
        best_pair = None
        for n1 in comp_list[0]:
            for n2 in comp_list[ci]:
                d = haversine_m(n1["x"], n1["y"], n2["x"], n2["y"])
                if d < best_d:
                    best_d = d
                    best_pair = (n1["id"], n2["id"])
        if best_pair:
            edges.append({
                "source": best_pair[0],
                "target": best_pair[1],
                "distance": round(best_d, 1),
            })
            union(best_pair[0], best_pair[1])
            # Merge component lists
            comp_list[0].extend(comp_list[ci])

    return nodes, edges


def generate_device_snapshots(nodes, seed=SEED):
    """
    Generate device location snapshots.

    Devices are initially placed with density variation:
    - Central area has more devices (denser)
    - Peripheral areas have fewer devices (sparser)

    Between snapshots, each device moves to a nearby node (simulating
    short-distance mobility).
    """
    rng = random.Random(seed)
    node_ids = [n["id"] for n in nodes]
    coords = {n["id"]: (n["x"], n["y"]) for n in nodes}

    # Build adjacency for mobility
    adj = {nid: [] for nid in node_ids}

    # Weight toward central nodes for initial placement
    center_weights = []
    for n in nodes:
        dx = n["x"] - CENTER_LON
        dy = n["y"] - CENTER_LAT
        dist_from_center = math.sqrt(dx ** 2 + dy ** 2)
        # Gaussian weighting: closer to center = higher probability
        w = math.exp(-dist_from_center ** 2 / (2 * 0.015 ** 2))
        center_weights.append(w)

    total_w = sum(center_weights)
    center_probs = [w / total_w for w in center_weights]

    # Initial placement
    def weighted_choice(probs):
        r = rng.random()
        cumulative = 0
        for i, p in enumerate(probs):
            cumulative += p
            if r <= cumulative:
                return i
        return len(probs) - 1

    device_positions = {}
    for d in range(NUM_DEVICES):
        idx = weighted_choice(center_probs)
        device_positions[f"dev_{d:03d}"] = node_ids[idx]

    snapshots = [dict(device_positions)]

    # Build adjacency from edges (we'll need to load edges)
    # For simplicity, generate adjacency from node proximity
    for i, n1 in enumerate(nodes):
        for j, n2 in enumerate(nodes):
            if i == j:
                continue
            d = haversine_m(n1["x"], n1["y"], n2["x"], n2["y"])
            if d <= MAX_EDGE_DIST_M:
                adj[n1["id"]].append(n2["id"])

    # Subsequent snapshots: each device moves to a neighbor with some probability
    for _ in range(NUM_SNAPSHOTS - 1):
        new_positions = {}
        for dev_id, current_node in device_positions.items():
            if rng.random() < 0.6 and adj[current_node]:
                # Move to a random neighbor
                new_positions[dev_id] = rng.choice(adj[current_node])
            else:
                # Stay put
                new_positions[dev_id] = current_node
        device_positions = new_positions
        snapshots.append(dict(device_positions))

    return snapshots


def main():
    """Generate and save all synthetic data."""
    here = os.path.dirname(os.path.abspath(__file__))

    print("=" * 60)
    print("GHOST - Synthetic Data Generator")
    print("=" * 60)

    print("\n[1/3] Generating road-network graph...")
    nodes, edges = generate_graph()
    print(f"  -> {len(nodes)} nodes, {len(edges)} edges")

    print("[2/3] Generating device snapshots...")
    snapshots = generate_device_snapshots(nodes)
    print(f"  -> {NUM_DEVICES} devices, {len(snapshots)} snapshots")

    print("[3/3] Saving data files...")
    with open(os.path.join(here, "city_graph_nodes.json"), "w") as f:
        json.dump(nodes, f, indent=2)
    with open(os.path.join(here, "city_graph_edges.json"), "w") as f:
        json.dump(edges, f, indent=2)
    with open(os.path.join(here, "device_snapshots.json"), "w") as f:
        json.dump(snapshots, f, indent=2)

    print(f"  -> Saved to {here}/")
    print("  * city_graph_nodes.json")
    print("  * city_graph_edges.json")
    print("  * device_snapshots.json")
    print()

    return nodes, edges, snapshots


if __name__ == "__main__":
    main()
