#!/usr/bin/env python3
import json
import os
import pandas as pd
import matplotlib.pyplot as plt

# Define benchmarks and file paths for the JSON reports
benchmarks = ["tpch", "job", "tpcds"]
file_paths = {
    "tpch": [
        "test/e7/tpch/exploit_index/reports.json",
        "test/e7/tpch/lambdatune/reports.json",
    ],
    "job": [
        "test/e7/job/exploit_index/reports.json",
        "test/e7/job/lambdatune/reports.json",
    ],
    "tpcds": [
        "test/e7/tpcds/exploit_index/reports.json",
        "test/e7/tpcds/lambdatune/reports.json",
    ],
}

# Mapping for nicer display names
display_names = {
    "exploit_index": "Ours",
    "lambdatune": "Lambda-Tune",
}

# Initialize a list to store all data
data = []

# Load and merge the data from all JSON files
for benchmark, paths in file_paths.items():
    for fp in paths:
        if os.path.exists(fp):
            with open(fp, "r") as f:
                reports = json.load(f)
                for report in reports:
                    report["benchmark"] = benchmark  # Tag the benchmark
                    report["file"] = fp  # Tag the source
                data.extend(reports)
        else:
            print(f"Warning: File {fp} not found.")

# Create DataFrame
df = pd.DataFrame(data)

# List of required columns
required_columns = [
    "round_index_creation_time",
    "round_query_execution_time",
    "round_config_reset_time",
    "round_reconfiguration_time",
    "file",
    "benchmark",
]

# For any missing required column, create it with default value 0
for col in required_columns:
    if col not in df.columns:
        df[col] = 0

# Define time components and their labels for the grouped bar chart
time_components = [
    "round_index_creation_time",
    "round_query_execution_time",
    "round_config_reset_time",
    "round_reconfiguration_time",
]
time_labels = [
    "Index Creation Time",
    "Query Execution Time",
    "Config Reset Time",
    "Reconfiguration Time",
]

# Group by benchmark and file, then compute the sums for each time component
grouped_sums = df.groupby(["benchmark", "file"])[time_components].sum()

# Retrieve unique benchmarks and sources from the multi-index
benchmarks_unique = grouped_sums.index.get_level_values("benchmark").unique()
sources = grouped_sums.index.get_level_values("file").unique()

# Plot each benchmark in a single grouped bar chart
plt.figure(figsize=(15, 8))
bar_width = 0.2  # Width of each bar
colors = ["blue", "green", "orange", "red"]

# To ensure bars for different benchmarks don't overlap,
# we offset groups based on the number of time components.
num_components = len(time_components)
for i, benchmark in enumerate(benchmarks_unique):
    benchmark_data = grouped_sums.loc[benchmark]
    x = range(len(benchmark_data))
    for j, component in enumerate(time_components):
        positions = [pos + j * bar_width + i * (num_components + 1) * bar_width for pos in x]
        plt.bar(
            positions,
            benchmark_data[component],
            width=bar_width,
            label=f"{benchmark.upper()} - {time_labels[j]}" if i == 0 else "",
            color=colors[j % len(colors)]
        )

# Set the x-ticks: infer them based on source groups for clarity.
# This assumes the same source order across benchmarks.
tick_positions = [pos + ((num_components - 1) * bar_width) / 2 for pos in range(len(sources))]
tick_labels = [display_names.get(source.split("/")[-2], source) for source in sources]

plt.xlabel("Source")
plt.ylabel("Time (Seconds)")
plt.title("Grouped Bar Chart: Time Components by Benchmark and Source")
plt.xticks(tick_positions, tick_labels)

plt.legend(title="Time Components")
plt.grid(axis="y", linestyle="--", alpha=0.7)
plt.tight_layout()

# Save the plot in both PNG and PDF formats
plot_filename = "e7_grouped_bar_chart_all_benchmarks"
plt.savefig(f"{plot_filename}.png")
plt.savefig(f"{plot_filename}.pdf")
print(f"Grouped bar chart saved as {plot_filename}.png and {plot_filename}.pdf")
plt.show()
