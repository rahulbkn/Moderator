import logging
import os
import sys
import inspect  # Added to safely detect and resolve coroutines if utils.py misbehaves
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl

from config import settings
from moderation import get_moderator
from utils import prepare_image

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ModerateRequest(BaseModel):
    image_url: HttpUrl


class DetectionResult(BaseModel):
    label: str
    confidence: float


class ModerateResponse(BaseModel):
    success: bool
    safe: bool
    nsfw_score: float
    detections: list[DetectionResult]


class ErrorResponse(BaseModel):
    success: bool = False
    error: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up moderation API")
    moderator = get_moderator()
    moderator.load_model()
    yield
    logger.info("Shutting down moderation API")


app = FastAPI(
    title="Image Moderation API",
    version="1.0.0",
    description="Moderate images for NSFW content using NudeNet",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"message": "Welcome to the Image Moderation API. See /docs for API documentation."}


@app.post("/moderate", response_model=ModerateResponse | ErrorResponse)
async def moderate(request: ModerateRequest):
    image_url = str(request.image_url)
    tmp_path = None
    try:
        tmp_path = await prepare_image(image_url)
        
        # Double-check guard: If prepare_image returned a coroutine, resolve it
        if inspect.iscoroutine(tmp_path):
            tmp_path = await tmp_path
            
        moderator = get_moderator()
        result = moderator.analyze(tmp_path)
        return result
    except ValueError as e:
        logger.warning("Validation error: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Moderation failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        # Strict validation check to completely prevent the "TypeError: stat..." crash
        if tmp_path and isinstance(tmp_path, (str, bytes, os.PathLike)):
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                logger.debug("Cleaned up temp file: %s", tmp_path)
        elif tmp_path:
            logger.error("Cleanup skipped: tmp_path resolved to an invalid type: %s", type(tmp_path))


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )
