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

import logging

import fireworks.client
import httpx

from fastapi import status
from hackathon.exception import AppException

logger = logging.getLogger(__name__)


def run_fireworks(
    prompt: str,
    context: str,
    api_key: str,
    temperature: float,
    top_p: float,
):
    question = prompt.format(context=context)

    fireworks.client.api_key = api_key
    try:
        response = fireworks.client.Completion.create(
            model="accounts/fireworks/models/llama-v2-70b-chat",
            prompt=question,
            max_tokens=1024,
            temperature=temperature,
            top_p=top_p,
        )
    except httpx.HTTPStatusError as err:
        logger.exception("Somthing go wrong with Fireworks.")
        raise AppException(status.HTTP_503_SERVICE_UNAVAILABLE, str(err))

    answer = response.choices[0].text
    return answer
