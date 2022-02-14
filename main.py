from typing import List, Tuple, Set, Callable, Optional, Dict
import networkx as nx
import mappings


def read_input() -> Tuple[Set[str], List[Tuple[str, str]]]:
    """
    Read the votes with the format:
    username
    poll_option
    username
    poll_option

    This is the format that I get when copy-pasting from groupme.
    """
    print('Input User Votes...')
    users = set()
    votes = []
    name = input()
    while name != "done":
        users.add(name)
        vote = input()
        votes.append((name, vote))
        name = input()

    return users, votes


def extract_poll_votes(user_votes: List[Tuple[str, str]], poll_answers: Set[str]) -> List[Tuple[str, str]]:
    """
    Get the votes matching specific poll answers

    :param user_votes: list of (user, vote) tuples
    :param poll_answers: set of possible answers to this poll
    :return: list of (user, vote) tuples for the current poll
    """

    output = []
    for user, vote in user_votes:
        if vote in poll_answers:
            output.append((user, vote))

    return output


def parse_nodes(users: Set[str]) -> nx.Graph:
    """
    Add user nodes to graph
    """

    graph = nx.Graph()

    for user in users:
        graph.add_node(user)

    return graph


def add_edges(graph: nx.Graph, votes: List[Tuple[str, str]], mapping: Dict[str, Dict[str, int]],
              poll_weight: int) -> nx.Graph:
    """
    For each poll response, add a weighted edge to all other users.

    :param graph: graph with all users added
    :param votes: list of all votes about this poll
    :param mapping: dict of dicts that tells what the edge weight should be
    :param poll_weight: multiplier to put on this poll's edge weights
    :return: graph with edges created/added to
    """

    vote_users = dict()

    for user, vote in votes:
        if len(vote_users.keys()) != 0:
            # Iterate over all existing users
            for e_vote, e_users in vote_users.items():
                score = mapping[vote][e_vote] * poll_weight
                for e_user in e_users:
                    curr_score = score
                    common_polls = 1
                    if graph.has_edge(user, e_user):
                        curr_score = graph.get_edge_data(user, e_user, 0)["weight"]
                        curr_score += score
                        common = graph.get_edge_data(user, e_user, 0)["common"]
                        common_polls += common
                        graph.remove_edge(user, e_user)
                    graph.add_edge(user, e_user, weight=curr_score, common=common_polls)

        if vote in vote_users.keys():
            vote_users[vote].append(user)
        else:
            vote_users[vote] = [user]

    return graph


def prune_edges(graph: nx.Graph, min_polls: int = 1) -> nx.Graph:
    """
    Delete edges where users didn't answer any of the same polls

    Normalize edge scores for users that did

    :param graph: graph with all users added and connected with edge weights
    :param min_polls: minimum polls users must have in common
    :return: graph with irrelevant pairings pruned
    """

    output = nx.Graph()

    for node in graph.nodes:
        output.add_node(node)

    pruned = 0

    for i, j, d in graph.edges(data=True):
        weight = d.get("weight", 0)
        common = d.get("common", 0)

        bonus = common / 100
        calc_weight = weight / common + bonus
        if common >= min_polls:
            output.add_edge(i, j, weight=calc_weight)
        else:
            pruned += 1

    print("Pruned", pruned, "edges")

    return output


def prune_nodes(graph: nx.Graph, min_polls: int = 0, verbose: bool = True) -> nx.Graph:
    """
    Remove edgeless nodes

    :param graph: graph with edges pruned
    :param min_polls: minimum polls users must have in common (same as prune_edges)
    :param verbose: print every pruned user
    :return: graph with edgeless nodes pruned
    """

    nodes = set(graph.nodes)

    for i, j in graph.edges:
        if i in nodes:
            nodes.remove(i)
        if j in nodes:
            nodes.remove(j)

    print(len(nodes), "users answered <", min_polls, "polls, pruned.")
    for node in nodes:
        graph.remove_node(node)
        if verbose:
            print(node, "pruned")

    return graph


def invert_graph_weights(graph: nx.graph) -> nx.graph:
    """
    Invert all scores. Useful if you want a "worst" pairing

    :param graph: graph with edges
    :return: graph with all-positive weight edges with inverse ranking
    """

    max_weight = 0
    for i, j, d in graph.edges(data=True):
        max_weight = d.get("weight", 0) if d.get("weight", 0) > max_weight else max_weight

    max_weight += 0.01

    output = nx.Graph()

    for node in graph.nodes:
        output.add_node(node)

    for i, j, d in graph.edges(data=True):
        output.add_edge(i, j, weight=max_weight - d.get("weight", 0))

    return output


def combine_pairings(graph: nx.Graph, pairings: Set[Tuple[str, str]]) -> nx.Graph:
    """
    Combine pairings into clusters

    Add together existing edge weights

    :param graph: graph pairings were generated from
    :param pairings: node pairings
    :return: graph where node pairings are now single nodes
    """

    combined_graph = graph.copy()

    straggler = print_straggler(pairings, graph)

    if straggler is not None:
        strongest_edge = (-1, None)

        for i, j, d in graph.edges(data=True):
            if i == straggler:
                if strongest_edge[0] < d.get("weight", 0):
                    strongest_edge = (d.get("weight", 0), j)

        # Merge straggler into its first choice
        a = strongest_edge[1]
        b = straggler
        node_name = str(a) + " + " + str(b)
        combined_graph.add_node(node_name)

        # add edges from a and b, adding scores together if they go to the same target
        edges_to_add = dict()

        for i, j, d in combined_graph.edges(data=True):
            weight = d.get("weight", 0)
            if (i == a and j == b) or (i == b and j == a):
                continue
            elif i == a:
                edges_to_add[j] = weight

        combined_graph.remove_node(straggler)

        for node, weight in edges_to_add.items():
            combined_graph.add_edge(node_name, node, weight=weight)

    # Process non-straggler pairings
    for pairing in pairings:
        a = pairing[0]
        b = pairing[1]
        node_name = a + " + " + b
        combined_graph.add_node(node_name)

        # add edges from a and b, adding scores together if they go to the same target
        edges_to_add = dict()

        for i, j, d in combined_graph.edges(data=True):
            weight = d.get("weight", 0)
            if (i == a and j == b) or (i == b and j == a):
                continue
            elif i == a or i == b:
                if combined_graph.has_edge(node_name, j):
                    score = combined_graph.get_edge_data(node_name, j, 0)["weight"]
                    weight += score
                edges_to_add[j] = weight
            elif j == a or j == b:
                if combined_graph.has_edge(node_name, i):
                    score = combined_graph.get_edge_data(node_name, i, 0)["weight"]
                    weight += score
                edges_to_add[i] = weight

        combined_graph.remove_node(a)
        combined_graph.remove_node(b)

        for node, weight in edges_to_add.items():
            combined_graph.add_edge(node_name, node, weight=weight)

    return combined_graph


def cluster(graph: nx.Graph, cluser_power: int) -> Set[Tuple[str, str]]:
    """
    Run the pairing algorithm the specified number of times to make teams or clusters of users

    :param graph: graph with nodes and edges
    :param cluser_power: number of times to cluster
    :return: clusters
    """

    graph = graph.copy()
    pairings = set()

    for power in range(cluser_power):
        pairings = nx.algorithms.max_weight_matching(graph)
        graph = combine_pairings(graph, pairings)
        print(graph)

    return pairings


def check_stability(pairings: Set[Tuple[str, str]], graph: nx.Graph, function: Callable[[nx.Graph], Set[Tuple[str]]],
                    checks: int = 20):
    """
    Repeat the function and check if the output changes

    :param pairings: result from the first time you ran the function
    :param graph: graph you ran the function on
    :param function: function to run
    :param checks: number of times to run the function
    :return: None
    """

    diff = 0
    for i in range(checks):
        graph = graph.copy()
        diff += len(function(graph).difference(pairings))

    print("\nStable Matching:", diff == 0, "Avg Diff:", diff / checks, "pairings out of", len(pairings), "total")
    print("Confidence Level:", (len(pairings) - diff / checks) / len(pairings))


def print_straggler(pairings: Set[Tuple[str, str]], graph: nx.Graph) -> Optional[str]:
    """
    Find any unpaired nodes with edges

    :param pairings: graph pairings
    :param graph: initial graph
    :return: straggler node if it exists
    """
    # Check for unpaired:
    matched = set()
    for pairing in pairings:
        matched.add(pairing[0])
        matched.add(pairing[1])

    straggler = None

    for node in graph.nodes:
        if node not in matched:
            print("Straggler Found:", node)
            straggler = node
            break

    return straggler


def print_pairings(pairings: Set[Tuple[str, str]], graph: nx.Graph = None):
    """
    Print all the pairings to the terminal in csv format
    """

    print("\n", len(pairings), "pairings generated:")
    for pair in pairings:
        if graph is not None:
            weight = round(graph.get_edge_data(pair[0], pair[1])["weight"], 2)
        else:
            weight = ""

        if len(pair[0]) > len(pair[1]):
            print(pair[0], pair[1], weight, sep=", ")
        else:
            print(pair[1], pair[0], weight, sep=", ")


def print_graph_metrics(graph: nx.Graph):
    """
    Print metrics about the given graph
    """

    total = 0
    for i, j, d in graph.edges(data=True):
        total += d.get("weight", 0)

    print()
    if len(graph.edges) > 0:
        print("Average edge weight:", round(total / len(graph.edges), 2))
    if len(graph.nodes) > 0:
        print("Average connections per node:", round(len(graph.edges) / len(graph.nodes), 2))
    print(graph)


def print_superlatives(graph: nx.Graph):
    """
    Print any "high score" or "low score" awards
    """

    largest = 0
    largest_list = []

    for i, j, d in graph.edges(data=True):
        weight = d.get("weight", 0)
        if weight > largest:
            largest = weight
            largest_list = [(i, j)]
        elif weight == largest:
            largest_list.append((i, j))

    print("\nStrongest pairing(s) with weight", largest)
    for pairing in largest_list:
        print(pairing)


def main(polls: List[Dict[str, Dict[str, int]]], poll_weights: List[int]):
    users, votes = read_input()

    graph = parse_nodes(users)

    print_graph_metrics(graph)

    for i, mapping in enumerate(polls):
        poll_votes = extract_poll_votes(votes, set(mapping.keys()))

        print("\n", len(poll_votes), "votes for poll")
        graph = add_edges(graph, poll_votes, mapping, poll_weights[i])

        print_graph_metrics(graph)

    min_polls = 2

    graph = prune_edges(graph, min_polls=min_polls)

    graph = prune_nodes(graph, min_polls=min_polls)

    print_graph_metrics(graph)

    # graph = invert_graph_weights(graph)

    result = nx.algorithms.max_weight_matching(graph)

    print_straggler(result, graph)

    print_pairings(result, graph)

    check_stability(result, graph, nx.algorithms.max_weight_matching)

    print_superlatives(graph)

    print_pairings(cluster(graph, 5))


if __name__ == '__main__':
    # Change these after you add a poll to mappings.py!
    polls = [mappings.poll_1(), mappings.poll_2(), mappings.poll_3()]
    poll_weights = [1, 1, 1]

    main(polls, poll_weights)
