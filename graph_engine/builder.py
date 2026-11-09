import networkx as nx

def build_graph(transactions):
    graph = nx.MultiDiGraph()

    for transaction in transactions:
        sender = transaction["sender"]
        receiver = transaction["receiver"]
        amount = transaction["amount"]

        graph.add_edge(
            sender,
            receiver,
            transaction_id=transaction["transaction_id"],
            amount=amount,
            timestamp=transaction["timestamp"]
        )

    return graph
