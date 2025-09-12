from typing import List, Optional

from client.httpx_wrapping.internal_client import InternalClient
from models.fleet.requests.jettison_cargo_req import JettisonCargoReq
from models.fleet.requests.navigate_ship_req import NavigateShipReq
from models.fleet.requests.purchase_cargo_req import PurchaseCargoReq
from models.fleet.requests.purchase_ship_req import PurchaseShipReq
from models.fleet.requests.refuel_req import RefuelReq
from models.fleet.responses.dock_ship_response import DockShipResponse
from models.fleet.responses.extract_resources_response import ExtractResourcesResponse
from models.fleet.responses.jettison_cargo_response import JettisonCargoResponse
from models.fleet.responses.navigate_ship_response import NavigateShipResponse
from models.fleet.responses.negotiate_contract_response import NegotiateContractResponse
from models.fleet.responses.orbit_ship_response import OrbitShipResponse
from models.fleet.responses.purchase_cargo_response import PurchaseCargoResponse
from models.fleet.responses.purchase_ship_response import PurchaseShipResponse
from models.fleet.responses.refuel_response import RefuelResponse
from models.fleet.ship import Ship, ShipNav, ShipCargo
from models.systems.waypoint import Waypoint


class Fleet:
    _client: InternalClient

    def __init__(self, client: InternalClient):
        self._client = client

    async def get_ships(self, count=-1) -> List[Ship]:
        return await self._client.get_paginated_list(Ship, url="/my/ships", max_count=count)

    async def get_ship(self, ship_symbol: str) -> Ship:
        return await self._client.get_data(Ship, url=f"/my/ships/{ship_symbol}")

    async def purchase_ship(self, purchase_req: PurchaseShipReq) -> PurchaseShipResponse:
        return await self._client.post(PurchaseShipResponse, url=f"/my/ships", req_data=purchase_req)

    async def dock_ship(self, ship_symbol: str) -> DockShipResponse:
        return await self._client.post(DockShipResponse, url=f"/my/ships/{ship_symbol}/dock")

    async def refuel_ship(self, ship_symbol: str, refuel_req: Optional[RefuelReq] = None) -> RefuelResponse:
        return await self._client.post(RefuelResponse, url=f"/my/ships/{ship_symbol}/refuel", req_data=refuel_req)

    async def orbit_ship(self, ship_symbol: str) -> OrbitShipResponse:
        return await self._client.post(OrbitShipResponse, url=f"/my/ships/{ship_symbol}/orbit")

    async def navigate_ship(self, ship_symbol: str, navigate_ship_req: NavigateShipReq) -> NavigateShipResponse:
        return await self._client.post(
            NavigateShipResponse,
            url=f"/my/ships/{ship_symbol}/navigate",
            req_data=navigate_ship_req
        )

    # TODO: add ability to use survey
    async def extract_resources(self, ship_symbol: str) -> ExtractResourcesResponse:
        return await self._client.post(ExtractResourcesResponse, url=f"/my/ships/{ship_symbol}/extract")

    async def jettison_cargo(self, ship_symbol: str, jettison_cargo_req: JettisonCargoReq) -> JettisonCargoResponse:
        return await self._client.post(
            JettisonCargoResponse,
            url=f"my/ships/{ship_symbol}/jettison",
            req_data=jettison_cargo_req
        )

    async def negotiate_contract(self, ship_symbol: str) -> NegotiateContractResponse:
        return await self._client.post(NegotiateContractResponse, url=f"my/ships/{ship_symbol}/negotiate/contract")

    async def purchase_cargo(self, ship_symbol: str, purchase_cargo_req: PurchaseCargoReq):
        return await self._client.post(
            PurchaseCargoResponse,
            url=f"/my/ships/{ship_symbol}/purchase",
            req_data=purchase_cargo_req
        )
