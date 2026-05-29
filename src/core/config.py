from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import cached_property


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="VERILAB_", env_file=".env", extra="ignore")

    anthropic_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("ANTHROPIC_API_KEY", "VERILAB_ANTHROPIC_API_KEY"),
    )
    openrouter_api_key: str = Field(
        default="",
        validation_alias=("OPENROUTER_API_KEY")
    )
    llm_model: str = "openrouter/qwen/qwen3.7-max"
    allowed_targets: str = ""
    db_path: str = "data/verilab.db"
    max_iterations: int = 10

    @cached_property
    def allowed_targets_list(self) -> list[str]:
        return [t.strip() for t in self.allowed_targets.split(",") if t.strip()]


settings = Settings()
