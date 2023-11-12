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

        "PricingModels":  """You will be given the input below in the form of code
that is the pricing function of some financial instrument. Return only JSON with these keys:
* InstrumentType - enum with values EuropeanOption, AmericanOption, DigitalOption, BarrierOption, DoubleNoTouchOption
* BuyOrSell - Enum with values Buy and Sell
* PutOrCall - Enum with values Put and Call
* Notional - floating number for the notional or principal amount without currency
* Strike - floating number for the strike price
* UpperBarrier - floating number for the upper barrier level
* LowerBarrier - floating number for the lower barrier level
Source code: ```{input}```""",

        "TermSheets": """You will be given the input below in the form of a term sheet describing
some financial instrument. Return only JSON with these keys:
* InstrumentType - enum with values Interest Rate Swap, Amortizing Swap, Cross-Currency Swap 
* Principal - floating number for the notional or principal amount without currency
* PrincipalCurrency - currency in ISO-4217 format
* MaturityDate - date in ISO-8601 format
* SettlementDate - date in ISO-8601 format
Term sheet: ```{input}```"""
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
