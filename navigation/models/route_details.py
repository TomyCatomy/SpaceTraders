from functools import cached_property
from typing import List

from pydantic import BaseModel, computed_field

from models.systems.waypoint import Waypoint


class RouteDetails(BaseModel):
    system: str
    source: Waypoint
    dest: Waypoint
    route_waypoints: List[str]
    total_distance: float
    biggest_hop_allowed: float
    biggest_hop_executed: float

    @computed_field
    @cached_property
    def route_id(self) -> str:
        ends_waypoints = [self.source, self.dest]
        ends_waypoints.sort(key=lambda waypoint: waypoint.symbol)
        return f"{ends_waypoints[0]}=>{ends_waypoints[1]}"
