from __future__ import annotations

import re
import time

from dotenv import load_dotenv

from fb_comment_agent.config import load_settings
from fb_comment_agent.facebook_graph import FacebookGraphClient
from fb_comment_agent.ollama_client import OllamaClient
from fb_comment_agent.prompting import build_reply_prompt, postprocess_reply
from fb_comment_agent.state import StateStore


def _redact(s: str) -> str:
    # Prevent leaking tokens in logs (requests exceptions can include full URLs)
    return re.sub(r"access_token=[^&\s]+", "access_token=REDACTED", s)


def main() -> None:
    load_dotenv()
    s = load_settings()

    fb = FacebookGraphClient(access_token=s.fb_access_token, api_version=s.fb_api_version)
    llm = OllamaClient(host=s.ollama_host, model=s.ollama_model, timeout_s=s.ollama_timeout_s)
    state = StateStore()

    print(
        f"Starting FB comment agent | page={s.fb_page_id} | model={s.ollama_model} | dry_run={s.dry_run}"
    )

    while True:
        try:
            posts = fb.get_recent_posts(s.fb_page_id, limit=s.lookback_posts)

            for post in posts:
                for c in fb.iter_comments_for_post(
                    post.id, limit=s.comment_limit_per_post, include_nested=True
                ):
                    if not c.id or state.has_replied(c.id):
                        continue

                    # Don't reply to your own Page comments
                    if c.from_id and c.from_id == s.fb_page_id:
                        continue

                    # Avoid replying to empty/very short comments
                    if len(c.message.strip()) < 2:
                        continue

                    parts = build_reply_prompt(
                        brand_name=s.brand_name,
                        brand_voice=s.brand_voice,
                        comment_text=c.message,
                        commenter_name=c.from_name,
                    )

                    res = llm.generate(
                        prompt=parts.prompt,
                        system=parts.system,
                        temperature=0.4,
                        top_p=0.9,
                        num_predict=220,
                    )
                    reply = postprocess_reply(res.text, max_chars=s.max_reply_chars)

                    if not reply:
                        continue

                    if s.dry_run:
                        print("---")
                        print(f"[DRY_RUN] Would reply to comment {c.id}")
                        if c.permalink_url:
                            print(f"Permalink: {c.permalink_url}")
                        print(f"Comment: {c.message}")
                        print(f"Reply: {reply}")
                        state.mark_replied(c.id, reply, c.post_id)
                        continue

                    resp = fb.reply_to_comment(c.id, reply)
                    reply_id = resp.get("id")
                    if reply_id:
                        stored = fb.get_comment(reply_id)
                        stored_msg = (stored.get("message") or "").strip()
                        stored_hidden = stored.get("is_hidden")
                        stored_private = stored.get("is_private")
                        if not stored_msg:
                            print(
                                f"Warning: reply {reply_id} has empty message after post (comment {c.id})"
                            )
                        if stored_hidden is True:
                            # If the reply was created hidden, unhide it so normal users can see it.
                            fb.set_comment_hidden(reply_id, False)
                            stored2 = fb.get_comment(reply_id)
                            print(
                                f"Warning: reply {reply_id} was hidden; attempted unhide. is_hidden={stored2.get('is_hidden')}"
                            )
                        if stored_private is True:
                            print(
                                f"Warning: reply {reply_id} is marked private by API (comment {c.id}). Normal users may not see it."
                            )
                    state.mark_replied(c.id, reply, c.post_id)
                    print(f"Replied to comment {c.id}")

        except Exception as e:
            print(f"Loop error: {_redact(str(e))}")

        time.sleep(s.poll_interval_s)


if __name__ == "__main__":
    main()
