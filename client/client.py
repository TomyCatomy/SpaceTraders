import random
import string

import httpx
import httpx_auth
from httpx import AsyncClient, HTTPStatusError, Limits

from client.agent import Agent
from client.contracts import Contracts
from client.fleet import Fleet
from client.httpx_wrapping.internal_client import InternalClient
from client.systems import Systems
from models.agents.responses.register_agent_response import RegisterAgentResponse

API_BASE_URL: str = "https://api.spacetraders.io/v2"


class Client:
    _client: InternalClient
    agent: Agent
    contracts: Contracts
    systems: Systems
    fleet: Fleet

    @staticmethod
    async def get_client(auth_token: str = None, faction: str = "COSMIC", agent_symbol: str = None):
        if agent_symbol is None:
            agent_symbol = Client.random_string_generator(14)

        httpx_client: AsyncClient = httpx.AsyncClient(base_url=API_BASE_URL,
                                                      limits=Limits(max_connections=10))
        internal_client: InternalClient = InternalClient(httpx_client)
        agent_property: Agent = Agent(internal_client)
        contracts_property: Contracts = Contracts(internal_client)
        fleet_property: Fleet = Fleet(internal_client)
        systems_property: Systems = Systems(internal_client)
        client = Client(internal_client, agent_property, contracts_property, fleet_property, systems_property)
        if await client.is_valid_auth_token(auth_token):
            client._client.auth = httpx_auth.HeaderApiKey(auth_token, "Authorization")
        else:
            client._client.auth = None
            await client.initialize_agent(agent_symbol, faction)

        return client

    def __init__(self, internal_client: InternalClient, agent: Agent, contracts: Contracts, fleet: Fleet,
                 systems: Systems):
        self._client = internal_client
        self.agent = agent
        self.contracts = contracts
        self.fleet = fleet
        self.systems = systems

    async def initialize_agent(self, agent_symbol, faction) -> str:
        """

        :param agent_symbol:
        :param faction:
        :return: The auth token
        """
        response: RegisterAgentResponse = await self.agent.register_agent(agent_symbol, faction)
        self._client.set_auth_token(response.token)
        return response.token

    async def is_valid_auth_token(self, auth_token):
        if auth_token is None:
            return False

        self._client.set_auth_token(auth_token)
        try:
            await self.agent.get_my_agent()
            return True
        except HTTPStatusError as error:
            if error.response.status_code == 401:
                return False

            raise

    @staticmethod
    def random_string_generator(str_size):
        chars = string.ascii_letters
        return ''.join(random.choice(chars) for _ in range(str_size))
