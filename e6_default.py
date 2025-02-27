import json


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

# Group configurations by config_id and keep only the latest one according to report_ts
grouped_configs = {}
for config in configs:
    config_id = config.get("config_id", "Unknown")
    # Use report_ts as a timestamp indicator; if missing, fall back on start_time.
    ts = config.get("report_ts", config.get("start_time", 0))
    # Update the grouping if this is the first entry for the id or if its timestamp is greater.
    if config_id not in grouped_configs or ts > grouped_configs[config_id].get(
        "report_ts", 0
    ):
        grouped_configs[config_id] = config

# Choose a baseline driver_config.
# If a config with id "config" exists, use its driver_config; otherwise, pick one arbitrarily.
if "config" in grouped_configs:
    baseline_driver_config = grouped_configs["config"].get("driver_config", {})
    baseline_indexes = grouped_configs["config"].get("created_indexes", [])
else:
    first_key = next(iter(grouped_configs))
    baseline_driver_config = grouped_configs[first_key].get("driver_config", {})
    baseline_indexes = grouped_configs[first_key].get("created_indexes", [])

# Iterate through each unique config and print differences and the latest total_completed_query_execution_time.
for config_id, config in grouped_configs.items():
    total_completed_time = config.get("total_completed_query_execution_time")
    driver_config = config.get("driver_config", {})
    created_indexes = config.get("created_indexes", [])
    differences = dict_diff(baseline_driver_config, driver_config)

    print(f"Config ID: {config_id}")
    print(f"Total Completed Query Execution Time: {total_completed_time}")
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
