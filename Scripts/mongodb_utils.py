from typing import TypeVar, Any, Optional, Type, List, Dict

from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from pymongo import UpdateOne, IndexModel

from config import config

T = TypeVar('T', bound=BaseModel)

mongodb_client = AsyncIOMotorClient(host=config.mongodb_connection_string)


async def database_setup(agent_symbol: str) -> None:
    database_names = await mongodb_client.list_database_names()
    if agent_symbol in database_names:
        return

    await create_database(agent_symbol)


async def create_database(agent_symbol: str) -> None:
    database = mongodb_client[agent_symbol]
    symbol_index_collections = [
        database["WAYPOINT"],
        database["MARKET"],
        database["SHIPYARD"],
        database["SURVEY"]
    ]
    for collection in symbol_index_collections:
        await collection.create_indexes([IndexModel("symbol"), IndexModel("system")])

    await database["WAYPOINT"].create_indexes([IndexModel("_cluster_id"), IndexModel("_is_cluster_border")])
    await database["SURVEY"].create_indexes([IndexModel("signature"), IndexModel("expiration")])
    await database["ROUTE"].create_indexes([IndexModel("route_id"), IndexModel("source"), IndexModel("dest"), IndexModel("system")])





async def upsert_one_to_unique_object_collection(
        agent_symbol: str,
        collection_name: str,
        document: T,
        unique_index: str="symbol"
):
    document_dict = document.model_dump()
    result = await mongodb_client[agent_symbol][collection_name].update_one(
        filter={ unique_index: document_dict[unique_index] },
        update={ "$set": document_dict },
        upsert=True
    )
    if not result.acknowledged:
        raise Exception("Didn't acknowledge update operation")


async def upsert_many_to_unique_object_collection(
        agent_symbol: str,
        collection_name: str,
        documents: List[T],
        unique_index: str="symbol"
):
    document_dicts = [document.model_dump() for document in documents]
    bulk_operations = [
        UpdateOne(
            filter={unique_index: document_dict[unique_index]},
            update={"$set": document_dict},
            upsert=True,
        )
        for document_dict in document_dicts
    ]
    result = await mongodb_client[agent_symbol][collection_name].bulk_write(bulk_operations)
    if not result.acknowledged:
        raise Exception("Didn't acknowledge insert operation")


async def get_objects_from_system(
        model_type: Type[T],
        agent_symbol: str,
        collection_name: str,
        system_symbol: str
) -> List[T]:
    result = await mongodb_client[agent_symbol][collection_name].find(
        filter={ "symbol": { "$regex": system_symbol } }
    ).to_list()
    return [model_type.model_validate(item) for item in result]


async def get_unique_object_if_inserted(
        model_type: Type[T],
        agent_symbol: str,
        collection_name: str,
        unique_index_value: Any,
        unique_index: str = "symbol"
) -> Optional[T]:
    result = await mongodb_client[agent_symbol][collection_name].find_one(
        filter={ unique_index: unique_index_value }
    )
    if not result:
        return None

    return model_type.model_validate(result)


async def get_system_objects_by_filter(
        model_type: Type[T],
        agent_symbol: str,
        collection_name: str,
        system_symbol: str,
        mongo_filter: Dict[str, Any],
        object_count: Optional[int] = None
) -> Optional[List[T]]:
    mongo_filter["system"] = system_symbol
    result = await mongodb_client[agent_symbol][collection_name].find(filter=mongo_filter).to_list(object_count)
    if not result:
        return None

    return [model_type.model_validate(result_object) for result_object in result]

