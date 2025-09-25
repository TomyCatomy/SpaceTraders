from typing import List

from client.client import Client
from models.systems.waypoint import Waypoint
from navigation.utils import distance_between


async def get_system_waypoints(client: Client, system_symbol: str):
    waypoints: List[Waypoint] = await client.systems.list_waypoints(system_symbol)
    return waypoints


def find_navigation_route(
        waypoint_route: List[Waypoint],
        dest_waypoint: Waypoint,
        waypoints: List[Waypoint],
        max_hop_distance: int
) -> List[Waypoint]:
    if distance_between(waypoint_route[-1], dest_waypoint) < max_hop_distance:
        waypoint_route.append(dest_waypoint)
        return waypoint_route

    in_range_waypoints = list(filter(
        lambda waypoint: distance_between(waypoint_route[-1], waypoint) <= max_hop_distance,
        waypoints
    ))
    sorted_waypoints = sort_waypoints_by_distance(dest_waypoint, in_range_waypoints)
    for next_hop_option in sorted_waypoints:
        if (next_hop_option.x, next_hop_option.y) in [(waypoint.x, waypoint.y) for waypoint in waypoint_route]:
            continue

        option_route = waypoint_route.copy()
        option_route.append(next_hop_option)
        result_route = find_navigation_route(
            option_route,
            dest_waypoint,
            waypoints,
            max_hop_distance,
        )
        if result_route[-1] == dest_waypoint:
            return result_route

    return waypoint_route


def sort_waypoints_by_distance(reference_waypoint: Waypoint, waypoint_list: List[Waypoint]) -> List[Waypoint]:
    sorted_waypoint_list = waypoint_list.copy()
    sorted_waypoint_list.sort(key=lambda waypoint: distance_between(reference_waypoint, waypoint))
    return sorted_waypoint_list
