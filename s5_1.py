#!/usr/bin/env python3
import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Set the experiment and benchmarks to plot
experiment = "s51"
benchmarks = ["tpch", "job", "tpcds"]

# Load and merge the data from all JSON files for each benchmark,
# tagging each record with its source and benchmark.
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
                    report["file"] = fp      # Tag the source file
                    report["benchmark"] = benchmark  # Tag the benchmark
                data.extend(reports)
        else:
            print(f"Warning: File {fp} not found.")

# Create a DataFrame with all collected data.
df = pd.DataFrame(data)

# List of required columns
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

# Convert numeric columns; non-numeric entries become NaN.
df["best_execution_time"] = pd.to_numeric(df["best_execution_time"], errors="coerce")
df["duration_seconds"] = pd.to_numeric(df["duration_seconds"], errors="coerce")

# Define display name mapping and colors for each source file, including benchmark info.
display_names = {}
colors = {}
for benchmark in benchmarks:
    # Determine friendly benchmark title.
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
    display_names[ours_fp] = f"{bench_title}: Ours"
    display_names[lambdatune_fp] = f"{bench_title}: λ-Tune"
    colors[ours_fp] = "blue"
    colors[lambdatune_fp] = "green"

# --- Plotting ---
# Create one subplot per benchmark and combine them in one overall figure.
num_benchmarks = len(benchmarks)
fig, axes = plt.subplots(nrows=1, ncols=num_benchmarks, figsize=(6*num_benchmarks, 6), sharey=False)

# Ensure axes is always an iterable.
if num_benchmarks == 1:
    axes = [axes]

for ax, benchmark in zip(axes, benchmarks):
    # Filter DataFrame for the current benchmark.
    sub_df = df[df["benchmark"] == benchmark]
    # For each source ('ours' and 'lambdatune'), plot the scatter and connecting line.
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
    # Convert benchmark name to proper title format: "tpch" -> "TPC-H", "tpcds" -> "TPC-DS"
    title = benchmark.upper().replace("TPCH", "TPC-H").replace("TPCDS", "TPC-DS")
    ax.set_title(f"{title} Benchmark")
    ax.set_xlabel("Duration (Seconds)")
    ax.set_ylabel("Best Execution Time")
    ax.grid(True)
    ax.legend(title="Source")

print("Scatter Plot: Duration vs Best Execution Time by Source for Each Benchmark")
plt.tight_layout(rect=[0, 0, 1, 0.93])
plot_filename = "s5_1_combined"
plt.savefig(f"{plot_filename}.png")
plt.savefig(f"{plot_filename}.pdf")
print(f"Scatter plot saved as {plot_filename}")
plt.show()

# --- Compute and Print Sums for Time Components per Source with Percentages ---
time_columns = [
    "round_index_creation_time",
    "round_query_execution_time",
    "round_config_reset_time",
    "round_reconfiguration_time",
]

# Group by file and compute the sums for each time column.
grouped_sums = df.groupby("file")[time_columns].sum()

print("\nFormatted Time Sums per Source with Percentages:\n")
for source, row in grouped_sums.iterrows():
    total = row.sum()
    disp_name = display_names.get(source, source)
    print(disp_name)
    for metric in time_columns:
        value = row[metric]
        pct = (value / total * 100) if total > 0 else 0
        print(f"{metric}: {value:.6f} ({pct:.2f}%)")
    print(f"sum: {total:.6f}\n")

# --- Compute and Print Best Execution Time Statistics per Source ---
print("\nBest Execution Time per Source (aggregated):\n")
# Aggregate only the minimum for best_execution_time.
grouped_best = df.groupby("file")["best_execution_time"].agg(["min"])
for source, stats in grouped_best.iterrows():
    disp_name = display_names.get(source, source)
    # If the value is infinite, replace it with NaN so that "inf" isn't printed.
    min_val = stats["min"] if not np.isinf(stats["min"]) else float("nan")
    print(f"{disp_name} -> Min: {min_val:.6f}")
