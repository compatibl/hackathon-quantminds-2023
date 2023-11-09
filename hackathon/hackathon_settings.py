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

from pydantic_settings import BaseSettings


@lru_cache
def get_settings():
    return Settings()


class Settings(BaseSettings):
    data_path: str = os.getenv("DATA_PATH", "./data")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    host: str = os.getenv("HOST", "localhost")
    port: int = os.getenv("PORT", 8000)
    workers: int = os.getenv("WORKERS", 1)
