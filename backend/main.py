import sys
from pathlib import Path

# Ensure project root is in sys.path
_ROOT = str(Path(__file__).resolve().parent.parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from backend.database import init_db
from backend import config
from backend.routes import health, jobs, clips
from backend.utils.logger import get_logger

log = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    config.ensure_directories()
    init_db()
    log.info("ClipForge AI backend started on port %d", config.BACKEND_PORT)
    log.info("Data directory: %s", config.DATA_DIR)
    yield
    log.info("ClipForge AI backend shutting down")


app = FastAPI(
    title="ClipForge AI API",
    description="Turn long YouTube videos into viral-ready short clips.",
    version="1.0.0",
    lifespan=lifespan,
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
# Allowed local origins + production origin regex
allowed_origins = [
    config.FRONTEND_URL,
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]
if config.FRONTEND_URL not in allowed_origins:
    allowed_origins.append(config.FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(set(allowed_origins)),
    allow_origin_regex=r"^https://.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Global Exception Handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again.",
            },
        },
    )


# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(health.router, tags=["health"])
app.include_router(jobs.router, tags=["jobs"])
app.include_router(clips.router, tags=["clips"])


@app.get("/")
def root():
    return {
        "success": True,
        "data": {"name": "ClipForge AI", "version": "1.0.0"},
        "error": None,
    }
