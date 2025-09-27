import dataclasses

import fastapi
import modern_di_fastapi
from lite_bootstrap import FastAPIBootstrapper
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

from app.api.notes import ROUTER as NOTES_ROUTER
from app.api.users import ROUTER as USERS_ROUTER
from app.settings import settings


def include_routers(app: fastapi.FastAPI) -> None:
    app.include_router(NOTES_ROUTER, prefix="/api")
    app.include_router(USERS_ROUTER, prefix="/api")


def build_app() -> fastapi.FastAPI:
    bootstrap_config = dataclasses.replace(
        settings.api_bootstrapper_config,
        opentelemetry_instrumentors=[
            SQLAlchemyInstrumentor(),
            AsyncPGInstrumentor(capture_parameters=True),  # type: ignore[no-untyped-call]
        ],
    )
    bootstrapper = FastAPIBootstrapper(bootstrap_config=bootstrap_config)
    app: fastapi.FastAPI = bootstrapper.bootstrap()
    modern_di_fastapi.setup_di(app)
    include_routers(app)
    return app
