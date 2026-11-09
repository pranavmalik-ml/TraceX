import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

from builder import build_graph
from traversal import bfs_trace


# ---------------------------------------
# 1. SETTINGS
# ---------------------------------------

START_ACCOUNT = "A"
MAX_HOPS = 3


# ---------------------------------------
# 2. LOAD TRANSACTION DATA
# ---------------------------------------

df = pd.read_csv("data/transactions.csv")

transactions = df.to_dict(orient="records")


# ---------------------------------------
# 3. BUILD TRACEX GRAPH
# ---------------------------------------

graph = build_graph(transactions)


# ---------------------------------------
# 4. RUN BFS TRACE
# ---------------------------------------

trace_nodes = bfs_trace(
    graph,
    START_ACCOUNT,
    MAX_HOPS
)

trace_nodes = set(trace_nodes)

print("Trace starting from:", START_ACCOUNT)
print("Maximum hops:", MAX_HOPS)
print("Accounts discovered:", trace_nodes)

# ---------------------------------------
# 4B. CALCULATE HOP LEVELS
# ---------------------------------------

hop_levels = nx.single_source_shortest_path_length(
    graph,
    START_ACCOUNT,
    cutoff=MAX_HOPS
)

print("Hop levels:")
print(hop_levels)


# ---------------------------------------
# 5. CREATE GRAPH LAYOUT
# ---------------------------------------

pos = {
    "A": (0, 0),

    "B": (3, 1),

    "C": (6, 1),
    "D": (3, 4),

    "E": (9, 3),
    "F": (6, 5),

    "K": (3, -3),
    "L": (6, -4),

    # Unrelated network
    "G": (9, -5),
    "H": (11, -3),
    "I": (13, -1),
    "J": (14, -4),
}

# Give any unknown accounts an automatic position
remaining_nodes = [
    node for node in graph.nodes()
    if node not in pos
]

if remaining_nodes:
    extra_pos = nx.spring_layout(
        graph.subgraph(remaining_nodes),
        seed=42
    )

    for node in remaining_nodes:
        x, y = extra_pos[node]
        pos[node] = (x + 5, y - 5)

# ---------------------------------------
# 6. NODE APPEARANCE
# ---------------------------------------

node_colors = []

for node in graph.nodes():

    if node == START_ACCOUNT:
        node_colors.append("red")

    elif node in trace_nodes:
        node_colors.append("orange")

    else:
        node_colors.append("lightgray")

node_sizes = []

for node in graph.nodes():

    if node == START_ACCOUNT:
        node_sizes.append(2800)

    elif node in trace_nodes:
        node_sizes.append(2200)

    else:
        node_sizes.append(1800)


# ---------------------------------------
# 7. EDGE APPEARANCE
# ---------------------------------------

trace_edges = set()

for source, target, key in graph.edges(keys=True):

    if source in trace_nodes and target in trace_nodes:
        trace_edges.add((source, target, key))



# ---------------------------------------
# 8. DRAW NODES
# ---------------------------------------

plt.figure(figsize=(14, 9))

nx.draw_networkx_nodes(
    graph,
    pos,
    node_color=node_colors,
    node_size=node_sizes
)


# ---------------------------------------
# 9. DRAW EDGES
# ---------------------------------------

for source, target, key in graph.edges(keys=True):

    if (source, target, key) in trace_edges:
        edge_color = "red"
        edge_width = 3
    else:
        edge_color = "gray"
        edge_width = 2

    # Default curve
    rad = 0.0

    # Special handling for important edges
    if source == "B" and target == "C":
        rad = 0.0

    elif source == "E" and target == "B":
        rad = 0.20

    elif source == "C" and target == "E":
        rad = -0.08

    elif source == "B" and target == "D":
        rad = 0.05

    elif source == "A" and target == "B":
        rad = 0.0

    elif source == "A" and target == "K":
        rad = 0.05

    nx.draw_networkx_edges(
        graph,
        pos,
        edgelist=[(source, target)],
        edge_color=edge_color,
        width=edge_width,
        arrows=True,
        arrowsize=28,
        arrowstyle="-|>",
        connectionstyle=f"arc3,rad={rad}",
        min_source_margin=20,
        min_target_margin=30
    )


# ---------------------------------------
# 10. DRAW ACCOUNT NAMES
# ---------------------------------------

nx.draw_networkx_labels(
    graph,
    pos,
    font_size=11,
    font_weight="bold"
)


# ---------------------------------------
# 11. DRAW TRANSACTION AMOUNTS
# ---------------------------------------

edge_labels = {}

for source, target, key, data in graph.edges(
    keys=True,
    data=True
):

    edge_labels[(source, target, key)] = (
    f"₹{data['amount']:,.0f}"
)


nx.draw_networkx_edge_labels(
    graph,
    pos,
    edge_labels=edge_labels,
    font_size=9,
    label_pos=0.5,
    rotate=False,
    bbox=dict(
        alpha=0.8,
        edgecolor="none",
        facecolor="white"
    )
)

# ---------------------------------------
# 12. TITLE
# ---------------------------------------

plt.title(
    f"TraceX Transaction Investigation\n"
    f"Starting Account: {START_ACCOUNT} | "
    f"Max Hops: {MAX_HOPS}"
)


# ---------------------------------------
# 13. SHOW GRAPH
# ---------------------------------------

plt.axis("off")

plt.tight_layout()

from matplotlib.lines import Line2D

legend_items = [
    Line2D(
        [0], [0],
        marker="o",
        color="w",
        label="Starting Account",
        markerfacecolor="red",
        markersize=12
    ),

    Line2D(
        [0], [0],
        marker="o",
        color="w",
        label="Traced Account",
        markerfacecolor="orange",
        markersize=12
    ),

    Line2D(
        [0], [0],
        marker="o",
        color="w",
        label="Unrelated Account",
        markerfacecolor="lightgray",
        markersize=12
    ),

    Line2D(
        [0], [0],
        color="red",
        linewidth=3,
        label="Traced Transaction"
    ),

    Line2D(
        [0], [0],
        color="gray",
        linewidth=2,
        label="Other Transaction"
    )
]

plt.legend(
    handles=legend_items,
    loc="upper left"
)

plt.show()