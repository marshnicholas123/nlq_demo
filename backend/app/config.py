from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import field_validator

class Settings(BaseSettings):
    aws_region: str
    aws_access_key_id: str
    aws_secret_access_key: str
    bedrock_model_id: str
    bedrock_kb_id: str
    mysql_host: str
    mysql_port: int
    mysql_database: str
    mysql_user: str
    mysql_password: str

    # Phoenix Observability Settings
    phoenix_enabled: bool = True
    phoenix_project_name: str = "text2sql-app"
    phoenix_endpoint: Optional[str] = None  # None or empty uses local Phoenix, or set to remote OTLP endpoint
    phoenix_launch_app: bool = False  # Set to True to launch Phoenix UI on startup (local dev only)

    @field_validator('phoenix_endpoint', mode='before')
    @classmethod
    def empty_str_to_none(cls, v):
        """Convert empty string to None for phoenix_endpoint"""
        if v == '' or (isinstance(v, str) and v.strip() == ''):
            return None
        return v

    class Config:
        env_file = ".env"

settings = Settings()