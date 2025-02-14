from datetime import datetime

from pydantic import BaseModel

from models.systems.waypoint import Waypoint


class ShipRoute(BaseModel):
    destination: Waypoint
    origin: Waypoint
    departureTime: datetime
    arrival: datetime


class ShipNav(BaseModel):
    systemSymbol: str
    waypointSymbol: str
    route: ShipRoute
    status: str
    flightMode: str
