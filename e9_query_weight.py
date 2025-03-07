#!/usr/bin/env python3
import json
import os
import pandas as pd
import matplotlib.pyplot as plt

experiment = "e9"
benchmark = "job"
# Define file paths for the two JSON reports
file_paths = [
    f"test/{experiment}/{benchmark}/query_weight/reports.json",
    f"test/{experiment}/{benchmark}/lambdatune/reports.json",
]

# Mapping for nicer display names
display_names = {
    f"test/{experiment}/{benchmark}/query_weight/reports.json": "Ours",
    f"test/{experiment}/{benchmark}/lambdatune/reports.json": "Lambda-Tune",
}

# Load and merge the data from both JSON files, tagging each record with its source file.
data = []
for fp in file_paths:
    if os.path.exists(fp):
        with open(fp, "r") as f:
            reports = json.load(f)
            for report in reports:
                report["file"] = fp  # Tag the source
            data.extend(reports)
    else:
        print(f"Warning: File {fp} not found.")

# Create a DataFrame
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

# Convert best_execution_time to numeric (any non-numeric becomes NaN)
df["best_execution_time"] = pd.to_numeric(df["best_execution_time"], errors="coerce")

# --- Plotting ---
# Define colors for each source for consistent plotting.
colors = {
    f"test/{experiment}/{benchmark}/query_weight/reports.json": "blue",
    f"test/{experiment}/{benchmark}/lambdatune/reports.json": "green",
}

plt.figure(figsize=(10, 6))
for source, group in df.groupby("file"):
    # Sort by duration_seconds so the connecting line is meaningful.
    group = group.sort_values("duration_seconds")
    plt.scatter(
        group["duration_seconds"],
        group["best_execution_time"],
        label=display_names.get(source, source),
        color=colors.get(source, "black"),
        alpha=0.7,
    )
    plt.plot(
        group["duration_seconds"],
        group["best_execution_time"],
        color=colors.get(source, "black"),
        linestyle="--",
        alpha=0.7,
    )

plt.xlabel("Duration (Seconds)")
plt.ylabel("Best Execution Time")
plt.title("Scatter Plot: Duration vs Best Execution Time by Source")
plt.legend(title="Source")
plt.grid(True)
plt.tight_layout()

plot_filename = f"{experiment}_order_query_{benchmark}"
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
