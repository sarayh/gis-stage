from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_PORT: int = 8080
    APP_NAME: str = "GIS-Stage"
    APP_VERSION: str = "1.0.0"

    DATABASE_URL: str = "postgresql://gis_user:gis_password@db:5432/gis_stage"

    LDAP_URL: str = "ldaps://ldap.ch-gisors.local"
    LDAP_BASE_DN: str = "ou=ou_ch_gisors,dc=ch-gisors,dc=local"
    LDAP_TIMEOUT: int = 5

    API_MAIL: str = "http://sendmail.ch-gisors.local/sendmail"
    SMTP_FROM: str = "gis-stage@ch-gisors.fr"
    SMTP_TIMEOUT: int = 10

    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    UPLOAD_DIR: str = "/data/uploads"
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024
    ALLOWED_EXTENSIONS: list = [".pdf", ".doc", ".docx", ".jpg", ".jpeg", ".png"]

    MAX_STAGES_YEAR: int = 2000
    MAX_ETUDIANTS: int = 5000
    MAX_DOCS_PER_STAGE: int = 10
    MAX_CONCURRENT_USERS: int = 50
    MAX_LIGNES_EXPORT: int = 10000

    RATE_LIMIT_REQUESTS: int = 30
    RATE_LIMIT_PERIOD: int = 60

    API_TIMEOUT: int = 10

    CORS_ORIGINS: list = ["http://localhost:3092", "http://127.0.0.1:3092"]

    # Configuration SH - Règles mission-critique
    SH_DEFAULT_MAX_ITEMS: int = 10000
    SH_MAX_SERVICES: int = 100
    SH_MAX_ETABLISSEMENTS: int = 200
    SH_MAX_PRESENCES_BATCH: int = 500
    SH_CORRELATION_DOMAIN: str = "GIS"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
