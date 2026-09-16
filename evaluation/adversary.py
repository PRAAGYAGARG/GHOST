import math
from collections import defaultdict
from algorithms.graph_utils import haversine_m


def compute_adversary_error(results, coords, snapshot):
    # Build the release distribution: P(reported | true)
    # Count how many times each (true_node, reported_node) pair appears
    release_counts = defaultdict(lambda: defaultdict(int))
    true_counts = defaultdict(int)

    available_results = [r for r in results if r.get("available", False)
                         and r.get("reported_node") is not None]

    if not available_results:
        return 0.0

    for r in available_results:
        true_n = r["true_node"]
        rep_n = r["reported_node"]
        release_counts[true_n][rep_n] += 1
        true_counts[true_n] += 1

    # Population prior: P(true = v)
    total_users = len(available_results)
    prior = {}
    for true_n, count in true_counts.items():
        prior[true_n] = count / total_users

    # For each released location o, compute adversary's best guess
    # and the resulting error
    # Group results by reported_node
    by_reported = defaultdict(list)
    for r in available_results:
        by_reported[r["reported_node"]].append(r)

    total_error = 0.0
    total_count = 0

    for reported_node, reports in by_reported.items():
        # Posterior: P(true = v | reported = o) for each possible true node
        posterior = {}
        for true_n in true_counts:
            # Likelihood: P(reported = o | true = v)
            likelihood = release_counts[true_n].get(reported_node, 0) / max(true_counts[true_n], 1)
            posterior[true_n] = likelihood * prior[true_n]

        # Normalize
        total_post = sum(posterior.values())
        if total_post <= 0:
            continue

        for v in posterior:
            posterior[v] /= total_post

        # Adversary's MAP guess: argmax P(true | reported)
        best_guess = max(posterior, key=posterior.get)

        # For each actual true location that produced this reported location,
        # compute the error = distance(true, adversary_guess)
        for r in reports:
            true_n = r["true_node"]
            error = haversine_m(
                coords[true_n][0], coords[true_n][1],
                coords[best_guess][0], coords[best_guess][1],
            )
            total_error += error
            total_count += 1

    return round(total_error / max(total_count, 1), 2)


def compute_multi_snapshot_adversary_error(all_results, coords, snapshots):
    errors = []
    for results, snapshot in zip(all_results, snapshots):
        err = compute_adversary_error(results, coords, snapshot)
        errors.append(err)

    if not errors:
        return 0.0
    return round(sum(errors) / len(errors), 2)
