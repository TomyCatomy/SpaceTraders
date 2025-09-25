import heapq
from math import sqrt
from typing import Dict, Tuple, Optional, List

from models.systems.waypoint import Waypoint
from navigation.models.route_details import RouteDetails


def distance_between(a: Waypoint, b: Waypoint) -> float:
    """Compute Euclidean distance between two waypoints."""
    return sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)


def dijkstra_shortest_path(
    waypoints: List[Waypoint],
    source: Waypoint,
    dest: Waypoint,
    biggest_hop_allowed: float
) -> Optional[RouteDetails]:
    """
    Compute the shortest route between source and dest waypoints using Dijkstra,
    constrained by a maximum hop distance.
    """
    # Build adjacency list with distance weights
    neighbors: Dict[Waypoint, List[Tuple[Waypoint, float]]] = {w: [] for w in waypoints}
    for i, w1 in enumerate(waypoints):
        for j in range(i + 1, len(waypoints)):
            w2 = waypoints[j]
            dist = distance_between(w1, w2)
            if dist <= biggest_hop_allowed:
                neighbors[w1].append((w2, dist))
                neighbors[w2].append((w1, dist))

    # Dijkstra setup
    pq: List[Tuple[float, Waypoint]] = [(0.0, source)]  # (distance_so_far, waypoint)
    distances: Dict[Waypoint, float] = {w: float("inf") for w in waypoints}
    previous: Dict[Waypoint, Optional[Waypoint]] = {w: None for w in waypoints}
    distances[source] = 0.0

    while pq:
        curr_dist, curr_wp = heapq.heappop(pq)

        if curr_wp == dest:
            break  # Found shortest path to destination

        if curr_dist > distances[curr_wp]:
            continue  # Skip stale entry

        for neighbor, weight in neighbors[curr_wp]:
            new_dist = curr_dist + weight
            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                previous[neighbor] = curr_wp
                heapq.heappush(pq, (new_dist, neighbor))

    # Reconstruct path if reachable
    if distances[dest] == float("inf"):
        return None  # No valid path under biggest_hop_allowed

    route_path: List[str] = []
    biggest_hop_executed = 0.0
    curr: Optional[Waypoint] = dest
    while curr is not None:
        route_path.append(curr.symbol)
        prev = previous[curr]
        if prev is not None:
            hop_dist = distance_between(curr, prev)
            biggest_hop_executed = max(biggest_hop_executed, hop_dist)
        curr = prev

    route_path.reverse()

    return RouteDetails(
        system=source.systemSymbol,
        source=source,
        dest=dest,
        route_waypoints=route_path,
        total_distance=distances[dest],
        biggest_hop_allowed=biggest_hop_allowed,
        biggest_hop_executed=biggest_hop_executed,
    )
