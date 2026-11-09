import networkx as nx


def find_path(graph, source, target):
    try:
        return nx.shortest_path(graph, source, target)
    except nx.NetworkXNoPath:
        return []