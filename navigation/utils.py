import heapq
import math
from typing import List, Optional, Tuple, Dict

from models.systems.waypoint import Waypoint
from navigation.models.route_details import RouteDetails


def distance_between(waypoint1: Waypoint, waypoint2: Waypoint) -> float:
    x_delta = waypoint1.x - waypoint2.x
    y_delta = waypoint1.y - waypoint2.y
    return math.sqrt(x_delta ** 2 + y_delta ** 2)


def dijkstra_shortest_path(
        routes: List[RouteDetails],
        start: str,
        end: str
) -> Optional[List[str]]:
    """
    Find the shortest path between two waypoints using Dijkstra's algorithm.

    Args:
        routes: List of RouteDetails (graph edges).
        start: Symbol of the starting waypoint.
        end: Symbol of the destination waypoint.

    Returns:
        (total_distance, path as list of waypoint symbols), or None if no path.
    """
    # Build adjacency list
    graph: Dict[str, List[Tuple[str, float]]] = {}
    for route in routes:
        src, dst, dist = route.source.symbol, route.dest.symbol, route.total_distance
        graph.setdefault(src, []).append((dst, dist))
        graph.setdefault(dst, []).append((src, dist))  # undirected

    # Priority queue for Dijkstra (distance, node, path)
    pq: List[Tuple[float, str, List[str]]] = [(0.0, start, [start])]
    visited: Dict[str, float] = {}

    while pq:
        current_dist, node, path = heapq.heappop(pq)

        # Skip if we already found a better path
        if node in visited and visited[node] <= current_dist:
            continue
        visited[node] = current_dist

        # Destination reached
        if node == end:
            return path

        # Expand neighbors
        for neighbor, weight in graph.get(node, []):
            if neighbor not in visited or current_dist + weight < visited[neighbor]:
                heapq.heappush(pq, (current_dist + weight, neighbor, path + [neighbor]))

    raise Exception("No path found")


