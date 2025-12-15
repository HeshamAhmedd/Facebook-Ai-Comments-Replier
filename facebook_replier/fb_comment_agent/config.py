from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    fb_page_id: str
    fb_access_token: str
    fb_api_version: str = "v20.0"

    ollama_host: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.1"
    ollama_timeout_s: int = 120

    poll_interval_s: int = 30
    lookback_posts: int = 10
    comment_limit_per_post: int = 50

    dry_run: bool = True

    brand_name: str = "Your Page"
    brand_voice: str = "Helpful, friendly, concise."
    max_reply_chars: int = 700


def _get_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def load_settings() -> Settings:
    fb_page_id = os.getenv("FB_PAGE_ID", "").strip()
    fb_access_token = os.getenv("FB_ACCESS_TOKEN", "").strip()
    if not fb_page_id or not fb_access_token:
        raise SystemExit(
            "Missing FB_PAGE_ID or FB_ACCESS_TOKEN in environment. "
            "Set them before running."
        )

    return Settings(
        fb_page_id=fb_page_id,
        fb_access_token=fb_access_token,
        fb_api_version=os.getenv("FB_API_VERSION", "v20.0").strip() or "v20.0",
        ollama_host=os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").strip()
        or "http://127.0.0.1:11434",
        ollama_model=os.getenv("OLLAMA_MODEL", "llama3.1").strip() or "llama3.1",
        ollama_timeout_s=int(os.getenv("OLLAMA_TIMEOUT_S", "120")),
        poll_interval_s=int(os.getenv("POLL_INTERVAL_S", "30")),
        lookback_posts=int(os.getenv("LOOKBACK_POSTS", "10")),
        comment_limit_per_post=int(os.getenv("COMMENT_LIMIT_PER_POST", "50")),
        dry_run=_get_bool("DRY_RUN", True),
        brand_name=os.getenv("BRAND_NAME", "Your Page").strip() or "Your Page",
        brand_voice=os.getenv("BRAND_VOICE", "Helpful, friendly, concise.").strip()
        or "Helpful, friendly, concise.",
        max_reply_chars=int(os.getenv("MAX_REPLY_CHARS", "700")),
    )
