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
import os

import replicate
from replicate.exceptions import ReplicateException

from hackathon.providers.base_provider import BaseProvider, ProviderAnswer, ProviderParam

logger = logging.getLogger(__name__)


class ReplicateProvider(BaseProvider):
    model_token_dict = {"llama-2-7b-chat": "13c3cdee13ee059ab779f0291d29054dab00a47dad8261375654de5540165fb0",
                        "llama-2-13b-chat": "f4e2de70d66816a838a89eeeb621910adffb0dd0baba3976c96980970978018d",
                        "llama-2-70b-chat": "02e509c789964a7ea8736978a43525956ef40397be9033abf9fd2badfe68c9e3"}
    
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
        os.environ["REPLICATE_API_TOKEN"] = self.api_key
        try:
            output = await replicate.async_run(
                f"meta/{param.provider_model}:{self.model_token_dict[param.provider_model]}",
                input={
                    "prompt": formatted_question,
                    "seed": param.seed,
                    "temperature": param.temperature,
                    "top_p": param.top_p,
                    "top_k": param.top_k,
                },
            )
            answer = "".join(output)
        except ReplicateException as err:
            answer = self.get_error_answer(str(err))
        except:
            answer = self.get_error_answer("Replicate is not available for now. Please try again later.")

        return ProviderAnswer(sample_id=param.sample_id, answer=answer)
