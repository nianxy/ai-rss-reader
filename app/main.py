from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.services.scheduler_service import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(_: FastAPI):
    start_scheduler()
    try:
        yield
    finally:
        stop_scheduler()


app = FastAPI(title='RSS Reader', lifespan=lifespan)
app.include_router(router)
