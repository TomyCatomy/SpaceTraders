from typing import List, Optional, Dict

from client.httpx_wrapping.internal_client import InternalClient
from models.systems.market import Market
from models.systems.shipyard import Shipyard
from models.systems.system import System
from models.systems.waypoint import Waypoint


class Systems:
    _client: InternalClient

    def __init__(self, client: InternalClient):
        self._client = client

    async def list_systems(self, count: int) -> List[System]:
        systems: List[System] = await self._client.get_paginated_list(response_item_type=System,
                                                                      url="/systems", max_count=count)
        return systems

    async def get_system(self, system_symbol: str) -> System:
        system: System = await self._client.get_data(response_type=System, url=f"/systems/{system_symbol}")
        return system

    async def list_waypoints(
            self, system_symbol: str, count: int=-1,
            waypoint_traits: Optional[List[str]]=None, waypoint_type: Optional[str]=None) -> List[Waypoint]:
        params: str = ""
        if waypoint_type is not None:
            params = f"type{waypoint_type}"

        if waypoint_traits is not None and len(waypoint_traits) > 0:
            params += f"&traits={"&traits=".join(waypoint_traits)}"

        waypoints: List[Waypoint] = await self._client.get_paginated_list(
            response_item_type=Waypoint,
            url=f"/systems/{system_symbol}/waypoints?{params}",
            max_count=count)

        return waypoints

    async def get_waypoint(self, system_symbol: str, waypoint_symbol) -> Waypoint:
        waypoint: Waypoint = await self._client.get_data(response_type=Waypoint,
                                                         url=f"/systems/{system_symbol}/waypoints/{waypoint_symbol}")
        return waypoint

    async def get_market(self, system_symbol: str, waypoint_symbol) -> Market:
        market: Market = await self._client.get_data(response_type=Market,
                                                     url=f"/systems/{system_symbol}/waypoints/{waypoint_symbol}/market")
        return market

    async def get_shipyard(self, system_symbol: str, waypoint_symbol) -> Shipyard:
        shipyard = await self._client.get_data(
            response_type=Shipyard,
            url=f"/systems/{system_symbol}/waypoints/{waypoint_symbol}/shipyard"
        )
        return shipyard
