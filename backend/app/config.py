from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    fernet_key: str
    database_url: str
    media_dir: str
    env: str


settings = Settings() # type: ignore - Variables injected from the .env
