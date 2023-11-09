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

from http import HTTPStatus
from typing import Optional

from fastapi import HTTPException


class AppException(HTTPException):
    http_status_info: dict[int, HTTPStatus] = {
        int(status): status for status in HTTPStatus
    }

    def __init__(
        self,
        status_code: int,
        detail: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)

        info = self.http_status_info.get(status_code)
        name_info = info.phrase if info else str(status_code)
        description_info = info.description if info else str(status_code)

        self.name = name if name is not None else name_info
        self.description = description if description is not None else description_info
