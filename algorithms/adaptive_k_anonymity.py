from collections import defaultdict
from algorithms.graph_utils import bfs_expand, compute_medoid, haversine_m


def run_adaptive_k_anonymity(nodes, edges, coords, adj, snapshot,
                              k=5, k_min=2, r_max=1500.0):
    # Count users at each node
    node_user_count = defaultdict(int)
    for dev_id, node_id in snapshot.items():
        node_user_count[node_id] += 1

    results = []
    for dev_id, true_node in snapshot.items():
        reported = False
        actual_k_used = k

        # Try decreasing k values from k down to k_min
        for try_k in range(k, k_min - 1, -1):
            region, users_found, radius = bfs_expand(
                adj, true_node, node_user_count, try_k, max_radius=r_max
            )

            if users_found >= try_k:
                # Success at this k level
                reported_node = compute_medoid(region, coords)
                loc_error = haversine_m(
                    coords[true_node][0], coords[true_node][1],
                    coords[reported_node][0], coords[reported_node][1],
                )
                actual_k_used = try_k

                results.append({
                    "device_id": dev_id,
                    "true_node": true_node,
                    "reported_node": reported_node,
                    "location_error": round(loc_error, 2),
                    "k_achieved": users_found,
                    "k_used": actual_k_used,
                    "k_target": k,
                    "region_size": len(region),
                    "region_radius": round(radius, 2),
                    "available": True,
                    "k_reduced": actual_k_used < k,
                })
                reported = True
                break

        if not reported:
            # Even k_min couldn't be met - still try to report with
            # whatever was found in the last attempt
            region, users_found, radius = bfs_expand(
                adj, true_node, node_user_count, 1, max_radius=r_max
            )
            if users_found >= 1:
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
                    "k_used": 1,
                    "k_target": k,
                    "region_size": len(region),
                    "region_radius": round(radius, 2),
                    "available": True,
                    "k_reduced": True,
                })
            else:
                # Truly no users found (shouldn't happen - user itself counts)
                results.append({
                    "device_id": dev_id,
                    "true_node": true_node,
                    "reported_node": None,
                    "location_error": None,
                    "k_achieved": 0,
                    "k_used": None,
                    "k_target": k,
                    "region_size": 0,
                    "region_radius": 0,
                    "available": False,
                    "k_reduced": True,
                })

    return results
