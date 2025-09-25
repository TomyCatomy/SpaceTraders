from typing import List, Optional

from httpx import HTTPStatusError

from client.httpx_wrapping.internal_client import InternalClient
from models.systems.market import Market
from models.systems.shipyard import Shipyard
from models.systems.system import System
from models.systems.waypoint import Waypoint


class Systems:
    _client: InternalClient

    def __init__(self, client: InternalClient):
        self._client = client

    async def list_systems(self, count: Optional[int] = None) -> List[System]:
        systems: List[System] = await self._client.get_paginated_list(
            response_item_type=System, url="/systems", max_count=count
        )
        return systems

    async def get_system(self, system_symbol: str) -> System:
        system: System = await self._client.get_data(response_type=System, url=f"/systems/{system_symbol}")
        return system

    async def list_waypoints(self, system_symbol: str, count: Optional[int] = None,
                             waypoint_traits: Optional[List[str]] = None, waypoint_type: Optional[str] = None
                             ) -> List[Waypoint]:
        params = []
        if waypoint_type is not None:
            params.append(f"type={waypoint_type}")

        if waypoint_traits is not None:
            params.extend([f"traits={trait}" for trait in waypoint_traits])

        params_str = "&".join(params)
        waypoints: List[Waypoint] = await self._client.get_paginated_list(
            response_item_type=Waypoint, url=f"/systems/{system_symbol}/waypoints?{params_str}", max_count=count
        )

        return waypoints

    async def get_waypoint(self, system_symbol: str, waypoint_symbol: str) -> Waypoint:
        waypoint: Waypoint = await self._client.get_data(
            response_type=Waypoint, url=f"/systems/{system_symbol}/waypoints/{waypoint_symbol}"
        )
        return waypoint

    async def get_market(self, system_symbol: str, waypoint_symbol) -> Market:
        market: Market = await self._client.get_data(
            response_type=Market, url=f"/systems/{system_symbol}/waypoints/{waypoint_symbol}/market"
        )
        return market

    async def get_shipyard(self, system_symbol: str, waypoint_symbol) -> Optional[Shipyard]:
        try:
            shipyard = await self._client.get_data(
                response_type=Shipyard, url=f"/systems/{system_symbol}/waypoints/{waypoint_symbol}/shipyard"
            )
            return shipyard
        except HTTPStatusError as ex:
            if ex.response.status_code == 4001:
                return None
