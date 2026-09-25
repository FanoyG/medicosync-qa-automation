from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.routes.auth_routes import router  # updated path

app = FastAPI(title="MedicoSync Auth Sandbox")

app.include_router(router)


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