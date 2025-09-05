import json
import pathlib
import pandas as pd
import matplotlib.pyplot as plt

# --- Configuration ---
plt.rcParams.update({
    "font.size": 18,
    "axes.titlesize": 24,
    "axes.labelsize": 22,
    "xtick.labelsize": 18,
    "ytick.labelsize": 18,
    "legend.fontsize": 18,
})

base_dir = pathlib.Path("test")
benchmarks = ["JOB", "TPCH", "TPCDS"]
models = ["ours", "4_llm"]

display_names = {
    "ours": "Gemini 2.5 Pro",
    "4_llm": "Gemini 2.5 Flash",
}

file_paths = {
    (benchmark, model): (
        base_dir / "4_llm" / benchmark.lower() / "reports.json"
        if model == "4_llm"
        else base_dir / "1_main" / benchmark.lower() / model / "reports.json"
    )
    for benchmark in benchmarks
    for model in models
}

# --- Data Processing ---
results = []
for (benchmark, model), file_path in file_paths.items():
    print(f"--- Processing: {file_path} ---")
    if not file_path.exists():
        print(f"Warning: File not found, skipping.")
        continue

    try:
        with open(file_path, "r") as f:
            reports_data = json.load(f)
            if not reports_data:
                print("Warning: No data in file.")
                continue

        min_best_time = float("inf")
        for report in reports_data:
            best_time = report.get("best_execution_time")
            if best_time is not None and best_time < min_best_time:
                min_best_time = best_time

        if min_best_time != float("inf"):
            results.append({
                "benchmark": benchmark,
                "model": model,
                "best_time": min_best_time,
            })
            print(f"    Best Time for {display_names[model]} on {benchmark}: {min_best_time:.2f}s")
        else:
            print("    No valid execution times found.")

    except (json.JSONDecodeError, IOError) as e:
        print(f"Error processing file {file_path}: {e}")

if not results:
    print("\nNo data processed. Exiting.")
    exit()

# --- Plotting ---
df = pd.DataFrame(results)
pivot_df = df.pivot(index="benchmark", columns="model", values="best_time").reindex(columns=models, index=benchmarks)
pivot_df.fillna(0, inplace=True) # Replace any missing data with 0 for plotting

# Create a subplot for each benchmark for individual y-scales
fig, axes = plt.subplots(
    nrows=1,
    ncols=len(benchmarks),
    figsize=(6 * len(benchmarks), 7),
    sharey=False  # Key parameter to allow different y-axis scales
)
if len(benchmarks) == 1:
    axes = [axes]  # Ensure axes is always iterable

# Plot each benchmark's data on its respective subplot
for ax, benchmark in zip(axes, benchmarks):
    pivot_df.loc[[benchmark]].plot(kind="bar", ax=ax, legend=False, width=0.5)

    ax.set_title(benchmark, pad=20)
    ax.set_xlabel("")
    ax.set_xticklabels([])  # Remove the benchmark name from x-axis ticks
    ax.tick_params(axis='x', length=0)
    ax.grid(axis="y", linestyle="--", alpha=0.7)

    # Annotate bars with their values
    for container in ax.containers:
        ax.bar_label(container, fmt="%.1f", padding=3, fontsize=14, weight="bold")

# Add a shared y-label and a main title for the entire figure
fig.text(0.04, 0.5, 'Best Time (s)', va='center', rotation='vertical', fontsize=22)
fig.suptitle("LLM Model Comparison", fontsize=24, y=1.0)

# Create a single shared legend for the models
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(
    handles,
    [display_names[label] for label in labels],
    title="Model",
    loc="upper center",
    bbox_to_anchor=(0.5, 0.93),
    ncol=len(models)
)

plt.tight_layout(rect=[0.05, 0, 0.98, 0.88])  # Adjust layout to prevent overlap
plt.savefig("4_llm_comparison.png", bbox_inches="tight")
plt.savefig("4_llm_comparison.pdf", bbox_inches="tight")
plt.show()

print("\n--- Script Finished ---")
