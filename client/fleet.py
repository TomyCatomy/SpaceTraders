from typing import List

from client.httpx_wrapping.internal_client import InternalClient
from models.fleet.ship import Ship


class Fleet:
    _client: InternalClient

    def __init__(self, client: InternalClient):
        self._client = client

    async def get_ships(self, count=-1) -> List[Ship]:
        return await self._client.get_paginated_list(Ship, url="/my/ships", max_count=count)

    async def get_ship(self, ship_symbol) -> Ship:
        return await self._client.get(Ship, url=f"/my/ships/{ship_symbol}")
