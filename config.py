from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    max_image_size: int = 1080
    nudenet_model: str = "default"
    log_level: str = "INFO"
    request_timeout: int = 30
    host: str = "0.0.0.0"
    port: int = 8000
    allowed_domains: list[str] = [
        "res.cloudinary.com",
        "cloudinary.com",
    ]

    model_config = {"protected_namespaces": ()}


settings = Settings()
