import json
import math
import heapq
from collections import defaultdict, deque


def haversine_m(lon1, lat1, lon2, lat2):
    R = 6_371_000  # Earth radius in metres
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2)
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def load_graph(nodes_path, edges_path):
    with open(nodes_path) as f:
        nodes = json.load(f)
    with open(edges_path) as f:
        edges = json.load(f)

    coords = {n["id"]: (n["x"], n["y"]) for n in nodes}
    adj = build_adjacency(nodes, edges)

    return nodes, edges, coords, adj


def build_adjacency(nodes, edges):
    adj = defaultdict(list)
    for n in nodes:
        if n["id"] not in adj:
            adj[n["id"]] = []

    for e in edges:
        adj[e["source"]].append((e["target"], e["distance"]))
        adj[e["target"]].append((e["source"], e["distance"]))

    return dict(adj)


def dijkstra(adj, source):
    dist = {source: 0.0}
    heap = [(0.0, source)]

    while heap:
        d, u = heapq.heappop(heap)
        if d > dist.get(u, float("inf")):
            continue
        for v, w in adj.get(u, []):
            nd = d + w
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                heapq.heappush(heap, (nd, v))

    return dist


def all_pairs_shortest_paths(adj, node_ids):
    apsp = {}
    for src in node_ids:
        dists = dijkstra(adj, src)
        for dst, d in dists.items():
            apsp[(src, dst)] = d
    return apsp


def bfs_expand(adj, start_node, user_locations, k, max_radius=None):
    visited = {start_node}
    region = [start_node]
    users_found = user_locations.get(start_node, 0)
    region_radius = 0.0

    if users_found >= k:
        return region, users_found, region_radius

    # BFS via priority queue (Dijkstra-like to respect edge distances)
    heap = []
    for neighbor, dist in adj.get(start_node, []):
        heapq.heappush(heap, (dist, neighbor))

    while heap:
        d, node = heapq.heappop(heap)

        if node in visited:
            continue

        # Check radius cap
        if max_radius is not None and d > max_radius:
            break

        visited.add(node)
        region.append(node)
        region_radius = d
        users_found += user_locations.get(node, 0)

        if users_found >= k:
            break

        for neighbor, edge_dist in adj.get(node, []):
            if neighbor not in visited:
                heapq.heappush(heap, (d + edge_dist, neighbor))

    return region, users_found, region_radius


def compute_medoid(region, coords):
    if len(region) == 1:
        return region[0]

    # Compute centroid
    lons = [coords[n][0] for n in region]
    lats = [coords[n][1] for n in region]
    c_lon = sum(lons) / len(lons)
    c_lat = sum(lats) / len(lats)

    # Find node closest to centroid
    best_id = region[0]
    best_dist = float("inf")
    for nid in region:
        d = haversine_m(coords[nid][0], coords[nid][1], c_lon, c_lat)
        if d < best_dist:
            best_dist = d
            best_id = nid

    return best_id


def nearest_node(lon, lat, coords):
    best_id = None
    best_dist = float("inf")

    for nid, (nx, ny) in coords.items():
        d = haversine_m(lon, lat, nx, ny)
        if d < best_dist:
            best_dist = d
            best_id = nid

    return best_id, best_dist
