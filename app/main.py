from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.endpoints.pages import router as pages_router
from app.api.v1.routers import api_router
from app.infrastructure.external.exceptions import KeitaroAPIError
from app.services.errors import (
    DomainValidationError,
    EntityNotFoundError,
    FlowDirtyError,
)

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="test_task_keitaro",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# 1) JSON API: /api/v1/...
app.include_router(api_router, prefix="/api")

# 2) HTML-страницы: / и /campaigns/{id}
app.include_router(pages_router)

# 3) Статика фронта (js/css). mkdir — чтобы mount не падал,
#    если папка ещё не создана (например, на чистом клоне репо)
static_dir = BASE_DIR / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


# ---------- Обработчики доменных ошибок ----------


@app.exception_handler(EntityNotFoundError)
async def _not_found_handler(request: Request, exc: EntityNotFoundError):
    return JSONResponse(status_code=404, content={"detail": exc.message})


@app.exception_handler(FlowDirtyError)
async def _dirty_handler(request: Request, exc: FlowDirtyError):
    return JSONResponse(status_code=409, content={"detail": exc.message})


@app.exception_handler(DomainValidationError)
async def _validation_handler(request: Request, exc: DomainValidationError):
    return JSONResponse(status_code=400, content={"detail": exc.message})


@app.exception_handler(KeitaroAPIError)
async def _keitaro_handler(request: Request, exc: KeitaroAPIError):
    # Покрывает и наследников: KeitaroNotFoundError, KeitaroAuthError
    return JSONResponse(
        status_code=502,
        content={"detail": f"Keitaro API error: {exc.message}"},
    )