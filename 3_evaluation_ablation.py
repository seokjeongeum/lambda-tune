#!/usr/bin/env python3
import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

# Increase global font sizes for clarity by 1.5x (original values multiplied by 1.5)
plt.rcParams.update(
    {
        "font.size": 21,  # Original 14 x 1.5
        "axes.titlesize": 27,  # Original 18 x 1.5
        "axes.labelsize": 24,  # Original 16 x 1.5
        "xtick.labelsize": 21,  # Original 14 x 1.5
        "ytick.labelsize": 21,  # Original 14 x 1.5
        "legend.fontsize": 21,  # Original 14 x 1.5
    }
)

# Define benchmarks and file paths for the JSON reports
benchmarks = ["JOB", "TPCDS", "TPCH"]
benchmark_display_map = {"JOB": "JOB", "TPCDS": "TPC-DS", "TPCH": "TPC-H"}
# Define methods and their corresponding path templates and display names
methods = {
    "ours": {
        "path_template": "test/1_main/{benchmark}/ours/reports.json",
        "display_name": "+Proactive\nIndex Utilization\n+Cost-Based\nQuery Prioritization",
    },
    "exploit_index_ablated": {
        "path_template": "test/3_evaluation_ablation/{benchmark}/exploit_index_ablated/reports.json",
        "display_name": "+Cost-Based\nQuery Prioritization",
    },
    "ei_oq_ablated": {
        "path_template": "test/3_evaluation_ablation/{benchmark}/ei_oq_ablated/reports.json",
        "display_name": r"$\lambda$-Tune",
    },
}

# Generate file paths and display names programmatically
file_paths = {benchmark: [] for benchmark in benchmarks}
display_names = {}

for benchmark in benchmarks:
    for method_info in methods.values():
        path = method_info["path_template"].format(benchmark=benchmark.lower())
        file_paths[benchmark].append(path)
        display_names[path] = method_info["display_name"]


# Load and merge the data from all JSON files
data = []
for benchmark, paths in file_paths.items():
    for fp in paths:
        if os.path.exists(fp):
            with open(fp, "r") as f:
                reports = json.load(f)
                # Tag each report with benchmark and file
                for report in reports:
                    report["benchmark"] = benchmark
                    report["file"] = fp
                data.extend(reports)
        else:
            print(f"Warning: File {fp} not found.")

# Create DataFrame and ensure required columns exist
df = pd.DataFrame(data)
required_columns = [
    "round_index_creation_time",
    "round_query_execution_time",  # Added query execution time
    "duration_seconds",
    "file",
    "benchmark",
]
for col in required_columns:
    if col not in df.columns:
        # Handle missing columns - assign 0 or raise error
        print(f"Warning: Column '{col}' not found. Assigning 0.")
        df[col] = 0
        # Alternatively, raise ValueError:
        # raise ValueError(f"Missing required column: {col}")

# Convert relevant columns to numeric, coercing errors
numeric_cols = [
    "round_index_creation_time",
    "round_query_execution_time",
    "duration_seconds",
]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Create a new column 'source' using the display_names mapping
df["source"] = df["file"].apply(lambda fp: display_names.get(fp, fp))

# Drop rows where essential numeric columns became NaN after conversion
df.dropna(subset=numeric_cols, inplace=True)

# Group data:
# Total time: use the last reported value per (benchmark, source)
total_time_grouped = (
    df.groupby(["benchmark", "source"]).last()["duration_seconds"].unstack(fill_value=0)
)
# Index creation time: sum over rounds per (benchmark, source)
index_time_grouped = (
    df.groupby(["benchmark", "source"])["round_index_creation_time"]
    .sum()
    .unstack(fill_value=0)
)
# Query execution time: sum over rounds per (benchmark, source) - NEW
query_time_grouped = (
    df.groupby(["benchmark", "source"])["round_query_execution_time"]
    .sum()
    .unstack(fill_value=0)
)


# Order benchmarks and sources
sources_order = [r"$\lambda$-Tune", "+Cost-Based\nQuery Prioritization", "+Proactive\nIndex Utilization\n+Cost-Based\nQuery Prioritization"]
total_time_grouped = total_time_grouped.reindex(benchmarks).reindex(
    columns=sources_order, fill_value=0
)
index_time_grouped = index_time_grouped.reindex(benchmarks).reindex(
    columns=sources_order, fill_value=0
)
query_time_grouped = query_time_grouped.reindex(benchmarks).reindex(  # NEW
    columns=sources_order, fill_value=0
)

# Calculate remaining (other) time - Optional, calculated but not plotted directly
other_time_grouped = total_time_grouped - index_time_grouped - query_time_grouped

# Print data that are plotted:
print("Time Breakdown Across Benchmarks and Sources:")
print("\nTotal Duration (Last Value):")
print(total_time_grouped)
print("\nIndex Creation Time (Sum):")
print(index_time_grouped)
print("\nQuery Execution Time (Sum):")  # Changed printout
print(query_time_grouped)
print("\nOther Time (Calculated):")  # Keep for reference
print(other_time_grouped)


# Define color mappings for the methods
color_mapping = {
    "+Proactive\nIndex Utilization\n+Cost-Based\nQuery Prioritization": ("#1f77b4", "#005792"),
    "+Cost-Based\nQuery Prioritization": ("#ff7f0e", "#d35400"),
    r"$\lambda$-Tune": ("#d62728", "#8b0000"),
}

# Create vertical subplots
fig, axes = plt.subplots(
    nrows=len(benchmarks), ncols=1, figsize=(10, 4.5 * len(benchmarks)), sharex=True
)
if len(benchmarks) == 1:
    axes = [axes]  # Ensure axes is iterable

for i, (ax, benchmark) in enumerate(zip(axes, benchmarks)):
    x = np.arange(len(sources_order))
    total_duration_vals = total_time_grouped.loc[benchmark].values
    index_vals = index_time_grouped.loc[benchmark].values
    query_vals = query_time_grouped.loc[benchmark].values

    bar_width = 0.5

    # Plot stacked bars for each source
    for j, source in enumerate(sources_order):
        index_color, query_color = color_mapping[source]
        # Plot Index Creation Time
        ax.bar(x[j], index_vals[j], width=bar_width, color=index_color)
        # Plot Query Execution Time on top
        ax.bar(
            x[j],
            query_vals[j],
            width=bar_width,
            bottom=index_vals[j],
            color=query_color,
        )

    max_y_val = max(total_duration_vals) if total_duration_vals.size > 0 else 1

    # Annotate each bar
    for j, (idx_time, total_dur) in enumerate(
        zip(index_vals, total_duration_vals)
    ):
        # Annotate Index Creation Time above its bar segment
        ax.text(
            j,
            idx_time,
            f"{int(idx_time)}s",
            ha="center",
            va="bottom",
            color="black",
            fontsize=16,
        )
        # Annotate Total Duration on top of the whole bar
        ax.text(
            j,
            total_dur,
            f"{int(total_dur)}s",
            ha="center",
            va="bottom",
            color="black",
            fontsize=16,
            fontweight="bold",
        )

    ax.set_title(
        f"{benchmark_display_map.get(benchmark, benchmark.upper())} Benchmark", pad=20
    )
    ax.set_xticks(x)
    # Use the full display names for the x-axis and rotate them
    if i == len(benchmarks) - 1:
        ax.set_xticklabels(sources_order, rotation=45, ha="right")
    else:
        ax.set_xticklabels([])
    if i == len(benchmarks) // 2:
        ax.set_ylabel("Time (Seconds)")
    ax.grid(axis="y", linestyle="--", alpha=0.7)
    ax.set_ylim(0, max_y_val * 1.3)

# Create a simplified global legend with distinct colors
legend_elements = [
    Patch(facecolor="#a9a9a9", label="Index Creation"),  # Light grey
    Patch(facecolor="#696969", label="Query Execution"),   # Dark grey
]
fig.legend(
    handles=legend_elements,
    loc="upper center",
    bbox_to_anchor=(0.5, 1.0),
    ncol=2,
    fontsize=21,
)

plt.tight_layout(rect=[0.02, 0.15, 0.98, 0.95])
plt.savefig("3_evaluation_ablation_comparison.png", bbox_inches="tight")
plt.savefig("3_evaluation_ablation_comparison.pdf", bbox_inches="tight")
plt.show()
