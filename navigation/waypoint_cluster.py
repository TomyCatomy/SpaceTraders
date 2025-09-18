import asyncio
from collections import deque
from typing import Dict, List, Set, Optional, Tuple

from Scripts.mongodb_utils import upsert_many_to_unique_object_collection
from client.client import Client
from config import config
from models.systems.waypoint import Waypoint
from navigation.models.route_details import RouteDetails
from navigation.utils import distance_between
from utils.system_info_utils import find_intra_cluster_voyage_route, get_system_waypoints


# ---------------- Helper Functions ----------------


def compute_neighbors(waypoints: List[Waypoint], max_distance: float) -> Dict[str, Set[str]]:
    """Precompute neighbors within distance d for all waypoints"""
    neighbors_map: Dict[str, Set[str]] = {}
    for w1 in waypoints:
        neighbors_map[w1.symbol] = {
            w2.symbol for w2 in waypoints
            if w1.symbol != w2.symbol and distance_between(w1, w2) <= max_distance
        }
    return neighbors_map


def expand_cluster(waypoint_symbol: str, neighbours_map: Dict[str, Set[str]], min_neighbours: int) -> Optional[Set[str]]:
    """
    Expand a cluster starting from a seed waypoint using the core-neighbor logic.
    Returns the full set of waypoints in this cluster.
    """
    local_neighbors = neighbours_map[waypoint_symbol]
    if len(local_neighbors) < min_neighbours:
        return None  # Not enough neighbors to form a cluster

    core: Set[str] = {waypoint_symbol}
    stack: List[str] = list(local_neighbors)
    cluster_set: Set[str] = set(core | local_neighbors)

    while stack:
        waypoint = stack.pop()
        if waypoint in core:
            continue

        waypoint_neighbours = neighbours_map[waypoint]
        for core_waypoint in list(core):
            core_waypoint_neighbors = neighbours_map[core_waypoint]
            if len(waypoint_neighbours & core_waypoint_neighbors) >= min_neighbours:
                core.add(waypoint)
                stack.extend([waypoint for waypoint in core_waypoint_neighbors if waypoint not in core])
                cluster_set.update(core_waypoint_neighbors)
                cluster_set.add(core_waypoint)
                break

    return cluster_set


def assign_remaining_waypoints(
        clusters: List[List[str]],
        neighbors_map: Dict[str, Set[str]]
) -> None:
    """
    Assign waypoints that were not included in any cluster
    by proximity to existing clusters.
    """
    unassigned: deque[str] = deque(
        [waypoint for waypoint in neighbors_map if all(waypoint not in cluster for cluster in clusters)]
    )

    while unassigned:
        waypoint = unassigned.popleft()
        assigned = False
        for cluster in clusters:
            if any(waypoint in neighbors_map[core_waypoint] for core_waypoint in cluster):
                cluster.append(waypoint)
                assigned = True
                break
        if not assigned:
            unassigned.append(waypoint)  # Requeue if not assigned yet


# ---------------- Main Function ----------------

def cluster_waypoints(
        neighbors_map: Dict[str, Set[str]],
        min_neighbours: int
) -> List[List[str]]:
    """
    Cluster waypoints based on proximity and minimum connections.
    """
    clusters: List[List[str]] = []
    evaluated: Set[str] = set()

    # Step 1: Build clusters
    for waypoint in neighbors_map:
        if waypoint in evaluated:
            continue
        cluster_set = expand_cluster(waypoint, neighbors_map, min_neighbours)
        if not cluster_set:
            evaluated.add(waypoint)
            continue
        clusters.append(list(cluster_set))
        evaluated.update(cluster_set)

    # Step 2: Assign remaining waypoints
    assign_remaining_waypoints(clusters, neighbors_map)

    return clusters


def intercluster_neighbor_pairs(
    neighbors_map: Dict[str, Set[str]],
    cluster_index: Dict[str, str]
) -> List[Tuple[str, str]]:
    """
    Return all neighbor pairs where the waypoints belong to different clusters.
    Each pair is returned only once (w1, w2) with w1 < w2 for uniqueness.
    """
    pairs: Set[Tuple[str, str]] = set()

    for w1, neighbors in neighbors_map.items():
        for w2 in neighbors:
            pair = (w1, w2)
            if cluster_index[w1] != cluster_index[w2]:
                pair = (min(*pair), max(*pair))
                pairs.add(pair)

    return list(pairs)


def get_cluster_index(clusters: list[list[str]]) -> dict[str, str]:
    """Build lookup from waypoint -> cluster index"""
    cluster_index: Dict[str, str] = {}
    for cluster in clusters:
        index = cluster[0]
        for waypoint in cluster:
            cluster_index[waypoint] = index
    return cluster_index


def border_waypoint_pairs(
    intercluster_pairs: List[Tuple[str, str]],
    clusters: List[List[str]]
) -> List[Tuple[str, str]]:
    """
    Given inter-cluster neighbor pairs and clusters, return for each cluster
    a list of all pairings (combinations) of border waypoints within that cluster.
    """
    # Map waypoint -> cluster index
    cluster_index: Dict[str, int] = {}
    for index, cluster in enumerate(clusters):
        for waypoint in cluster:
            cluster_index[waypoint] = index

    # Collect border waypoints for each cluster
    border_points: Dict[int, Set[str]] = {i: set() for i in range(len(clusters))}
    for w1, w2 in intercluster_pairs:
        border_points[cluster_index[w1]].add(w1)
        border_points[cluster_index[w2]].add(w2)

    # Generate all intra-cluster pairings of border waypoints
    result: List[Tuple[str, str]] = []
    for index, cluster in enumerate(clusters):
        cluster_border_points = sorted(border_points[index])
        pairings: List[Tuple[str, str]] = []
        for i in range(len(cluster_border_points)):
            for j in range(i + 1, len(cluster_border_points)):
                pair = (cluster_border_points[i], cluster_border_points[j])
                pairings.append((min(*pair), max(*pair)))
        result.extend(pairings)

    return result


def get_voyage_details(source: Waypoint, dest: Waypoint, waypoints: List[Waypoint], max_hop_distance: int) -> RouteDetails:
    voyage_waypoints = find_intra_cluster_voyage_route([source], dest, waypoints, max_hop_distance)
    total_distance = 0
    for index, waypoint in voyage_waypoints[:-1]:
        total_distance += distance_between(waypoint, index + 1)

    return RouteDetails(
        system=source.systemSymbol,
        source=source,
        dest=dest,
        route_waypoints=[waypoint.symbol for waypoint in voyage_waypoints],
        total_distance=total_distance
    )


async def cache_waypoint_clusters(client: Client, system_symbol: str) -> None:
    waypoints = await get_system_waypoints(client, system_symbol)
    waypoint_dict = {waypoint.symbol: waypoint for waypoint in waypoints}
    neighbours_map = compute_neighbors(waypoints, max_distance=400)
    clusters = cluster_waypoints(neighbours_map, 3)
    cluster_index = get_cluster_index(clusters)
    intercluster_pairs = intercluster_neighbor_pairs(neighbours_map, cluster_index)
    border_waypoints: Set[str] = set()
    for w1, w2 in intercluster_pairs:
        border_waypoints.update({ w1, w2 })

    for waypoint_symbol in waypoint_dict:
        waypoint = waypoint_dict[waypoint_symbol]
        waypoint.internal_cluster_id = cluster_index[waypoint_symbol]
        waypoint.internal_is_cluster_border = waypoint_symbol in border_waypoints


    border_pairs = border_waypoint_pairs(intercluster_pairs, clusters)
    pairs_to_compute_nav_routes = intercluster_pairs + border_pairs
    pair_voyages_details = [
        get_voyage_details(waypoint_dict[w1], waypoint_dict[w2], waypoints, 50)
        for w1, w2 in pairs_to_compute_nav_routes
    ]
    await asyncio.gather(
        upsert_many_to_unique_object_collection(config.agent_symbol, "WAYPOINTS", list(waypoint_dict.values()), unique_index="symbol"),
        upsert_many_to_unique_object_collection(config.agent_symbol, "ROUTE_DETAILS", pair_voyages_details, unique_index="route_id")
    )

