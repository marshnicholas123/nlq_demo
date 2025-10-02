from pydantic_settings import BaseSettings

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
    
    class Config:
        env_file = ".env"

settings = Settings()