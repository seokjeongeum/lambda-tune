import json
import math


def dict_diff(baseline, current):
    """
    Compare two dictionaries and return a dictionary with keys where the values differ.
    For each key found, return a tuple: (baseline_value, current_value).
    """
    diff = {}
    all_keys = set(baseline.keys()).union(current.keys())
    for key in all_keys:
        base_val = baseline.get(key)
        curr_val = current.get(key)
        if base_val != curr_val:
            diff[key] = (base_val, curr_val)
    return diff


# Load JSON data from file
with open("test/lambdatune/reports.json", "r") as file:
    configs = json.load(file)

# Find baseline configuration with id "config" regardless of its completion status.
baseline_config = None
for config in configs:
    if config.get("config_id", "Unknown") == "config":
        # Use report_ts if available; otherwise, fall back on start_time
        ts = config.get("report_ts", config.get("start_time", 0))
        if baseline_config is None or ts > baseline_config.get("report_ts", baseline_config.get("start_time", 0)):
            baseline_config = config

if baseline_config is None:
    print("Baseline config with id 'config' not found. Exiting.")
    exit(1)

baseline_driver_config = baseline_config.get("driver_config", {})

# Group all configurations by config_id and keep only the latest one according to report_ts.
grouped_configs = {}
for config in configs:
    config_id = config.get("config_id", "Unknown")
    ts = config.get("report_ts", config.get("start_time", 0))
    if config_id not in grouped_configs or ts > grouped_configs[config_id].get("report_ts", 0):
        grouped_configs[config_id] = config

# Iterate through each unique config and compare its driver_config to the baseline.
for config_id, config in grouped_configs.items():
    # If the configuration is not completed, treat total_query_execution_time as infinity.
    if not config.get("completed", False):
        total_query_time = math.inf
    else:
        total_query_time = config.get("total_query_execution_time")
    
    driver_config = config.get("driver_config", {})
    created_indexes = config.get("created_indexes", [])
    differences = dict_diff(baseline_driver_config, driver_config)

    print(f"Config ID: {config_id}")
    print(f"Total Query Execution Time: {total_query_time}")
    print("Differences in driver_config (baseline vs. current):")
    if differences:
        for key, (base_val, curr_val) in differences.items():
            print(f"  {key}: baseline = {base_val}, current = {curr_val}")
    else:
        print("  No differences compared to baseline.")

    print("Created Indexes:")
    if created_indexes:
        for index in created_indexes:
            print(f"  {index}")
    else:
        print("  No indexes created.")
    print("-" * 50)
