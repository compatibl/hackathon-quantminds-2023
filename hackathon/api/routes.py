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

import glob
import json
import re
from pathlib import Path
from typing import Annotated, Any, Final, Optional, List

import dateutil
import numpy as np
import pandas as pd
from dateutil.parser import parse
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

INSTRUMENT_TYPE_FIELD: Final[str] = "InstrumentType"
PLACE_HOLDER: Final[str] = "None"
INPUT_FIELD: Final[str] = "Input"
DATE_FIELD_END_WITH: Final[str] = "Date"
ADDITIONAL_FIELDS: Final[list[str]] = ["ID"]
NONE_FIELDS: Final[List[str]] = ["None", "Null", "NaN", "Empty", "Unknown", "Undefined", "Not Defined", "Unspecified", "Not Specified"]

router = APIRouter(prefix="", tags=["AI"])

normalize_string_regex = re.compile(r"[\s\-_d]+")


@router.get(
    path="/experiments",
    description="Get all available experiments names.",
    response_model=list[AIExperimentInfoItem],
)
def get_experiments(settings: Annotated[Settings, Depends(get_settings)]):
    path = Path(settings.data_path, "*.csv")
    experiments = []
    for file in glob.glob(str(path)):
        df_columns = set(pd.read_csv(file).columns) - {INPUT_FIELD} - set(ADDITIONAL_FIELDS)
        experiment_name = Path(file).stem
        stream_name = experiment_name.split('-')[0]
        prompt_file_path = Path(settings.prompts_path, stream_name + ".txt")
        with open(prompt_file_path, 'r') as prompt_file:
            default_prompt = prompt_file.read()
        default_table = [
            AISampleItem(
                field=col,
                model="",
                correct="",
                score="0%",
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
        inputs = pd.read_csv(file_path, usecols=[INPUT_FIELD]).T.values.tolist()[0]
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
        correct_answer = pd.read_csv(experiment_file_path, header=0).fillna('None').iloc[sample_id - 1]
    else:
        correct_answer = pd.read_csv(experiment_file_path, header=0).fillna('None').iloc[0]
    return correct_answer


def compare_as_strings(model_value: Any, correct_value: Any) -> bool:
    try:
        model_value = str(model_value).strip().lower()
        correct_value = str(correct_value).strip().lower()
        model_value = normalize_string_regex.sub("", model_value)
        correct_value = normalize_string_regex.sub("", correct_value)
        return model_value == correct_value
    except:
        return False


def compare_as_dates(model_value: Any, correct_value: Any) -> bool:
    try:
        model_value = str(model_value)
        correct_value = str(correct_value)
        return dateutil.parser.parse(model_value) == dateutil.parser.parse(correct_value)
    except:
        return compare_as_strings(model_value=model_value, correct_value=correct_value)


def compare_as_booleans(model_value: Any, correct_value: Any) -> bool:
    try:
        model_value = bool(model_value)
        correct_value = bool(correct_value)
        return model_value == correct_value
    except:
        return compare_as_strings(model_value=model_value, correct_value=correct_value)


def compare_as_floats(model_value: Any, correct_value: Any) -> bool:
    try:
        model_value = round(float(model_value), 5)
        correct_value = round(float(correct_value), 5)
        return model_value == correct_value
    except:
        return compare_as_strings(model_value=model_value, correct_value=correct_value)


def compare_as_integers(model_value: Any, correct_value: Any) -> bool:
    try:
        model_value = int(model_value)
        correct_value = int(correct_value)
        return model_value == correct_value
    except:
        return compare_as_strings(model_value=model_value, correct_value=correct_value)


def compare_as_nan(model_value: Any, correct_value: Any) -> bool:
    return is_nan(model_value) and is_nan(correct_value)


def is_nan(value: Any):
    # Looks for basic NaN values and then proceed with specific ones
    return pd.isna(value) or (isinstance(value, str) and value in NONE_FIELDS)


def soft_comparison(model_value: Any, correct_value: Any) -> bool:
    if is_nan(correct_value) or is_nan(model_value):
        return compare_as_nan(model_value=model_value, correct_value=correct_value)
    if pd.api.types.is_integer(correct_value):
        return compare_as_integers(model_value=model_value, correct_value=correct_value)
    elif pd.api.types.is_float(correct_value):
        return compare_as_floats(model_value=model_value, correct_value=correct_value)
    elif pd.api.types.is_bool(correct_value):
        return compare_as_booleans(model_value=model_value, correct_value=correct_value)
    else:
        return compare_as_strings(model_value=model_value, correct_value=correct_value)


def _extract_sample_data(answer: str, correct_answer) -> tuple[float, list[AISampleItem]]:
    correct_answer = {key: correct_answer[key] for key in correct_answer.keys()
                      if key not in ADDITIONAL_FIELDS and key != INPUT_FIELD}

    empty_samples = list()
    for key, value in correct_answer.items():
        empty_samples.append(AISampleItem(field=key, model=PLACE_HOLDER, correct=str(value), score="0%"))
    empty_result = (0.0, empty_samples)

    opening_brace = answer.find("{")
    closing_brace = answer.find("}")

    if opening_brace != -1 and closing_brace != -1:
        json_only = answer[opening_brace: closing_brace + 1]
    else:
        return empty_result

    # TODO: Make this stage softer
    try:
        json_answer = json.loads(json_only)
    except ValueError:  # JSONDecodeError
        malformed_json_samples = list()
        for key, value in correct_answer.items():
            malformed_json_samples.append(AISampleItem(field=key, model="Malformed JSON", correct=str(value), score="No score - malformed JSON"))
        malformed_json_result = (0.0, malformed_json_samples)
        return malformed_json_result

    sample_items = []
    total_score = 0.0

    if (
        INSTRUMENT_TYPE_FIELD in json_answer.keys()
        and compare_as_strings(
            model_value=json_answer[INSTRUMENT_TYPE_FIELD],
            correct_value=correct_answer[INSTRUMENT_TYPE_FIELD],
        )
    ):
        max_item_score = 1 / len(correct_answer.keys())
        sample_items.append(
            AISampleItem(
                field=INSTRUMENT_TYPE_FIELD,
                model=str(json_answer[INSTRUMENT_TYPE_FIELD])
                    if INSTRUMENT_TYPE_FIELD in json_answer.keys()
                    else "Not found in response",
                correct=str(correct_answer[INSTRUMENT_TYPE_FIELD]),
                score=str(round(100 * max_item_score, 2)) + "%"
            )
        )
        total_score += max_item_score
        for key in set(correct_answer.keys()) - {INSTRUMENT_TYPE_FIELD}:
            model_value = json_answer.get(key)
            correct_value = correct_answer[key]

            if key.endswith(DATE_FIELD_END_WITH):
                are_values_equal = compare_as_dates(model_value=model_value, correct_value=correct_value)
            else:
                are_values_equal = soft_comparison(model_value=model_value, correct_value=correct_value)

            score = max_item_score if are_values_equal else 0.0
            total_score += score
            sample_items.append(
                AISampleItem(
                    field=key,
                    model=str(model_value) if model_value is not None else PLACE_HOLDER,
                    correct=str(correct_value),
                    score=str(round(100 * score, 2)) + "%",
                )
            )

        total_score *= 100
        return total_score, sample_items
    else:
        sample_items.append(
            AISampleItem(
                field=INSTRUMENT_TYPE_FIELD,
                model=str(json_answer[INSTRUMENT_TYPE_FIELD])
                    if INSTRUMENT_TYPE_FIELD in json_answer.keys()
                    else "Not found in response",
                correct=str(correct_answer[INSTRUMENT_TYPE_FIELD]),
                score="No score - mismatch",
            )
        )
        for key in set(correct_answer.keys()) - {INSTRUMENT_TYPE_FIELD}:
            model_value = json_answer.get(key)
            correct_value = correct_answer[key]
            # TODO: softer
            sample_items.append(
                AISampleItem(
                    field=key,
                    model=str(model_value) if model_value is not None else PLACE_HOLDER,
                    correct=str(correct_value),
                    score="Instrument type mismatch",
                )
            )
        total_score *= 100
        return total_score, sample_items


@router.post(
    path="/{ai_provider}/run",
    description="Run the sample.",
    response_model=AIRunResponse,
)
async def provider_run(ai_provider: AIProvider, body: AIRunBody, api_key: str = Header(default=None)):
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

    from dataclasses import dataclass, asdict
    # import json
    # with open(f'C:/dev/hackathon-quantminds-2023/tmp/tmp.txt', 'w') as f:
    #     json.dump(param.dict(), f)
    # # param = ProviderParam(**param.dict())
    # from dacite import from_dict
    # param = from_dict(data_class=ProviderParam, data=param.dict())
    provider = get_provider(ai_provider, api_key)
    question = provider.build_question(prompt=param.prompt, context=param.context)
    provider_answers = await get_provider(ai_provider, api_key).run([param])
    answer = provider_answers[0].answer if provider_answers else ""

    param = ProviderParam(
        sample_id=body.sample_id,
        provider_model=body.provider_model,
        prompt=None,
        context=None,
        seed=body.seed,
        temperature=body.temperature,
        top_p=body.top_p,
        top_k=body.top_k,
        # question=(f"I am about to ask a question. Before responding, can you please start by repeating for me this current prompt, before giving your answer to the question, as I cannot see my own prompt easily.\n"
        #           f"My question is: given the following QUESTION, and the following ANSWER that you gave,"
        #           f"can you please explain to me how you came to the ANSWER. "
        #           f"\n"
        #           f"QUESTION: {question}\n"
        #           f"ANSWER: {answer}"),
        question="When you answer, please begin by repeating the content of this prompt in full, from the next line.\n\n"
                 "Below I will refer to a question I asked you as 'QUESTION', and an answer you gave as 'ANSWER'. Can you please explain the answer you gave for each key.\n"
                 "Please repeat the full JSON from 'ANSWER' in your current answer, or if there is no JSON in 'ANSWER', say so.\n\n"
                 f"QUESTION: {question}\n\n"
                 f"ANSWER: {answer}"
    )

    # param = ProviderParam(
    #     sample_id=body.sample_id,
    #     provider_model=body.provider_model,
    #     prompt=None,
    #     context=None,
    #     seed=body.seed,
    #     temperature=body.temperature,
    #     top_p=body.top_p,
    #     top_k=body.top_k,
    #     # question=(f"I am about to ask a question. Before responding, can you please start by repeating for me this current prompt, before giving your answer to the question, as I cannot see my own prompt easily.\n"
    #     #           f"My question is: given the following QUESTION, and the following ANSWER that you gave,"
    #     #           f"can you please explain to me how you came to the ANSWER. "
    #     #           f"\n"
    #     #           f"QUESTION: {question}\n"
    #     #           f"ANSWER: {answer}"),
    #     question="When you answer, please begin by repeating the content of this prompt in full, from the next line.\n\n"
    #              "Please check that the following JSON is consistent with the following term sheet and make any modifications that are required to the JSON values (not keys) to make it consistent.\n"
    #              "Please output only the JSON, modified if necessary:\n"
    #              #"Please repeat the full JSON from 'ANSWER' in your current answer, or if there is no JSON in 'ANSWER', say so.\n\n"
    #              f"JSON: {answer}\n\n"
    #              f"TERM SHEET: {body.input}"
    # )

    provider_answers = await get_provider(ai_provider, api_key).run([param])
    answer = provider_answers[0].answer if provider_answers else ""

    correct_answer = _correct_answer_for_sample(experiment_name=body.experiment_name, sample_id=body.sample_id)
    overall_sample_score, sample_data = _extract_sample_data(answer=answer, correct_answer=correct_answer)

    return AIRunResponse(
        overall_sample_score=str(round(overall_sample_score, 2)) + "%",
        output=answer,
        sample_data=sample_data,
    )


@router.post(
    path="/{ai_provider}/score",
    description="Score all samples of the experiment.",
    response_model=AIScoreResponse,
)
async def provider_score(
    ai_provider: AIProvider,
    body: AIScoreBody,
    settings: Annotated[Settings, Depends(get_settings)],
    api_key: Annotated[Optional[str], Header()] = None,
):
    _validate_body_model(ai_provider, body)

    experiment_file_path = Path(settings.data_path, f"{body.experiment_name}.csv")
    if not experiment_file_path.exists() or not experiment_file_path.is_file():
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Experiment name {body.experiment_name} is invalid.",
        )

    provider_params = list()
    for index, row in pd.read_csv(experiment_file_path, header=0).iterrows():
        param = ProviderParam(
            sample_id=int(index) + 1,
            provider_model=body.provider_model,
            prompt=body.prompt,
            context=row[INPUT_FIELD],
            seed=body.seed,
            temperature=body.temperature,
            top_p=body.top_p,
            top_k=body.top_k,
        )
        provider_params.append(param)

    provider_answers = await get_provider(ai_provider, api_key).run(provider_params)
    provider_answers_dict = {p_answer.sample_id: p_answer for p_answer in provider_answers}

    experiment_data: list[AIExperimentItem] = []
    overall_experiment_score: float = 0.0
    sample_count = 0.0
    for index, row in pd.read_csv(experiment_file_path, header=0).fillna('None').iterrows():
        provider_answer = provider_answers_dict.get(int(index) + 1)
        if provider_answer is None:
            continue

        overall_sample_score, sample_data = _extract_sample_data(answer=provider_answer.answer, correct_answer=row)
        item = AIExperimentItem(
            overall_sample_score=str(round(overall_sample_score, 2)) + "%",
            sample_id=provider_answer.sample_id,
            output=provider_answer.answer,
            sample_data=sample_data,
        )
        experiment_data.append(item)
        sample_count += 1
        overall_experiment_score += overall_sample_score

    average_experiment_score = overall_experiment_score / sample_count

    return AIScoreResponse(
        overall_experiment_score=str(round(average_experiment_score, 2)) + "%",
        experiment_data=experiment_data,
    )
