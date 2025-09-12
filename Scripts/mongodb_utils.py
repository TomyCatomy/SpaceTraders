from typing import TypeVar, Any, Optional, Type, List

from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)


async def upsert_one_to_unique_object_collection(
        collection: AsyncIOMotorCollection,
        document: T,
        unique_index: str="symbol"
):
    document_dict = document.model_dump()
    result = await collection.update_one(
        filter={ unique_index: document_dict[unique_index] },
        update={ "$set": document_dict },
        upsert=True
    )
    if not result.acknowledged:
        raise Exception("Didn't acknowledge update operation")


async def get_objects_from_system(
        model_type: Type[T],
        collection: AsyncIOMotorCollection,
        system_symbol: str
) -> List[T]:
    result = await collection.find(
        filter={ "symbol": { "$regex": system_symbol } }
    ).to_list()
    return [model_type.model_validate(item) for item in result]


async def get_unique_object_if_inserted(
        model_type: Type[T],
        collection: AsyncIOMotorCollection,
        unique_index_value: Any,
        unique_index: str = "symbol"
) -> Optional[T]:
    result = await collection.find_one(
        filter={ unique_index: unique_index_value }
    )
    if not result:
        return None

    return model_type.model_validate(result)
