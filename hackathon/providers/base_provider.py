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

import abc
import asyncio
from dataclasses import dataclass
from typing import Final, Optional


@dataclass
class ProviderParam:
    sample_id: int
    provider_model: str
    prompt: Optional[str] = None
    context: Optional[str] = None
    seed: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None


@dataclass
class ProviderAnswer:
    sample_id: int
    answer: str


class BaseProvider(abc.ABC):
    RETRY_ATTEMPT: Final[int] = 3

    def __init__(self, api_key: str):
        self.api_key = api_key

    @abc.abstractmethod
    async def get_answer(self, param: ProviderParam) -> ProviderAnswer:
        ...

    async def run(self, params: list[ProviderParam]) -> list[ProviderAnswer]:
        coroutines = [self.get_answer(param) for param in params]
        if coroutines:
            results = await asyncio.gather(*coroutines)
        else:
            results = list()
        return results

    @staticmethod
    def get_error_answer(msg: str = "") -> str:
        return f"An error has occurred: {msg}"

    @staticmethod
    def build_question(prompt: str, context: str) -> str:
        if "{input}" not in prompt:
            prompt += "\nYour answer should be based on the following input: \n```\n{input}\n```"

        question = prompt.format(input=context)
        return question

    @staticmethod
    def add_llama_formatting(question: str) -> str:
        if not question.startswith("[INST]") or not question.startswith("<s>[INST]"):
            question = "[INST]" + question

        if not question.endswith("[/INST]"):
            question = question + "[/INST]"

        return question
