import json
import pathlib
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# --- Configuration ---
BASE_TEST_DIR = pathlib.Path("test/1_main")
# BENCHMARKS = ["job", "tpcds", "tpch"]  # Order for plotting
BENCHMARKS = ["tpcds"]  # Plot only TPCH
METHODS = ["lambdatune", "ours"]
OUTPUT_FILENAME = "1.3_query_comparison"
BENCHMARK_DISPLAY_MAP = {"job": "JOB", "tpch": "TPC-H", "tpcds": "TPC-DS"}

# Increase global font sizes for clarity
plt.rcParams.update(
    {
        "font.size": 14,
        "axes.titlesize": 20,
        "axes.labelsize": 16,
        "xtick.labelsize": 10,
        "ytick.labelsize": 12,
        "legend.fontsize": 14,
    }
)

def find_best_config_id(reports_data):
    """Finds the config_id with the minimum best_execution_time from a list of reports."""
    if not reports_data:
        return None

    min_best_time = float("inf")
    best_config_id = None
    for report in reports_data:
        best_time = report.get("best_execution_time")
        if isinstance(best_time, (int, float)) and best_time < min_best_time:
            min_best_time = best_time
            best_config_id = report.get("config_id")
    return best_config_id


def get_aggregated_query_times(reports_data, config_id):
    """Aggregates query times from all reports matching a specific config_id."""
    if not config_id:
        return {}

    aggregated_times = {}
    for report in reports_data:
        if report.get("config_id") == config_id:
            query_times_raw = report.get("round_completed_query_times", {})
            for key, value in query_times_raw.items():
                new_key = "q" + key[5:] if key.startswith("query") else key
                aggregated_times[new_key] = value
    return aggregated_times


def main():
    """Main function to generate a single comparison plot with subplots."""
    print("--- Generating Query Execution Time Comparison Plot ---")

    # Adjusted figsize for better legend placement
    fig, axes = plt.subplots(len(BENCHMARKS), 1, figsize=(20, 10), sharex=False)
    if len(BENCHMARKS) == 1:
        axes = [axes]

    for ax, benchmark in zip(axes, BENCHMARKS):
        print(f"\nProcessing benchmark: {benchmark.upper()}...")
        benchmark_data = {}
        for method in METHODS:
            report_path = BASE_TEST_DIR / benchmark / method / "reports.json"
            
            if not report_path.exists():
                print(f"  Report file not found for '{method}'.")
                benchmark_data[method] = {}
                continue

            try:
                with open(report_path, "r") as f:
                    all_reports = json.load(f)
            except (json.JSONDecodeError, IOError):
                print(f"  Could not read or parse report for '{method}'.")
                benchmark_data[method] = {}
                continue

            best_config = find_best_config_id(all_reports)

            if best_config:
                query_times = get_aggregated_query_times(all_reports, best_config)
                benchmark_data[method] = query_times
                print(f"  Found {len(query_times)} aggregated query times for '{method}' (config: {best_config})")
            else:
                print(f"  Could not find a best config for '{method}'.")
                benchmark_data[method] = {}

        df = pd.DataFrame(benchmark_data).fillna(0)
        df.index.name = "query"
        df.reset_index(inplace=True)

        if df.empty:
            ax.text(0.5, 0.5, "No data available", ha="center", va="center")
            ax.set_title(
                f"Query Execution Time Comparison for {BENCHMARK_DISPLAY_MAP.get(benchmark, benchmark.upper())}"
            )
            continue

        # Sort by query name using natural sorting
        df["sort_key_num"] = df["query"].str.extract(r"(\d+)", expand=False).astype(int)
        df["sort_key_char"] = df["query"].str.extract(r"([a-zA-Z])", expand=False).fillna("")
        df.sort_values(by=["sort_key_num", "sort_key_char"], inplace=True)
        df.drop(columns=["sort_key_num", "sort_key_char"], inplace=True)
        
        # --- 1. Print Query Times Table ---
        print("\n--- Query Execution Times (s) ---")
        df_display = df.copy()
        df_display["lambdatune"] = df_display["lambdatune"].map('{:.2f}'.format)
        df_display["ours"] = df_display["ours"].map('{:.2f}'.format)
        df_display.rename(columns={"lambdatune": "Lambda-Tune", "ours": "Ours"}, inplace=True)
        print(df_display.to_string(index=False))

        x = np.arange(len(df))
        width = 0.4

        # --- 2. Display as λ-Tune ---
        ax.bar(x - width / 2, df["lambdatune"], width, label=r"$\lambda$-Tune", color="#1f77b4")
        ax.bar(x + width / 2, df["ours"], width, label="Ours", color="#ff7f0e")

        ax.set_ylabel("Execution Time (s)")
        ax.set_title(
            f"Query Execution Time Comparison for {BENCHMARK_DISPLAY_MAP.get(benchmark, benchmark.upper())}"
        )
        ax.set_xticks(x)
        ax.set_xticklabels(df["query"], rotation=90)
        ax.grid(axis="y", linestyle="--", alpha=0.7)
        
        if benchmark in ["job", "tpcds"]:
            ax.set_yscale("log")
            ax.set_ylim(bottom=0.01)

        # --- 3. Use axis-level legend to prevent overlap ---
        ax.legend()

    plt.tight_layout()
    
    # Save files
    png_file = f"{OUTPUT_FILENAME}.png"
    pdf_file = f"{OUTPUT_FILENAME}.pdf"
    plt.savefig(png_file, bbox_inches="tight")
    plt.savefig(pdf_file, bbox_inches="tight")
    print(f"\nSaved combined plot to {png_file} and {pdf_file}")
    plt.close(fig)

    print("\n--- Plot Generation Finished ---")

if __name__ == "__main__":
    main()
