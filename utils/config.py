from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    main_db_url: str
    file_db_url: str

    secret_key: str
    refresh_secret_key: str
    algorithm: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_MINUTES: int

    class Config:
        env_file = Path(Path(__file__).resolve().parent.parent) / ".env"

print(f"Loading environment variables from: {Settings.Config.env_file}")
settings = Settings()