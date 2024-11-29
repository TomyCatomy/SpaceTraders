from datetime import datetime
from typing import Type, TypeVar, Tuple, List, Dict

import httpx_auth
from httpx import Response, AsyncClient
from pydantic import BaseModel, RootModel

from models.data import Data
from models.meta import Meta


class InternalClient:
    T = TypeVar('T', bound=BaseModel)

    _client: AsyncClient

    def __init__(self, client: AsyncClient):
        self._client = client
        self._next_request = datetime.min

    def set_auth_token(self, token: str):
        self._client.auth = httpx_auth.HeaderApiKey(f"Bearer {token}", "Authorization")

    async def post_data(self, response_type: Type[T], url: str, req_data: BaseModel) -> T:
        req_content: Data = Data(data=req_data)
        return await self.post(response_type, url, req_content)

    async def post(self, response_type: Type[T], url: str, req_data: BaseModel) -> T:
        req_json = req_data.model_dump_json(exclude_none=True)
        response: Response = await self._client.post(url=url, json=req_json)
        return InternalClient._extract_data_from_response(response_type, response)

    async def get(self, response_type: Type[T], url: str, params: Dict[str, str] = None) -> T:
        response: Response = await self._client.get(url=url, params=params)
        return InternalClient._extract_data_from_response(response_type, response)

    async def get_paginated_list(self, response_item_type: Type[T], url: str,
                                 params: Dict[str, str] = None, max_count: int = -1) -> List[T]:
        response_type = self._get_list_model(response_item_type)
        items, meta = await self.get_with_meta(response_type, url=url, params=params)
        item_list: List[response_item_type] = items.root
        count = meta.total
        if 0 <= max_count <= count:
            count = max_count

        next_page = 2
        while len(item_list) < count:
            params = {"page": str(next_page)}
            page = await self.get(response_type, url, params)
            item_list.extend(page.root)
            next_page += 1

        return item_list[:count]

    async def get_with_meta(self, response_type: Type[T], url: str, params: Dict[str, str] = None) -> Tuple[T, Meta]:
        response: Response = await self._client.get(url=url, params=params)
        return InternalClient._extract_data_and_meta_from_response(response_type, response)

    @staticmethod
    def _get_list_model(item_model: Type[T]):
        class ListModel(RootModel):
            root: List[item_model]

        return ListModel

    @staticmethod
    def _extract_data_and_meta_from_response(response_type: Type[T], response: Response) -> Tuple[T, Meta]:
        response.raise_for_status()
        response_json: str = response.json()
        response_content: Data = Data.model_validate(response_json)
        return response_type.model_validate(response_content.data), response_content.meta

    @staticmethod
    def _extract_data_from_response(response_type: Type[T], response: Response) -> T:
        data, meta = InternalClient._extract_data_and_meta_from_response(response_type, response)
        return data
