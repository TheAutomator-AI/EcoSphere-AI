from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    database_url: str = 'sqlite:///./ecosystem_local.db'
    allowed_origins: str = 'http://localhost:3000'
    supabase_url: str = ''
    supabase_jwt_audience: str = 'authenticated'
    supabase_service_role_key: str = ''
    supabase_storage_bucket: str = 'ecosphere-evidence'
    dev_auth_mode: bool = False
    upload_dir: str = './uploads'
    max_file_bytes: int = 8388608

settings = Settings()
