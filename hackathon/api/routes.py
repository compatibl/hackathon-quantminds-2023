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
import logging
from pathlib import Path
from typing import Annotated, Optional

import pandas as pd
from fastapi import APIRouter, Depends, status
from fastapi.params import Header

from hackathon.exception import AppException
from hackathon.hackathon_settings import Settings, get_settings
from hackathon.models.ai_models import (
    AIBaseBody,
    AIExperimentInfoItem,
    AIExperimentItem,
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
from hackathon.providers.base_provider import ProviderParam
from hackathon.providers.manager import get_provider

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["AI"])


@router.get(
    path="/experiments",
    description="Get all available experiments names.",
    response_model=list[AIExperimentInfoItem],
)
def get_experiments(settings: Annotated[Settings, Depends(get_settings)]):
    path = Path(settings.data_path, "*.csv")
    experiments = []
    for file in glob.glob(str(path)):
        df_columns = set(pd.read_csv(file).columns) - {'input'}
        experiment_name = Path(file).stem
        default_prompt = settings.default_prompts[experiment_name.split('-')[0]]
        default_table = [
            AISampleItem(
                field=col,
                model="",
                correct="",
                score=0.0,
            )
            for col in df_columns
        ]
        info_item = AIExperimentInfoItem(
            experiment_name=experiment_name,
            default_prompt=default_prompt,
            default_table=default_table,
        )
        experiments.append(info_item)
    return experiments


@router.get(
    path="/experiment/{experiment_name}",
    description="Get sample inputs of the experiment.",
)
def get_experiment_inputs(
    experiment_name: str, settings: Annotated[Settings, Depends(get_settings)]
) -> list[SampleInputResponse]:
    file_path = Path(settings.data_path, f"{experiment_name}.csv")
    try:
        inputs = pd.read_csv(file_path, usecols=["Input"]).T.values.tolist()[0]
        result = [SampleInputResponse(index=index, value=value) for index, value in enumerate(inputs, start=1)]
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
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"For {provider.value} provider the next field should be specified: {param.value}",
            )
    return True


def _validate_body_model(provider: AIProvider, body: AIBaseBody) -> bool:
    if body.provider_model not in provider.models:
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Model {body.provider_model} is not supported by {provider} provider.",
        )
    return True


def _correct_answer_for_sample(experiment_name: str, sample_id: int):
    experiment_file_path = Path(__file__).parents[2].joinpath(f"data/{experiment_name}.csv")
    if not experiment_name.endswith("Custom"):
        correct_answer = pd.read_csv(experiment_file_path, header=0).iloc[sample_id - 1]
    else:
        correct_answer = pd.read_csv(experiment_file_path, header=0).iloc[0]
    return correct_answer


def _extract_sample_data(answer: str, correct_answer) -> tuple[float, list[AISampleItem]]:

    del correct_answer["Input"]

    opening_brace = answer.find("{")
    closing_brace = answer.find("}")

    if opening_brace != -1 and closing_brace != -1:
        json_only = answer[opening_brace: closing_brace + 1]

    else:
        return 0.0, [
            AISampleItem(
                field=k,
                model="-",
                correct=str(v),
                score=0.0,
            )
            for k, v in correct_answer.items()
        ]

    # TODO: Make this stage softer
    try:
        json_answer = json.loads(json_only)
    except ValueError:  # JSONDecodeError
        return 0.0, [
            AISampleItem(
                field=k,
                model="-",
                correct=str(v),
                score=0.0,
            )
            for k, v in correct_answer.items()
        ]

    logger.debug(json_answer)

    sample_items = []
    total_score = 0.0

    if 'InstrumentType' in json_answer.keys() and correct_answer['InstrumentType'] == json_answer['InstrumentType']:
        item_score = round(1 / len(json_answer.keys()), 2)
        sample_items.append(
            AISampleItem(
                field='InstrumentType',
                model=json_answer[
                    'InstrumentType'] if 'InstrumentType' in json_answer.keys() else "Not found in response",
                correct=correct_answer['InstrumentType'],
                score=item_score,
            )
        )
        total_score += item_score
        for key in set(correct_answer.keys()) - {'InstrumentType'}:
            model_value = str(json_answer.get(key, '-'))
            correct_value = str(correct_answer[key])
            # TODO: softer
            score = item_score if model_value == correct_value else 0.0
            total_score += score
            sample_items.append(AISampleItem(field=key, model=model_value, correct=correct_value, score=score))

        return total_score, sample_items
    else:
        item_score = 0
        sample_items.append(
            AISampleItem(
                field='InstrumentType',
                model=json_answer[
                    'InstrumentType'] if 'InstrumentType' in json_answer.keys() else "Not found in response",
                correct=correct_answer['InstrumentType'] + " (no score - mismatch)",
                score=item_score,
            )
        )
        for key in set(correct_answer.keys()) - {'InstrumentType'}:
            model_value = str(json_answer.get(key, '-'))
            correct_value = str(correct_answer[key]) + " (no score - instrument type mismatch)"
            # TODO: softer
            sample_items.append(AISampleItem(field=key, model=model_value, correct=correct_value, score=0))

        total_score = 0
        return total_score, sample_items


@router.post(
    path="/{ai_provider}/run",
    description="Run the sample.",
    response_model=AIRunResponse,
)
async def run(ai_provider: AIProvider, body: AIRunBody, api_key: str = Header(default=None)):
    _validate_body_model_params(ai_provider, body)
    _validate_body_model(ai_provider, body)

    param = ProviderParam(
        sample_id=body.sample_id,
        provider_model=body.provider_model,
        prompt=body.prompt,
        context=body.input,
        seed=body.seed,
        temperature=body.temperature,
        top_p=body.top_p,
        top_k=body.top_k,
    )
    provider_answers = await get_provider(ai_provider, api_key).run([param])
    answer = provider_answers[0].answer if provider_answers else ""

    correct_answer = _correct_answer_for_sample(experiment_name=body.experiment_name, sample_id=body.sample_id)
    overall_sample_score, sample_data = _extract_sample_data(answer=answer, correct_answer=correct_answer)

    return AIRunResponse(
        overall_sample_score=round(overall_sample_score, 2),
        output=answer,
        sample_data=sample_data,
    )


@router.post(
    path="/{ai_provider}/score",
    description="Score all samples of the experiment.",
    response_model=AIScoreResponse,
)
async def score(
    ai_provider: AIProvider,
    body: AIScoreBody,
    settings: Annotated[Settings, Depends(get_settings)],
    api_key: Annotated[Optional[str], Header()] = None,
):
    _validate_body_model_params(ai_provider, body)
    _validate_body_model(ai_provider, body)

    experiment_file_path = Path(settings.data_path, f"{body.experiment_name}.csv")
    if not experiment_file_path.exists() or not experiment_file_path.is_file():
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Experiment name {body.experiment_name} is invalid.",
        )

    provider = get_provider(ai_provider, api_key)
    experiment_data: list[AIExperimentItem] = []
    overall_experiment_score: float = 0.0
    provider_params = list()
    with open(experiment_file_path, newline="", encoding="utf-8-sig") as csvfile:
        csvreader = csv.DictReader(csvfile)
        for index, row in enumerate(csvreader, start=1):
            param = ProviderParam(
                sample_id=index,
                provider_model=body.provider_model,
                prompt=body.prompt,
                context=row["Input"],
                seed=body.seed,
                temperature=body.temperature,
                top_p=body.top_p,
                top_k=body.top_k,
            )
            provider_params.append(param)

    provider_answers = await provider.run(provider_params)
    provider_answers_dict = {p_answer.sample_id: p_answer for p_answer in provider_answers}

    with open(experiment_file_path, newline="", encoding="utf-8-sig") as csvfile:
        csvreader = csv.DictReader(csvfile)
        for index, row in enumerate(csvreader, start=1):
            provider_answer = provider_answers_dict.get(index)
            if provider_answer is None:
                continue

            overall_sample_score, sample_data = _extract_sample_data(answer=provider_answer.answer, correct_answer=row)
            item = AIExperimentItem(
                overall_sample_score=round(overall_sample_score, 2),
                sample_id=provider_answer.sample_id,
                output=provider_answer.answer,
                sample_data=sample_data,
            )
            experiment_data.append(item)
            overall_experiment_score += overall_sample_score

    return AIScoreResponse(
        overall_experiment_score=round(overall_experiment_score, 2),
        experiment_data=experiment_data,
    )
