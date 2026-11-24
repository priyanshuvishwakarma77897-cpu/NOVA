
from fastapi import FastAPI
from backend.app.core.exceptions import AppException
from backend.app.core.exception_handlers import (
    app_exception_handler,
    general_exception_handler,
)
from backend.app.core.config import settings
from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.auth import router as auth_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }

app.include_router(
    auth_router,
    prefix=settings.API_V1_PREFIX + "/auth",
    tags=["Authentication"],
)
app.include_router(
    health_router,
    prefix=settings.API_V1_PREFIX + "/health",
    tags=["Health"],
)
