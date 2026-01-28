from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import time
import uuid
from datetime import datetime

from app.core.config import settings
from app.core.database import engine, Base
from app.api import auth, etudiants, stages, services, etablissements, documents, presences, rapports, seed


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Application de gestion des stages - Hôpital de Gisors",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    correlation_id = f"RX-GIS-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:4]}"
    request.state.correlation_id = correlation_id

    start_time = time.time()
    response = await call_next(request)
    duration = int((time.time() - start_time) * 1000)

    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["X-Response-Time"] = f"{duration}ms"

    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Erreur de validation des données",
                "details": exc.errors()
            },
            "meta": {
                "correlation_id": correlation_id
            }
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Une erreur interne est survenue"
            },
            "meta": {
                "correlation_id": correlation_id
            }
        }
    )


app.include_router(auth.router, prefix="/api")
app.include_router(etudiants.router, prefix="/api")
app.include_router(stages.router, prefix="/api")
app.include_router(services.router, prefix="/api")
app.include_router(etablissements.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(presences.router, prefix="/api")
app.include_router(rapports.router, prefix="/api")
app.include_router(seed.router, prefix="/api/seed", tags=["Données de test"])


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION
    }


@app.get("/")
async def root():
    return {
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "documentation": "/docs"
    }
