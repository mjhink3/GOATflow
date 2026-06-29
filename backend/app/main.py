from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_pool, close_pool, ensure_schema
from app.routers import auth, signals, player, horns, stakes, churn, log, leaderboard, behavioral


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = await create_pool()
    async with pool.acquire() as conn:
        await ensure_schema(conn)
    yield
    await close_pool()


app = FastAPI(title="GOATflow API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(signals.router, prefix="/signals", tags=["signals"])
app.include_router(player.router, prefix="/player", tags=["player"])
app.include_router(horns.router, prefix="/horns", tags=["horns"])
app.include_router(stakes.router, prefix="/stakes", tags=["stakes"])
app.include_router(churn.router, prefix="/churn", tags=["churn"])
app.include_router(log.router, prefix="/log", tags=["log"])
app.include_router(leaderboard.router, prefix="/leaderboard", tags=["leaderboard"])
app.include_router(behavioral.router, prefix="/behavioral", tags=["behavioral"])


@app.get("/health")
async def health():
    return {"status": "ok"}
