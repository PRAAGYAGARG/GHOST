from collections import defaultdict
from algorithms.graph_utils import bfs_expand, compute_medoid, haversine_m


def run_base_k_anonymity(nodes, edges, coords, adj, snapshot, k=5):
    # Count users at each node
    node_user_count = defaultdict(int)
    for dev_id, node_id in snapshot.items():
        node_user_count[node_id] += 1

    results = []
    for dev_id, true_node in snapshot.items():
        # BFS with NO radius cap
        region, users_found, radius = bfs_expand(
            adj, true_node, node_user_count, k, max_radius=None
        )

        if users_found >= k:
            # Success: report medoid
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
                "available": True,
            })
        else:
            # FAILED: drop report
            results.append({
                "device_id": dev_id,
                "true_node": true_node,
                "reported_node": None,
                "location_error": None,
                "k_achieved": users_found,
                "region_size": len(region),
                "region_radius": round(radius, 2),
                "available": False,
            })

    return results
