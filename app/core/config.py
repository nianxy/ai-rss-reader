from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_host: str = Field(default='0.0.0.0', alias='APP_HOST')
    app_port: int = Field(default=8000, alias='APP_PORT')

    database_url: str = Field(default='sqlite:///./rss_reader.db', alias='DATABASE_URL')
    rss_config_path: str = Field(default='config/rss_config.yaml', alias='RSS_CONFIG_PATH')

    fetch_cron: str = Field(default='*/30 * * * *', alias='FETCH_CRON')
    daily_summary_cron: str = Field(default='30 8 * * *', alias='DAILY_SUMMARY_CRON')

    llm_api_key: str = Field(default='', alias='LLM_API_KEY')
    llm_base_url: str = Field(default='https://api.openai.com/v1', alias='LLM_BASE_URL')
    llm_model: str = Field(default='gpt-4o-mini', alias='LLM_MODEL')

    smtp_host: str = Field(default='', alias='SMTP_HOST')
    smtp_port: int = Field(default=587, alias='SMTP_PORT')
    smtp_username: str = Field(default='', alias='SMTP_USERNAME')
    smtp_password: str = Field(default='', alias='SMTP_PASSWORD')
    smtp_use_tls: bool = Field(default=True, alias='SMTP_USE_TLS')
    email_from: str = Field(default='', alias='EMAIL_FROM')
    email_to: str = Field(default='', alias='EMAIL_TO')

    server_base_url: str = Field(default='http://127.0.0.1:8000', alias='SERVER_BASE_URL')


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
