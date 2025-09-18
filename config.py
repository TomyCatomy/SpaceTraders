from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    agent_symbol: str
    faction_symbol: str
    agent_token: Optional[str] = None
    account_token: Optional[str] = None
    mongodb_connection_string: str

    model_config = SettingsConfigDict(env_file='.env', case_sensitive=False)


config = Config()
