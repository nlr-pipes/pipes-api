from __future__ import annotations

import logging
from contextlib import asynccontextmanager

# Access groups
from pipes.accessgroups.routes import router as accessgroups_router
from pipes.accessgroups.schemas import AccessGroupDocument

# Catalog Datasets
from pipes.catalogdatasets.routes import router as catalogdatasets_router
from pipes.catalogdatasets.schemas import CatalogDatasetDocument

# Catalog Models
from pipes.catalogmodels.routes import router as catalogmodels_router
from pipes.catalogmodels.schemas import CatalogModelDocument

# Settings
from pipes.config.settings import settings
from pipes.datasets.routes import router as datasets_router

# Datasets
from pipes.datasets.schemas import DatasetDocument
from pipes.handoffs.routes import router as handoffs_router

# Handoffs
from pipes.handoffs.schemas import HandoffDocument

# Health
from pipes.health.routes import router as health_router
from pipes.modelruns.routes import router as modelruns_router

# Modelruns
from pipes.modelruns.schemas import ModelRunDocument

# Models
from pipes.models.routes import router as models_router
from pipes.models.schemas import ModelDocument
from pipes.projectruns.routes import router as projectruns_router

# Projectruns
from pipes.projectruns.schemas import ProjectRunDocument
from pipes.projects.routes import router as projects_router

# Projects
from pipes.projects.schemas import ProjectDocument
from pipes.tasks.routes import router as tasks_router

# Tasks
from pipes.tasks.schemas import TaskDocument

# Teams
from pipes.teams.routes import router as teams_router
from pipes.teams.schemas import TeamDocument

# Users
from pipes.users.routes import router as users_router
from pipes.users.schemas import UserDocument

# Version
from pipes.version import __version__

from beanie import init_beanie
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    """FastAPI application life span"""
    # Init beanie
    if settings.PIPES_ENV in ["dev", "stage", "prod"]:
        docdb_uri = "mongodb://{}:{}@{}:{}/{}".format(
            settings.PIPES_DOCDB_USER,
            settings.PIPES_DOCDB_PASS,
            settings.PIPES_DOCDB_HOST,
            settings.PIPES_DOCDB_PORT,
            settings.PIPES_DOCDB_NAME,
        )
        docdb_uri += "?replicaSet=rs0&readPreference=secondaryPreferred&retryWrites=false"
    else:
        docdb_uri = f"mongodb://{settings.PIPES_DOCDB_HOST}:{settings.PIPES_DOCDB_PORT}/{settings.PIPES_DOCDB_NAME}"

    motor_client = AsyncIOMotorClient(docdb_uri)

    await init_beanie(
        database=motor_client[settings.PIPES_DOCDB_NAME],
        document_models=[
            ProjectDocument,
            ProjectRunDocument,
            ModelDocument,
            ModelRunDocument,
            DatasetDocument,
            HandoffDocument,
            TaskDocument,
            TeamDocument,
            UserDocument,
            CatalogModelDocument,
            CatalogDatasetDocument,
            AccessGroupDocument,
        ],
    )

    yield

    # Close motor client
    motor_client.close()


app = FastAPI(
    title=settings.TITLE,
    version=__version__,
    debug=settings.DEBUG,
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log validation errors for debugging"""
    body = await request.body()
    logger.error(f"Validation error for {request.method} {request.url}")
    logger.error(f"Request body: {body.decode('utf-8')}")
    logger.error(f"Validation errors: {exc.errors()}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": body.decode("utf-8")},
    )


# CORS settings - https://fastapi.tiangolo.com/tutorial/cors/
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_credentials=False,  # TODO: Update later
    allow_methods=settings.ALLOW_METHODS,
    allow_headers=settings.ALLOW_HEADERS,
)

# Routers
app.include_router(health_router, prefix="/api", tags=["health"])
app.include_router(catalogmodels_router, prefix="/api", tags=["catalogmodels"])
app.include_router(catalogdatasets_router, prefix="/api", tags=["catalogdatasets"])
app.include_router(projects_router, prefix="/api", tags=["projects"])
app.include_router(projectruns_router, prefix="/api", tags=["projectruns"])
app.include_router(models_router, prefix="/api", tags=["models"])
app.include_router(modelruns_router, prefix="/api", tags=["modelruns"])
app.include_router(datasets_router, prefix="/api", tags=["datasets"])
app.include_router(handoffs_router, prefix="/api", tags=["handoffs"])
app.include_router(tasks_router, prefix="/api", tags=["tasks"])
app.include_router(teams_router, prefix="/api", tags=["teams"])
app.include_router(users_router, prefix="/api", tags=["users"])
app.include_router(accessgroups_router, prefix="/api", tags=["accessgroups"])


@app.get("/")
async def welcome():
    return RedirectResponse("/api")
