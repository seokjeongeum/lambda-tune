import os
import glob
import json
import math
import matplotlib.pyplot as plt

# Find all JSON files matching the structure "test/e4/<token>/<method>/reports.json"
file_paths = glob.glob("test/e4/*/*/reports.json")
if not file_paths:
    print("No files found matching the pattern.")
    exit(1)

# Group data by token budget and method
# Structure: data_group[token][method] = {"x": [...], "y": [...]}
data_group = {}

for file_path in file_paths:
    parts = file_path.split(os.sep)
    # Expecting parts like: ['test', 'e4', '<token>', '<method>', 'reports.json']
    if len(parts) < 5:
        continue
    token = parts[2]  # e.g. "196", "251", etc.
    method = parts[3]  # e.g. "lambdatune" or "naive"

    # Load JSON data
    with open(file_path, "r") as f:
        records = json.load(f)

    # Iterate over each record to extract duration_seconds and best_execution_time.
    for record in records:
        x_val = record.get("duration_seconds")
        best_time = record.get("best_execution_time")
        # Skip entries with missing values or non-finite best_execution_time
        if x_val is None or best_time is None or math.isinf(best_time):
            continue
        data_group.setdefault(token, {}).setdefault(method, {"x": [], "y": []})
        data_group[token][method]["x"].append(x_val)
        data_group[token][method]["y"].append(best_time)

# Get sorted list of token budgets
tokens = sorted(data_group.keys())

# Create one subplot per token budget
n_groups = len(tokens)
fig, axs = plt.subplots(1, n_groups, figsize=(6 * n_groups, 5), squeeze=False)

# Define marker styles for each method
method_markers = {"lambdatune": "o", "naive": "^"}

# Plot data for each token group using line plots
for i, token in enumerate(tokens):
    ax = axs[0, i]
    methods = data_group[token]
    for method, values in methods.items():
        # Sort the data by x value to create a proper line plot
        if len(values["x"]) > 1:
            sorted_pairs = sorted(
                zip(values["x"], values["y"]), key=lambda pair: pair[0]
            )
            sorted_x, sorted_y = zip(*sorted_pairs)
        else:
            sorted_x, sorted_y = values["x"], values["y"]
        ax.plot(
            sorted_x,
            sorted_y,
            label=method,
            marker=method_markers.get(method, "o"),
            alpha=0.8,
        )
    ax.set_title(f"Token budget: {token}")
    ax.set_xlabel("duration_seconds")
    ax.set_ylabel("best_execution_time")
    ax.legend()
    ax.grid(True)

plt.tight_layout()
# Save the figure as we're in a headless environment
output_filename = "plot.png"
plt.savefig(output_filename)
plt.close()
print(f"Plot saved to {output_filename}")
