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

    SHARD_SHARED_HOST: str = "localhost"
    SHARD_1_PORT: int = 3307
    SHARD_2_PORT: int = 3308
    SHARD_3_PORT: int = 3309
    SHARD_DB_USER: str = ""
    SHARD_DB_PASSWORD: str = ""
    SHARD_DB_NAME: str = ""
    RIDE_SHARD_LOOKUP_MODE: str = "modulo"

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

    def shard_port(self, shard_id: int) -> int:
        if shard_id == 0:
            return self.SHARD_1_PORT
        if shard_id == 1:
            return self.SHARD_2_PORT
        if shard_id == 2:
            return self.SHARD_3_PORT
        raise ValueError(f"Invalid shard_id: {shard_id}. Expected one of 0, 1, 2")

    def shard_database_uri(self, shard_id: int) -> str:
        user = self.SHARD_DB_USER or self.MYSQL_USER
        password = self.SHARD_DB_PASSWORD or self.MYSQL_PASSWORD
        db_name = self.SHARD_DB_NAME or self.MYSQL_DB
        host = self.SHARD_SHARED_HOST or self.MYSQL_HOST
        port = self.shard_port(shard_id)
        return f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"


settings = Settings()
