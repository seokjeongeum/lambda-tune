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
sources_order = ["Ours", "λ-Tune"]
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


# Define color mappings (renamed for clarity)
color_mapping_index = {"Ours": "#1f77b4", "λ-Tune": "#ff7f0e"}
color_mapping_query = {"Ours": "#005792", "λ-Tune": "#d35400"}  # Renamed from _other

# Create vertical subplots (one for each benchmark) arranged horizontally.
fig, axes = plt.subplots(
    nrows=1, ncols=len(benchmarks), figsize=(6 * len(benchmarks), 6), sharey=False
)
if len(benchmarks) == 1:
    axes = [axes]  # Ensure axes is iterable

for ax, benchmark in zip(axes, benchmarks):
    x = np.arange(len(sources_order))
    total_duration_vals = total_time_grouped.loc[benchmark].values  # Overall duration
    index_vals = index_time_grouped.loc[benchmark].values
    query_vals = query_time_grouped.loc[benchmark].values  # Use query time values

    bar_width = 0.5

    # Plot vertical stacked bars: bottom segment for index creation time.
    bar1 = ax.bar(  # Assign to variable to potentially use later
        x,
        index_vals,
        width=bar_width,
        color=[color_mapping_index[src] for src in sources_order],
        label="Index Creation Time",
    )
    # Plot top segment for query execution time.
    bar2 = ax.bar(  # Assign to variable
        x,
        query_vals,
        width=bar_width,
        bottom=index_vals,
        color=[color_mapping_query[src] for src in sources_order],
        label="Query Execution Time",
    )

    # Get max y value for this subplot to scale padding
    max_y_val = max(total_duration_vals) if total_duration_vals.size > 0 else 1
    # Define a minimum padding fraction (e.g., 2% of the axis height)
    min_padding_fraction = 0.02
    # Define absolute minimum padding in data units
    min_abs_y_padding = max_y_val * min_padding_fraction

    # Annotate each bar
    for i, (idx_time, query_time, total_dur) in enumerate(
        zip(index_vals, query_vals, total_duration_vals)
    ):
        pct_index = (idx_time / total_dur * 100) if total_dur > 0 else 0
        idx_str = f"{idx_time:,.1f}s"
        tot_str = f"{total_dur:,.1f}s"

        # --- Annotation for Index Time + Percentage ---
        # Calculate potential y position (middle of index bar)
        potential_y_mid_index = idx_time / 2
        # Ensure the label y position is at least min_abs_y_padding above 0
        index_label_y = max(potential_y_mid_index, min_abs_y_padding)

        # Adjust text color based on potential background, default to black
        text_color = "black"
        # Optional: Make text white only if the bar segment is sufficiently tall AND the label fits
        # if idx_time > max_y_val * 0.1 and index_label_y < idx_time * 0.9: # Check if bar is tall and label fits
        #     text_color = "white"

        ax.text(
            x[i],
            index_label_y,
            f"{idx_str}\n({pct_index:.1f}%)",
            ha="center",
            va="bottom",  # Place bottom of text at the calculated y, looks better with offset
            color=text_color,  # Use calculated text color
            fontsize=18,
            weight="bold",
        )

        # --- Draw separator line ---
        # Only draw if index time is greater than 0 to avoid line at bottom
        if idx_time > 0:
            ax.hlines(
                y=idx_time,
                xmin=x[i] - bar_width / 2,
                xmax=x[i] + bar_width / 2,
                colors="grey",
                linestyles="--",
                linewidth=1,
            )

        # --- Annotate Total Duration (above the stacked bar) ---
        ax.text(
            x[i],
            total_dur + min_abs_y_padding,  # Use padding for consistent offset
            tot_str,
            ha="center",
            va="bottom",
            color="black",
            fontsize=21,
            weight="bold",
        )

    # Increase the title padding
    ax.set_title(f"{benchmark.upper()} Benchmark", pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(sources_order)
    ax.set_ylabel("Time (Seconds)")
    ax.grid(axis="y", linestyle="--", alpha=0.7)
    # Set y-limit based on OVERALL duration, ensuring enough space for top annotation
    ax.set_ylim(0, max_y_val * 1.35)  # Increased headroom slightly more

# Create one global legend and position it near the top center.
legend_elements = [
    Patch(facecolor=color_mapping_index["Ours"], label="Ours - Index Creation"),
    Patch(facecolor=color_mapping_query["Ours"], label="Ours - Query Execution"),
    Patch(facecolor=color_mapping_index["λ-Tune"], label="λ-Tune - Index Creation"),
    Patch(facecolor=color_mapping_query["λ-Tune"], label="λ-Tune - Query Execution"),
]
fig.legend(
    handles=legend_elements,
    loc="upper center",
    bbox_to_anchor=(0.5, 1.18),
    ncol=2,
    fontsize=21,
)

plt.tight_layout(rect=[0.02, 0.02, 0.98, 0.90])
plt.savefig("s5_2_index_query_time_v2.png", bbox_inches="tight")  # New filename
plt.savefig("s5_2_index_query_time_v2.pdf", bbox_inches="tight")  # New filename
plt.show()
