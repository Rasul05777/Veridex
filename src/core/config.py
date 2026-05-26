from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import cached_property


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="VERILAB_", env_file=".env", extra="ignore")

    anthropic_api_key: str = ""
    llm_model: str = "claude-sonnet-4-6"
    allowed_targets: str = ""
    db_path: str = "data/verilab.db"
    max_iterations: int = 10

    @cached_property
    def allowed_targets_list(self) -> list[str]:
        return [t.strip() for t in self.allowed_targets.split(",") if t.strip()]


settings = Settings()
