from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    max_image_size: int = 1080
    model_cache_dir: str = "~/.nudenet"
    log_level: str = "INFO"
    request_timeout: int = 30
    host: str = "0.0.0.0"
    port: int = 8000
    allowed_domains: list[str] = [
        "res.cloudinary.com",
        "cloudinary.com",
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
