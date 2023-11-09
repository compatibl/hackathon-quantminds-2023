# Copyright (C) 2023-present The Project Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware

from hackathon.api import routes
from hackathon.exception import AppException
from hackathon.hackathon_settings import get_settings

app = FastAPI()

app.include_router(routes.router)

trusted_origins = ["*"]

# FIXME: Mikita
app.add_middleware(
    CORSMiddleware,
    allow_origins=trusted_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


static_files_dir = Path(__file__).parents[1].joinpath("wwwroot")
app.mount("/", StaticFiles(directory=static_files_dir, html=True), name="static")


@app.exception_handler(AppException)
async def app_exception_handler(_, exc: AppException):
    content = {
        "name": exc.name,
        "description": exc.description,
        "detail": exc.detail,
    }
    return JSONResponse(content=content, status_code=exc.status_code, headers=exc.headers)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_, exc):
    headers = getattr(exc, "headers", None)
    app_exception = AppException(status_code=exc.status_code, detail=exc.detail, headers=headers)
    return await app_exception_handler(_, app_exception)


def main(host: str, port: int, workers: int):
    uvicorn.run(
        app="main:app",
        host=host,
        port=port,
        workers=workers,
    )


if __name__ == "__main__":
    settings = get_settings()
    main(host=settings.host, port=settings.port, workers=settings.workers)
