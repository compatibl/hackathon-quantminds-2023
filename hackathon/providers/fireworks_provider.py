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

import asyncio
import logging

import fireworks.client
from fireworks.client.error import FireworksError

from hackathon.providers.base_provider import BaseProvider, ProviderAnswer, ProviderParam

logger = logging.getLogger(__name__)


class FireworksProvider(BaseProvider):
    async def run(self, params: list[ProviderParam]) -> list[ProviderAnswer]:
        coroutines = [self._run(param) for param in params]
        if coroutines:
            results = await asyncio.gather(*coroutines)
        else:
            results = list()
        return results

    async def _run(self, param: ProviderParam) -> ProviderAnswer:
        question = self.build_question(prompt=param.prompt, context=param.context)
        formatted_question = self.add_llama_formatting(question)
        fireworks.client.api_key = self.api_key
        try:
            response = await fireworks.client.Completion.acreate(
                model=f"accounts/fireworks/models/{param.provider_model}",
                prompt=formatted_question,
                max_tokens=1024,
                temperature=param.temperature,
                top_p=param.top_p,
            )
            answer = response.choices[0].text
        except FireworksError as err:
            try:
                answer = self.get_error_answer(err.args[0]["fault"]["faultstring"])
            except:
                answer = self.get_error_answer(str(err))
        except:
            answer = self.get_error_answer("Fireworks is not available for now. Please try again later.")

        return ProviderAnswer(sample_id=param.sample_id, answer=answer)
