from __future__ import annotations

import logging
import logging.config
import traceback
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, Request
from starlette.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from app.schemas import rebuild_models

rebuild_models()

from app.api.main import api_router
from app.api.routes.media import router as media_router
from app.api.routes import sockets

from app.logging_config import LOGGING_CONFIG
from fastadmin import fastapi_app as admin_app
from fastadmin.settings import settings as admin_settings
from config import settings

admin_settings.ADMIN_USER_MODEL = "UserModel"
admin_settings.ADMIN_USER_MODEL_USERNAME_FIELD = "username"
admin_settings.ADMIN_SECRET_KEY = settings.SECRET_KEY

from app.admin.models import (
    bot,
    user,
    subscriber,
    message,
    session,
    step,
    widget,
    channel,
    connection,
    request,
    emitter,
    cron,
    note,
    template,
    credentials,
)
from app.admin import dashboard
from database import sessionmanager
from app.broker import broker
from app.fast_socket_app import fast_socket_app
from app.engine.request import global_http_client
from uvicorn.config import LOGGING_CONFIG as UVICORN_LOGGING_CONFIG

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown tasks for the FastAPI application."""
    try:
        await broker.start()
        await fast_socket_app.start()
        logging.info("Background services started")
        yield
    except Exception as exc:
        logging.error(f"Failed to start background services: {exc}")
    finally:
        await broker.close()
        await fast_socket_app.stop()
        logging.info("Background services stopped")
        await global_http_client.aclose()
        if sessionmanager.engine is not None:  # pyright: ignore
            await sessionmanager.close()


app = FastAPI(
    lifespan=lifespan,
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    logger.error(f"Unhandled error: {exc}\n{tb}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "error": str(exc),
        },
    )


app.mount('/static', StaticFiles(directory=settings.STATIC_ROOT), name='static')
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(sockets.router, tags=["ws"])
app.include_router(media_router, prefix=f"/{settings.MEDIA_URL}", tags=["media"])
app.mount("/admin", admin_app)


@app.get("/health", tags=["health"])
async def healthcheck():
    return JSONResponse(content={"status": "ok"})


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins; restrict in production.
    allow_credentials=False,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, ...).
    allow_headers=["*"],  # Allow all headers.
)


if __name__ == "__main__":
    UVICORN_LOGGING_CONFIG["formatters"]["default"]["fmt"] = "%(asctime)s [%(name)s] %(levelprefix)s %(message)s"
    UVICORN_LOGGING_CONFIG["formatters"]["access"]["fmt"] = '%(levelprefix)s %(asctime)s :: %(client_addr)s - "%(request_line)s" %(status_code)s'
    uvicorn.run("main:app", host="0.0.0.0", reload=True, port=8003, log_config=UVICORN_LOGGING_CONFIG)
