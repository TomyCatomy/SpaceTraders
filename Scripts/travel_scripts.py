import asyncio
import math
import os.path
from asyncio import sleep
from datetime import datetime, timezone
from typing import List

import dotenv

from client.client import Client
from models.contracts.contract import Contract
from models.contracts.requests.deliver_cargo_to_contract_req import DeliverCargoToContractReq
from models.fleet.requests.jettison_cargo_req import JettisonCargoReq
from models.fleet.requests.navigate_ship_req import NavigateShipReq
from models.fleet.requests.purchase_ship_req import PurchaseShipReq
from models.fleet.ship import Ship
from models.fleet.ship_nav import ShipNav
from models.systems.market import Market
from models.systems.shipyard import Shipyard
from models.systems.waypoint import Waypoint

async def sleep_until_arrival(nav: ShipNav):
    seconds_to_arrival = (nav.route.arrival - datetime.now(tz=timezone.utc)).total_seconds()
    print(f"Sleeping {seconds_to_arrival} seconds for ship to arrive")
    await sleep(seconds_to_arrival)


async def navigate_ship(client: Client, ship_symbol: str, dest_waypoint_symbol: str) -> None:
    ship = await client.fleet.get_ship(ship_symbol)

    if ship.nav.waypointSymbol == dest_waypoint_symbol:
        return

    if ship.nav.status == "IN_TRANSIT":
        if ship.nav.route.origin.symbol == ship.nav.route.destination.symbol == dest_waypoint_symbol:
            return
        await sleep_until_arrival(ship.nav)

    if ship.nav.status != "DOCKED":
        await client.fleet.dock_ship(ship_symbol)

    await client.fleet.refuel_ship(ship_symbol)
    await client.fleet.orbit_ship(ship_symbol)
    result = await client.fleet.navigate_ship(ship_symbol, NavigateShipReq(waypointSymbol=dest_waypoint_symbol))
    await sleep_until_arrival(result.nav)


async def get_system_markets(client: Client, system_symbol: str):
    waypoints: List[Waypoint] = await client.systems.list_waypoints(system_symbol, waypoint_traits=["MARKETPLACE"])
    markets: List[Market] = []
    for waypoint in waypoints:
        market: Market = await client.systems.get_market(system_symbol, waypoint.symbol)
        markets.append(market)

    return markets


def distance_between(waypoint1: Waypoint, waypoint2: Waypoint) -> float:
    x_delta = waypoint1.x - waypoint2.x
    y_delta = waypoint1.y - waypoint2.y
    return math.sqrt(x_delta ** 2 + y_delta ** 2)


def sort_waypoints_by_distance(reference_waypoint: Waypoint, waypoint_list: List[Waypoint]) -> None:
    waypoint_list.sort(key=lambda waypoint: distance_between(reference_waypoint, waypoint))


async def get_extraction_waypoint(client: Client, ship: Ship) -> Waypoint:
    waypoints = await client.systems.list_waypoints(ship.nav.systemSymbol, waypoint_traits=["COMMON_METAL_DEPOSITS"])
    sort_waypoints_by_distance(ship.nav.route.origin, waypoints)
    return waypoints[0]


async def ship_cargo_is_full(client: Client, ship_symbol: str) -> bool:
    ship = await client.fleet.get_ship(ship_symbol)
    return ship.cargo.capacity == ship.cargo.units


async def extract_until_resource_full(client: Client, extractor_symbol: str, resource_symbols: List[str]) -> None:
    while not await ship_cargo_is_full(client=client, ship_symbol=extractor_symbol):
        response = await client.fleet.extract_resources(extractor_symbol)
        await jettison_redundant_resources(
            client=client,
            ship_symbol=extractor_symbol,
            necessary_resource_symbols=resource_symbols
        )
        await asyncio.sleep(response.cooldown.remainingSeconds)


async def jettison_redundant_resources(client: Client, ship_symbol: str, necessary_resource_symbols: List[str]) -> None:
    ship = await client.fleet.get_ship(ship_symbol=ship_symbol)
    for resource in ship.cargo.inventory:
        if resource.symbol not in necessary_resource_symbols:
            await client.fleet.jettison_cargo(
                ship_symbol=ship_symbol,
                jettison_cargo_req=JettisonCargoReq(symbol=resource.symbol, units=resource.units)
            )


async def get_waypoint(client: Client, waypoint_symbol: str) -> Waypoint:
    return await client.systems.get_waypoint(waypoint_symbol[:6], waypoint_symbol)


async def get_shipyard(client: Client, waypoint_symbol: str) -> Shipyard:
    return await client.systems.get_shipyard(waypoint_symbol[:6], waypoint_symbol)


async def buy_extractor(client: Client, system_symbol: str) -> Ship:
    shipyards = await client.systems.list_waypoints(system_symbol=system_symbol, waypoint_traits=["SHIPYARD"])
    ships = await client.fleet.get_ships()
    for shipyard in shipyards:
        if len([ship for ship in ships if ship.nav.waypointSymbol == shipyards[0]]) == 0:
            probe = [ship for ship in ships if ship.registration.role == "SATELLITE"][0]
            await navigate_ship(client=client, ship_symbol=probe.symbol, dest_waypoint_symbol=shipyard.symbol)
            extended_shipyard = await get_shipyard(client, shipyard.symbol)
            if "SHIP_MINING_DRONE" in [ship_type.type for ship_type in extended_shipyard.shipTypes]:
                response = await client.fleet.purchase_ship(
                    purchase_req=PurchaseShipReq(shipType="SHIP_MINING_DRONE", waypointSymbol=shipyard.symbol)
                )
                return response.ship


async def get_contract(client: Client) -> Contract:
    contracts = await client.contracts.get_contract_list()
    if len(contracts) > 0:
        contract = contracts[0]
    else:
        ships = await client.fleet.get_ships()
        command_ship = [ship for ship in ships if ship.registration.role == "COMMAND"][0]
        contract = (await client.fleet.negotiate_contract(command_ship.symbol)).contract

    if not contract.accepted:
        return await client.contracts.accept_contract(contract.id)

    return contract


async def basic_automation_cycle():
    symbol = dotenv.get_key(os.path.join("..", ".env"), "USER")
    agent_token = dotenv.get_key(os.path.join("..", ".env"), "TOKEN")
    account_token = dotenv.get_key(os.path.join("..", ".env"), "ACCOUNT_TOKEN")
    client, agent_token = await Client.get_client(
        agent_auth_token=agent_token,
        account_auth_token=account_token,
        agent_symbol=symbol
    )
    dotenv.set_key(os.path.join("..", ".env"), "TOKEN", agent_token)
    contract = await get_contract(client)
    necessary_resources = {
        order.tradeSymbol for order in contract.terms.deliver
        if order.unitsRequired > order.unitsFulfilled
    }
    incomplete_order_waypoints = {
        await get_waypoint(client, order.destinationSymbol) for order in contract.terms.deliver
        if order.unitsRequired > order.unitsFulfilled
    }
    ships: List[Ship] = await client.fleet.get_ships()
    extractors = [ship for ship in ships if ship.registration.role == "EXTRACTOR"]
    if len(extractors) == 0:
        extractor = await buy_extractor(client, ships[0].nav.systemSymbol)
    else:
        extractor = extractors[0]

    extraction_astroid: Waypoint = await get_extraction_waypoint(client, extractor)
    await navigate_ship(client, extractor.symbol, extraction_astroid.symbol)
    await extract_until_resource_full(
        client=client,
        extractor_symbol=extractor.symbol,
        resource_symbols=list(necessary_resources)
    )
    while len(incomplete_order_waypoints) > 0:
        extractor = await client.fleet.get_ship(extractor.symbol)
        distance_sorted_incomplete_order_waypoints = list(incomplete_order_waypoints)
        sort_waypoints_by_distance(extractor.nav.route.origin, distance_sorted_incomplete_order_waypoints)
        closest_waypoint = distance_sorted_incomplete_order_waypoints[0]
        await navigate_ship(client=client, ship_symbol=extractor.symbol, dest_waypoint_symbol=closest_waypoint)
        current_waypoint = closest_waypoint
        for order in contract.terms.deliver:
            if order.destinationSymbol == current_waypoint and order.unitsRequired > order.unitsFulfilled:
                relevant_inventory_item_if_exists = [
                    item for item in extractor.cargo.inventory
                    if item.symbol == order.tradeSymbol
                ]
                if len(relevant_inventory_item_if_exists) == 1:
                    deliver_cargo_req_body = DeliverCargoToContractReq(
                        shipSymbol=extractor.symbol,
                        tradeSymbol=order.tradeSymbol,
                        units=min(
                            [
                                order.unitsRequired - order.unitsFulfilled,
                                extractor.cargo, relevant_inventory_item_if_exists[0].units
                            ]
                        )
                    )
                    await client.contracts.deliver_cargo_to_contract(contract.id, deliver_cargo_req_body)

    pass


if __name__ == "__main__":
    asyncio.run(basic_automation_cycle())
