import asyncio
import os

import dotenv

from Scripts.mongodb_utils import database_setup
from Scripts.travel_scripts import get_system_symbol, get_accepted_contract
from client.client import Client
from config import config
from utils.initialization_utils import initialize_system


async def system_navigation_init(dotenv_file_path: str) -> None:
    client, new_agent_token = await Client.get_client(
        agent_auth_token=config.agent_token,
        agent_symbol=config.agent_symbol
    )
    dotenv.set_key(dotenv_file_path, "TOKEN", new_agent_token)

    await database_setup(config.agent_symbol)

    contract = await get_accepted_contract(client)
    system_symbol = get_system_symbol(contract.terms.deliver[0].destinationSymbol)
    await initialize_system(client, system_symbol)

if __name__ == "__main__":
    asyncio.run(system_navigation_init(os.path.join("..", ".env")))

