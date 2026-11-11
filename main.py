import json
from contextlib import asynccontextmanager
from pathlib import Path
import asyncio
import sys

from fastapi import FastAPI, Request, status
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from app.routes.auth_routes import router  # updated path

from app.core.database import Base, async_engine
from app.core.config import settings

from app.models.user import User

FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@asynccontextmanager
async def lifespan(app: FastAPI):
    # This runs when Uvicorn starts up!
    async with async_engine.begin() as conn:
        # Asynchronously generates all tables (like "user") if they don't exist
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Clean up operations go here (if any)

app = FastAPI(title="MedicoSync Auth Sandbox", lifespan=lifespan)

app.include_router(router)


@app.get("/login", include_in_schema=False)
async def frontend_home():
    return FileResponse(FRONTEND_DIR / "Auth.html")


@app.get("/config.js", include_in_schema=False)
async def frontend_config():
    return Response(
        content=f"window.baseUrl = {json.dumps(settings.base_url)};\n",
        media_type="application/javascript",
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )


@app.exception_handler(PermissionError)
async def permission_error_handler(request: Request, exc: PermissionError):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": str(exc)}
    )
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")