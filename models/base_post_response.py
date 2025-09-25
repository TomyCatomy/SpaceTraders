from abc import abstractmethod, ABC

from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel


class BasePostResponse(BaseModel, ABC):
    @abstractmethod
    def cache_result(self, mongo_database: AsyncIOMotorDatabase):
        pass
