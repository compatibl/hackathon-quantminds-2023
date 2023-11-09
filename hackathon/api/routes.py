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

import csv
import glob
import json
from pathlib import Path
from typing import Annotated, Tuple

import pandas as pd
from fastapi import APIRouter, Depends
from fastapi.params import Header
from starlette import status

from hackathon.exception import AppException
from hackathon.hackathon_settings import get_settings
from hackathon.models.ai_models import (
    AIBaseBody,
    AIModelParamItem,
    AIProvider,
    AIProviderResponseItem,
    AIRunBody,
    AIRunResponse,
    AISampleItem,
    AIScoreBody,
    AIScoreResponse,
    SampleInputResponse,
)
from hackathon.providers.fireworks_provider import run_fireworks
from hackathon.providers.openai_provider import run_openai
from hackathon.providers.replicate_provider import run_replicate

router = APIRouter(prefix="", tags=["AI"])


@router.get(path="/experiments", description="Get all available experiments names.")
def get_experiments(settings: Annotated[dict, Depends(get_settings)]) -> list[str]:
    path = Path(settings.data_path, "*.csv")
    return [Path(file).stem for file in glob.glob(str(path))]


@router.get(
    path="/experiment/{experiment_name}",
    description="Get sample inputs of the experiment.",
)
def get_experiment_inputs(
    experiment_name: str, settings: Annotated[dict, Depends(get_settings)]
) -> list[SampleInputResponse]:
    file_path = Path(settings.data_path, f"{experiment_name}.csv")
    try:
        inputs = pd.read_csv(file_path, usecols=["input"]).T.values.tolist()[0]
        result = [SampleInputResponse(index=index + 1, value=value) for index, value in enumerate(inputs)]
    except FileNotFoundError:
        raise AppException(status.HTTP_400_BAD_REQUEST, f"Experiment {experiment_name} not exists.")
    except pd.errors.EmptyDataError:
        return []
    except ValueError:
        raise AppException(
            status.HTTP_400_BAD_REQUEST,
            f"File {str(file_path)} has incorrect structure.",
        )
    return result


@router.get(
    path="/providers",
    description="Get supported AI providers.",
    response_model=list[AIProviderResponseItem],
)
async def get_ai_providers():
    response_providers = list()
    for provider in AIProvider:
        available_params = list()
        for param in provider.available_params:
            param_item = AIModelParamItem(param_name=param.value, default_value=param.default_value)
            available_params.append(param_item)
        provider_item = AIProviderResponseItem(
            provider_name=provider.value,
            models=provider.models,
            available_params=available_params,
        )
        response_providers.append(provider_item)
    return response_providers


def _validate_body_model_params(provider: AIProvider, body: AIBaseBody) -> bool:
    for param in provider.available_params:
        if getattr(body, param.value, None) is None:
            raise AppException(
                422,
                f"For {provider.value} provider the next field should be specified: {param.value}",
            )
    return True


def _validate_body_model(provider: AIProvider, body: AIBaseBody) -> bool:
    if body.provider_model not in provider.models:
        raise AppException(422, "Invalid provider model.")
    return True


# Temporary function
def _correct_answer_for_input(input: str):
    experiment_file_path = Path(__file__).parents[2].joinpath(f"data/experiment_test.csv")
    with open(experiment_file_path, newline="", encoding="utf-8-sig") as csvfile:
        csvreader = csv.DictReader(csvfile)
        for row in csvreader:
            if row['input'] == input:
                return row
    return None


def _extract_sample_data(answer: str, correct_answer) -> Tuple[float, list[AISampleItem]]:
    # TODO: Improve logic
    if correct_answer is None:
        return 0.0, []

    del correct_answer["input"]

    opening_brace = answer.find("{")
    closing_brace = answer.find("}")

    if opening_brace != -1 and closing_brace != -1:
        json_only = answer[opening_brace : closing_brace + 1]

    else:
        return 0.0, [
            AISampleItem(
                field=k,
                model="-",
                correct=v,
                score=0.0,
            )
            for k, v in correct_answer.items()
        ]

    # TODO: Make this stage softer
    try:
        json_answer = json.loads(json_only)
    except Exception as err:  # JSONDecodeError
        return 0.0, [
            AISampleItem(
                field=k,
                model="-",
                correct=v,
                score=0.0,
            )
            for k, v in correct_answer.items()
        ]

    print(json_answer)

    item_score = 1 / len(json_answer.keys())
    sample_items = []
    total_score = 0.0
    if 'instrument_type' in json_answer.keys() and correct_answer['instrument_type'] == json_answer['instrument_type']:
        sample_items.append(
            AISampleItem(
                field='instrument_type',
                model=json_answer['instrument_type'],
                correct=correct_answer['instrument_type'],
                score=item_score,
            )
        )
        for key in set(correct_answer.keys()) - {'instrument_type'}:
            model_value = str(json_answer.get(key, '-'))
            correct_value = correct_answer[key]
            # TODO: softer
            score = item_score if model_value == correct_value else 0.0
            total_score += score
            sample_items.append(AISampleItem(field=key, model=model_value, correct=correct_value, score=score))

        return total_score, sample_items

    return 0.0, [
        AISampleItem(
            field=k,
            model=str(json_answer.get(k, '-')),
            correct=v,
            score=0.0,
        )
        for k, v in correct_answer.items()
    ]


@router.post(
    path="/{ai_provider}/run",
    description="Run the sample.",
    response_model=AIRunResponse,
)
async def run(ai_provider: AIProvider, body: AIRunBody, api_key: str = Header(default=None)):
    _validate_body_model_params(ai_provider, body)
    _validate_body_model(ai_provider, body)

    # TODO: use provider_model in calculations
    body.provider_model

    if ai_provider == AIProvider.REPLICATE:
        answer = run_replicate(
            prompt=body.prompt,
            context=body.input,
            seed=body.seed,
            temperature=body.temperature,
            top_p=body.top_p,
            top_k=body.top_k,
            api_key=api_key,
        )
    elif ai_provider == AIProvider.FIREWORKS:
        answer = run_fireworks(
            prompt=body.prompt,
            context=body.input,
            temperature=body.temperature,
            top_p=body.top_p,
            api_key=api_key,
        )
    elif ai_provider == AIProvider.OPENAI:
        answer = run_openai(
            prompt=body.prompt,
            context=body.input,
            temperature=body.temperature,
            api_key=api_key,
        )
    else:
        raise AppException(500, "Unsupported AI provider.")
    print(answer)

    # TODO: Temporary solution until we don't have the experiment name and sample number (only works because we only have one test file)
    correct_answer = _correct_answer_for_input(body.input)

    overall_sample_score, sample_data = _extract_sample_data(answer=answer, correct_answer=correct_answer)

    return AIRunResponse(
        overall_sample_score=overall_sample_score,
        output=answer,
        sample_data=sample_data,
    )


@router.post(
    path="/{ai_provider}/score",
    description="Score all samples of the experiment.",
    # response_model=AIScoreResponse,
)
async def score(ai_provider: AIProvider, body: AIScoreBody, api_key: str = Header(default=None)):
    _validate_body_model_params(ai_provider, body)
    _validate_body_model(ai_provider, body)

    prompt = body.prompt
    seed = body.seed
    temperature = body.temperature
    top_p = body.top_p
    top_k = body.top_k

    provider_model = body.provider_model

    experiment_file_path = Path(__file__).parents[2].joinpath(f"data/{body.experiment_name.lower()}.csv")
    if not experiment_file_path.exists() or not experiment_file_path.is_file():
        raise AppException(422, "Invalid experiment name.")

    experiment_data = []
    overall_experiment_score = 0.0
    with open(experiment_file_path, newline="", encoding="utf-8-sig") as csvfile:
        csvreader = csv.DictReader(csvfile)
        for index, row in enumerate(csvreader):
            context = row["input"]
            if ai_provider == AIProvider.REPLICATE:
                answer = run_replicate(
                    prompt=prompt,
                    context=context,
                    seed=seed,
                    temperature=temperature,
                    top_p=top_p,
                    top_k=top_k,
                    api_key=api_key,
                )
            elif ai_provider == AIProvider.FIREWORKS:
                answer = run_fireworks(
                    prompt=prompt,
                    context=context,
                    api_key=api_key,
                    temperature=temperature,
                    top_p=top_p,
                )
            elif ai_provider == AIProvider.OPENAI:
                answer = run_openai(
                    prompt=prompt,
                    context=context,
                    temperature=temperature,
                    api_key=api_key,
                )
            else:
                raise AppException(500, "Unsupported AI provider.")

            overall_sample_score, sample_data = _extract_sample_data(answer=answer, correct_answer=row)
            experiment_data.append(
                {
                    "overall_sample_score": overall_sample_score,
                    "sample_id": index + 1,
                    "output": answer,
                    "sample_data": sample_data,
                }
            )
            overall_experiment_score += overall_sample_score

    # TODO create model in the format below
    return {"overall_experiment_score": overall_experiment_score, "experiment_data": experiment_data}
