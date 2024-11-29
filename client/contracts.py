from typing import List

from client.httpx_wrapping.internal_client import InternalClient
from models.contracts.contract import Contract


class Contracts:
    _client: InternalClient

    def __init__(self, client: InternalClient):
        self._client = client

    async def get_contract_list(self, count=-1) -> List[Contract]:
        return await self._client.get_paginated_list(Contract, "/my/contracts", max_count=count)
