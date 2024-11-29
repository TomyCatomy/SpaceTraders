from typing import Optional

from pydantic import BaseModel


class RegisterAgentReq(BaseModel):
    faction: str
    symbol: str
    email: Optional[str] = None
