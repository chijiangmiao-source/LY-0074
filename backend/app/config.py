from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "花店花桶周转管理系统"
    DEBUG: bool = True
    
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "flower_shop"
    
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    class Config:
        env_file = ".env"


settings = Settings()
