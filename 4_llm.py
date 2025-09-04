import json
import pathlib
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

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
benchmarks = ["JOB", "TPCH"]
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
pivot_df = df.pivot(index="benchmark", columns="model", values="best_time").reindex(models, axis=1)

fig, ax = plt.subplots(figsize=(12, 8))
pivot_df.plot(kind="bar", ax=ax, width=0.8)

ax.set_title("LLM Model Comparison", pad=20)
ax.set_ylabel("Best Time (s)")
ax.set_xlabel("")
ax.set_xticklabels(pivot_df.index, rotation=0)
ax.grid(axis="y", linestyle="--", alpha=0.7)

# Add annotations
for container in ax.containers:
    ax.bar_label(container, fmt="%.1f", padding=3, fontsize=16, weight="bold")

# Rename legend labels
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles, [display_names[label] for label in labels], title="Model")

plt.tight_layout()
plt.savefig("4_llm_comparison.png", bbox_inches="tight")
plt.savefig("4_llm_comparison.pdf", bbox_inches="tight")
plt.show()

print("\n--- Script Finished ---")
