import models
from client.httpx_wrapping.internal_client import InternalClient
from models.agents.requests.register_agent_req import RegisterAgentReq
from models.agents.responses.register_agent_response import RegisterAgentResponse


class Agent:
    _client: InternalClient

    def __init__(self, client: InternalClient):
        self._client = client

    async def register_agent(self, symbol: str, faction: str) -> RegisterAgentResponse:
        req_data = RegisterAgentReq(symbol=symbol, faction=faction)
        response = await self._client.post(response_type=RegisterAgentResponse,
                                           url="/register",
                                           req_data=req_data)
        return response

    async def get_my_agent(self) -> models.agents.agent.Agent:
        response = await self._client.get(response_type=models.agents.agent.Agent, url="/my/agent")
        return response
