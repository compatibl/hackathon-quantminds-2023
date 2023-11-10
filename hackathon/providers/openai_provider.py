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

import openai
from openai import OpenAIError

from hackathon.providers.base_provider import BaseProvider, ProviderAnswer, ProviderParam


class OpenAIProvider(BaseProvider):
    async def get_answer(self, param: ProviderParam) -> ProviderAnswer:
        question = self.build_question(prompt=param.prompt, context=param.context)
        openai.api_key = self.api_key
        messages = [{"role": "user", "content": question}]
        try:
            response = await openai.ChatCompletion.acreate(
                model=param.provider_model,
                messages=messages,
                temperature=param.temperature,
            )
            answer = response["choices"][0]["message"]["content"]
        except OpenAIError as err:
            answer = self.get_error_answer(str(err))
        except:
            answer = self.get_error_answer("OpenAI is not available for now. Please try again later.")

        return ProviderAnswer(sample_id=param.sample_id, answer=answer)
