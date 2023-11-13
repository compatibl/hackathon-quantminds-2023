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

from typing import Final

import aiohttp
import openai
from openai import OpenAIError
from tenacity import retry, stop_after_attempt

from hackathon.providers.base_provider import BaseProvider, ProviderAnswer, ProviderParam


class OpenAIProvider(BaseProvider):
    REQUEST_TIMEOUT: Final[int] = 120

    async def run(self, params: list[ProviderParam]) -> list[ProviderAnswer]:
        async with aiohttp.ClientSession() as session:
            openai.aiosession.set(session)
            openai.api_key = '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' # self.api_key
            return await super().run(params)

    async def get_answer(self, param: ProviderParam) -> ProviderAnswer:
        try:
            response = await self._openai_create(param)
            answer = response["choices"][0]["message"]["content"]
        except OpenAIError as err:
            answer = self.get_error_answer(str(err))
        except:
            answer = self.get_error_answer("OpenAI is not available for now. Please try again later.")
        return ProviderAnswer(sample_id=param.sample_id, answer=answer)

    @retry(reraise=True, stop=stop_after_attempt(BaseProvider.RETRY_ATTEMPT))
    async def _openai_create(self, param: ProviderParam):
        if not param.question:
            question = self.build_question(prompt=param.prompt, context=param.context)
        else:
            question = param.question
        messages = [{"role": "user", "content": question}]
        return await openai.ChatCompletion.acreate(
            model=param.provider_model,
            messages=messages,
            temperature=param.temperature,
            request_timeout=self.REQUEST_TIMEOUT,
        )
