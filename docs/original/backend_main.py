"""Create and configure the D&R Dashboard FastAPI application."""

import os

from fastapi import FastAPI, Security
from fastapi.middleware.cors import CORSMiddleware
from app.core.auth import require_authenticated_user
from app.openapi import (
    API_DESCRIPTION,
    API_TITLE,
    API_VERSION,
    OPENAPI_TAGS,
    configure_openapi_compatibility,
    generate_operation_id,
    get_openapi_contact,
    get_openapi_servers,
)
from app.routes.system_routes import router as system_router
from app.routes.summary_routes import router as summary_router
from app.routes.effective_point_routes import router as effective_point_router
from app.routes.vehicle_line_routes import router as vehicle_line_router
from app.routes.fede_status_routes import router as fede_status_router, router_v1 as fede_status_v1_router
from app.routes.export_routes import router as export_router
from app.routes.milestone_readiness_routes import router as milestone_readiness_router
from app.routes.cost_routes import router as cost_router
from app.routes.dvp_glidepath_routes import router as dvp_glidepath_router
from app.routes.pmt_routes import router as pmt_router
from app.routes.dpa5_routes import router as dpa5_router

app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    contact=get_openapi_contact(),
    license_info={"name": "Ford Internal Use Only"},
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=OPENAPI_TAGS,
    servers=get_openapi_servers(),
    generate_unique_id_function=generate_operation_id,
)

# Crunch and other API catalogs broadly support the OpenAPI 3.0.x contract.
app.openapi_version = "3.0.3"

default_cors_origins = {
    "http://localhost:4200",
    "http://127.0.0.1:4200",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
}
configured_cors_origins = {
    origin.strip().rstrip("/")
    for origin in os.getenv("CORS_ALLOW_ORIGINS", "").split(",")
    if origin.strip()
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(default_cors_origins | configured_cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health and API documentation remain public. All business routers require a
# validated Entra access token with the configured delegated scope.
protected_dependencies = [Security(require_authenticated_user)]

app.include_router(system_router)
app.include_router(summary_router, dependencies=protected_dependencies)
app.include_router(effective_point_router, dependencies=protected_dependencies)
app.include_router(vehicle_line_router, dependencies=protected_dependencies)
app.include_router(fede_status_router, dependencies=protected_dependencies)
app.include_router(fede_status_v1_router, dependencies=protected_dependencies)
app.include_router(export_router, dependencies=protected_dependencies)
app.include_router(
    milestone_readiness_router, dependencies=protected_dependencies
)
app.include_router(cost_router, dependencies=protected_dependencies)
app.include_router(dvp_glidepath_router, dependencies=protected_dependencies)
app.include_router(pmt_router, dependencies=protected_dependencies)
app.include_router(dpa5_router, dependencies=protected_dependencies)

configure_openapi_compatibility(app)
