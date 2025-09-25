from typing import List, Optional

from client.httpx_wrapping.internal_client import InternalClient
from models.contracts.contract import Contract
from models.contracts.requests.deliver_cargo_to_contract_req import DeliverCargoToContractReq
from models.contracts.responses.accept_contract_response import AcceptContractResponse
from models.contracts.responses.deliver_cargo_to_contract_response import DeliverCargoToContractResponse


class Contracts:
    _client: InternalClient

    def __init__(self, client: InternalClient):
        self._client = client

    async def get_contract_list(self, count: Optional[int] = None) -> List[Contract]:
        return await self._client.get_paginated_list(Contract, "/my/contracts", max_count=count)

    async def get_contract(self, contract_id: str):
        return await self._client.get_data(Contract, f"/my/contracts/{contract_id}")

    async def deliver_cargo_to_contract(
            self,
            contract_id: str,
            body: DeliverCargoToContractReq
    ) -> DeliverCargoToContractResponse:
        return await self._client.post(
            DeliverCargoToContractResponse,
            f"/my/contracts/{contract_id}/deliver",
            req_data=body
        )

    async def accept_contract(self, contract_id: str) -> AcceptContractResponse:
        return await self._client.post(
            AcceptContractResponse,
            f"/my/contracts/{contract_id}/accept"
        )
