import os
import sys
import json
import time

# Ensure the project root is on the Python path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from data.generate_synthetic_data import main as generate_data
from algorithms.graph_utils import load_graph
from algorithms.base_k_anonymity import run_base_k_anonymity
from algorithms.distance_bounded_k_anonymity import run_distance_bounded_k_anonymity
from algorithms.adaptive_k_anonymity import run_adaptive_k_anonymity
from algorithms.clipped_dp import run_clipped_dp, run_base_dp
from evaluation.metrics import compute_multi_snapshot_metrics
from evaluation.adversary import compute_multi_snapshot_adversary_error
from evaluation.compare import (
    ensure_dirs,
    plot_error_comparison,
    plot_privacy_utility,
    plot_availability,
    plot_radar,
    plot_error_distribution,
    plot_graph,
    save_comparison_table,
    generate_summary_report,
    print_summary_table,
)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DATA_DIR   = os.path.join(PROJECT_ROOT, "data")
FIG_DIR    = os.path.join(PROJECT_ROOT, "results", "figures")
TABLE_DIR  = os.path.join(PROJECT_ROOT, "results", "tables")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "outputs")

# Algorithm parameters
K_ANON_K     = 5        # Target k for k-anonymity variants
K_ANON_R_MAX = 1500.0   # Radius cap in metres
K_ANON_K_MIN = 2        # Minimum k for adaptive variant
DP_EPSILON   = 1.0      # Privacy budget for DP variants
DP_R_MAX     = 1000.0   # Noise clip radius for clipped DP


def main():
    start_time = time.time()

    print()
    print("=" * 64)
    print("|  GHOST: Graph-based Heuristic Obfuscation & Security Toolkit |")
    print("|  Benchmark for Location Privacy in Smart City IoT Networks   |")
    print("=" * 64)
    print()

    # ===================================================================
    # STEP 1: Generate synthetic data
    # ===================================================================
    print("-" * 64)
    print("  STEP 1/4 - Generating Synthetic Data")
    print("-" * 64)

    nodes, edges, snapshots = generate_data()

    # Load graph into structured format
    nodes_path = os.path.join(DATA_DIR, "city_graph_nodes.json")
    edges_path = os.path.join(DATA_DIR, "city_graph_edges.json")
    nodes, edges, coords, adj = load_graph(nodes_path, edges_path)

    # Load snapshots
    snapshots_path = os.path.join(DATA_DIR, "device_snapshots.json")
    with open(snapshots_path) as f:
        snapshots = json.load(f)

    print(f"  Graph: {len(nodes)} nodes, {len(edges)} edges")
    print(f"  Snapshots: {len(snapshots)} time steps, {len(snapshots[0])} devices each")
    print()

    # ===================================================================
    # STEP 2: Run all algorithms
    # ===================================================================
    print("-" * 64)
    print("  STEP 2/4 - Running Privacy Algorithms")
    print("-" * 64)
    print()

    all_raw_results = {}

    # --- Algorithm: Base k-Anonymity (Baseline) ---
    print(f"  [1/5] Base k-Anonymity (k={K_ANON_K}, unbounded)...")
    results_base_k = []
    for i, snap in enumerate(snapshots):
        r = run_base_k_anonymity(nodes, edges, coords, adj, snap, k=K_ANON_K)
        results_base_k.append(r)
    all_raw_results["base_k_anon"] = results_base_k
    print(f"        -> Done ({sum(len(r) for r in results_base_k)} reports)")

    # --- Algorithm 1: Distance-Bounded k-Anonymity ---
    print(f"  [2/5] Distance-Bounded k-Anonymity (k={K_ANON_K}, r_max={K_ANON_R_MAX}m)...")
    results_dist = []
    for i, snap in enumerate(snapshots):
        r = run_distance_bounded_k_anonymity(
            nodes, edges, coords, adj, snap,
            k=K_ANON_K, r_max=K_ANON_R_MAX
        )
        results_dist.append(r)
    all_raw_results["dist_bounded"] = results_dist
    print(f"        -> Done ({sum(len(r) for r in results_dist)} reports)")

    # --- Algorithm 2: Adaptive k-Anonymity ---
    print(f"  [3/5] Adaptive k-Anonymity (k={K_ANON_K}, k_min={K_ANON_K_MIN}, r_max={K_ANON_R_MAX}m)...")
    results_adaptive = []
    for i, snap in enumerate(snapshots):
        r = run_adaptive_k_anonymity(
            nodes, edges, coords, adj, snap,
            k=K_ANON_K, k_min=K_ANON_K_MIN, r_max=K_ANON_R_MAX
        )
        results_adaptive.append(r)
    all_raw_results["adaptive_k_anon"] = results_adaptive
    print(f"        -> Done ({sum(len(r) for r in results_adaptive)} reports)")

    # --- Algorithm: Base DP (Baseline) ---
    print(f"  [4/5] Base Differential Privacy (eps={DP_EPSILON}, unbounded)...")
    results_base_dp = []
    for i, snap in enumerate(snapshots):
        r = run_base_dp(nodes, edges, coords, adj, snap,
                        epsilon=DP_EPSILON, seed=42 + i)
        results_base_dp.append(r)
    all_raw_results["base_dp"] = results_base_dp
    print(f"        -> Done ({sum(len(r) for r in results_base_dp)} reports)")

    # --- Algorithm 3: Clipped DP ---
    print(f"  [5/5] Clipped-Noise DP (eps={DP_EPSILON}, r_max={DP_R_MAX}m)...")
    results_clipped = []
    for i, snap in enumerate(snapshots):
        r = run_clipped_dp(nodes, edges, coords, adj, snap,
                           epsilon=DP_EPSILON, r_max=DP_R_MAX, seed=42 + i)
        results_clipped.append(r)
    all_raw_results["clipped_dp"] = results_clipped
    print(f"        -> Done ({sum(len(r) for r in results_clipped)} reports)")

    print()

    # ===================================================================
    # STEP 3: Compute metrics
    # ===================================================================
    print("-" * 64)
    print("  STEP 3/4 - Computing Evaluation Metrics")
    print("-" * 64)
    print()

    all_metrics = {}
    adversary_errors = {}

    for algo_key, raw_results in all_raw_results.items():
        print(f"  Computing metrics for: {algo_key}...")
        metrics = compute_multi_snapshot_metrics(raw_results)
        all_metrics[algo_key] = metrics

        adv_err = compute_multi_snapshot_adversary_error(
            raw_results, coords, snapshots
        )
        adversary_errors[algo_key] = adv_err

    # Print summary table to console
    print_summary_table(all_metrics, adversary_errors)

    # ===================================================================
    # STEP 4: Generate outputs
    # ===================================================================
    print("-" * 64)
    print("  STEP 4/4 - Generating Figures, Tables & Report")
    print("-" * 64)
    print()

    ensure_dirs(FIG_DIR, TABLE_DIR)

    print("  Generating figures...")
    plot_error_comparison(all_metrics, FIG_DIR)
    plot_privacy_utility(all_metrics, adversary_errors, FIG_DIR)
    plot_availability(all_metrics, FIG_DIR)
    plot_radar(all_metrics, adversary_errors, FIG_DIR)
    plot_error_distribution(all_raw_results, FIG_DIR)
    plot_graph(nodes, edges, snapshots[0], FIG_DIR)

    print("\n  Generating tables...")
    save_comparison_table(all_metrics, adversary_errors, TABLE_DIR)

    print("\n  Generating summary report...")
    generate_summary_report(all_metrics, adversary_errors, OUTPUT_DIR)

    # Save raw results as JSON for reference
    results_json_path = os.path.join(PROJECT_ROOT, "results", "raw_results.json")
    serialisable = {}
    for algo, snapshots_results in all_raw_results.items():
        serialisable[algo] = {
            "metrics": all_metrics[algo],
            "adversary_error": adversary_errors[algo],
        }
    with open(results_json_path, "w") as f:
        json.dump(serialisable, f, indent=2)
    print(f"  * Saved {results_json_path}")

    elapsed = time.time() - start_time
    print()
    print("=" * 64)
    print(f"|  ALL DONE in {elapsed:.1f}s{' ' * (48 - len(f'{elapsed:.1f}'))}|")
    print("|                                                              |")
    print("|  Outputs:                                                    |")
    print("|    * results/figures/    -> 6 comparison plots               |")
    print("|    * results/tables/     -> CSV comparison table             |")
    print("|    * outputs/            -> Summary report (Markdown)        |")
    print("=" * 64)
    print()


if __name__ == "__main__":
    main()
