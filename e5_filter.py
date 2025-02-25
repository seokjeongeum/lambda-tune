import os
import glob
import json
import math
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.colors import Normalize

# Define marker styles for each method
method_markers = {"lambdatune": "o", "naive": "^"}

# Find all JSON files matching the structure "test/e5/<token>/<method>/reports.json"
file_paths = glob.glob("test/e5/*/*/reports.json")
if not file_paths:
    print("No files found matching the pattern.")
    exit(1)

# Group data by token and method
# Structure: data_group[token][method] = {"x": [...], "y": [...]}
data_group = {}

for file_path in file_paths:
    parts = file_path.split(os.sep)
    # Expected parts structure: ['test', 'e5', '<token>', '<method>', 'reports.json']
    if len(parts) < 5:
        continue
    token = parts[2]  # Extract token from the third part
    method = parts[3]  # Extract method from the fourth part

    # Load JSON data
    with open(file_path, "r") as f:
        records = json.load(f)

    # Extract duration_seconds and best_execution_time for each record
    for record in records:
        x_val = record.get("duration_seconds")
        best_time = record.get("best_execution_time")
        # Skip records with missing values or infinite best_execution_time
        if x_val is None or best_time is None or math.isinf(best_time):
            continue
        data_group.setdefault(token, {}).setdefault(method, {"x": [], "y": []})
        data_group[token][method]["x"].append(x_val)
        data_group[token][method]["y"].append(best_time)

# Sort tokens numerically (ignoring non-digit tokens by treating them as infinity)
tokens = sorted(
    data_group.keys(), key=lambda x: int(x) if x.isdigit() else float("inf")
)
valid_tokens = [int(x) for x in tokens if x.isdigit()]

# Set up color normalization based on the token values
if valid_tokens:
    norm = Normalize(vmin=min(valid_tokens), vmax=max(valid_tokens))
else:
    norm = Normalize(vmin=0, vmax=1)
cmap = cm.RdBu

# Map each token to a color from the colormap
token_colors = {
    token: cmap(norm(int(token) if token.isdigit() else float("inf")))
    for token in data_group.keys()
}

fig_comb, ax_comb = plt.subplots(figsize=(10, 6))
for token, methods in data_group.items():
    color = token_colors[token]
    for method, values in methods.items():
        if len(values["x"]) > 1:
            sorted_pairs = sorted(
                zip(values["x"], values["y"]), key=lambda pair: pair[0]
            )
            sorted_x, sorted_y = zip(*sorted_pairs)
        else:
            sorted_x, sorted_y = values["x"], values["y"]
        ax_comb.plot(
            sorted_x,
            sorted_y,
            label=f"{method} (Token: {token})",
            marker=method_markers.get(method, "o"),
            color=color,
            alpha=0.8,
        )

# Add a colorbar to represent token values in the plot
sm = cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax_comb, orientation="horizontal", pad=0.2)
cbar.set_label("Token Value")

ax_comb.set_title("Performance Comparison Across Token Budgets")
ax_comb.set_xlabel("duration_seconds")
ax_comb.set_ylabel("best_execution_time")
ax_comb.legend(loc="upper left", bbox_to_anchor=(1.05, 1), borderaxespad=0.0)

plt.tight_layout()
output_comb = "e5_fig.png"
plt.savefig(output_comb)
plt.close(fig_comb)
print(f"Combined plot saved to {output_comb}")
