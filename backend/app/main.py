"""Application entrypoint.

Run locally:
    uvicorn app.main:app --reload    (from inside backend/)

The interactive API docs (great for demos!) are at http://localhost:8000/docs
"""
import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import tasks, executions
from .scheduler import scheduler_loop

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # create tables on startup (simple MVP choice; v2 = real migrations via Alembic)
    Base.metadata.create_all(bind=engine)
    scheduler = asyncio.create_task(scheduler_loop())
    yield
    scheduler.cancel()


app = FastAPI(title="Scheduled Task Manager", version="0.1.0", lifespan=lifespan)

# STUDY NOTE: allow_origins is pinned to the frontend URL, NOT "*".
# In v2 add auth + credentials and this becomes important.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router)
app.include_router(executions.router)


@app.get("/health")
def health():
    """Used by the demo task 'Self health check' - a task that calls our
    OWN api so the demo works offline."""
    return {"status": "ok"}
