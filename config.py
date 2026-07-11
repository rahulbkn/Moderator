from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    max_image_size: int = 1280
    min_image_size: int = 640
    model_inference_resolution: int = 640
    nsfw_threshold: float = 0.45
    nsfw_multi_detection_threshold: float = 0.38
    falconsai_enabled: bool = True
    falconsai_model_name: str = "Falconsai/nsfw_image_detection"
    falconsai_min_score: float = 0.5
    log_level: str = "INFO"
    request_timeout: int = 30
    host: str = "0.0.0.0"
    port: int = 8000
    allowed_domains: list[str] = []

    model_config = {"protected_namespaces": ()}


settings = Settings()
