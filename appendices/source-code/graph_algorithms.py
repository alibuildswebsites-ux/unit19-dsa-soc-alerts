"""Shortest-path algorithms used for a small SOC network example."""

from __future__ import annotations

import heapq
import math
from itertools import count
from collections.abc import Mapping, Sequence
from numbers import Real
from typing import TypeVar

N = TypeVar("N")
Graph = Mapping[N, Sequence[tuple[N, Real]]]


class NegativeCycleError(ValueError):
    """A negative-weight cycle is reachable from the requested source."""


def _validated_edges(graph: Graph[N], source: N) -> list[tuple[N, N, float]]:
    if source not in graph:
        raise ValueError("source node is not present in graph")
    edges: list[tuple[N, N, float]] = []
    for origin, neighbours in graph.items():
        for destination, weight in neighbours:
            if destination not in graph:
                raise ValueError(f"edge endpoint {destination!r} is not present in graph")
            if isinstance(weight, bool) or not isinstance(weight, Real) or not math.isfinite(float(weight)):
                raise ValueError("edge weights must be finite real numbers")
            edges.append((origin, destination, float(weight)))
    return edges


def dijkstra(graph: Graph[N], source: N) -> dict[N, float]:
    """Return distances from source using a min-heap; requires non-negative edges."""
    edges = _validated_edges(graph, source)
    if any(weight < 0 for _, _, weight in edges):
        raise ValueError("Dijkstra requires non-negative edge weights")
    distances = {node: math.inf for node in graph}
    distances[source] = 0.0
    sequence = count()
    frontier: list[tuple[float, int, N]] = [(0.0, next(sequence), source)]
    # Stale heap entries are ignored after a shorter route updates a node.
    while frontier:
        distance, _, node = heapq.heappop(frontier)
        if distance != distances[node]:
            continue
        for neighbour, weight in graph[node]:
            candidate = distance + float(weight)
            if candidate < distances[neighbour]:
                distances[neighbour] = candidate
                heapq.heappush(frontier, (candidate, next(sequence), neighbour))
    return distances


def bellman_ford(graph: Graph[N], source: N) -> dict[N, float]:
    """Return distances in O(VE), supporting negative edges and detecting cycles."""
    edges = _validated_edges(graph, source)
    distances = {node: math.inf for node in graph}
    distances[source] = 0.0
    # A shortest simple path contains at most V-1 edges.
    for _ in range(max(0, len(graph) - 1)):
        changed = False
        for origin, destination, weight in edges:
            if distances[origin] != math.inf and distances[origin] + weight < distances[destination]:
                distances[destination] = distances[origin] + weight
                changed = True
        if not changed:
            break
    # One further relaxation would prove a reachable negative-weight cycle.
    for origin, destination, weight in edges:
        if distances[origin] != math.inf and distances[origin] + weight < distances[destination]:
            raise NegativeCycleError("reachable negative-weight cycle detected")
    return distances
