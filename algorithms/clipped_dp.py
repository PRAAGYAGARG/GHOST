import math
import numpy as np
from algorithms.graph_utils import haversine_m, nearest_node


def _metres_to_degrees(metres, ref_lat):
    lat_deg = metres / 111_320.0
    lon_deg = metres / (111_320.0 * math.cos(math.radians(ref_lat)))
    return lon_deg, lat_deg


def _degrees_to_metres(lon_deg, lat_deg, ref_lat):
    lat_m = lat_deg * 111_320.0
    lon_m = lon_deg * 111_320.0 * math.cos(math.radians(ref_lat))
    return math.sqrt(lon_m ** 2 + lat_m ** 2)


def run_clipped_dp(nodes, edges, coords, adj, snapshot,
                    epsilon=1.0, r_max=1000.0, seed=42):
    rng = np.random.RandomState(seed)

    # Compute sensitivity: grid spacing (average edge length)
    total_dist = sum(e["distance"] for e in edges)
    sensitivity_m = total_dist / max(len(edges), 1)  # avg edge length

    results = []
    for dev_id, true_node in snapshot.items():
        true_lon, true_lat = coords[true_node]

        # Laplace scale in metres
        scale_m = sensitivity_m / epsilon

        # Draw Laplace noise in metres
        noise_lon_m = rng.laplace(0, scale_m)
        noise_lat_m = rng.laplace(0, scale_m)

        # Compute noise magnitude
        noise_magnitude = math.sqrt(noise_lon_m ** 2 + noise_lat_m ** 2)

        # CLIP noise if r_max is set
        clipped = False
        if r_max is not None and noise_magnitude > r_max:
            clip_factor = r_max / noise_magnitude
            noise_lon_m *= clip_factor
            noise_lat_m *= clip_factor
            noise_magnitude = r_max
            clipped = True

        # Convert noise from metres to degrees
        lon_offset, lat_offset = _metres_to_degrees(
            abs(noise_lon_m), true_lat
        ), _metres_to_degrees(abs(noise_lat_m), true_lat)

        # Properly handle signs
        noisy_lon = true_lon + math.copysign(lon_offset[0], noise_lon_m)
        noisy_lat = true_lat + math.copysign(_metres_to_degrees(abs(noise_lat_m), true_lat)[1], noise_lat_m)

        # Project to nearest graph node
        projected_node, proj_dist = nearest_node(noisy_lon, noisy_lat, coords)

        # Total location error: true node -> projected node
        loc_error = haversine_m(
            true_lon, true_lat,
            coords[projected_node][0], coords[projected_node][1],
        )

        results.append({
            "device_id": dev_id,
            "true_node": true_node,
            "reported_node": projected_node,
            "location_error": round(loc_error, 2),
            "noise_magnitude_m": round(noise_magnitude, 2),
            "clipped": clipped,
            "epsilon": epsilon,
            "available": True,  # DP always produces a report
        })

    return results


def run_base_dp(nodes, edges, coords, adj, snapshot, epsilon=1.0, seed=42):
    return run_clipped_dp(
        nodes, edges, coords, adj, snapshot,
        epsilon=epsilon, r_max=None, seed=seed
    )
