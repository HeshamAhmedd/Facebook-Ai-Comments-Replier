from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional

import requests


@dataclass(frozen=True)
class FacebookComment:
    id: str
    message: str
    from_id: Optional[str]
    from_name: Optional[str]
    created_time: Optional[str]
    post_id: Optional[str]
    permalink_url: Optional[str]


@dataclass(frozen=True)
class FacebookPost:
    id: str
    permalink_url: Optional[str]


class FacebookGraphClient:
    def __init__(self, access_token: str, api_version: str = "v20.0") -> None:
        self.access_token = access_token
        self.base = f"https://graph.facebook.com/{api_version}"

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        params = {**params, "access_token": self.access_token}
        r = requests.get(f"{self.base}/{path.lstrip('/')}", params=params, timeout=30)
        r.raise_for_status()
        return r.json()

    def _post(self, path: str, data: dict[str, Any]) -> dict[str, Any]:
        data = {**data, "access_token": self.access_token}
        r = requests.post(f"{self.base}/{path.lstrip('/')}", data=data, timeout=30)
        r.raise_for_status()
        return r.json()

    def get_recent_posts(self, page_id: str, limit: int = 10) -> list[FacebookPost]:
        data = self._get(
            f"{page_id}/feed",
            {
                "fields": "id,permalink_url",
                "limit": str(limit),
            },
        )
        posts: list[FacebookPost] = []
        for item in data.get("data", []) or []:
            pid = item.get("id")
            if not pid:
                continue
            posts.append(FacebookPost(id=pid, permalink_url=item.get("permalink_url")))
        return posts

    def iter_comments_for_post(
        self,
        post_id: str,
        limit: int = 50,
        include_nested: bool = True,
    ) -> Iterable[FacebookComment]:
        # filter=stream returns most relevant comments in a stream
        params = {
            "fields": "id,message,from,created_time,permalink_url,parent",
            "filter": "stream",
            "order": "chronological",
            "limit": str(limit),
        }
        data = self._get(f"{post_id}/comments", params)
        for item in data.get("data", []) or []:
            msg = (item.get("message") or "").strip()
            if not msg:
                continue
            from_obj = item.get("from") or {}
            from_id = from_obj.get("id")
            from_name = from_obj.get("name")
            parent = item.get("parent") or {}
            parent_id = parent.get("id")

            # Skip nested replies unless requested
            if not include_nested and parent_id:
                continue

            yield FacebookComment(
                id=item.get("id"),
                message=msg,
                from_id=from_id,
                from_name=from_name,
                created_time=item.get("created_time"),
                post_id=post_id,
                permalink_url=item.get("permalink_url"),
            )

    def reply_to_comment(self, comment_id: str, message: str) -> dict[str, Any]:
        # POST /{comment_id}/comments?message=...
        return self._post(f"{comment_id}/comments", {"message": message})

    def get_comment(self, comment_id: str) -> dict[str, Any]:
        return self._get(
            f"{comment_id}",
            {
                "fields": "id,message,from,created_time,permalink_url,is_hidden,is_private,parent",
            },
        )

    def set_comment_hidden(self, comment_id: str, is_hidden: bool) -> dict[str, Any]:
        # POST /{comment_id}?is_hidden=false
        return self._post(f"{comment_id}", {"is_hidden": "true" if is_hidden else "false"})
