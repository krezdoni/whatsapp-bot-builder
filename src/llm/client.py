"""
Client for the locally-hosted LLM (Med42-70B or Meditron-70B) served via vLLM.
Uses the OpenAI-compatible /v1/chat/completions endpoint — no health data leaves the EU.
"""
from dataclasses import dataclass
from typing import AsyncIterator
import httpx

from src.config import get_settings
from src.llm.prompts import (
    build_system_prompt,
    needs_disclaimer,
    ensure_disclaimer,
    summarise_profile_for_context,
)


@dataclass
class ChatMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


class LLMClient:
    def __init__(self):
        self._settings = get_settings()

    async def chat(
        self,
        user_message: str,
        history: list[ChatMessage] | None = None,
        profile_data: dict | None = None,
        disclaimer_index: int = 0,
    ) -> str:
        profile_summary = summarise_profile_for_context(profile_data) if profile_data else None
        system_prompt = build_system_prompt(profile_summary)

        messages = [{"role": "system", "content": system_prompt}]
        for msg in (history or []):
            messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": user_message})

        response_text = await self._call_llm(messages)

        if needs_disclaimer(response_text):
            response_text = ensure_disclaimer(response_text, disclaimer_index)

        return response_text

    async def _call_llm(self, messages: list[dict]) -> str:
        s = self._settings
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{s.llm_base_url}/chat/completions",
                json={
                    "model": s.llm_model,
                    "messages": messages,
                    "max_tokens": s.llm_max_tokens,
                    "temperature": s.llm_temperature,
                    "stream": False,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def stream_chat(
        self,
        user_message: str,
        history: list[ChatMessage] | None = None,
        profile_data: dict | None = None,
    ) -> AsyncIterator[str]:
        """Streaming variant — yields text chunks as they arrive from vLLM."""
        profile_summary = summarise_profile_for_context(profile_data) if profile_data else None
        system_prompt = build_system_prompt(profile_summary)

        messages = [{"role": "system", "content": system_prompt}]
        for msg in (history or []):
            messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": user_message})

        s = self._settings
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{s.llm_base_url}/chat/completions",
                json={
                    "model": s.llm_model,
                    "messages": messages,
                    "max_tokens": s.llm_max_tokens,
                    "temperature": s.llm_temperature,
                    "stream": True,
                },
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        import json
                        chunk = json.loads(line[6:])
                        delta = chunk["choices"][0]["delta"].get("content", "")
                        if delta:
                            yield delta


_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
