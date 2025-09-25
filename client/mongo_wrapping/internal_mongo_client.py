from typing import Type, Optional, List, Dict, Any

from flatten_dict import flatten
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import UpdateOne
from tenacity import stop_after_attempt, retry

from client.consts import BaseModelType


class InternalMongoClient:
    def __init__(self, mongo_client: AsyncIOMotorClient):
        self._mongo_client = mongo_client
        self._entities_db = mongo_client["GAME_ENTITIES"]
        self._covered_criteria = mongo_client["COVERED_CRITERIA"]

    @retry(stop=stop_after_attempt(3))
    async def get_game_entity_from_db(self, response_type: Type[BaseModelType],
                                      entity_id: str, id_field_name: str = "symbol") -> Optional[BaseModelType]:
        collection = self._entities_db[response_type.__name__]
        search_filter = {id_field_name: entity_id}
        response = await collection.find_one(search_filter)
        return response_type.model_validate(response)

    @retry(stop=stop_after_attempt(3))
    async def update_game_entity_in_db(self, entity: BaseModelType, id_field_name: str = "symbol") -> None:
        collection = self._entities_db[entity.__class__.__name__]
        entity_object = entity.model_dump()
        search_filter = {id_field_name: entity_object[id_field_name]}
        await collection.update_one(search_filter, entity_object, upsert=True)

    @retry(stop=stop_after_attempt(3))
    async def list_game_entities_in_db(self, response_type: Type[BaseModelType],
                                       search_filter: Optional[Dict[str, Any]] = None, count: Optional[int] = None
                                       ) -> Optional[List[BaseModelType]]:
        search_criteria = flatten({"search_filter": search_filter or {}}, reducer="dot")
        search_criteria["$or"] = [{"count": {"$lte": count}},{"count": None}]
        available_filter = await self._covered_criteria[response_type.__name__].find_one(search_criteria)
        if not available_filter:
            return None

        collection = self._entities_db[response_type.__name__]
        result_objects = await collection.find(search_filter).to_list(count)
        return [response_type.model_validate(result_object) for result_object in result_objects]

    @retry(stop=stop_after_attempt(3))
    async def update_game_entities_in_db(self, entities: List[BaseModelType], covered_filter: Optional[Dict[str, Any]],
                                         count: Optional[int], id_field_name: str = "symbol") -> None:
        covered_criteria = { "covered_filter": covered_filter or {}, "count": count }
        entity_collection = self._entities_db[entities.__class__.__name__]
        metadata_collection = self._covered_criteria[entities.__class__.__name__]
        entity_objects = [entity.model_dump() for entity in entities]
        requests = [
            UpdateOne({id_field_name: entity_object[id_field_name]}, entity_object, upsert=True)
            for entity_object in entity_objects
        ]
        await entity_collection.bulk_write(requests)
        await metadata_collection.update_one(covered_filter, covered_filter, upsert=True)

    @staticmethod
    def get_client(mongodb_connection_string: str) -> "InternalMongoClient":
        motor_client = AsyncIOMotorClient(mongodb_connection_string)
        return InternalMongoClient(motor_client)
