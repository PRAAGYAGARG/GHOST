# GHOST: Graph-based Heuristic Obfuscation and Security Toolkit

> **A Benchmark Toolkit for Graph-Based Location Privacy Algorithms for the Design of Smart City IoT Networks**

## Team Members

| Name | Registration No. |
|------|-----------------|
| Praagya Garg | 23BCT0016 |
| Himacharan Reddy | 23BCT0114 |
| Sujal G M | 23BCT0058 |

---

## What is GHOST?

GHOST is a Python toolkit that benchmarks **3 graph-based location privacy algorithms** on a synthetic smart-city road network. It measures how well each algorithm protects user locations from an adversary, while tracking how much useful information is lost in the process.

**In simple terms:** Smart city IoT devices (sensors, phones, etc.) constantly share their locations. This is useful for traffic management, safety, etc., but also risky — someone could track you. GHOST tests different ways to hide your location and tells you which method works best.

---

## The 3 Algorithms We Implement

### Algorithm 1: Distance-Bounded k-Anonymity
- **What it does:** Searches nearby graph nodes to find at least `k` other users, so your location gets hidden among them. BUT it stops searching after a maximum radius (`r_max`), even if it hasn't found `k` users yet.
- **Why it's better than base k-anonymity:** Base k-anonymity has NO distance limit — in sparse areas, the search goes very far, producing huge errors. Or it fails entirely and drops the report. Distance-bounded always reports *something*, with bounded error.
- **Parameters:** `k=5` (target anonymity set), `r_max=1500m` (maximum search radius)

### Algorithm 2: Adaptive k-Anonymity with Hysteresis
- **What it does:** Starts searching for `k` users. If it can't find `k` within the radius cap, it tries `k-1`, then `k-2`, all the way down to `k_min`. Reports the medoid as soon as ANY reduced target is met.
- **Why it's better:** Base k-anonymity drops the entire report if `k` users aren't found. This version almost never drops — availability goes way up.
- **Parameters:** `k=5` (target), `k_min=2` (minimum acceptable), `r_max=1500m`

### Algorithm 3: Clipped-Noise Differential Privacy (Bounded Laplace)
- **What it does:** Adds random Laplace noise to your coordinates (standard DP), BUT clips the noise so it never exceeds `r_max` metres. Then maps the noisy point to the nearest road-network node.
- **Why it's better:** Standard DP has unbounded noise — occasionally the noisy point ends up kilometres away. Clipping ensures the worst-case error is bounded.
- **Parameters:** `ε=1.0` (privacy budget), `r_max=1000m` (max noise radius)
- **Limitation:** The formal ε-DP guarantee is weakened by clipping (stated explicitly).

### Baseline 1: Base k-Anonymity (Unbounded BFS)
- Standard BFS expansion with no radius cap. Fails (drops report) if `k` users aren't found.

### Baseline 2: Base Differential Privacy (Unbounded Laplace)
- Standard planar Laplace mechanism with no clipping. Noise can be arbitrarily large.

---

## How We Evaluate (Unified Metrics)

A key contribution is that **all algorithms are compared on the same physical scale (metres)**, unlike prior work where k-anonymity and DP used incompatible metrics.

| Metric | What It Measures |
|--------|-----------------|
| **Adversary Expected Error (m)** | How many metres off an optimal adversary's guess would be — this is our unified privacy metric. Higher = better privacy. |
| **Average Location Error (m)** | Mean distance between true and reported location. Lower = better utility. |
| **Max Location Error (m)** | Worst-case error for any single report. Lower = more consistent. |
| **P95 Location Error (m)** | 95th percentile error. Shows how bad it gets for most reports. |
| **Availability (%)** | Percentage of reports that were successfully generated (not dropped). Higher = better. |

---

## Folder Structure

```
GHOST/
├── README.md                          ← You are here
├── requirements.txt                   ← Python dependencies (numpy, matplotlib)
├── run_all.py                         ← Single-command entry point — run this!
│
├── data/                              ← Data generation
│   ├── generate_synthetic_data.py     ← Creates synthetic graph + device locations
│   ├── city_graph_nodes.json          ← (auto-generated) Graph nodes
│   ├── city_graph_edges.json          ← (auto-generated) Graph edges
│   └── device_snapshots.json          ← (auto-generated) Device location snapshots
│
├── algorithms/                        ← Privacy algorithm implementations
│   ├── __init__.py
│   ├── graph_utils.py                 ← Shared: BFS, Dijkstra, haversine, medoid
│   ├── base_k_anonymity.py            ← Baseline: unbounded k-anonymity
│   ├── distance_bounded_k_anonymity.py← Algo 1: radius-capped k-anonymity
│   ├── adaptive_k_anonymity.py        ← Algo 2: k-reduction with hysteresis
│   └── clipped_dp.py                  ← Algo 3: bounded Laplace DP + baseline DP
│
├── evaluation/                        ← Evaluation & visualization
│   ├── __init__.py
│   ├── metrics.py                     ← Privacy, utility, availability metrics
│   ├── adversary.py                   ← Optimal Bayesian adversary model
│   └── compare.py                     ← Cross-algorithm figures & tables
│
├── results/                           ← (auto-generated) Output directory
│   ├── figures/                       ← 6 comparison plots (PNG)
│   │   ├── fig1_error_comparison.png
│   │   ├── fig2_privacy_utility_tradeoff.png
│   │   ├── fig3_availability_comparison.png
│   │   ├── fig4_radar_chart.png
│   │   ├── fig5_error_distribution.png
│   │   └── fig6_graph_visualization.png
│   ├── tables/
│   │   └── comparison_table.csv       ← Full metrics CSV
│   └── raw_results.json               ← Raw metrics JSON
│
└── outputs/
    └── summary_report.md              ← Human-readable evaluation report
```

---

## Purpose of Each File

| File | Purpose |
|------|---------|
| `run_all.py` | **Main entry point.** Runs the entire pipeline: generate data → run algorithms → compute metrics → create figures/tables/report. This is the only file you need to run. |
| `data/generate_synthetic_data.py` | Creates a synthetic 200-node road network graph (modelling a ~5km × 5km Beijing city area) and places 80 IoT devices on it across 5 time snapshots. Uses density variation to simulate real-world sparse/dense areas. |
| `algorithms/graph_utils.py` | Shared utility functions: graph loading, BFS traversal, Dijkstra shortest paths, haversine distance, medoid computation, nearest-node projection. Used by all algorithms. |
| `algorithms/base_k_anonymity.py` | Baseline k-anonymity: expands BFS until k users found, fails if it can't. Demonstrates the availability problem in sparse areas. |
| `algorithms/distance_bounded_k_anonymity.py` | **Algorithm 1:** Adds a radius cap to BFS. Always reports (never drops). Bounds worst-case error. |
| `algorithms/adaptive_k_anonymity.py` | **Algorithm 2:** Retries with lower k values if target k can't be met. Maximises availability while maintaining reasonable privacy. |
| `algorithms/clipped_dp.py` | **Algorithm 3:** Clips Laplace noise to a maximum radius. Also includes the unbounded DP baseline for comparison. |
| `evaluation/metrics.py` | Computes standardised metrics (avg/max/P95/median error, availability) on a common physical scale. |
| `evaluation/adversary.py` | Implements an optimal Bayesian adversary that estimates how well it can guess true locations — the unified privacy metric. |
| `evaluation/compare.py` | Generates 6 publication-quality comparison figures, a CSV table, and a Markdown summary report. |

---

## How to Run

### Prerequisites
- **Python 3.8+** (tested with Python 3.10+)
- **pip** (Python package manager)

### Step 1: Install Dependencies

```bash
cd GHOST
pip install -r requirements.txt
```

This installs:
- `numpy` — numerical operations
- `matplotlib` — figure generation

### Step 2: Run Everything

```bash
python run_all.py
```

That's it! One command runs the entire pipeline.

### What Happens When You Run It

1. **Data Generation** (~1 sec): Creates synthetic graph and device snapshots
2. **Algorithm Execution** (~5-10 sec): Runs all 5 algorithms on all snapshots
3. **Metric Computation** (~2 sec): Computes unified evaluation metrics
4. **Output Generation** (~3 sec): Creates all figures, tables, and report

**Total runtime: ~15-20 seconds**

---

## What Outputs You Will See

### Console Output
A nicely formatted progress log followed by a summary table:

```
╔══════════════════════════════════════════════════════════════╗
║  GHOST: Graph-based Heuristic Obfuscation & Security Toolkit ║
╚══════════════════════════════════════════════════════════════╝

  STEP 1/4 — Generating Synthetic Data
  ...
  STEP 2/4 — Running Privacy Algorithms
  ...

===============================================================================
  GHOST — EVALUATION RESULTS SUMMARY
===============================================================================
Algorithm              Avg Err(m)  Max Err(m)  P95 Err(m)  Avail(%)  Adv Err(m)
-------------------------------------------------------------------------------
  Base k-Anon              ...         ...         ...        XX.X%        ...
  Dist-Bounded k-Anon      ...         ...         ...       100.0%        ...
  Adaptive k-Anon          ...         ...         ...       100.0%        ...
  Base DP                  ...         ...         ...       100.0%        ...
  Clipped DP               ...         ...         ...       100.0%        ...
===============================================================================
```

### Generated Figures (in `results/figures/`)

| Figure | What It Shows |
|--------|--------------|
| `fig1_error_comparison.png` | Bar chart comparing average, P95, and maximum location error across all 5 algorithms |
| `fig2_privacy_utility_tradeoff.png` | Scatter plot showing the fundamental tradeoff — privacy (adversary error) on Y-axis vs utility loss (location error) on X-axis |
| `fig3_availability_comparison.png` | Bar chart showing what percentage of reports each algorithm successfully generates |
| `fig4_radar_chart.png` | Spider/radar chart showing all 5 metrics for all algorithms on a single normalised scale |
| `fig5_error_distribution.png` | Box plots showing the distribution of per-user errors — reveals outliers and consistency |
| `fig6_graph_visualization.png` | The synthetic road network with IoT device positions marked in red |

### Tables (in `results/tables/`)
- `comparison_table.csv` — Full metrics comparison in CSV format

### Report (in `outputs/`)
- `summary_report.md` — Human-readable Markdown report with findings and interpretation

---

## Research Gaps Addressed

| Gap | Problem | Our Solution |
|-----|---------|-------------|
| **Gap 1** | k-anonymity fails completely when < k users nearby | Distance-bounded and adaptive variants always report, never fail |
| **Gap 2** | No way to compare k-anonymity and DP on same scale | Unified adversary expected error metric (metres) for all algorithms |
| **Gap 3** | DP noise is unbounded → occasional wild errors | Clipped DP bounds worst-case error to r_max metres |
| **Gap 4** | No evidence that simple fixes work as well as complex ones | Our single-parameter modifications achieve substantial improvements |

---

## Base Paper

**Title:** A Privacy-Preserving Location Data Collection Framework for IoT-Based Smart Cities  
**Journal:** Elsevier — Computer Networks (2024)  
**Link:** [https://www.sciencedirect.com/science/article/pii/S1570870524001434](https://www.sciencedirect.com/science/article/pii/S1570870524001434)

---

## Key References

1. L. Sweeney (2002). *k-Anonymity: A Model for Protecting Privacy.* Int. J. Uncertainty, Fuzziness and Knowledge-Based Systems.
2. M. F. Mokbel, C.-Y. Chow, W. G. Aref (2006). *The New Casper.* Proc. VLDB.
3. C. Dwork, F. McSherry, K. Nissim, A. Smith (2006). *Calibrating Noise to Sensitivity in Private Data Analysis.* Proc. TCC.
4. M. E. Andrés, N. E. Bordenabe, K. Chatzikokolakis, C. Palamidessi (2013). *Geo-Indistinguishability.* Proc. ACM CCS.
5. R. Shokri, G. Theodorakopoulos, J.-Y. Le Boudec, J.-P. Hubaux (2011). *Quantifying Location Privacy.* IEEE S&P.

---

*Built with Python • NumPy • Matplotlib*
