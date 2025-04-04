# -*- coding: utf-8 -*-
import json
import math
import os
import pathlib  # Using pathlib for easier path manipulation
from collections import defaultdict  # Useful for nested dictionaries

import matplotlib.pyplot as plt

try:
    from adjustText import adjust_text
except ImportError:
    print("Error: The 'adjustText' library is not installed.")
    print("Please install it using: pip install adjustText")
    exit()  # Exit if the required library is not found

# --- Configuration ---
# (Same as before)
base_dir = "test"
file_paths_to_process = [
    pathlib.Path(base_dir, "s51", "job", "lambdatune", "reports.json"),
    pathlib.Path(base_dir, "s51", "job", "ours", "reports.json"),
    pathlib.Path(base_dir, "s51", "tpcds", "lambdatune", "reports.json"),
    pathlib.Path(base_dir, "s51", "tpcds", "ours", "reports.json"),
    pathlib.Path(base_dir, "s51", "tpch", "lambdatune", "reports.json"),
    pathlib.Path(base_dir, "s51", "tpch", "ours", "reports.json"),
]
benchmark_order = ["job", "tpcds", "tpch"]
num_benchmarks = len(benchmark_order)
output_filename_base = "s5_1"
output_formats = ["png", "pdf"]
title_map = {"job": "JOB", "tpcds": "TPC-DS", "tpch": "TPC-H"}
legend_label_map = {"lambdatune": "λ-Tune", "ours": "Ours"}
grouped_plot_data = defaultdict(lambda: defaultdict(list))

# --- Data Processing Loop for Each File ---
# (Same as before - code omitted for brevity)
for file_path in file_paths_to_process:
    print(f"--- Processing file: {file_path} ---")
    try:
        benchmark_name = file_path.parts[-3]
        method_name = file_path.parts[-2]
        if benchmark_name not in benchmark_order:
            print(
                f"Warning: Benchmark '{benchmark_name}' from path not in defined order. Skipping file: {file_path}"
            )
            continue
        print(f"    Benchmark: {benchmark_name}, Method: {method_name}")
    except IndexError:
        print(
            f"Warning: Could not determine benchmark/method from path structure: {file_path}"
        )
        continue
    try:
        with open(file_path, "r") as f:
            content = f.read()
            if not content:
                continue
            reports_data = json.loads(content)
            if not isinstance(reports_data, list):
                continue
            if not reports_data:
                continue
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        continue
    except json.JSONDecodeError as e:
        print(f"Error: Could not decode JSON from {file_path}: {e}")
        continue
    except Exception as e:
        print(f"An unexpected error occurred while reading {file_path}: {e}")
        continue

    processed_configs = set()
    first_valid_points_in_file = {}
    for report in reports_data:
        config_id = report.get("config_id")
        best_time = report.get("best_execution_time")
        duration = report.get("duration_seconds")
        if not config_id or best_time is None or duration is None:
            continue
        if config_id not in processed_configs:
            if isinstance(best_time, (int, float)) and best_time != float("inf"):
                first_valid_points_in_file[config_id] = (duration, best_time)
                processed_configs.add(config_id)

    points_added = 0
    for duration, best_time in first_valid_points_in_file.values():
        grouped_plot_data[benchmark_name][method_name].append((duration, best_time))
        points_added += 1

    if points_added > 0:
        print(
            f"    Found {points_added} unique first valid points for {benchmark_name}/{method_name}."
        )
    else:
        print(f"    No suitable first valid data points found in {file_path}.")


# --- Plotting Section (Implementing Option 2: adjustText for TPC-DS with TUNING) ---
print("\n--- Generating Plots ---")

if not grouped_plot_data:
    print("No data found from any file to plot.")
else:
    # Increase figure width slightly more
    fig, axes = plt.subplots(
        1, num_benchmarks, figsize=(8 * num_benchmarks, 6)
    )  # Increased width factor from 7 to 8
    if num_benchmarks == 1:
        axes = [axes]

    legend_info = {}

    for i, benchmark_name in enumerate(benchmark_order):
        ax = axes[i]
        print(f"\nGenerating subplot for benchmark: {benchmark_name} (Axis {i})")
        plot_title = title_map.get(benchmark_name, benchmark_name.upper())

        if benchmark_name not in grouped_plot_data:
            print(f"  No data found for benchmark: {benchmark_name}")
            ax.set_title(f"{plot_title} (No Data)")
            ax.text(
                0.5,
                0.5,
                "No data available",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            ax.grid(False)
            continue

        methods_data = grouped_plot_data[benchmark_name]
        plot_successful_for_benchmark = False
        plot_method_order = ["lambdatune", "ours"]
        texts_for_adjust = []

        for method_name in plot_method_order:
            if method_name not in methods_data:
                continue
            points = methods_data[method_name]
            if not points:
                continue

            try:
                sorted_points = sorted(points, key=lambda item: item[0])
            except TypeError as e:
                print(
                    f"Error sorting points for {benchmark_name}/{method_name}: {e}. Points: {points}"
                )
                continue

            x_vals = [p[0] for p in sorted_points]
            y_vals = [p[1] for p in sorted_points]
            if not x_vals:
                continue

            mapped_label = legend_label_map.get(method_name, method_name)
            (line,) = ax.plot(
                x_vals,
                y_vals,
                marker="o",
                linestyle="-",
                markersize=5,
                label=mapped_label,
            )
            print(
                f"  Plotting line for: {method_name} (as '{mapped_label}') ({len(x_vals)} points)"
            )
            plot_successful_for_benchmark = True

            # --- Store Text Annotations for TPC-DS ONLY ---
            if benchmark_name == "tpcds":
                for x, y in zip(x_vals, y_vals):
                    # Use smaller font size
                    texts_for_adjust.append(
                        ax.text(
                            x, y, f"{y:.2f}", fontsize=7
                        )  # Reduced fontsize from 8 to 7
                    )

            if mapped_label not in legend_info:
                legend_info[mapped_label] = line

        # --- Apply adjust_text AFTER plotting lines for the TPC-DS subplot with TUNED parameters ---
        if benchmark_name == "tpcds" and texts_for_adjust:
            print(
                f"  Applying adjust_text to {len(texts_for_adjust)} labels for TPC-DS (Tuned)..."
            )
            try:
                adjust_text(
                    texts_for_adjust,
                    ax=ax,
                    # Increase force parameters and iterations
                    force_points=(0.2, 0.2),  # Increase repulsion from points
                    force_text=(
                        0.3,
                        0.5,
                    ),  # Increase repulsion between texts (more vertically)
                    expand_points=(
                        1.3,
                        1.3,
                    ),  # Slightly larger exclusion zone around points
                    lim=500,  # Increase iteration limit
                    arrowprops=dict(arrowstyle="-", color="grey", lw=0.5),
                )
                print("  adjust_text applied.")
            except Exception as e:
                print(f"  Error applying adjust_text: {e}")

        # Configure subplot
        ax.set_title(plot_title)
        ax.set_xlabel("Duration (s)")
        ax.set_ylabel("Best Time (s)")
        ax.grid(True, linestyle="--", alpha=0.6)

    # Configure figure
    if legend_info:
        sorted_labels = sorted(legend_info.keys())
        sorted_handles = [legend_info[lbl] for lbl in sorted_labels]
        fig.legend(
            sorted_handles,
            sorted_labels,
            title="Method",
            loc="upper center",
            bbox_to_anchor=(0.5, 0.03),
            ncol=len(sorted_labels),
        )

    plt.tight_layout(rect=[0, 0.08, 1, 0.95])

    # Save plots
    print("\n--- Saving Plots ---")
    for fmt in output_formats:
        output_filename = f"{output_filename_base}.{fmt}"
        try:
            plt.savefig(output_filename, format=fmt, bbox_inches="tight", dpi=300)
            print(f"Saved plot to: {output_filename}")
        except Exception as e:
            print(f"Error saving plot to {output_filename}: {e}")

    plt.show()

print("\n--- Script Finished ---")
