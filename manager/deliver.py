"""Discord webhook delivery: one message per brief, edits over re-spam,
content-hash idempotency, dry-run prints instead of posting.

Missing webhook URL degrades to stdout with a visible banner — jobs never
crash on delivery config.
"""

from __future__ import annotations

import hashlib
import logging
import os
import time

import requests

log = logging.getLogger("manager")

_EMBED_LIMIT = 4000  # Discord embed description hard cap is 4096


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _embeds(title: str, body: str) -> list[dict]:
    chunks, rest = [], body
    while rest and len(chunks) < 10:
        chunks.append(rest[:_EMBED_LIMIT])
        rest = rest[_EMBED_LIMIT:]
    out = [{"title": title if i == 0 else f"{title} (cont. {i + 1})",
            "description": c, "color": 0x2E8B57} for i, c in enumerate(chunks)]
    if rest:
        out[-1]["description"] += "\n… (truncated)"
    return out or [{"title": title, "description": "(empty)", "color": 0x2E8B57}]


def _request(method: str, url: str, payload: dict) -> requests.Response | None:
    for attempt in (1, 2):
        try:
            resp = requests.request(method, url, json=payload, timeout=15)
            if resp.status_code in (200, 204):
                return resp
            if resp.status_code == 429:
                time.sleep(float(resp.headers.get("Retry-After", "2")))
                continue
            log.error("discord %s -> %s %s", method, resp.status_code, resp.text[:200])
            return None
        except requests.RequestException as e:  # noqa: PERF203
            log.warning("discord attempt %d failed: %s", attempt, e)
            time.sleep(2)
    return None


def deliver(store, brief_key: str, title: str, body: str,
            dry_run: bool = False, webhook: str | None = None) -> str:
    """Returns one of: printed | unchanged | posted | edited | disabled | failed."""
    if dry_run:
        print(f"\n{'=' * 60}\n{title}\n{'=' * 60}\n{body}")
        return "printed"

    h = _hash(title + body)
    msg_id, old_hash = store.message(brief_key)
    if old_hash == h:
        log.info("deliver[%s]: unchanged, skipping", brief_key)
        return "unchanged"

    webhook = webhook or os.environ.get("DISCORD_WEBHOOK_URL", "")
    if not webhook:
        print(f"\n[DELIVERY DISABLED — set DISCORD_WEBHOOK_URL in .env]\n"
              f"{'=' * 60}\n{title}\n{'=' * 60}\n{body}")
        store.save_message(brief_key, None, h)
        return "disabled"

    payload = {"embeds": _embeds(title, body)}
    if msg_id:
        resp = _request("PATCH", f"{webhook}/messages/{msg_id}", payload)
        if resp is not None:
            store.save_message(brief_key, msg_id, h)
            log.info("deliver[%s]: edited message %s", brief_key, msg_id)
            return "edited"
        # edited message may have been deleted — fall through to a fresh post

    resp = _request("POST", f"{webhook}?wait=true", payload)
    if resp is None:
        return "failed"
    new_id = str(resp.json().get("id", "")) if resp.text else ""
    store.save_message(brief_key, new_id or None, h)
    log.info("deliver[%s]: posted message %s", brief_key, new_id)
    return "posted"
