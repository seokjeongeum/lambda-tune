#!/usr/bin/env python3
import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

# Increase global font sizes for clarity by 1.5x (original values multiplied by 1.5)
plt.rcParams.update({
    'font.size': 21,          # Original 14 x 1.5
    'axes.titlesize': 27,     # Original 18 x 1.5
    'axes.labelsize': 24,     # Original 16 x 1.5
    'xtick.labelsize': 21,    # Original 14 x 1.5
    'ytick.labelsize': 21,    # Original 14 x 1.5
    'legend.fontsize': 21     # Original 14 x 1.5
})

# Define benchmarks and file paths for the JSON reports
benchmarks = ["TPC-H", "JOB", "TPC-DS"]
file_paths = {
    "TPC-H": [
        "test/s52/tpch/ours/reports.json",
        "test/s52/tpch/lambdatune/reports.json",
    ],
    "JOB": [
        "test/s52/job/ours/reports.json",
        "test/s52/job/lambdatune/reports.json",
    ],
    "TPC-DS": [
        "test/s52/tpcds/ours/reports.json",
        "test/s52/tpcds/lambdatune/reports.json",
    ],
}

# Mapping for nicer display names
display_names = {
    "test/s52/tpch/ours/reports.json": "Ours",
    "test/s52/tpch/lambdatune/reports.json": "λ-Tune",
    "test/s52/job/ours/reports.json": "Ours",
    "test/s52/job/lambdatune/reports.json": "λ-Tune",
    "test/s52/tpcds/ours/reports.json": "Ours",
    "test/s52/tpcds/lambdatune/reports.json": "λ-Tune",
}

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
    "duration_seconds",
    "file",
    "benchmark",
]
for col in required_columns:
    if col not in df.columns:
        df[col] = 0

# Create a new column 'source' using the display_names mapping
df["source"] = df["file"].apply(lambda fp: display_names.get(fp, fp))

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

# Order benchmarks and sources
sources_order = ["Ours", "λ-Tune"]
total_time_grouped = total_time_grouped.reindex(benchmarks).reindex(
    columns=sources_order, fill_value=0
)
index_time_grouped = index_time_grouped.reindex(benchmarks).reindex(
    columns=sources_order, fill_value=0
)

# Calculate remaining (other) time
remainder_grouped = total_time_grouped - index_time_grouped

# Print data that are plotted:
print("Time Breakdown Across Benchmarks and Sources:")
print("\nTotal Time Grouped:")
print(total_time_grouped)
print("\nIndex Creation Time Grouped:")
print(index_time_grouped)
print("\nRemaining (Other) Time Grouped:")
print(remainder_grouped)

# Define color mappings (saturated colors for clarity)
color_mapping_index = {"Ours": "#1f77b4", "λ-Tune": "#ff7f0e"}
color_mapping_other = {"Ours": "#005792", "λ-Tune": "#d35400"}

# Create vertical subplots (one for each benchmark) arranged horizontally.
fig, axes = plt.subplots(
    nrows=1, ncols=len(benchmarks), figsize=(6 * len(benchmarks), 6), sharey=False
)

for ax, benchmark in zip(axes, benchmarks):
    x = np.arange(len(sources_order))
    total_vals = total_time_grouped.loc[benchmark].values
    index_vals = index_time_grouped.loc[benchmark].values
    remainder_vals = remainder_grouped.loc[benchmark].values

    bar_width = 0.5

    # Plot vertical stacked bars: bottom segment for index creation time.
    ax.bar(
        x,
        index_vals,
        width=bar_width,
        color=[color_mapping_index[src] for src in sources_order],
    )
    ax.bar(
        x,
        remainder_vals,
        width=bar_width,
        bottom=index_vals,
        color=[color_mapping_other[src] for src in sources_order],
    )

    # Annotate each bar
    for i, (idx_time, tot_time) in enumerate(zip(index_vals, total_vals)):
        pct = (idx_time / tot_time * 100) if tot_time > 0 else 0
        idx_str = f"{idx_time:,.1f}s"
        tot_str = f"{tot_time:,.1f}s"
        ax.text(
            x[i],
            idx_time + 0.02 * tot_time,
            f"{idx_str}\n({pct:.1f}%)",
            ha="center",
            va="bottom",
            color="black",
            fontsize=18,
        )
        ax.hlines(
            y=idx_time,
            xmin=x[i] - bar_width / 2,
            xmax=x[i] + bar_width / 2,
            colors="grey",
            linestyles="--",
            linewidth=1,
        )
        # Increase offset (from 0.05 to 0.10) for the total time text to avoid overlap with the title.
        ax.text(
            x[i],
            tot_time + 0.10 * tot_time,
            tot_str,
            ha="center",
            va="bottom",
            color="black",
            fontsize=21,
        )

    # Increase the title padding so that the title doesn't crowd the upper data.
    ax.set_title(f"{benchmark.upper()} Benchmark", pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(sources_order)
    ax.set_ylabel("Time (Seconds)")
    ax.grid(axis="y", linestyle="--", alpha=0.7)
    # Set y-limit to provide extra space for annotations (10% extra space)
    ax.set_ylim(0, max(total_vals) * 1.25)

# Create one global legend and position it near the top center.
legend_elements = [
    Patch(facecolor=color_mapping_index["Ours"], label="Ours - Index Creation"),
    Patch(facecolor=color_mapping_other["Ours"], label="Ours - Other Time"),
    Patch(facecolor=color_mapping_index["λ-Tune"], label="λ-Tune - Index Creation"),
    Patch(facecolor=color_mapping_other["λ-Tune"], label="λ-Tune - Other Time"),
]
fig.legend(
    handles=legend_elements,
    loc="upper center",
    bbox_to_anchor=(0.5, 1.18),  # Adjusted upwards from (0.5, 1.10)
    ncol=4,
    title="Time Breakdown",
    fontsize=21,
)

plt.tight_layout(rect=[0.02, 0.02, 0.98, 0.98])
plt.savefig("s5_2.png", bbox_inches="tight")
plt.savefig("s5_2.pdf", bbox_inches="tight")
plt.show()
