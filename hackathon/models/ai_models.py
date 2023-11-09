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

import enum
from typing import Optional, Union

from pydantic import BaseModel, Field


class AIModelParam(str, enum.Enum):
    def __new__(cls, name: str, default_value: Union[int, float]):
        obj = str.__new__(cls, name)
        obj._value_ = name
        obj.default_value = default_value
        return obj

    SEED = "seed", 1
    TEMP = "temperature", 0.2
    TOP_P = "top_p", 0.85
    TOP_K = "top_k", 70


class AIModel(str, enum.Enum):
    LLAMA_V2_70B_CHAT = "llama-v2-70b-chat"
    LLAMA_V2_7B_CHAT = "llama-v2-7b-chat"
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    GPT_4 = "gpt-4"


class AIProvider(str, enum.Enum):
    def __new__(
        cls, name: str, models: list[str], available_params: list[AIModelParam]
    ):
        obj = str.__new__(cls, name)
        obj._value_ = name
        obj.models = models
        obj.available_params = available_params
        return obj

    REPLICATE = (
        "replicate",
        [AIModel.LLAMA_V2_70B_CHAT, AIModel.LLAMA_V2_7B_CHAT],
        [AIModelParam.SEED, AIModelParam.TEMP, AIModelParam.TOP_P, AIModelParam.TOP_K],
    )
    OPENAI = (
        "openai",
        [AIModel.GPT_3_5_TURBO, AIModel.GPT_4],
        [AIModelParam.TEMP],
    )
    FIREWORKS = (
        "fireworks",
        [AIModel.LLAMA_V2_70B_CHAT, AIModel.LLAMA_V2_7B_CHAT],
        [AIModelParam.TEMP, AIModelParam.TOP_P],
    )


class AIBaseBody(BaseModel):
    provider_model: str = Field(description="Provider model.")
    seed: Optional[int] = Field(
        default=None,
        description="Model seed (use the same seed to reproduce the answer).",
    )
    temperature: Optional[float] = Field(
        default=None,
        description="Model temperature (lower is deterministic, higher more creative).",
    )
    top_p: Optional[float] = Field(
        default=None,
        description="Cumulative probability of tokens to sample from.",
    )
    top_k: Optional[int] = Field(
        default=None,
        description="Num tokens to sample from.",
    )


class AIRunBody(AIBaseBody):
    experiment_name: str = Field(description="Experiment name.")
    sample_id: Optional[int] = Field(default=None, description="Sample Id.")
    input: str = Field(description="AI request input")
    prompt: Optional[str] = Field(default=None, description="AI request prompt.")


class AIScoreBody(AIBaseBody):
    experiment_name: str = Field(description="Experiment name.")
    prompt: str = Field(description="AI request prompt.")


class AISampleItem(BaseModel):
    field: str
    model: str
    correct: str
    score: float


class AIExperimentItem(BaseModel):
    overall_sample_score: float
    sample_id: int
    output: str
    sample_data: list[AISampleItem]


class AIScoreResponse(BaseModel):
    overall_experiment_score: float
    experiment_data: list[AIExperimentItem]


class SampleInputResponse(BaseModel):
    index: int = Field(description="Sample Id.")
    value: str = Field(description="Value.")


class AIRunResponse(BaseModel):
    overall_sample_score: float
    output: str = Field(description="AI response.")
    sample_data: list[AISampleItem]


class AIModelParamItem(BaseModel):
    param_name: AIModelParam
    default_value: Union[int, float]


class AIProviderResponseItem(BaseModel):
    provider_name: str
    models: list[AIModel]
    available_params: list[AIModelParamItem]


class AIExperimentInfoItem(BaseModel):
    experiment_name: str
    default_prompt: str
    default_table: list[AISampleItem]
