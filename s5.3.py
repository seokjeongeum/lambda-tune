#!/usr/bin/env python3
import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

# Define benchmarks and file paths for the JSON reports
benchmarks = ["tpc-h", "job", "tpc-ds"]
file_paths = {
    "tpc-h": [
        "test/e7/tpch/exploit_index/reports.json",
        "test/e7/tpch/lambdatune/reports.json",
    ],
    "job": [
        "test/e7/job/exploit_index/reports.json",
        "test/e7/job/lambdatune/reports.json",
    ],
    "tpc-ds": [
        "test/e7/tpcds/exploit_index/reports.json",
        "test/e7/tpcds/lambdatune/reports.json",
    ],
}

# Mapping for nicer display names
display_names = {
    "test/e7/tpch/exploit_index/reports.json": "Ours",
    "test/e7/tpch/lambdatune/reports.json": "Lambda-Tune",
    "test/e7/job/exploit_index/reports.json": "Ours",
    "test/e7/job/lambdatune/reports.json": "Lambda-Tune",
    "test/e7/tpcds/exploit_index/reports.json": "Ours",
    "test/e7/tpcds/lambdatune/reports.json": "Lambda-Tune",
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
# Total time is taken from the last reported value per (benchmark, source)
total_time_grouped = (
    df.groupby(["benchmark", "source"]).last()["duration_seconds"].unstack(fill_value=0)
)
# Index creation time is summed over rounds per (benchmark, source)
index_time_grouped = (
    df.groupby(["benchmark", "source"])["round_index_creation_time"]
    .sum()
    .unstack(fill_value=0)
)

# Order benchmarks and sources
sources_order = ["Ours", "Lambda-Tune"]
total_time_grouped = total_time_grouped.reindex(benchmarks).reindex(
    columns=sources_order, fill_value=0
)
index_time_grouped = index_time_grouped.reindex(benchmarks).reindex(
    columns=sources_order, fill_value=0
)

# Calculate remaining (other) time
remainder_grouped = total_time_grouped - index_time_grouped

# Print data that are plotted:
print("Total Time Grouped:")
print(total_time_grouped)
print("\nIndex Creation Time Grouped:")
print(index_time_grouped)
print("\nRemaining (Other) Time Grouped:")
print(remainder_grouped)

# Define color mappings (saturated colors for clarity)
color_mapping_index = {"Ours": "#1f77b4", "Lambda-Tune": "#ff7f0e"}
color_mapping_other = {"Ours": "#005792", "Lambda-Tune": "#d35400"}

# Create vertical subplots (one for each benchmark) arranged horizontally.
# Independent y-axes for each subplot.
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
        # When the index creation time is very short compared to total (e.g., in tpc-ds),
        # reposition the index creation annotation above the dashed line.
        if (
            benchmark.lower() == "tpc-ds"
            and tot_time > 0
            and (idx_time / tot_time < 0.1)
        ):
            ax.text(
                x[i],
                idx_time + 0.02 * tot_time,
                f"{idx_str}\n({pct:.1f}%)",
                ha="center",
                va="bottom",
                color="black",
                fontsize=8,
            )
        else:
            ax.text(
                x[i],
                idx_time / 2,
                f"{idx_str}\n({pct:.1f}%)",
                ha="center",
                va="center",
                color="black",
                fontsize=10,
            )
        ax.hlines(
            y=idx_time,
            xmin=x[i] - bar_width / 2,
            xmax=x[i] + bar_width / 2,
            colors="grey",
            linestyles="--",
            linewidth=1,
        )
        ax.text(
            x[i],
            tot_time + 0.05 * tot_time,
            tot_str,
            ha="center",
            va="bottom",
            color="black",
            fontsize=10,
        )

    ax.set_title(f"{benchmark.upper()} Benchmark")
    ax.set_xticks(x)
    ax.set_xticklabels(sources_order)
    ax.set_ylabel("Time (Seconds)")
    ax.grid(axis="y", linestyle="--", alpha=0.7)

# Create one global legend and position it inside the figure near the top center.
legend_elements = [
    Patch(facecolor=color_mapping_index["Ours"], label="Ours - Index Creation"),
    Patch(facecolor=color_mapping_other["Ours"], label="Ours - Other Time"),
    Patch(
        facecolor=color_mapping_index["Lambda-Tune"],
        label="Lambda-Tune - Index Creation",
    ),
    Patch(
        facecolor=color_mapping_other["Lambda-Tune"], label="Lambda-Tune - Other Time"
    ),
]
# Move the legend higher by adjusting bbox_to_anchor to (0.5, 1.10)
fig.legend(
    handles=legend_elements,
    loc="upper center",
    bbox_to_anchor=(0.5, 1.10),
    ncol=4,
    title="Time Breakdown",
    fontsize=10,
)

plt.tight_layout(rect=[0.02, 0.02, 0.98, 1.0])
plt.savefig("s5.3.png", bbox_inches="tight")
plt.savefig("s5.3.pdf", bbox_inches="tight")
plt.show()
