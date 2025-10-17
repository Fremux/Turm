from contextlib import asynccontextmanager

import uvicorn
from core.db import init_database
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from routers import router

from settings import settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_database()
    yield
    # Close connection to DB

app = FastAPI(debug=settings.SERVER_TEST,
              lifespan=lifespan,
              title="GoraSLavoy",
              )

app.add_middleware(
    GZipMiddleware,
    minimum_size=2000
)

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
