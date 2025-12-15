from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class PromptParts:
    system: str
    prompt: str


def _sanitize(text: str, max_len: int = 1200) -> str:
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text[:max_len]


def build_reply_prompt(
    *,
    brand_name: str,
    brand_voice: str,
    comment_text: str,
    commenter_name: str | None,
) -> PromptParts:
    safe_comment = _sanitize(comment_text)
    safe_name = _sanitize(commenter_name or "")

    system = (
        f"You are the Social Media Coordinator for '{brand_name}'. "
        f"Brand voice: {brand_voice}\n\n"
        "Rules:\n"
        "- Write ONE short reply (1-3 sentences).\n"
        "- Be polite, natural, and on-brand.\n"
        "- If the comment is a complaint, apologize and ask one clarifying question.\n"
        "- If the comment asks for pricing/availability and you don't know, ask for location or link to DM.\n"
        "- Do NOT mention you are an AI or model.\n"
        "- Do NOT invent facts (hours, prices, policies).\n"
        "- Avoid sensitive/personal data requests.\n"
    )

    prompt = (
        "Write a reply to this Facebook comment.\n\n"
        f"Commenter name: {safe_name or 'Unknown'}\n"
        f"Comment: {safe_comment}\n\n"
        "Reply:" 
    )

    return PromptParts(system=system, prompt=prompt)


def postprocess_reply(text: str, max_chars: int = 700) -> str:
    # Trim, remove surrounding quotes, strip non-visible chars, and ensure max length
    text = text.strip().strip('"').strip("'")
    # Remove control/format characters (can render as "blank" on some clients)
    text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C")
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_chars:
        text = text[: max_chars - 1].rstrip() + "…"
    return text
