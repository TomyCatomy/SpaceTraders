from Scripts.mongodb_utils import database_setup
from client.client import Client
from navigation.waypoint_cluster import cache_waypoint_clusters


async def initialize_system(client: Client, system_symbol: str) -> None:
    await database_setup(system_symbol)
    await cache_waypoint_clusters(client, system_symbol)

