from __future__ import annotations

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import Settings
from app.llm.prompts import SYSTEM_PROMPT, build_user_prompt


class LLMClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.timeout = settings.request_timeout_seconds

    def _endpoint_and_key(self) -> tuple[str, str]:
        if self.settings.llm_provider == "groq":
            return "https://api.groq.com/openai/v1/chat/completions", self.settings.groq_api_key
        return "https://api.openai.com/v1/chat/completions", self.settings.openai_api_key

    @retry(
        reraise=True,
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=1, max=20),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError, RuntimeError)),
    )
    def extract(self, text: str) -> str:
        endpoint, api_key = self._endpoint_and_key()
        payload = {
            "model": self.settings.llm_model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(text)},
            ],
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(endpoint, headers=headers, json=payload)
            if response.status_code == 429:
                raise RuntimeError("Rate limit encountered from LLM provider")
            response.raise_for_status()
            data = response.json()

        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"Unexpected LLM response shape: {data}") from exc
