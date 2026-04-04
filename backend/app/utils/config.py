from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://user:password@localhost:5432/fundeb_insights"
    debug: bool = False
    allowed_origins: list[str] = ["http://localhost:5500", "http://127.0.0.1:5500"]

    model_config = {"env_file": ".env"}

    @property
    def cors_origins(self) -> list[str]:
        """Merge default local origins with any extra origins from ALLOWED_ORIGINS env var."""
        defaults = ["http://localhost:5500", "http://127.0.0.1:5500"]
        for origin in self.allowed_origins:
            if origin not in defaults:
                defaults.append(origin)
        return defaults


settings = Settings()
