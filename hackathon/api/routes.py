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
from functools import partial

import pandas as pd
from fastapi import APIRouter, Depends, status
from fastapi.params import Header

from hackathon.exception import AppException
from hackathon.hackathon_settings import get_settings, Settings
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
    AIExperimentItem,
)
from hackathon.providers.fireworks_provider import run_fireworks
from hackathon.providers.openai_provider import run_openai
from hackathon.providers.replicate_provider import run_replicate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["AI"])

DEFAULT_PROMPTS = {"code": "You will be given the context below in the form of code that is the pricing function of some financial instrument.\nReturn only JSON with keys:\ninstrument_type - enum with values european_option, american_option, digital_option, barrier_option\nbuy_sell - enum with values buy and sell\nput_call - enum with values put and call\ndf - discou\nfactor\nstrike - strike price\nbarrier - barrier price (use this key only for barrier_option)\nCode:\n```\n{context}\n```",
                   "text": "Pay attention and remember information below.\nContext:\n```\n{context}\n```\nAccording to the information in the  context above, fill following fields:\ninstrument_type: string,\ninitial_date: date,\nend_date: date"}


@router.get(path="/experiments", description="Get all available experiments names.")
def get_experiments(settings: Annotated[Settings, Depends(get_settings)]):
    path = Path(settings.data_path, "*.csv")
    experiments = []
    for file in glob.glob(str(path)):
        df_columns = set(pd.read_csv(file).columns) - {'input'}
        experiment_name = Path(file).stem
        default_prompt = DEFAULT_PROMPTS[experiment_name.split('-')[0]]
        default_table = [
            AISampleItem(
                field=col,
                model="",
                correct="",
                score=0.0,
            )
            for col in df_columns
        ]
        experiments.append(
            {"experiment_name": experiment_name,
             "default_prompt": default_prompt,
             "default_table": default_table
             }
        )
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
        inputs = pd.read_csv(file_path, usecols=["input"]).T.values.tolist()[0]
        result = [SampleInputResponse(sample_id=index, value=value) for index, value in enumerate(inputs, start=1)]
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


# Temporary function
def _correct_answer_for_input(input: str):
    experiment_file_path = Path(__file__).parents[2].joinpath(f"data/code-test.csv")
    with open(experiment_file_path, newline="", encoding="utf-8-sig") as csvfile:
        csvreader = csv.DictReader(csvfile)
        for row in csvreader:
            if row['input'] == input:
                return row
    return None


def _extract_sample_data(answer: str, correct_answer) -> tuple[float, list[AISampleItem]]:
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
    except ValueError:  # JSONDecodeError
        return 0.0, [
            AISampleItem(
                field=k,
                model="-",
                correct=v,
                score=0.0,
            )
            for k, v in correct_answer.items()
        ]

    logger.debug(json_answer)

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


def _get_answer(
    ai_provider: AIProvider,
    prompt: str,
    context: str,
    api_key: str,
    seed: Optional[int] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    top_k: Optional[int] = None,
):
    run_func = {
        AIProvider.REPLICATE: partial(
            run_replicate,
            prompt=prompt,
            context=context,
            seed=seed,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            api_key=api_key,
        ),
        AIProvider.FIREWORKS: partial(
            run_fireworks,
            prompt=prompt,
            context=input,
            temperature=temperature,
            top_p=top_p,
            api_key=api_key,
        ),
        AIProvider.OPENAI: partial(
            run_openai,
            prompt=prompt,
            context=input,
            temperature=temperature,
            api_key=api_key,
        ),
    }.get(ai_provider)
    assert run_func, f"There is no implementation for {ai_provider}"
    return run_func()


@router.post(
    path="/{ai_provider}/run",
    description="Run the sample.",
    response_model=AIRunResponse,
)
async def run(ai_provider: AIProvider, body: AIRunBody, api_key: str = Header(default=None)):
    _validate_body_model_params(ai_provider, body)
    _validate_body_model(ai_provider, body)

    # TODO: use provider_model in calculations
    # body.provider_model

    answer = _get_answer(
        ai_provider=ai_provider,
        prompt=body.prompt,
        context=body.input,
        api_key=api_key,
        seed=body.seed,
        temperature=body.temperature,
        top_p=body.top_p,
        top_k=body.top_k,
    )
    logger.debug(answer)

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

    # TODO: use provider_model in calculations
    # body.provider_model

    experiment_file_path = Path(settings.data_path, f"{body.experiment_name}.csv")
    if not experiment_file_path.exists() or not experiment_file_path.is_file():
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Experiment name {body.experiment_name} is invalid.",
        )

    experiment_data: list[AIExperimentItem] = []
    overall_experiment_score: float = 0.0
    with open(experiment_file_path, newline="", encoding="utf-8-sig") as csvfile:
        csvreader = csv.DictReader(csvfile)
        for index, row in enumerate(csvreader, start=1):
            answer = _get_answer(
                ai_provider=ai_provider,
                prompt=body.prompt,
                context=row["input"],
                api_key=api_key,
                seed=body.seed,
                temperature=body.temperature,
                top_p=body.top_p,
                top_k=body.top_k,
            )

            overall_sample_score, sample_data = _extract_sample_data(answer=answer, correct_answer=row)
            item = AIExperimentItem(
                overall_sample_score=round(overall_sample_score, 2),
                sample_id=index + 1,
                output=answer,
                sample_data=sample_data,
            )
            experiment_data.append(item)
            overall_experiment_score += overall_sample_score

    return AIScoreResponse(
        overall_experiment_score=round(overall_experiment_score, 2),
        experiment_data=experiment_data,
    )
