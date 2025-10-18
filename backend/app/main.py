import uvicorn

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware

from routers import router
from settings import settings
from core.db import init_database
from core.broker import consumer_start, consumer_stop, producer_start, producer_stop


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_database()
    await consumer_start()
    await producer_start()
    yield
    await consumer_stop()
    await producer_stop()


app = FastAPI(
    debug=settings.SERVER_TEST,
    lifespan=lifespan,
    title="GoraSLavoy",
)

app.add_middleware(GZipMiddleware, minimum_size=2000)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router)


def main():
    uvicorn.run(
        "main:app",
        host=settings.SERVER_ADDR,
        port=settings.SERVER_PORT,
        reload=settings.SERVER_TEST,
        log_level="debug" if settings.SERVER_TEST else "info",
    )


if __name__ == "__main__":
    main()
