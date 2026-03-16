from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


# reads configuration from .env file and provides settings for the application
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "RAJAK Backend"
    APP_ENV: str = "development"
    API_V1_PREFIX: str = "/api/v1"

    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_DB: str = "cabSharing"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"
        )


settings = Settings()
