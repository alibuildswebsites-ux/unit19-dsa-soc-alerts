import math

import pytest

from soc_alerts.graph_algorithms import NegativeCycleError, dijkstra, bellman_ford
from soc_alerts.sorting import insertion_sort, merge_sort


def test_insertion_sort_orders_values_and_is_stable():
    values = [(2, "a"), (1, "b"), (2, "c"), (1, "d")]
    insertion_sort(values, key=lambda item: item[0])
    assert values == [(1, "b"), (1, "d"), (2, "a"), (2, "c")]


def test_merge_sort_orders_values_stably_without_mutating_input():
    values = [(3, "a"), (1, "b"), (3, "c"), (2, "d")]
    assert merge_sort(values, key=lambda item: item[0]) == [
        (1, "b"), (2, "d"), (3, "a"), (3, "c")
    ]
    assert values == [(3, "a"), (1, "b"), (3, "c"), (2, "d")]


def test_sorting_handles_empty_and_single_item_inputs():
    empty = []
    insertion_sort(empty)
    assert empty == []
    assert merge_sort([]) == []
    one = [7]
    insertion_sort(one)
    assert one == [7]
    assert merge_sort([7]) == [7]


def test_dijkstra_finds_shortest_paths_on_nonnegative_soc_network():
    graph = {
        "sensor": [("switch", 4), ("gateway", 2)],
        "switch": [("server", 5)],
        "gateway": [("switch", 1), ("server", 8)],
        "server": [],
        "isolated": [],
    }
    distances = dijkstra(graph, "sensor")
    assert distances["server"] == 8
    assert distances["switch"] == 3
    assert math.isinf(distances["isolated"])


def test_dijkstra_rejects_negative_edge_weights():
    graph = {"a": [("b", -1)], "b": []}
    with pytest.raises(ValueError, match="non-negative"):
        dijkstra(graph, "a")


def test_bellman_ford_supports_negative_edges_and_detects_negative_cycles():
    graph = {
        "a": [("b", 4), ("c", 5)],
        "b": [("c", -2)],
        "c": [],
    }
    assert bellman_ford(graph, "a")["c"] == 2
    cycle = {"a": [("b", 1)], "b": [("a", -2)]}
    with pytest.raises(NegativeCycleError):
        bellman_ford(cycle, "a")


def test_shortest_path_algorithms_validate_source_and_edge_endpoints():
    graph = {"a": [("missing", 1)]}
    with pytest.raises(ValueError, match="source"):
        dijkstra(graph, "unknown")
    with pytest.raises(ValueError, match="endpoint"):
        bellman_ford(graph, "a")


def test_dijkstra_supports_unorderable_node_identifiers_at_equal_distances():
    left, right, goal = object(), object(), object()
    graph = {left: [(goal, 2)], right: [(goal, 2)], goal: []}
    assert dijkstra(graph, left)[goal] == 2


def test_algorithms_match_builtin_sort_for_seeded_data():
    import random

    generator = random.Random(19)
    values = [generator.randrange(-50, 51) for _ in range(200)]
    insertion = values.copy()
    insertion_sort(insertion)
    assert insertion == sorted(values)
    assert merge_sort(values) == sorted(values)
