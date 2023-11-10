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

import openai
from fastapi import status

from hackathon.exception import AppException

logger = logging.getLogger(__name__)


def run_openai(prompt: str, context: str, temperature: float, api_key: str):
    question = prompt.format(context=context)
    openai.api_key = api_key
    messages = [{"role": "user", "content": question}]
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            temperature=temperature,
        )
    except openai.error.AuthenticationError:
        raise AppException(status.HTTP_400_BAD_REQUEST, "Invalid OpenAI API key.")
    except openai.error.OpenAIError as err:
        logger.exception("Somthing go wrong with OpenAI.")
        raise AppException(status.HTTP_503_SERVICE_UNAVAILABLE, str(err))

    answer = response["choices"][0]["message"]["content"]
    return answer
