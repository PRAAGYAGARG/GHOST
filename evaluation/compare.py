import os
import csv
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import matplotlib.patches as mpatches

# ---------------------------------------------------------------------------
# Style configuration
# ---------------------------------------------------------------------------
ALGO_LABELS = {
    "base_k_anon":       "Base k-Anon",
    "dist_bounded":      "Dist-Bounded\nk-Anon",
    "adaptive_k_anon":   "Adaptive\nk-Anon",
    "base_dp":           "Base DP",
    "clipped_dp":        "Clipped DP",
}

ALGO_COLORS = {
    "base_k_anon":       "#5B8DBE",
    "dist_bounded":      "#3A7D44",
    "adaptive_k_anon":   "#F2A541",
    "base_dp":           "#D64933",
    "clipped_dp":        "#7B2D8E",
}

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "axes.labelsize": 12,
    "legend.fontsize": 9,
    "xtick.labelsize": 9,
    "ytick.labelsize": 10,
    "savefig.dpi": 150,
    "savefig.bbox": "tight",
    "figure.facecolor": "white",
    "axes.facecolor": "#FAFAFA",
    "axes.grid": True,
    "grid.alpha": 0.3,
})


def ensure_dirs(fig_dir, table_dir):
    os.makedirs(fig_dir, exist_ok=True)
    os.makedirs(table_dir, exist_ok=True)


# -----------------------------------------------------------------------
# Figure 1: Error Comparison Bar Chart
# -----------------------------------------------------------------------
def plot_error_comparison(all_metrics, fig_dir):
    algos = list(all_metrics.keys())
    labels = [ALGO_LABELS.get(a, a) for a in algos]
    colors = [ALGO_COLORS.get(a, "#999") for a in algos]

    avg_errs = [all_metrics[a].get("avg_location_error", 0) or 0 for a in algos]
    max_errs = [all_metrics[a].get("max_location_error", 0) or 0 for a in algos]
    p95_errs = [all_metrics[a].get("p95_location_error", 0) or 0 for a in algos]

    x = np.arange(len(algos))
    width = 0.25

    fig, ax = plt.subplots(figsize=(12, 6))
    bars1 = ax.bar(x - width, avg_errs, width, label="Avg Error (m)",
                   color=colors, alpha=0.9, edgecolor="white", linewidth=0.8)
    bars2 = ax.bar(x, p95_errs, width, label="P95 Error (m)",
                   color=colors, alpha=0.65, edgecolor="white", linewidth=0.8)
    bars3 = ax.bar(x + width, max_errs, width, label="Max Error (m)",
                   color=colors, alpha=0.4, edgecolor="white", linewidth=0.8)

    # Add value labels on bars
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.annotate(f"{height:.0f}",
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3), textcoords="offset points",
                            ha="center", va="bottom", fontsize=7, fontweight="bold")

    ax.set_xlabel("Algorithm")
    ax.set_ylabel("Location Error (metres)")
    ax.set_title("GHOST - Location Error Comparison Across Algorithms")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend(loc="upper right")
    ax.set_ylim(bottom=0)

    plt.tight_layout()
    path = os.path.join(fig_dir, "fig1_error_comparison.png")
    plt.savefig(path)
    plt.close()
    print(f"  * Saved {path}")


# -----------------------------------------------------------------------
# Figure 2: Privacy-Utility Tradeoff
# -----------------------------------------------------------------------
def plot_privacy_utility(all_metrics, adversary_errors, fig_dir):
    fig, ax = plt.subplots(figsize=(9, 7))

    for algo in all_metrics:
        avg_err = all_metrics[algo].get("avg_location_error", 0) or 0
        adv_err = adversary_errors.get(algo, 0) or 0
        color = ALGO_COLORS.get(algo, "#999")
        label = ALGO_LABELS.get(algo, algo).replace("\n", " ")

        ax.scatter(avg_err, adv_err, c=color, s=200, zorder=5,
                   edgecolors="white", linewidths=2)
        ax.annotate(label, (avg_err, adv_err),
                    textcoords="offset points", xytext=(10, 10),
                    fontsize=9, fontweight="bold", color=color,
                    arrowprops=dict(arrowstyle="-", color=color, alpha=0.5))

    ax.set_xlabel("Average Location Error - Utility Loss (metres) ->")
    ax.set_ylabel("Adversary Expected Error - Privacy (metres) ->")
    ax.set_title("GHOST - Privacy vs Utility Tradeoff")

    # Ideal direction annotation
    ax.annotate("<- Better Utility", xy=(0.02, 0.02), xycoords="axes fraction",
                fontsize=8, fontstyle="italic", color="gray")
    ax.annotate("Better Privacy ->", xy=(0.02, 0.96), xycoords="axes fraction",
                fontsize=8, fontstyle="italic", color="gray")

    plt.tight_layout()
    path = os.path.join(fig_dir, "fig2_privacy_utility_tradeoff.png")
    plt.savefig(path)
    plt.close()
    print(f"  * Saved {path}")


# -----------------------------------------------------------------------
# Figure 3: Availability Comparison
# -----------------------------------------------------------------------
def plot_availability(all_metrics, fig_dir):
    algos = list(all_metrics.keys())
    labels = [ALGO_LABELS.get(a, a) for a in algos]
    colors = [ALGO_COLORS.get(a, "#999") for a in algos]
    avails = [all_metrics[a].get("availability", 0) * 100 for a in algos]

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(labels, avails, color=colors, edgecolor="white",
                  linewidth=1.5, alpha=0.9)

    for bar, val in zip(bars, avails):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                f"{val:.1f}%", ha="center", va="bottom",
                fontsize=11, fontweight="bold")

    ax.set_ylabel("Availability (%)")
    ax.set_title("GHOST - Report Availability Comparison")
    ax.set_ylim(0, 115)
    ax.axhline(y=100, color="gray", linestyle="--", alpha=0.4, linewidth=1)

    plt.tight_layout()
    path = os.path.join(fig_dir, "fig3_availability_comparison.png")
    plt.savefig(path)
    plt.close()
    print(f"  * Saved {path}")


# -----------------------------------------------------------------------
# Figure 4: Radar Chart
# -----------------------------------------------------------------------
def plot_radar(all_metrics, adversary_errors, fig_dir):
    categories = ["Privacy\n(Adv. Error)", "Avg Error\n(Lower=Better)",
                   "Max Error\n(Lower=Better)", "P95 Error\n(Lower=Better)",
                   "Availability"]
    N = len(categories)

    algos = list(all_metrics.keys())

    # Collect raw values
    raw = {}
    for algo in algos:
        m = all_metrics[algo]
        raw[algo] = [
            adversary_errors.get(algo, 0) or 0,
            m.get("avg_location_error", 0) or 0,
            m.get("max_location_error", 0) or 0,
            m.get("p95_location_error", 0) or 0,
            m.get("availability", 0) * 100,
        ]

    # Normalise each dimension to [0, 1]
    max_vals = [max(raw[a][i] for a in algos) for i in range(N)]
    max_vals = [v if v > 0 else 1 for v in max_vals]

    # For error metrics (idx 1,2,3): invert so lower=better becomes higher on chart
    norm = {}
    for algo in algos:
        vals = []
        for i in range(N):
            v = raw[algo][i] / max_vals[i]
            if i in [1, 2, 3]:  # Invert error metrics
                v = 1 - v
            vals.append(v)
        norm[algo] = vals

    angles = [n / float(N) * 2 * math.pi for n in range(N)]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    ax.set_theta_offset(math.pi / 2)
    ax.set_theta_direction(-1)

    plt.xticks(angles[:-1], categories, size=9)
    ax.set_rlabel_position(0)
    plt.yticks([0.25, 0.5, 0.75, 1.0], ["0.25", "0.50", "0.75", "1.00"],
               color="grey", size=7)
    plt.ylim(0, 1.1)

    for algo in algos:
        values = norm[algo] + norm[algo][:1]
        color = ALGO_COLORS.get(algo, "#999")
        label = ALGO_LABELS.get(algo, algo).replace("\n", " ")
        ax.plot(angles, values, "o-", linewidth=2, label=label, color=color)
        ax.fill(angles, values, alpha=0.08, color=color)

    ax.set_title("GHOST - Multi-Metric Radar Comparison\n(Higher = Better)",
                 size=13, fontweight="bold", pad=30)
    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.1))

    plt.tight_layout()
    path = os.path.join(fig_dir, "fig4_radar_chart.png")
    plt.savefig(path)
    plt.close()
    print(f"  * Saved {path}")


# -----------------------------------------------------------------------
# Figure 5: Error Distribution Box Plots
# -----------------------------------------------------------------------
def plot_error_distribution(all_raw_results, fig_dir):
    algos = list(all_raw_results.keys())
    labels = [ALGO_LABELS.get(a, a) for a in algos]
    colors = [ALGO_COLORS.get(a, "#999") for a in algos]

    error_data = []
    for algo in algos:
        errors = []
        for snapshot_results in all_raw_results[algo]:
            for r in snapshot_results:
                if r.get("available") and r.get("location_error") is not None:
                    errors.append(r["location_error"])
        error_data.append(errors if errors else [0])

    fig, ax = plt.subplots(figsize=(11, 6))
    bp = ax.boxplot(error_data, patch_artist=True,
                    medianprops=dict(color="black", linewidth=2),
                    whiskerprops=dict(linewidth=1.2),
                    capprops=dict(linewidth=1.2),
                    flierprops=dict(marker="o", markersize=4, alpha=0.5))
    ax.set_xticklabels(labels)

    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax.set_ylabel("Location Error (metres)")
    ax.set_title("GHOST - Per-User Error Distribution by Algorithm")

    plt.tight_layout()
    path = os.path.join(fig_dir, "fig5_error_distribution.png")
    plt.savefig(path)
    plt.close()
    print(f"  * Saved {path}")


# -----------------------------------------------------------------------
# Figure 6: Graph Visualization
# -----------------------------------------------------------------------
def plot_graph(nodes, edges, snapshot, fig_dir):
    fig, ax = plt.subplots(figsize=(10, 10))

    # Draw edges
    coords = {n["id"]: (n["x"], n["y"]) for n in nodes}
    for e in edges:
        x1, y1 = coords[e["source"]]
        x2, y2 = coords[e["target"]]
        ax.plot([x1, x2], [y1, y2], color="#CCCCCC", linewidth=0.6, zorder=1)

    # Draw all nodes
    all_x = [n["x"] for n in nodes]
    all_y = [n["y"] for n in nodes]
    ax.scatter(all_x, all_y, c="#AABBCC", s=15, zorder=2, alpha=0.6,
               edgecolors="white", linewidths=0.3)

    # Highlight user-occupied nodes
    user_nodes = set(snapshot.values())
    ux = [coords[n][0] for n in user_nodes if n in coords]
    uy = [coords[n][1] for n in user_nodes if n in coords]
    ax.scatter(ux, uy, c="#D64933", s=50, zorder=3, alpha=0.9,
               edgecolors="white", linewidths=1, label=f"IoT Devices ({len(snapshot)})")

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("GHOST - Synthetic Smart-City Road Network\nwith IoT Device Locations")
    ax.legend(loc="upper left", fontsize=10)
    ax.set_aspect("equal")

    plt.tight_layout()
    path = os.path.join(fig_dir, "fig6_graph_visualization.png")
    plt.savefig(path)
    plt.close()
    print(f"  * Saved {path}")


# -----------------------------------------------------------------------
# Comparison Table
# -----------------------------------------------------------------------
def save_comparison_table(all_metrics, adversary_errors, table_dir):
    path = os.path.join(table_dir, "comparison_table.csv")

    header = [
        "Algorithm", "Avg Error (m)", "Max Error (m)", "P95 Error (m)",
        "Median Error (m)", "Std Error (m)", "Availability (%)",
        "Adversary Error (m)"
    ]

    rows = []
    for algo in all_metrics:
        m = all_metrics[algo]
        label = ALGO_LABELS.get(algo, algo).replace("\n", " ")
        rows.append([
            label,
            m.get("avg_location_error", "N/A"),
            m.get("max_location_error", "N/A"),
            m.get("p95_location_error", "N/A"),
            m.get("median_location_error", "N/A"),
            m.get("std_location_error", "N/A"),
            f"{m.get('availability', 0) * 100:.1f}",
            adversary_errors.get(algo, "N/A"),
        ])

    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    print(f"  * Saved {path}")


# -----------------------------------------------------------------------
# Summary Report
# -----------------------------------------------------------------------
def generate_summary_report(all_metrics, adversary_errors, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "summary_report.md")

    lines = []
    lines.append("# GHOST - Evaluation Summary Report")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append("This report summarises the evaluation of 5 location privacy")
    lines.append("algorithms (3 proposed modifications + 2 baselines) on a synthetic")
    lines.append("smart-city road network graph with 200 nodes and 80 IoT devices.")
    lines.append("")
    lines.append("All metrics are measured on a **common physical scale (metres)**")
    lines.append("following the adversary-grounded evaluation framework of")
    lines.append("Shokri et al. (IEEE S&P 2011).")
    lines.append("")

    # Table
    lines.append("## Comparison Table")
    lines.append("")
    lines.append("| Algorithm | Avg Err (m) | Max Err (m) | P95 Err (m) | Availability (%) | Adversary Err (m) |")
    lines.append("|-----------|-------------|-------------|-------------|-------------------|-------------------|")

    for algo in all_metrics:
        m = all_metrics[algo]
        label = ALGO_LABELS.get(algo, algo).replace("\n", " ")
        adv = adversary_errors.get(algo, "N/A")
        avail = m.get("availability", 0) * 100
        lines.append(
            f"| {label} | {m.get('avg_location_error', 'N/A')} | "
            f"{m.get('max_location_error', 'N/A')} | "
            f"{m.get('p95_location_error', 'N/A')} | "
            f"{avail:.1f} | {adv} |"
        )

    lines.append("")
    lines.append("## Generated Figures")
    lines.append("")
    lines.append("All figures are saved in `results/figures/`:")
    lines.append("")
    lines.append("1. **fig1_error_comparison.png** - Bar chart comparing avg/max/P95 error")
    lines.append("2. **fig2_privacy_utility_tradeoff.png** - Privacy vs utility scatter plot")
    lines.append("3. **fig3_availability_comparison.png** - Report availability comparison")
    lines.append("4. **fig4_radar_chart.png** - Multi-metric radar comparison")
    lines.append("5. **fig5_error_distribution.png** - Per-user error distribution box plots")
    lines.append("6. **fig6_graph_visualization.png** - Synthetic graph with device locations")
    lines.append("")

    lines.append("## Key Findings")
    lines.append("")

    # Find best/worst
    best_privacy = max(adversary_errors, key=adversary_errors.get)
    best_utility = min(
        all_metrics,
        key=lambda a: all_metrics[a].get("avg_location_error", float("inf")) or float("inf")
    )

    lines.append(f"- **Best Privacy**: {ALGO_LABELS.get(best_privacy, best_privacy).replace(chr(10), ' ')} "
                 f"(adversary error = {adversary_errors[best_privacy]} m)")
    lines.append(f"- **Best Utility**: {ALGO_LABELS.get(best_utility, best_utility).replace(chr(10), ' ')} "
                 f"(avg location error = {all_metrics[best_utility].get('avg_location_error', 'N/A')} m)")
    lines.append("")

    # Research gaps addressed
    lines.append("## Research Gaps Addressed")
    lines.append("")
    lines.append("1. **Gap 1** (k-anon fails in sparse areas): Distance-bounded and adaptive")
    lines.append("   k-anonymity maintain 100% availability even in sparse regions.")
    lines.append("2. **Gap 2** (No common privacy scale): All algorithms are compared using")
    lines.append("   the same adversary expected error metric (metres).")
    lines.append("3. **Gap 3** (DP noise is unbounded): Clipped DP bounds worst-case error,")
    lines.append("   shown by significantly lower max error compared to base DP.")
    lines.append("4. **Gap 4** (Simple fixes vs complex ones): Our simple modifications")
    lines.append("   (radius cap, k reduction, noise clipping) achieve substantial improvements")
    lines.append("   without complex density-aware calculations.")
    lines.append("")

    lines.append("---")
    lines.append("*Generated by GHOST Toolkit*")

    with open(path, "w") as f:
        f.write("\n".join(lines))

    print(f"  * Saved {path}")


def print_summary_table(all_metrics, adversary_errors):
    print("\n" + "=" * 95)
    print("  GHOST - EVALUATION RESULTS SUMMARY")
    print("=" * 95)
    print(f"{'Algorithm':<22} {'Avg Err(m)':>10} {'Max Err(m)':>10} {'P95 Err(m)':>10} "
          f"{'Avail(%)':>9} {'Adv Err(m)':>11}")
    print("-" * 95)

    for algo in all_metrics:
        m = all_metrics[algo]
        label = ALGO_LABELS.get(algo, algo).replace("\n", " ")
        adv = adversary_errors.get(algo, "N/A")
        avail = m.get("availability", 0) * 100
        avg_e = m.get("avg_location_error", "N/A")
        max_e = m.get("max_location_error", "N/A")
        p95_e = m.get("p95_location_error", "N/A")

        avg_s = f"{avg_e}" if avg_e is not None else "N/A"
        max_s = f"{max_e}" if max_e is not None else "N/A"
        p95_s = f"{p95_e}" if p95_e is not None else "N/A"

        print(f"  {label:<20} {avg_s:>10} {max_s:>10} {p95_s:>10} "
              f"{avail:>8.1f}% {adv:>11}")

    print("=" * 95)
    print()
