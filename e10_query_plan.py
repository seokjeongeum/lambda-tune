#!/usr/bin/env python3
import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import pprint

# Increase plot font sizes globally by 1.5x
plt.rcParams.update(
    {
        "font.size": 21,  # General font size (1.5x of 14)
        "axes.titlesize": 24,  # Axes title font size (1.5x of 16)
        "axes.labelsize": 21,  # Axes label font size (1.5x of 14)
        "xtick.labelsize": 18,  # x tick label font size (1.5x of 12)
        "ytick.labelsize": 18,  # y tick label font size (1.5x of 12)
        "legend.fontsize": 18,  # Legend font size (1.5x of 12)
    }
)

# Set the experiment and benchmarks
experiment = "e10"
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
                    report["file"] = fp  # Tag the source file
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

# Define display name mapping and colors for each source file.
display_names = {}
print_names = {}  # For printing with benchmark names
colors = {}
for benchmark in benchmarks:
    # Convert benchmark name to proper title format
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

    # For legend - only method name
    display_names[ours_fp] = "Ours"
    display_names[lambdatune_fp] = "λ-Tune"

    # For printing - method name with benchmark
    print_names[ours_fp] = f"{bench_title}: Ours"
    print_names[lambdatune_fp] = f"{bench_title}: λ-Tune"

    colors[ours_fp] = "blue"
    colors[lambdatune_fp] = "green"

# --- Plotting ---
# Create one subplot per benchmark and combine them in one overall figure.
num_benchmarks = len(benchmarks)
fig, axes = plt.subplots(
    nrows=1, ncols=num_benchmarks, figsize=(6 * num_benchmarks, 6), sharey=False
)

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
    # Convert benchmark name to proper title format
    title = benchmark.upper().replace("TPCH", "TPC-H").replace("TPCDS", "TPC-DS")
    ax.set_title(f"{title} Benchmark")
    ax.set_xlabel("Duration (Seconds)")
    ax.set_ylabel("Best Execution Time")
    ax.grid(True)

# Create a single combined legend for the entire figure, positioned upward.
handles = []
labels = []
for ax in axes:
    h, l = ax.get_legend_handles_labels()
    for handle, label in zip(h, l):
        if label not in labels:
            handles.append(handle)
            labels.append(label)

fig.legend(
    handles,
    labels,
    loc="upper center",
    bbox_to_anchor=(0.5, 1.15),
    ncol=len(labels),
    title="Source",
)

print("Scatter Plot: Duration vs Best Execution Time by Source for Each Benchmark")
plt.tight_layout(rect=[0, 0, 1, 0.92])
plot_filename = f"e10_query_plan"
plt.savefig(f"{plot_filename}.png", bbox_inches="tight")
plt.savefig(f"{plot_filename}.pdf", bbox_inches="tight")
print(f"Scatter plot saved as {plot_filename}")
plt.show()

# --- Compute and Print Sums for Time Components per Source with Percentages ---
time_columns = [
    "round_index_creation_time",
    "round_query_execution_time",
]

# Group by file and compute the sums for each time column.
grouped_sums = df.groupby("file")[time_columns].sum()

print("\nFormatted Time Sums per Source with Percentages:\n")
for source, row in grouped_sums.iterrows():
    total = row.sum()
    disp_name = print_names.get(source, source)  # Use print_names for printing
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
    disp_name = print_names.get(source, source)  # Use print_names for printing
    # If the value is infinite, replace it with NaN so that "inf" isn't printed.
    min_val = stats["min"] if not np.isinf(stats["min"]) else float("nan")
    print(f"{disp_name} -> Min: {min_val:.6f}")

# --- Print Config ID, Total Query Execution Time, and Source for Last Entry per Config ID ---
print(
    "\nConfig ID, Total Query Execution Time, and Source for last entry per config id:\n"
)
pp = pprint.PrettyPrinter(indent=4)

# Group by config_id to process each config_id separately
grouped_by_config = df.groupby("config_id")

for config_id, group in grouped_by_config:
    # Get the last row for this config_id
    last_row = group.iloc[-1]

    # Extract information from the last row
    total_qet = last_row.get("total_query_execution_time", "N/A")
    file_val = last_row.get("file", "N/A")
    source_label = display_names.get(file_val, file_val)

    print(
        f"Config ID: {config_id}, Total Query Execution Time: {total_qet}, Source: {source_label}"
    )

    # Process lambda_tune_config from the last row
    lambda_tune_config = last_row.get("lambda_tune_config", "N/A")
    if isinstance(lambda_tune_config, dict):
        sorted_lambda = {
            key: lambda_tune_config[key] for key in sorted(lambda_tune_config)
        }
        print("lambda_tune_config:")
        pp.pprint(sorted_lambda)
    elif isinstance(lambda_tune_config, list):
        try:
            sorted_lambda = sorted(lambda_tune_config)
        except Exception:
            sorted_lambda = lambda_tune_config
        print("lambda_tune_config:")
        pp.pprint(sorted_lambda)
    else:
        print(f"lambda_tune_config: {lambda_tune_config}")

    # For created_indexes, concatenate all indexes from all rows with this config_id
    # First, determine the type of created_indexes
    index_type = None
    for idx, row in group.iterrows():
        created_indexes = row.get("created_indexes", None)
        if created_indexes is not None:
            if isinstance(created_indexes, dict):
                index_type = "dict"
                break
            elif isinstance(created_indexes, list):
                index_type = "list"
                break

    # Concatenate based on the type
    if index_type == "dict":
        # For dictionaries, merge them
        all_indexes = {}
        for idx, row in group.iterrows():
            indexes = row.get("created_indexes", {})
            if isinstance(indexes, dict):
                all_indexes.update(indexes)

        # Sort the concatenated dict by keys
        sorted_indexes = {key: all_indexes[key] for key in sorted(all_indexes)}
        print("created_indexes (concatenated):")
        pp.pprint(sorted_indexes)

    elif index_type == "list":
        # For lists, concatenate them and avoid duplicates manually
        all_indexes = []
        for idx, row in group.iterrows():
            indexes = row.get("created_indexes", [])
            if isinstance(indexes, list):
                # Add each index to all_indexes if it's not already there
                for index in indexes:
                    if index not in all_indexes:
                        all_indexes.append(index)

        # Sort if possible
        try:
            all_indexes.sort()
        except:
            pass

        print("created_indexes (concatenated):")
        pp.pprint(all_indexes)

    else:
        # If we couldn't determine a consistent type, just print 'N/A'
        print("created_indexes (concatenated): N/A")

    print("\n" + "-" * 40 + "\n")
