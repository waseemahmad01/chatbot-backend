from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    openai_api_key: str
    groq_api_key: str
    jwt_secret: str
    jwt_expiration_time: int
    currency_api_key: str
    tavily_api_key: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
