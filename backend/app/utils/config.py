from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://user:password@localhost:5432/fundeb_insights"
    debug: bool = False
    allowed_origins: list[str] = ["http://localhost:5500", "http://127.0.0.1:5500"]

    model_config = {"env_file": ".env"}


settings = Settings()
