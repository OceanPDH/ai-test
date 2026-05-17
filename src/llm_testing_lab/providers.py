from __future__ import annotations

import os
from dataclasses import dataclass

from llm_testing_lab.case_loader import EvaluationCase


class ProviderError(RuntimeError):
    """Raised when a model provider cannot be used."""


@dataclass
class SampleProvider:
    """Return curated answers from each test case so the eval pipeline works offline."""

    def answer(self, case: EvaluationCase) -> str:
        return case.sample_answer


@dataclass
class DeepSeekProvider:
    """Call DeepSeek with an OpenAI-compatible client."""

    model: str = "deepseek-chat"
    api_key_env: str = "DEEPSEEK_API_KEY"

    def __post_init__(self) -> None:
        api_key = os.getenv(self.api_key_env) or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ProviderError(f"Set {self.api_key_env} or OPENAI_API_KEY before using the deepseek provider.")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ProviderError("Install the openai package before using the deepseek provider.") from exc
        self._client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    def answer(self, case: EvaluationCase) -> str:
        prompt = f"""你是一个客服帮助中心助手。只能根据给定文档回答，不要编造文档中没有的信息。

文档:
{case.context}

用户问题:
{case.question}

请用中文简洁回答。"""
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        return response.choices[0].message.content or ""


def get_provider(name: str):
    if name == "sample":
        return SampleProvider()
    if name == "deepseek":
        return DeepSeekProvider()
    raise ProviderError(f"Unknown provider: {name}")
