from collections import deque


def bfs_trace(graph, start, max_hops):
    visited = set()
    queue = deque([(start, 0)])
    result = []

    while queue:
        current, hops = queue.popleft()

        if current in visited:
            continue

        visited.add(current)
        result.append(current)

        if hops >= max_hops:
            continue

        for neighbour in graph.successors(current):
            if neighbour not in visited:
                queue.append((neighbour, hops + 1))

    return result


def bfs_trace_backward(graph, start, max_hops):
    visited = set()
    queue = deque([(start, 0)])
    result = []

    while queue:
        current, hops = queue.popleft()

        if current in visited:
            continue

        visited.add(current)
        result.append(current)

        if hops >= max_hops:
            continue

        for neighbour in graph.predecessors(current):
            if neighbour not in visited:
                queue.append((neighbour, hops + 1))

    return result


def get_neighbours(graph, account):
    return {
        "incoming": list(graph.predecessors(account)),
        "outgoing": list(graph.successors(account))
    }


def get_account_metrics(graph, account):
    return {
        "fan_in": graph.in_degree(account),
        "fan_out": graph.out_degree(account)
    }