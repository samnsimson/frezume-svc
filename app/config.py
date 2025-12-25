from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    port: Optional[int] = Field(default=8888, env="PORT")
    host: Optional[str] = Field(default="0.0.0.0", env="HOST")
    api_key: Optional[str] = Field(default=None, env="API_KEY")
    nebius_api_key: Optional[str] = Field(default=None, env="NEBIUS_API_KEY")
    nebius_api_url: Optional[str] = Field(default=None, env="NEBIUS_API_URL")
    nebius_model: Optional[str] = Field(default=None, env="NEBIUS_MODEL")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    llama_cloud_api_key: Optional[str] = Field(default=None, env="LLAMA_CLOUD_API_KEY")
    aws_access_key_id: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    aws_region: Optional[str] = Field(default="us-east-1", env="AWS_REGION")
    aws_s3_bucket: Optional[str] = Field(default=None, env="AWS_S3_BUCKET")
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    jwt_secret: Optional[str] = Field(default=None, env="JWT_SECRET")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
