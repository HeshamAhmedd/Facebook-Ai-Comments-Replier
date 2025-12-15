from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Optional

import requests


@dataclass(frozen=True)
class OllamaResult:
    text: str
    raw: dict[str, Any]


class OllamaClient:
    def __init__(self, host: str, model: str, timeout_s: int = 120) -> None:
        self.host = host.rstrip("/")
        self.model = model
        self.timeout_s = timeout_s

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.4,
        top_p: float = 0.9,
        num_predict: int = 220,
    ) -> OllamaResult:
        # Ollama /api/generate supports 'system' and 'prompt'
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "num_predict": num_predict,
            },
        }
        if system:
            payload["system"] = system

        url = f"{self.host}/api/generate"
        r = requests.post(url, json=payload, timeout=self.timeout_s)
        r.raise_for_status()
        data = r.json()
        text = (data.get("response") or "").strip()
        return OllamaResult(text=text, raw=data)
