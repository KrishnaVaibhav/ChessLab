from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.db.session import init_db
from app.services.engine import pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await pool.start()
    yield
    await pool.stop()


app = FastAPI(title="ChessLab API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
