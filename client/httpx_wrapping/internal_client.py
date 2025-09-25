from typing import Type, Tuple, List, Dict, Optional, Any

import httpx_auth
from httpx import Response, AsyncClient
from pydantic import BaseModel, RootModel

from client.consts import BaseModelType
from client.mongo_wrapping.internal_mongo_client import InternalMongoClient
from models.base_space_traders_response import BaseSpaceTradersResponse
from models.meta import Meta


class InternalClient:
    def __init__(self, http_client: AsyncClient, mongo_client: InternalMongoClient):
        self._http_client = http_client
        self._mongo_client = mongo_client

    def set_auth_token(self, token: Optional[str]):
        if token is None:
            self._http_client.auth = None
        else:
            self._http_client.auth = httpx_auth.HeaderApiKey(f"Bearer {token}", "Authorization")

    async def post(self, response_type: Type[BaseModelType], url: str,
                   req_data: Optional[BaseModel] = None) -> BaseModelType:
        req_json = req_data.model_dump(exclude_none=True) if req_data is not None else None
        response = await self._http_client.post(url=url, json=req_json)
        return InternalClient._extract_data_from_response(response_type, response)

    async def get_entity(self, response_type: Type[BaseModelType], url: str,
                         entity_id: str, entity_id_field_name: str = "symbol",
                         url_params: Optional[Dict[str, str]] = None
                         ) -> BaseModelType:
        cached_result = await self._mongo_client.get_game_entity_from_db(response_type, entity_id, entity_id_field_name)
        if cached_result is not None:
            return cached_result

        result = await self.get_data(response_type, url, url_params)
        await self._mongo_client.update_game_entity_in_db(response_type, entity_id_field_name, result)
        return result

    async def get_data(self, response_type: Type[BaseModelType], url: str, params: Optional[Dict[str, str]] = None
                       ) -> BaseModelType:
        response = await self._internal_get(url=url, params=params)
        return InternalClient._extract_data_from_response(response_type, response)

    async def get_entities(self, response_type: Type[BaseModelType], url: str, url_params: Optional[Dict[str, str]] = None,
                           mongo_search_filter: Optional[Dict[str, Any]] = None, count: Optional[int] = None,
                           entity_id_field_name: str = "symbol") -> List[BaseModelType]:
        cached_result = await self._mongo_client.list_game_entities_in_db(response_type, mongo_search_filter, count)
        if cached_result is not None:
            return cached_result

        result = await self.get_paginated_list(response_type, url, url_params)
        await self._mongo_client.update_game_entities_in_db(result, mongo_search_filter, count, entity_id_field_name)
        return result


    async def get_paginated_list(self, response_item_type: Type[BaseModelType], url: str,
                                 params: Optional[Dict[str, str]] = None,
                                 max_count: Optional[int] = None) -> List[BaseModelType]:
        response_type = self._get_list_model(response_item_type)
        items, meta = await self._get_with_meta(response_type, url=url, params=params)
        item_list: List[response_item_type] = items.root
        count = meta.total
        if 0 <= max_count <= count:
            count = max_count

        next_page = 2
        while len(item_list) < count:
            params = {"page": str(next_page)}
            page = await self.get_data(response_type, url, params)
            item_list.extend(page.root)
            next_page += 1

        return item_list[:count]

    async def _get_with_meta(self, response_type: Type[BaseModelType], url: str, params: Optional[Dict[str, str]] = None
                             ) -> Tuple[BaseModelType, Meta]:
        response = await self._internal_get(url=url, params=params)
        return InternalClient._extract_data_and_meta_from_response(response_type, response)

    async def _internal_get(self, url: str, params: Optional[Dict[str, str]] = None) -> Response:
        params_str = "&".join(params) if params is not None else None
        full_url = f"{url}?{params_str}" if params is not None else url
        response = await self._http_client.get(url=full_url, params=params)
        return response

    @staticmethod
    def _get_list_model(item_model: Type[BaseModelType]):
        class ListModel(RootModel):
            root: List[item_model]

        return ListModel

    @staticmethod
    def _extract_data_and_meta_from_response(response_type: Type[BaseModelType], response: Response) -> Tuple[
        BaseModelType, Meta]:
        response.raise_for_status()
        response_json = response.json()
        response_content = BaseSpaceTradersResponse.model_validate(response_json)
        return response_type.model_validate(response_content.data), response_content.meta

    @staticmethod
    def _extract_data_from_response(response_type: Type[BaseModelType], response: Response) -> BaseModelType:
        data, meta = InternalClient._extract_data_and_meta_from_response(response_type, response)
        return data
