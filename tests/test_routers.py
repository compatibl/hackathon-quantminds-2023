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

import pytest
from httpx import Client

from hackathon.hackathon_settings import get_settings


def test_get_experiments_ok(client: Client):
    response = client.get("/experiments")
    assert response.is_success


def test_get_experiment_by_name_ok(client: Client):
    experiment_name = "code-test"
    response = client.get(f"/experiment/{experiment_name}")
    assert response.is_success


def test_get_providers_ok(client: Client):
    response = client.get(f"/providers")
    assert response.is_success
    data: list = response.json()
    assert len(data) > 0
    item: dict = data[0]
    assert set(item.keys()) == {"provider_name", "models", "available_params"}
    available_params: list = item["available_params"]
    assert len(available_params) > 0
    available_params_item: dict = available_params[0]
    assert set(available_params_item.keys()) == {"default_value", "param_name"}


run_test_cases = [
    {
        "provider": "openai",
        "experiment_name": "code-test",
        "sample_id": 1,
        "model": "gpt-4",
        "params": {"temperature": 0.2},
        "api_key": "{API_KEY_SHOULD_BE_PLACED_HERE}",
    },
    {
        "provider": "replicate",
        "experiment_name": "code-test",
        "sample_id": 1,
        "model": "llama-v2-7b-chat",
        "params": {"seed": 1, "temperature": 0.2, "top_p": 0.85, "top_k": 70},
        "api_key": "{API_KEY_SHOULD_BE_PLACED_HERE}",
    },
]


@pytest.mark.parametrize(
    argnames="test_case",
    argvalues=run_test_cases,
    ids=[str(item) for item in run_test_cases],
)
def test_run_sample_ok(client: Client, test_case: dict):
    response = client.post(
        url=f"/{test_case['provider']}/run",
        headers={"api-key": test_case["api_key"]},
        json={
            **test_case["params"],
            "sample_id": test_case["sample_id"],
            "experiment_name": test_case["experiment_name"],
            "provider_model": test_case["model"],
            "input": "double param1 = -1;\ndouble param2 = 100000;\ndouble param3 = 0.9;\ndouble param4 = 100.0;\n "
            "\nstd::vector<double> price(const std::vector<double>& underlying) {\n \nstd::vector<double> "
            "payoff(underlying.size());\nfor (size_t i = 0; i < underlying.size(); i++) {\n   payoff[i] = param1 * "
            "param2 * (param4 - underlying[i] > 0 ? 1 : 0) * param3;\n}\n \ndouble average = "
            "std::accumulate(payoff.begin(), payoff.end(), 0.0) / payoff.size();\nreturn average;\n}",
            "prompt": get_settings().default_prompts["PricingModels"],
        },
    )
    assert response.is_success


score_test_cases = [
    {
        "provider": "openai",
        "model": "gpt-4",
        "experiment_name": "code-test",
        "params": {"temperature": 0.2},
        "api_key": "{API_KEY_SHOULD_BE_PLACED_HERE}",
    },
    {
        "provider": "replicate",
        "model": "llama-v2-7b-chat",
        "experiment_name": "code-test",
        "params": {"seed": 1, "temperature": 0.2, "top_p": 0.85, "top_k": 70},
        "api_key": "{API_KEY_SHOULD_BE_PLACED_HERE}",
    },
]


@pytest.mark.parametrize(
    argnames="test_case",
    argvalues=score_test_cases,
    ids=[str(item) for item in score_test_cases],
)
def test_score_experiment_ok(client: Client, test_case: dict):
    response = client.post(
        url=f"/{test_case['provider']}/score",
        headers={"api-key": test_case["api_key"]},
        json={
            **test_case["params"],
            "provider_model": test_case["model"],
            "experiment_name": test_case["experiment_name"],
            "prompt": get_settings().default_prompts["PricingModels"],
        },
    )
    assert response.is_success
