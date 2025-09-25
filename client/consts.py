from typing import TypeVar

from pydantic import BaseModel

BaseModelType = TypeVar('BaseModelType', bound=BaseModel)
