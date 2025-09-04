# -*- coding: utf-8 -*-
import json
import pathlib  # Using pathlib for easier path manipulation

# --- Configuration ---
base_dir = pathlib.Path("test")
file_paths_to_process = [
    base_dir / "1_main" / "job" / "ours" / "reports.json",
    base_dir / "2_prompt_ablation" / "data_definition_language_ablated" / "reports.json",
    base_dir / "2_prompt_ablation" / "query_weight_ablated" / "reports.json",
    base_dir / "2_prompt_ablation" / "qw_ddl_ablated" / "reports.json",
    base_dir / "2_prompt_ablation" / "qw_ws_ablated" / "reports.json",
    base_dir / "2_prompt_ablation" / "workload_statistics_ablated" / "reports.json",
    base_dir / "2_prompt_ablation" / "ws_ddl_ablated" / "reports.json",
]
benchmark_order = ["job"]
num_benchmarks = len(benchmark_order)
output_filename_base = "2_prompt_ablation_comparison"
output_formats = ["png", "pdf"]
title_map = {"job": "JOB Benchmark Prompt Ablation"}
legend_label_map = {
    "ours": "Ours (Full Prompt)",
    "data_definition_language_ablated": "Ablated (DDL)",
    "query_weight_ablated": "Ablated (Query Weight)",
    "qw_ddl_ablated": "Ablated (QW+DDL)",
    "qw_ws_ablated": "Ablated (QW+WS)",
    "workload_statistics_ablated": "Ablated (Workload Statistics)",
    "ws_ddl_ablated": "Ablated (WS+DDL)",
}
table_data = []

# --- Data Processing Loop for Each File ---
for file_path in file_paths_to_process:
    print(f"--- Processing file: {file_path} ---")
    if not file_path.exists():
        print(f"Warning: File not found: {file_path}")
        continue

    try:
        if "1_main" in file_path.parts:
            benchmark_name = "job"
            method_name = "ours"
        else:
            benchmark_name = "job"
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

    file_min_best_time = float("inf")
    file_max_duration = 0.0
    processed_configs = set()
    first_valid_points_in_file = {}
    for report in reports_data:
        config_id = report.get("config_id")
        best_time = report.get("best_execution_time")
        duration = report.get("duration_seconds")
        if not config_id or best_time is None or duration is None:
            continue

        if isinstance(best_time, (int, float)) and best_time != float("inf"):
            file_min_best_time = min(file_min_best_time, best_time)
        if isinstance(duration, (int, float)):
            file_max_duration = max(file_max_duration, duration)

        if config_id not in processed_configs:
            if isinstance(best_time, (int, float)) and best_time != float("inf"):
                first_valid_points_in_file[config_id] = (duration, best_time)
                processed_configs.add(config_id)

    points_added = 0
    for duration, best_time in first_valid_points_in_file.values():
        points_added += 1

    if points_added > 0:
        print(
            f"    Found {points_added} unique first valid points for {benchmark_name}/{method_name}."
        )
        print(f"    Best Execution Time: {file_min_best_time if file_min_best_time != float('inf') else 'N/A'}")
        table_data.append({
            "method_key": method_name,
            "method_display": legend_label_map.get(method_name, method_name),
            "best_time": file_min_best_time if file_min_best_time != float('inf') else 'N/A',
        })
    else:
        print(f"    No suitable first valid data points found in {file_path}.")


# --- Results Summary Table ---
print("\n--- Generating Results Table ---")

if not table_data:
    print("No data found from any file to create a table.")
else:
    # Define a consistent order for the methods in the table
    method_order = [
        "ours",
        "data_definition_language_ablated",
        "query_weight_ablated",
        "workload_statistics_ablated",
        "qw_ddl_ablated",
        "qw_ws_ablated",
        "ws_ddl_ablated",
    ]
    # Sort the collected data according to the desired order
    order_map = {key: i for i, key in enumerate(method_order)}
    table_data.sort(key=lambda x: order_map.get(x["method_key"], 99))

    # Prepare headers and find column widths for alignment
    headers = ["Method", "Best Execution Time (s)"]
    # Determine the maximum width needed for the method column
    max_method_width = max(len(h) for h in [row["method_display"] for row in table_data] + [headers[0]])

    # Print table header
    header_line = f"{headers[0]:<{max_method_width}} | {headers[1]:>25}"
    print(header_line)
    print("-" * len(header_line))

    # Print each row of data
    for row in table_data:
        best_time_str = (
            f"{row['best_time']:.2f}" if isinstance(row["best_time"], (int, float)) else "N/A"
        )
        data_line = f"{row['method_display']:<{max_method_width}} | {best_time_str:>25}"
        print(data_line)

print("\n--- Script Finished ---")
