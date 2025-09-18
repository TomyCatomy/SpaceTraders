import asyncio
import math
import os.path
from asyncio import sleep
from datetime import datetime, timezone
from functools import cache
from typing import List, Optional, Set

import dotenv

from Scripts.mongodb_utils import (get_system_objects_by_filter,
                                   get_objects_from_system, database_setup, upsert_one_to_unique_object_collection,
                                   get_unique_object_if_inserted)
from client.client import Client
from config import config
from models.contracts.contract import Contract, ContractOrder
from models.contracts.requests.deliver_cargo_to_contract_req import DeliverCargoToContractReq
from models.fleet.requests.jettison_cargo_req import JettisonCargoReq
from models.fleet.requests.navigate_ship_req import NavigateShipReq
from models.fleet.requests.purchase_cargo_req import PurchaseCargoReq
from models.fleet.requests.purchase_ship_req import PurchaseShipReq
from models.fleet.requests.refuel_req import RefuelReq
from models.fleet.ship import Ship, ShipInventoryItem
from models.fleet.ship_nav import ShipNav
from models.systems.market import Market
from models.systems.shipyard import Shipyard
from models.systems.waypoint import Waypoint
from navigation.models.route_details import RouteDetails
from navigation.utils import distance_between, dijkstra_shortest_path
from utils.initialization_utils import initialize_system
from utils.system_info_utils import get_system_waypoints, sort_waypoints_by_distance, find_intra_cluster_voyage_route

FUEL = "FUEL"

FUEL_STATION = "FUEL_STATION"

SHIP_SURVEYOR = "SHIP_SURVEYOR"

SURVEYOR = "SURVEYOR"

SHIPYARD = "SHIPYARD"

EXCAVATOR = "EXCAVATOR"

COMMAND_SHIP_TYPE = "COMMAND"

SATELLITE_SHIP_TYPE = "SATELLITE"

SHIPYARDS_MONGO_COLLECTION = "SHIPYARDS"

COMMON_METAL_DEPOSITS = "COMMON_METAL_DEPOSITS"

MARKETPLACE = "MARKETPLACE"
DOCKED = "DOCKED"
SHIP_MINING_DRONE_SHIP_TYPE = "SHIP_MINING_DRONE"
IN_TRANSIT = "IN_TRANSIT"
MAX_DISTANCE_PER_FUEL_UNIT = 1


def time_left_in_seconds(target_time: datetime) -> float:
    return (target_time - datetime.now(tz=timezone.utc)).total_seconds()


async def sleep_until_arrival(nav: ShipNav):
    seconds_to_arrival = time_left_in_seconds(nav.route.arrival)
    print(f"Sleeping {seconds_to_arrival} seconds for ship to arrive")
    await sleep(seconds_to_arrival)


async def navigate_ship(client: Client, ship_symbol: str, dest_waypoint_symbol: str) -> None:
    ship = await client.fleet.get_ship(ship_symbol)
    if ship.nav.status == IN_TRANSIT:
        await sleep_until_arrival(ship.nav)

    ship = await client.fleet.get_ship(ship_symbol)
    if ship.nav.waypointSymbol == dest_waypoint_symbol:
        return

    await prep_ship(client, ship)
    result = await client.fleet.navigate_ship(ship_symbol, NavigateShipReq(waypointSymbol=dest_waypoint_symbol))
    await sleep_until_arrival(result.nav)


async def get_cluster_waypoints(client: Client, waypoint_symbol: str) -> List[Waypoint]:
    waypoint = await get_waypoint(client, waypoint_symbol)
    cluster_waypoints = await get_system_objects_by_filter(
        Waypoint, config.agent_symbol, "WAYPOINTS", waypoint.systemSymbol, waypoint.internal_cluster_id,
        "internal_cluster_id"
    )
    return cluster_waypoints


async def voyage_ship(client: Client, ship_symbol: str, dest_waypoint: Waypoint) -> None:
    ship = await client.fleet.get_ship(ship_symbol)
    system_symbol = dest_waypoint.systemSymbol
    waypoints = await get_system_waypoints(client, system_symbol)
    if ship.nav.status == IN_TRANSIT:
        await sleep_until_arrival(ship.nav)

    ship = await client.fleet.get_ship(ship_symbol)
    origin_waypoint = await get_waypoint(client, ship.nav.route.origin.symbol)
    dest_waypoint = await get_waypoint(client, ship.nav.route.destination.symbol)
    waypoints_in_cluster = await get_cluster_waypoints(client, origin_waypoint.internal_cluster_id)
    cluster_waypoint_symbols = [waypoint.symbol for waypoint in waypoints_in_cluster]
    system_fuel_stations = await get_system_fuel_stations(client, system_symbol)
    fuel_stations = [waypoint for waypoint in system_fuel_stations if waypoint.symbol in cluster_waypoint_symbols]
    max_hop_distance = ship.fuel.capacity * MAX_DISTANCE_PER_FUEL_UNIT
    if origin_waypoint.systemSymbol != dest_waypoint.systemSymbol:
        raise Exception("Inter-system voyages currently not supported")

    route = find_voyage_route(
        origin_waypoint,
        dest_waypoint,
        fuel_stations,
        waypoints,
        max_hop_distance
    )
    for waypoint in route:
        await navigate_ship(client, ship_symbol, waypoint.symbol)


def get_fuel_units_in_cargo(ship: Ship):
    fuel_units_in_cargo = [item.units for item in ship.cargo.inventory if item.symbol == FUEL]
    if len(fuel_units_in_cargo) == 0:
        return 0

    return fuel_units_in_cargo[0]


def find_voyage_route(
        origin_waypoint: Waypoint,
        dest_waypoint: Waypoint,
        fuel_stations: List[Waypoint],
        waypoints: List[Waypoint],
        max_hop_distance: int
) -> List[Waypoint]:
    in_range_fuel_stations = list(filter(
        lambda fuel_station: distance_between(origin_waypoint, fuel_station) <= distance_between(origin_waypoint,
                                                                                                 dest_waypoint) * 0.7,
        fuel_stations
    ))
    sorted_fuel_stations = sort_waypoints_by_distance(dest_waypoint, in_range_fuel_stations)
    route_to_fuel_station = find_intra_cluster_voyage_route(
        [origin_waypoint],
        sorted_fuel_stations[0],
        waypoints,
        max_hop_distance
    )
    route_to_dest = find_intra_cluster_voyage_route(
        [sorted_fuel_stations[0]],
        dest_waypoint,
        waypoints,
        max_hop_distance
    )
    route = route_to_fuel_station
    route.extend(route_to_dest[1:])
    return route


async def find_intercluster_voyage_route(origin: Waypoint, destination: Waypoint) -> List[str]:
    routes = await get_objects_from_system(RouteDetails, config.agent_symbol, "ROUTE_DETAILS", origin.systemSymbol)
    route_dict = {route.route_id: route for route in routes}
    path_stop_waypoints = dijkstra_shortest_path(routes, origin.symbol, destination.symbol)
    path_route_ids = []
    for index, waypoint in enumerate(path_stop_waypoints[:-1]):
        ends_waypoints = [waypoint, path_stop_waypoints[index + 1]]
        ends_waypoints.sort(key=lambda item: item.symbol)
        path_route_ids.append(f"{ends_waypoints[0]}=>{ends_waypoints[1]}")

    path_routes = [route_dict[route_id] for route_id in path_route_ids]
    full_path: List[str] = []
    [full_path.extend([waypoint for waypoint in route.route_waypoints]) for route in path_routes]

    return full_path


async def prep_ship(client: Client, ship: Ship) -> None:
    if ship.nav.status != DOCKED:
        await client.fleet.dock_ship(ship.symbol)

    current_waypoint = ship.nav.route.origin
    refuel_from_cargo = True
    if MARKETPLACE in [trait.symbol for trait in current_waypoint.traits]:
        marketplace = await client.systems.get_market(current_waypoint.systemSymbol, current_waypoint.symbol)
        if FUEL in [good.symbol for good in marketplace.tradeGoods]:
            refuel_from_cargo = False
            await client.fleet.purchase_cargo(
                ship.symbol,
                PurchaseCargoReq(symbol=FUEL, units=ship.cargo.capacity - ship.cargo.units))

    if refuel_from_cargo or FUEL in [item.symbol for item in ship.cargo.inventory]:
        refuel_amount = int(math.ceil(ship.fuel.capacity - ship.fuel.current) / 100)
        if refuel_from_cargo:
            fuel_units_in_cargo = get_fuel_units_in_cargo(ship)
            refuel_amount = min([refuel_amount, fuel_units_in_cargo])

        await client.fleet.refuel_ship(ship.symbol, RefuelReq(units=refuel_amount, fromCargo=refuel_from_cargo))

    await client.fleet.orbit_ship(ship.symbol)


@cache
async def get_system_markets(client: Client, system_symbol: str):
    waypoints: List[Waypoint] = await client.systems.list_waypoints(
        system_symbol,
        waypoint_traits=[MARKETPLACE],
    )
    markets: List[Market] = []
    for waypoint in waypoints:
        if MARKETPLACE not in [trait.symbol for trait in waypoint.traits]:
            continue

        market: Market = await client.systems.get_market(system_symbol, waypoint.symbol)
        markets.append(market)

    return markets


@cache
async def get_system_fuel_stations(client: Client, system_symbol: str):
    waypoints: List[Waypoint] = await client.systems.list_waypoints(
        system_symbol,
        waypoint_type=FUEL_STATION,
    )
    return waypoints


async def get_extraction_waypoint(client: Client, ship: Ship) -> Waypoint:
    waypoints = await client.systems.list_waypoints(ship.nav.systemSymbol, waypoint_traits=[COMMON_METAL_DEPOSITS])
    non_stripped_waypoints = [
        waypoint for waypoint in waypoints
        if "STRIPPED" not in [trait.symbol for trait in waypoint.traits]
    ]
    sorted_waypoints = sort_waypoints_by_distance(ship.nav.route.origin, non_stripped_waypoints)
    return sorted_waypoints[0]


async def ship_cargo_is_full(client: Client, ship_symbol: str) -> bool:
    ship = await client.fleet.get_ship(ship_symbol)
    return ship.cargo.capacity == ship.cargo.units


async def extract_until_resource_full(client: Client, extractor_symbol: str, resource_symbols: List[str]) -> None:
    while not await ship_cargo_is_full(client=client, ship_symbol=extractor_symbol):
        extractor = await client.fleet.get_ship(extractor_symbol)
        print(f"Extractor cargo before extraction: {extractor.cargo}")
        await sleep_for_cooldown(extractor)
        response = await client.fleet.extract_resources(extractor_symbol)
        print(f"Extracted the following: {response.extraction.extraction_yield}")
        await jettison_redundant_resources(
            client=client,
            ship_symbol=extractor_symbol,
            necessary_resource_symbols=resource_symbols
        )


async def sleep_for_cooldown(extractor) -> None:
    if not extractor.cooldown.expiration:
        return

    remaining_seconds = time_left_in_seconds(extractor.cooldown.expiration)
    print(f"Waiting for cooldown for {remaining_seconds} seconds")
    await asyncio.sleep(remaining_seconds)


async def jettison_redundant_resources(
        client: Client,
        ship_symbol: str,
        necessary_resource_symbols: List[str]
) -> None:
    ship = await client.fleet.get_ship(ship_symbol=ship_symbol)
    for resource in ship.cargo.inventory:
        if resource.symbol not in necessary_resource_symbols:
            await client.fleet.jettison_cargo(
                ship_symbol=ship_symbol,
                jettison_cargo_req=JettisonCargoReq(symbol=resource.symbol, units=resource.units)
            )


def get_system_symbol(waypoint_symbol: str) -> str:
    return "-".join(waypoint_symbol.split("-")[:2])


async def get_waypoint(client: Client, waypoint_symbol: str) -> Waypoint:
    waypoint = await get_unique_object_if_inserted(Waypoint, config.agent_symbol, "WAYPOINT", waypoint_symbol)
    if waypoint:
        return waypoint

    return await client.systems.get_waypoint(get_system_symbol(waypoint_symbol), waypoint_symbol)


async def get_shipyard(client: Client, waypoint_symbol: str) -> Shipyard:
    shipyard = await client.systems.get_shipyard(get_system_symbol(waypoint_symbol), waypoint_symbol)
    await upsert_one_to_unique_object_collection(config.agent_symbol, "SHIPYARDS", document=shipyard)
    return shipyard


async def buy_ship_if_available(
        client: Client,
        shipyard_symbol: str,
        ship_type: str
) -> Optional[Ship]:
    shipyard = await get_shipyard(client, shipyard_symbol)
    if ship_type in shipyard.shipTypes:
        response = await client.fleet.purchase_ship(
            PurchaseShipReq(shipType=ship_type, waypointSymbol=shipyard_symbol)
        )
        return response.ship

    return None


async def get_explored_shipyard_with_ship_type_if_exists(
        required_ship_type: str,
        system_symbol: str,
) -> Optional[Shipyard]:
    explored_shipyards = await get_objects_from_system(Shipyard, config.agent_symbol, "SHIPYARDS", system_symbol)
    relevant_shipyards = [
        shipyard for shipyard in explored_shipyards
        if required_ship_type in [ship_type.type for ship_type in shipyard.shipTypes]
    ]
    return relevant_shipyards[0]


async def buy_ship(client: Client, system_symbol: str, ship_type: str) -> Ship:
    shipyards = await client.systems.list_waypoints(
        system_symbol=system_symbol,
        waypoint_traits=[SHIPYARD]
    )
    ships = await client.fleet.get_ships()

    for ship in ships:
        if ship.nav.status == IN_TRANSIT:
            continue

        if ship.nav.waypointSymbol in [shipyard.symbol for shipyard in shipyards]:
            bought_ship = await buy_ship_if_available(
                client,
                ship.nav.waypointSymbol,
                ship_type
            )
            if bought_ship:
                return bought_ship

    probe = [ship for ship in ships if ship.registration.role == SATELLITE_SHIP_TYPE][0]
    known_extractor_seller = await get_explored_shipyard_with_ship_type_if_exists(
        ship_type,
        system_symbol
    )
    if known_extractor_seller:
        extractor_seller_waypoint = await client.systems.get_waypoint(system_symbol, known_extractor_seller.symbol)
        await voyage_ship(client=client, ship_symbol=probe.symbol, dest_waypoint=extractor_seller_waypoint)
        result = await client.fleet.purchase_ship(PurchaseShipReq(
            shipType=ship_type,
            waypointSymbol=known_extractor_seller.symbol)
        )
        return result.ship

    for shipyard in shipyards:
        known_shipyard_data = await get_unique_object_if_inserted(Shipyard, config.agent_symbol,
                                                                  SHIPYARDS_MONGO_COLLECTION, shipyard.symbol)
        if known_shipyard_data:
            continue

        if shipyard.symbol not in [ship.nav.waypointSymbol for ship in ships]:
            extractor_seller_waypoint = await client.systems.get_waypoint(system_symbol, known_extractor_seller.symbol)
            await voyage_ship(client=client, ship_symbol=probe.symbol, dest_waypoint=extractor_seller_waypoint)

        extractor = await buy_ship_if_available(client, shipyard.symbol, ship_type)
        if extractor:
            return extractor

    raise Exception("Couldn't find suitable extractor")


async def get_accepted_contract(client: Client) -> Contract:
    contract = await get_contract(client)

    if not contract.accepted:
        return (await client.contracts.accept_contract(contract.id)).contract

    return contract


async def get_contract(client: Client):
    contracts = await client.contracts.get_contract_list()
    if len(contracts) > 0:
        return contracts[0]

    return await acquire_contract(client)


async def acquire_contract(client: Client):
    ships = await client.fleet.get_ships()
    command_ship = [ship for ship in ships if ship.registration.role == COMMAND_SHIP_TYPE][0]
    contract = (await client.fleet.negotiate_contract(command_ship.symbol)).contract
    return contract


async def get_ship(client: Client, ship_role: str, ship_type: str) -> Ship:
    ships: List[Ship] = await client.fleet.get_ships()
    extractors = [ship for ship in ships if ship.registration.role == ship_role]
    if len(extractors) == 0:
        return await buy_ship(client, ships[0].nav.systemSymbol, ship_type)
    else:
        return extractors[0]


async def deposit_contract_resources(client: Client, contract_id: str, extractor_symbol: str) -> Set[Waypoint]:
    contract = await client.contracts.get_contract(contract_id)
    uncompleted_order_waypoints = {
        await get_waypoint(client, order.destinationSymbol) for order in contract.terms.deliver
        if order.unitsRequired > order.unitsFulfilled
    }
    while len(uncompleted_order_waypoints) > 0:
        extractor = await client.fleet.get_ship(extractor_symbol)
        if extractor.cargo.units == 0:
            return uncompleted_order_waypoints

        uncompleted_order_waypoints = await deposit_contract_resources_in_planet(
            client,
            contract,
            extractor.symbol,
            uncompleted_order_waypoints
        )

    return set()


async def deposit_contract_resources_in_planet(
        client: Client,
        contract: Contract,
        extractor_symbol: str,
        uncompleted_order_waypoints: Set[Waypoint]
) -> Set[Waypoint]:
    uncompleted_order_waypoints = uncompleted_order_waypoints.copy()
    extractor = await client.fleet.get_ship(extractor_symbol)
    current_waypoint = await voyage_to_closest_waypoint(client, extractor, list(uncompleted_order_waypoints))
    for order in contract.terms.deliver:
        if order.destinationSymbol == current_waypoint.symbol and order.unitsRequired > order.unitsFulfilled:
            await deliver_cargo_to_order_if_possible(client, contract, extractor, order)

    uncompleted_order_waypoints.remove(current_waypoint)
    return uncompleted_order_waypoints


async def voyage_to_closest_waypoint(client: Client, ship: Ship, waypoints: List[Waypoint]):
    closest_waypoint = await get_closest_waypoint(ship.nav.route.origin, waypoints)
    await voyage_ship(client=client, ship_symbol=ship.symbol, dest_waypoint=closest_waypoint)
    current_waypoint = closest_waypoint
    return current_waypoint


async def get_closest_waypoint(reference_waypoint: Waypoint, uncompleted_order_waypoints: List[Waypoint]) -> Waypoint:
    sorted_order_waypoints = sort_waypoints_by_distance(reference_waypoint, list(uncompleted_order_waypoints))
    closest_waypoint = sorted_order_waypoints[0]
    return closest_waypoint


async def deliver_cargo_to_order_if_possible(
        client: Client,
        contract: Contract,
        extractor: Ship,
        order: ContractOrder
) -> None:
    relevant_inventory_item_if_exists = [item for item in extractor.cargo.inventory if item.symbol == order.tradeSymbol]
    if len(relevant_inventory_item_if_exists) == 1:
        await deliver_cargo_to_order(client, contract, extractor, order, relevant_inventory_item_if_exists[0])


async def deliver_cargo_to_order(
        client: Client,
        contract: Contract,
        ship: Ship,
        order: ContractOrder,
        relevant_inventory_item: ShipInventoryItem):
    deliver_cargo_req_body = DeliverCargoToContractReq(
        shipSymbol=ship.symbol,
        tradeSymbol=order.tradeSymbol,
        units=min([order.unitsRequired - order.unitsFulfilled, relevant_inventory_item.units])
    )
    await client.fleet.dock_ship(ship.symbol)
    await client.contracts.deliver_cargo_to_contract(contract.id, deliver_cargo_req_body)


async def basic_automation_cycle(dotenv_file_path: str):
    client, new_agent_token = await Client.get_client(
        agent_auth_token=config.agent_token,
        agent_symbol=config.agent_symbol
    )
    dotenv.set_key(dotenv_file_path, "AGENT_TOKEN", new_agent_token)

    await database_setup(config.agent_symbol)

    contract = await get_accepted_contract(client)
    system_symbol = get_system_symbol(contract.terms.deliver[0].destinationSymbol)
    extractor = await get_ship(client, EXCAVATOR, SHIP_MINING_DRONE_SHIP_TYPE)
    await deposit_contract_resources(client, contract.id, extractor.symbol)
    necessary_resources = {
        order.tradeSymbol for order in contract.terms.deliver
        if order.unitsRequired > order.unitsFulfilled
    }

    extraction_astroid: Waypoint = await get_extraction_waypoint(client, extractor)
    await voyage_ship(client, extractor.symbol, extraction_astroid)
    await extract_until_resource_full(
        client=client,
        extractor_symbol=extractor.symbol,
        resource_symbols=list(necessary_resources)
    )
    await deposit_contract_resources(client, contract.id, extractor.symbol)


if __name__ == "__main__":
    asyncio.run(basic_automation_cycle(".env"))
