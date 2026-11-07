import asyncio
import logging
import os
from contextlib import asynccontextmanager

import psycopg
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api import health, images, sessions, users
from db import repository as repo
from db.connection import close_pool
from services import image_service

logger = logging.getLogger(__name__)

PURGE_INTERVAL_SECONDS = 600

async def _purge_inactive_images_forever() -> None:
    while True:
        try:
            await asyncio.to_thread(image_service.purge_inactive_images)
        except Exception:
            logger.exception("could not delete inactive images")
        await asyncio.sleep(PURGE_INTERVAL_SECONDS)

@asynccontextmanager
async def lifespan(_app: FastAPI):
    purge_task = asyncio.create_task(_purge_inactive_images_forever())
    yield
    purge_task.cancel()
    try:
        await purge_task
    except asyncio.CancelledError:
        pass
    close_pool()

app = FastAPI(
    title="Sprint Form Analyzer API",
    version="0.2.0",
    lifespan=lifespan,
)

_origins = [
    origin.strip()
    for origin in os.getenv("AGOS_CORS_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins or ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(repo.ValidationError)
async def _validation_error(request: Request, exc: repo.ValidationError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})

@app.exception_handler(repo.ConflictError)
async def _conflict_error(request: Request, exc: repo.ConflictError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})

@app.exception_handler(psycopg.IntegrityError)
async def _integrity_error(request: Request, exc: psycopg.IntegrityError):
    return JSONResponse(
        status_code=409, content={"detail": "constraint violation"}
    )

@app.exception_handler(psycopg.OperationalError)
async def _database_unavailable(request: Request, exc: psycopg.OperationalError):
    return JSONResponse(
        status_code=503, content={"detail": "database unavailable"}
    )

app.include_router(health.router)
app.include_router(users.router)
app.include_router(sessions.router)
app.include_router(images.router)
