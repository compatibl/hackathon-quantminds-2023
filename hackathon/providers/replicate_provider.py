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
import os

import replicate
from fastapi import status
from replicate.exceptions import ReplicateException

from hackathon.exception import AppException

logger = logging.getLogger(__name__)


def run_replicate(*, prompt: str, context: str, seed: int, temperature: float, top_p: float, top_k: int, api_key: str):
    question = prompt.format(context=context)
    os.environ["REPLICATE_API_TOKEN"] = api_key
    try:
        output = replicate.run(
            "meta/llama-2-70b-chat:02e509c789964a7ea8736978a43525956ef40397be9033abf9fd2badfe68c9e3",
            input={
                "prompt": question,
                "seed": seed,
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
            },
        )
    except ReplicateException as err:
        logger.exception("Somthing go wrong with Replicate.")
        raise AppException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(err),
        )

    answer = ""
    for item in output:
        answer += item

    return answer
