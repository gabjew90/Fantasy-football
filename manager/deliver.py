"""Delivery: GitHub Issues (primary, zero secrets) or Gmail SMTP (fallback).

Inside Actions, github-actions[bot] opens an issue titled with the alert
subject and @mentions the owner — GitHub's own notification system turns
that into email + GitHub-app push, no SMTP anywhere. Updates to the same
event are comments on the same issue (one thread). SMTP_* env vars still
work when no GITHUB_TOKEN is present.

Subject-line convention IS the interface: time-critical alerts start with
[ACT NOW] and carry the instruction + minutes-to-lock in the subject itself,
so the lock screen alone is decision-sufficient; weekly briefs start with
[BRIEF]. One email per event; updates to the same event reply into the
thread (In-Reply-To) rather than starting a new one. Content-hash
idempotency: re-running an unchanged job sends nothing.

Missing SMTP secrets degrade to stdout with a visible banner — jobs never
crash on delivery config. --dry-run prints instead of sending.
"""

from __future__ import annotations

import hashlib
import logging
import os
import smtplib
import time
from email.message import EmailMessage
from email.utils import make_msgid
from html import escape

import requests

log = logging.getLogger("manager")

SMTP_HOST, SMTP_PORT = "smtp.gmail.com", 465


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _md_html(body: str) -> str:
    """Tiny markdown-ish -> phone-readable HTML (headers, bold, bullets)."""
    out = []
    for raw in body.splitlines():
        line = escape(raw)
        while "**" in line:
            line = line.replace("**", "<b>", 1).replace("**", "</b>", 1)
        if line.startswith("# "):
            out.append(f"<h2>{line[2:]}</h2>")
        elif line.startswith("## "):
            out.append(f"<h3>{line[3:]}</h3>")
        elif line.startswith("- "):
            out.append(f"<li>{line[2:]}</li>")
        elif not line.strip():
            out.append("<br>")
        else:
            out.append(f"<p>{line}</p>")
    return ("<html><body style='font-family:-apple-system,Segoe UI,sans-serif;"
            "font-size:15px;line-height:1.45'>" + "\n".join(out) + "</body></html>")


def deliver(store, brief_key: str, subject: str, body: str,
            dry_run: bool = False, act_now: bool = False) -> str:
    """Returns: printed | unchanged | sent | updated | disabled | failed."""
    prefix = "[ACT NOW] " if act_now else "[BRIEF] "
    full_subject = prefix + subject

    if dry_run:
        print(f"\n{'=' * 60}\nSUBJECT: {full_subject}\n{'=' * 60}\n{body}")
        return "printed"

    h = _hash(full_subject + body)
    prev_id, old_hash = store.message(brief_key)
    if old_hash == h:
        log.info("deliver[%s]: unchanged, skipping", brief_key)
        return "unchanged"

    token = os.environ.get("GITHUB_TOKEN", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if token and repo:
        result = _github_issue(store, brief_key, full_subject, body, prev_id,
                               token, repo)
        if result != "failed":
            store.save_message(brief_key, store.message(brief_key)[0], h)
        return result

    user = os.environ.get("SMTP_USER", "")
    pw = os.environ.get("SMTP_APP_PASSWORD", "")
    to = os.environ.get("ALERT_EMAIL_TO", "")
    if not (user and pw and to):
        print(f"\n[DELIVERY DISABLED — no GITHUB_TOKEN (issue delivery) and "
              f"no SMTP_* vars]\nSUBJECT: {full_subject}\n{'=' * 60}\n{body}")
        store.save_message(brief_key, None, h)
        return "disabled"

    msg = EmailMessage()
    msg["Subject"] = full_subject
    msg["From"] = user
    msg["To"] = to
    msg_id = make_msgid()
    msg["Message-ID"] = msg_id
    if prev_id:  # update the same event's thread, don't re-spam
        msg["In-Reply-To"] = prev_id
        msg["References"] = prev_id
    msg.set_content(body)
    msg.add_alternative(_md_html(body), subtype="html")

    for attempt in (1, 2):
        try:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30) as s:
                s.login(user, pw)
                s.send_message(msg)
            store.save_message(brief_key, msg_id, h)
            state = "updated" if prev_id else "sent"
            log.info("deliver[%s]: %s (%s)", brief_key, state, full_subject)
            return state
        except Exception as e:  # noqa: BLE001, PERF203
            log.warning("smtp attempt %d failed: %s", attempt, e)
            time.sleep(3)
    return "failed"


def _github_issue(store, brief_key: str, title: str, body: str,
                  prev_id: str | None, token: str, repo: str) -> str:
    """Create (or comment on) the event's issue; the @mention makes GitHub
    notify the owner — email + app push, no SMTP anywhere."""
    mention = os.environ.get("MENTION", "@" + repo.split("/")[0])
    headers = {"Authorization": f"Bearer {token}",
               "Accept": "application/vnd.github+json"}
    api = f"https://api.github.com/repos/{repo}"
    payload = f"{mention}\n\n{body}"
    try:
        if prev_id:  # update = a comment on the same issue -> one thread
            r = requests.post(f"{api}/issues/{prev_id}/comments",
                              headers=headers, timeout=20,
                              json={"body": f"**UPDATE — {title}**\n\n{payload}"})
            r.raise_for_status()
            log.info("deliver[%s]: commented on issue #%s", brief_key, prev_id)
            return "updated"
        r = requests.post(f"{api}/issues", headers=headers, timeout=20,
                          json={"title": title, "body": payload})
        r.raise_for_status()
        num = str(r.json().get("number"))
        store.save_message(brief_key, num, "pending")
        log.info("deliver[%s]: opened issue #%s (%s)", brief_key, num, title)
        return "sent"
    except requests.RequestException as e:
        log.error("github issue delivery failed: %s", e)
        return "failed"
