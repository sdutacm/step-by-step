import asyncio
import sys

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI, Request
from loguru import logger

from app.routers.admin import router as admin_router
from app.routers.auth import router as auth_router
from app.routers.board import router as board_router
from app.routers.group import router as group_router
from app.routers.group_import import router as group_import_router
from app.routers.problem import router as problem_router
from app.routers.solution import router as solution_router
from app.routers.source import router as source_router
from app.routers.step import router as step_router
from sources import sources
from sources.base import SourceBase

logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
)
logger.add(
    "logs/app_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="30 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG",
)

app = FastAPI()

scheduler = BackgroundScheduler()


def create_sync_problems_task(source_cls: SourceBase):
    source_name = source_cls.__name__

    def task():
        logger.info(f"Starting scheduled {source_name} problems sync")
        try:
            asyncio.run(source_cls.problems())
        except Exception as e:
            logger.error(f"Error syncing {source_name} problems: {e}")

    return task


def create_sync_solutions_task(source_cls: SourceBase):
    source_name = source_cls.__name__

    def task():
        logger.info(f"Starting scheduled {source_name} solutions sync")
        try:
            asyncio.run(source_cls.solutions())
        except Exception as e:
            logger.error(f"Error syncing {source_name} solutions: {e}")

    return task


@app.on_event("startup")
async def startup_event():
    logger.info("Application startup")
    for source_cls in sources:
        scheduler.add_job(
            create_sync_problems_task(source_cls),
            CronTrigger(hour=0, minute=0),
            id=f"sync_{source_cls.__name__.lower()}_problems",
            replace_existing=True,
        )
        scheduler.add_job(
            create_sync_solutions_task(source_cls),
            IntervalTrigger(minutes=1),
            id=f"sync_{source_cls.__name__.lower()}_solutions",
            replace_existing=True,
        )
    scheduler.start()
    logger.info("Scheduler started")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown")
    scheduler.shutdown()


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(
        f"Response: {request.method} {request.url.path} - {response.status_code}"
    )
    return response


app.include_router(auth_router)
app.include_router(source_router)
app.include_router(solution_router)
app.include_router(step_router)
app.include_router(problem_router)
app.include_router(group_router)
app.include_router(group_import_router)
app.include_router(admin_router)
app.include_router(board_router)


@app.get("/")
def read_root():
    return {"message": "Hello World"}
