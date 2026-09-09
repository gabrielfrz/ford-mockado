from pydantic import BaseSettings
class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./demo.db"
settings = Settings()
