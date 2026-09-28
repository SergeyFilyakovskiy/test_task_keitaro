from pathlib import Path

from pydantic import Field
from pydantic.types import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).parent.parent.parent.parent.parent / ".env"

class Config(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=ENV_FILE if ENV_FILE.exists() else None,
        case_sensitive=True,
        extra='ignore'
    )

    postgres_user: str = Field(validation_alias='POSTGRES_USER')
    postgres_password: SecretStr = Field(validation_alias='POSTGRES_PASSWORD')
    postgres_host: str = Field(validation_alias='POSTGRES_HOST')
    postgres_port: int = Field(validation_alias='POSTGRES_PORT')
    postgres_db_name: str = Field(validation_alias='POSTGRES_AUTH_DB')

    keitaro_api_url: str = Field(
        default="https://your-keitaro-domain.com/admin_api/v1",
        validation_alias="KEITARO_API_URL",
    )
    keitaro_api_key: SecretStr = Field(validation_alias="KEITARO_API_KEY")

    @property
    def db_async_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:"
            f"{self.postgres_password.get_secret_value()}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db_name}"
        )

    @property
    def db_migrations_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:"
            f"{self.postgres_password.get_secret_value()}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db_name}"
        )

settings = Config()  # type: ignore
