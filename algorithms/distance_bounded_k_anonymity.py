from collections import defaultdict
from algorithms.graph_utils import bfs_expand, compute_medoid, haversine_m


def run_distance_bounded_k_anonymity(nodes, edges, coords, adj, snapshot,
                                      k=5, r_max=1500.0):
    # Count users at each node
    node_user_count = defaultdict(int)
    for dev_id, node_id in snapshot.items():
        node_user_count[node_id] += 1

    results = []
    for dev_id, true_node in snapshot.items():
        # BFS WITH radius cap
        region, users_found, radius = bfs_expand(
            adj, true_node, node_user_count, k, max_radius=r_max
        )

        # Always report (even if < k users found within cap)
        reported_node = compute_medoid(region, coords)
        loc_error = haversine_m(
            coords[true_node][0], coords[true_node][1],
            coords[reported_node][0], coords[reported_node][1],
        )

        results.append({
            "device_id": dev_id,
            "true_node": true_node,
            "reported_node": reported_node,
            "location_error": round(loc_error, 2),
            "k_achieved": users_found,
            "region_size": len(region),
            "region_radius": round(radius, 2),
            "available": True,  # Always available (never drops)
            "k_target_met": users_found >= k,
        })

    return results
