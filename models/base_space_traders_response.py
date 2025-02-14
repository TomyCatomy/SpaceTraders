from pydantic import BaseModel

from models.meta import Meta


class BaseSpaceTradersResponse(BaseModel):
    data: object
    meta: Meta = None
