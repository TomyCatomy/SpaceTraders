from pydantic import BaseModel


class Meta(BaseModel):
    total: int
    page: int
    limit: int
