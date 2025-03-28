#!/usr/bin/env python3
import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Increase plot font sizes globally by 1.5x
plt.rcParams.update(
    {
        "font.size": 21,
        "axes.titlesize": 24,
        "axes.labelsize": 21,
        "xtick.labelsize": 18,
        "ytick.labelsize": 18,
        "legend.fontsize": 18,
    }
)

# Set the experiment and benchmarks
experiment = "e10"
benchmarks = ["tpch", "job", "tpcds"]

# Load and merge the data
data = []
for benchmark in benchmarks:
    file_paths = [
        f"test/{experiment}/{benchmark}/ours/reports.json",
        f"test/{experiment}/{benchmark}/lambdatune/reports.json",
    ]
    for fp in file_paths:
        if os.path.exists(fp):
            with open(fp, "r") as f:
                reports = json.load(f)
                for report in reports:
                    report["file"] = fp
                    report["benchmark"] = benchmark
                data.extend(reports)
        else:
            print(f"Warning: File {fp} not found.")

# Create DataFrame
df = pd.DataFrame(data)

# Check required columns
required_columns = [
    "duration_seconds",
    "best_execution_time",
    "round_index_creation_time",
    "round_query_execution_time",
    "round_config_reset_time",
    "round_reconfiguration_time",
    "file",
]
missing_columns = [col for col in required_columns if col not in df.columns]
if missing_columns:
    raise ValueError(f"Missing columns: {missing_columns}")

# Convert numeric columns
df["best_execution_time"] = pd.to_numeric(df["best_execution_time"], errors="coerce")
df["duration_seconds"] = pd.to_numeric(df["duration_seconds"], errors="coerce")

# Filter out rows representing timeouts BEFORE plotting
df_valid_runs_for_plot = df[
    df["timeout"] >= 0
].copy()  # Keep only non-timeout runs for plotting
print(
    f"Original data points: {len(df)}, Points for plotting (non-timeout): {len(df_valid_runs_for_plot)}"
)


# Define display name mapping and colors
display_names = {}
print_names = {}
colors = {}
for benchmark in benchmarks:
    if benchmark.lower() == "tpch":
        bench_title = "TPC-H"
    elif benchmark.lower() == "job":
        bench_title = "JOB"
    elif benchmark.lower() == "tpcds":
        bench_title = "TPC-DS"
    else:
        bench_title = benchmark.upper()

    ours_fp = f"test/{experiment}/{benchmark}/ours/reports.json"
    lambdatune_fp = f"test/{experiment}/{benchmark}/lambdatune/reports.json"

    display_names[ours_fp] = "Ours"
    display_names[lambdatune_fp] = "λ-Tune"
    print_names[ours_fp] = f"{bench_title}: Ours"
    print_names[lambdatune_fp] = f"{bench_title}: λ-Tune"
    colors[ours_fp] = "blue"
    colors[lambdatune_fp] = "green"

# --- Plotting ---
num_benchmarks = len(benchmarks)
fig, axes = plt.subplots(
    nrows=1, ncols=num_benchmarks, figsize=(6 * num_benchmarks, 6), sharey=False
)
if num_benchmarks == 1:
    axes = [axes]

for ax, benchmark in zip(axes, benchmarks):
    # Use the PRE-FILTERED data (valid runs only)
    sub_df = df_valid_runs_for_plot[df_valid_runs_for_plot["benchmark"] == benchmark]

    if sub_df.empty:
        print(
            f"Warning: No valid runs (non-timeout) found for benchmark '{benchmark}'. Skipping plot."
        )
        title = benchmark.upper().replace("TPCH", "TPC-H").replace("TPCDS", "TPC-DS")
        ax.set_title(f"{title} Benchmark (No Valid Data)")
        ax.set_xlabel("Duration (Seconds)")
        ax.set_ylabel("Best Execution Time")
        ax.grid(True)
        continue

    for source, group in sub_df.groupby("file"):
        group = group.sort_values("duration_seconds")
        ax.scatter(
            group["duration_seconds"],
            group["best_execution_time"],
            label=display_names.get(source, source),
            color=colors.get(source, "black"),
            alpha=0.7,
        )
        ax.plot(
            group["duration_seconds"],
            group["best_execution_time"],
            color=colors.get(source, "black"),
            linestyle="--",
            alpha=0.7,
        )
    title = benchmark.upper().replace("TPCH", "TPC-H").replace("TPCDS", "TPC-DS")
    ax.set_title(f"{title} Benchmark")
    ax.set_xlabel("Duration (Seconds)")
    ax.set_ylabel("Best Execution Time")
    ax.grid(True)

# Create combined legend
handles, labels = [], []
for ax_orig in fig.axes:
    h, l = ax_orig.get_legend_handles_labels()
    for handle, label in zip(h, l):
        if label not in labels:
            handles.append(handle)
            labels.append(label)

if handles and labels:
    fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.15),
        ncol=len(labels),
    )

print("\nScatter Plot: Duration vs Best Execution Time (excluding timeouts) by Source")
plt.tight_layout(rect=[0, 0, 1, 0.95])
plot_filename = "s5_1_combined_valid_runs"  # Updated filename
plt.savefig(f"{plot_filename}.png", bbox_inches="tight")
plt.savefig(f"{plot_filename}.pdf", bbox_inches="tight")
print(f"Plot excluding timeouts saved as {plot_filename}")
plt.show()

# --- Compute and Print Sums for Time Components ---
# Use the original df for time component sums
time_columns = [
    "round_index_creation_time",
    "round_query_execution_time",
]
for col in time_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df_for_sums = df.dropna(subset=time_columns).copy()
grouped_sums = df_for_sums.groupby("file")[time_columns].sum()

print("\nFormatted Time Sums per Source (Based on valid time entries):\n")
if not grouped_sums.empty:
    for source, row in grouped_sums.iterrows():
        total = row.sum()
        disp_name = print_names.get(source, source)
        print(disp_name)
        for metric in time_columns:
            value = row[metric]
            pct = (value / total * 100) if total > 0 else 0
            print(f"{metric}: {value:.6f} ({pct:.2f}%)")
        print(f"sum: {total:.6f}\n")
else:
    print("No valid time data found for summing.")

# --- Compute and Print Best Execution Time Statistics ---
# Use df_valid_runs_for_plot for Min Best Execution Time (among successful runs)
print("\nBest Execution Time per Source (aggregated, excluding timeouts):\n")
if not df_valid_runs_for_plot.empty:
    # Calculate min only on valid (non-timeout) runs
    grouped_best_valid = df_valid_runs_for_plot.groupby("file")[
        "best_execution_time"
    ].agg(["min"])
    for source, stats in grouped_best_valid.iterrows():
        disp_name = print_names.get(source, source)
        min_val = stats["min"]
        print(f"{disp_name} -> Min (non-timeout): {min_val:.6f}")

    # Optionally, show the count of timeouts if needed
    timeout_counts = df[df["best_execution_time"] < 0].groupby("file").size()
    if not timeout_counts.empty:
        print("\nTimeout Counts per Source:")
        for source, count in timeout_counts.items():
            disp_name = print_names.get(source, source)
            print(f"{disp_name} -> Timeouts: {count}")

else:
    print("No valid execution time data (>=0) found for aggregation.")
