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

import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    default_prompts: dict[str, str] = {
        "code": "You will be given the context below in the form of code that is the pricing function of some financial"
        " instrument.\nReturn only JSON with keys:\ninstrument_type - enum with values european_option, american_option"
        ", digital_option, barrier_option\nbuy_sell - enum with values buy and sell\nput_call - enum with values put "
        "and call\ndf - discount factor\nstrike - strike price\nbarrier - barrier price (use this key only for "
        "barrier_option)\nCode:\n```\n{input}\n```",
        "text": "Pay attention and remember information below.\nContext:\n```\n{input}\n```\nAccording to the "
        "information in the context above, return only JSON with keys:\ninstrument_type: string,\nmaturity_date: date,"
        "\nsettlement_date: date",
    }
    allow_origins: list[str] = ["http://localhost:3000"]
    static_path: Path = Path(__file__).parents[1].joinpath("./wwwroot")
    data_path: Path = Path(__file__).parents[1].joinpath("./data")
    log_level: str = os.getenv("LOG_LEVEL", "DEBUG")
    host: str = os.getenv("UVICORN_HOST", "localhost")
    port: int = os.getenv("UVICORN_PORT", 8000)
    workers: int = os.getenv("UVICORN_WORKERS", 1)


@lru_cache
def get_settings() -> Settings:
    return Settings()
