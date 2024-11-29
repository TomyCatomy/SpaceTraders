from pydantic import BaseModel

from models.meta import Meta


class Data(BaseModel):
    data: object
    meta: Meta = None
