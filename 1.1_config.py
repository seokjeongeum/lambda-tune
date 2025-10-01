import json
import pathlib

# Configuration
BASE_TEST_DIR = pathlib.Path("/workspaces/lambda-tune/test")
CONFIG_DIR = pathlib.Path("/workspaces/lambda-tune/lambdatune/configs")
BENCHMARKS = ["job", "tpch", "tpcds"]
METHODS = ["lambdatune", "ours"]


def find_best_config(benchmark_name, method_name):
    """Finds and prints the best configuration for a given benchmark and method."""
    print(f"--- Processing Benchmark: {benchmark_name.upper()} / Method: {method_name.upper()} ---")
    
    reports_path = BASE_TEST_DIR / "1_main" / benchmark_name / method_name / "reports.json"

    if not reports_path.exists():
        print(f"  Warning: '{reports_path}' not found.")
        return

    try:
        with open(reports_path, "r") as f:
            reports_data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"  Error reading or parsing {reports_path}: {e}")
        return

    if not isinstance(reports_data, list) or not reports_data:
        print(f"  No data found in {reports_path}")
        return

    # Find the report with the best execution time
    best_report = None
    min_best_time = float("inf")

    for report in reports_data:
        best_time = report.get("best_execution_time")
        if best_time is not None and best_time < min_best_time:
            min_best_time = best_time
            best_report = report

    if not best_report:
        print("  Could not find a report with a valid execution time.")
        return

    config_id = best_report.get("config_id")
    if not config_id:
        print("  Best report found, but it is missing a 'config_id'.")
        return

    # Correct path to the configuration file
    config_file_path = (
        CONFIG_DIR
        / "1_main"
        / benchmark_name
        / method_name
        / f"{config_id}.json"
    )

    if not config_file_path.exists():
        print(f"  Best Config ID: {config_id}")
        print(f"  Warning: Configuration file not found at '{config_file_path}'")
        return

    try:
        with open(config_file_path, "r") as f:
            config_data = json.load(f)

        print(f"  Best Config ID: {config_id}")
        print(f"  Best Execution Time: {min_best_time:.2f}s")
        print("  Configuration:")

        # Extract and print the specific content
        try:
            content_str = config_data["response"]["choices"][0]["message"]["content"]
            # The content is a JSON string, so we load and re-dump it for pretty printing
            content_json = json.loads(content_str)
            print(json.dumps(content_json, indent=4))
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as e:
            print(f"    Error: Could not parse the configuration content: {e}")
            print("    Falling back to printing the full configuration:")
            print(json.dumps(config_data, indent=4))

    except (json.JSONDecodeError, IOError) as e:
        print(f"  Error reading or parsing config file {config_file_path}: {e}")


def main():
    """Main function to process all benchmarks."""
    for benchmark in BENCHMARKS:
        for method in METHODS:
            find_best_config(benchmark, method)
            print("")  # Add a newline for better separation

if __name__ == "__main__":
    main()
