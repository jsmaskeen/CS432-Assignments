from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


# reads configuration from .env file and provides settings for the application
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "RAJAK Backend"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    API_V1_PREFIX: str = "/api/v1"
    FRONTEND_ORIGIN: str = "http://localhost:5173"
    AUDIT_LOG_FILE: str = "audit.log"
    ADMIN_BOOTSTRAP_USERNAME: str = ""

    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_DB: str = "cabSharing"

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120

    ORS_API_KEY: str = ""
    ORS_BASE_URL: str = "https://api.openrouteservice.org"

    DB_POOL_SIZE: int = 30
    DB_MAX_OVERFLOW: int = 60
    DB_POOL_TIMEOUT: int = 15

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"
        )


settings = Settings()
