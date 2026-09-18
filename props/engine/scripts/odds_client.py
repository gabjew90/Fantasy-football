#!/usr/bin/env python3
"""The Odds API v4 client for nfl-prop-research.

Stages: events (free), markets (1 request), odds (1 request per market).
Never prints the API key. Caches responses under ./cache. Writes line-archive
rows (JSONL) with --archive. Optionally pushes archive rows to a GitHub repo
when GITHUB_TOKEN and LINE_ARCHIVE_REPO are set.

Credential lookup: ODDS_API_PROXY_BASE_URL, then ODDS_API_KEY env var, then
--key, then --key-file (default: the bundled resources/credential.env).

Usage:
  python odds_client.py events [--home "Buffalo Bills" --away "Detroit Lions"]
  python odds_client.py markets EVENT_ID
  python odds_client.py odds EVENT_ID [--markets m1,m2] [--books draftkings,fanduel]
                        [--archive] [--snapshot opening|decision|closing|interim]
                        [--season 2026 --week 2]
"""
import argparse
import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SPORT = "americanfootball_nfl"
DIRECT_BASE = f"https://api.the-odds-api.com/v4/sports/{SPORT}"
ALLOWLIST = [
    "spreads", "totals", "player_pass_yds", "player_pass_tds",
    "player_rush_yds", "player_reception_yds", "player_receptions",
    "player_anytime_td",
]
DEFAULT_BOOKS = "draftkings,fanduel"
CACHE = Path("cache")
QUOTA_HEADERS = ("x-requests-remaining", "x-requests-used", "x-requests-last")


def now_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def redact(text, key):
    if not key:
        return text
    return text.replace(key, "<REDACTED>")


def load_credential(args):
    proxy = os.environ.get("ODDS_API_PROXY_BASE_URL")
    if proxy:
        return {"mode": "proxy", "base": proxy.rstrip("/"), "key": None}
    key = os.environ.get("ODDS_API_KEY")
    if not key and args.key:
        key = args.key
    key_file = args.key_file or str(Path(__file__).resolve().parent.parent / "resources" / "credential.env")
    if not key and Path(key_file).exists():
        txt = Path(key_file).read_text()
        m = re.search(r"ODDS_API_KEY\s*=\s*([A-Za-z0-9]+)", txt)
        key = m.group(1) if m else None
    if not key:
        return None
    return {"mode": "odds_api", "base": DIRECT_BASE, "key": key}


def build_url(cred, stage, event_id=None, params=None):
    params = dict(params or {})
    if cred["mode"] == "proxy":
        if stage == "events":
            path = "/events"
        elif stage == "markets":
            path = "/markets"
            params["eventId"] = event_id
        else:
            path = "/odds"
            params["eventId"] = event_id
    else:
        params["apiKey"] = cred["key"]
        if stage == "events":
            path = "/events"
        elif stage == "markets":
            path = f"/events/{event_id}/markets"
        else:
            path = f"/events/{event_id}/odds"
    return cred["base"] + path + "?" + urllib.parse.urlencode(params)


def get(url, key, timeout=30):
    """Return (status, headers dict, body text). Raises on non-HTTP failures."""
    req = urllib.request.Request(url, headers={"User-Agent": "nfl-prop-research/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, {k.lower(): v for k, v in r.headers.items()}, r.read().decode()
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        return e.code, {k.lower(): v for k, v in e.headers.items()}, redact(body, key)


def classify(status, headers, body):
    if status == 200:
        return "OK"
    if status in (401, 403):
        return "AUTH_FAILURE"
    if status == 429 or headers.get("x-requests-remaining") == "0":
        return "QUOTA_EXHAUSTED"
    if headers.get("x-deny-reason"):
        return "NETWORK_ENVIRONMENT_BLOCKED"
    if status == 404:
        return "ASSET_NOT_FOUND"
    return f"HTTP_ERROR_{status}"


def quota(headers):
    return {h: headers.get(h) for h in QUOTA_HEADERS}


def cache_write(name, payload):
    CACHE.mkdir(exist_ok=True)
    (CACHE / name).write_text(json.dumps(payload, indent=1))


def run_stage(cred, stage, event_id=None, params=None, cache_name=None):
    url = build_url(cred, stage, event_id, params)
    status, headers, body = get(url, cred["key"])
    cls = classify(status, headers, body)
    rec = {
        "stage": stage, "retrieved_at_utc": now_utc(), "status": status,
        "class": cls, "quota": quota(headers),
        "endpoint": redact(url, cred["key"]).replace("apiKey=<REDACTED>", "apiKey=<omitted>"),
        "params": {k: v for k, v in (params or {}).items()},
    }
    if cls == "OK":
        try:
            rec["data"] = json.loads(body)
        except json.JSONDecodeError:
            rec["class"] = "SCHEMA_MISMATCH"
            rec["body_head"] = body[:300]
    else:
        rec["body_head"] = body[:300]
    if cache_name:
        cache_write(cache_name, rec)
    return rec


def archive_rows(rec, snapshot, season, week, source):
    d = rec["data"]
    q = rec["quota"]
    rows = []
    for b in d.get("bookmakers", []):
        for m in b.get("markets", []):
            for o in m.get("outcomes", []):
                rows.append({
                    "retrieved_at_utc": rec["retrieved_at_utc"],
                    "snapshot_type": snapshot,
                    "season": season, "week": week,
                    "event_id": d["id"], "commence_time": d["commence_time"],
                    "home_team": d["home_team"], "away_team": d["away_team"],
                    "bookmaker": b["key"], "market": m["key"],
                    "player": o.get("description"), "outcome": o.get("name"),
                    "point": o.get("point"), "price_american": o.get("price"),
                    "last_update": m.get("last_update"),
                    "requests_remaining": q["x-requests-remaining"],
                    "requests_used": q["x-requests-used"],
                    "requests_last": q["x-requests-last"],
                    "source": source,
                })
    return rows


def append_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    seen = set()
    if path.exists():
        for line in path.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                seen.add(dedupe_key(r))
    new = [r for r in rows if dedupe_key(r) not in seen]
    with path.open("a") as f:
        for r in new:
            f.write(json.dumps(r) + "\n")
    return len(new)


def dedupe_key(r):
    return (r["event_id"], r["bookmaker"], r["market"], r["player"],
            r["outcome"], r["point"], r["last_update"])


def github_append(rows, repo, token, path_in_repo):
    """Append rows to a JSONL file in a GitHub repo via the Contents API."""
    api = f"https://api.github.com/repos/{repo}/contents/{path_in_repo}"
    hdr = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
           "User-Agent": "nfl-prop-research/1.0"}
    existing, sha = "", None
    req = urllib.request.Request(api, headers=hdr)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            meta = json.loads(r.read().decode())
            existing = base64.b64decode(meta["content"]).decode()
            sha = meta["sha"]
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise
    seen = {dedupe_key(json.loads(l)) for l in existing.splitlines() if l.strip()}
    new = [r for r in rows if dedupe_key(r) not in seen]
    if not new:
        return 0
    content = existing + ("" if existing.endswith("\n") or not existing else "\n")
    content += "".join(json.dumps(r) + "\n" for r in new)
    body = {"message": f"archive {len(new)} rows {now_utc()}",
            "content": base64.b64encode(content.encode()).decode()}
    if sha:
        body["sha"] = sha
    req = urllib.request.Request(api, data=json.dumps(body).encode(), headers=hdr, method="PUT")
    with urllib.request.urlopen(req, timeout=30) as r:
        r.read()
    return len(new)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["events", "markets", "odds"])
    ap.add_argument("event_id", nargs="?")
    ap.add_argument("--home"); ap.add_argument("--away")
    ap.add_argument("--markets", default=",".join(ALLOWLIST))
    ap.add_argument("--books", default=DEFAULT_BOOKS)
    ap.add_argument("--archive", action="store_true")
    ap.add_argument("--snapshot", default="interim",
                    choices=["opening", "decision", "closing", "interim"])
    ap.add_argument("--season", type=int); ap.add_argument("--week", type=int)
    ap.add_argument("--archive-file")
    ap.add_argument("--key-file"); ap.add_argument("--key")
    args = ap.parse_args()

    cred = load_credential(args)
    if not cred:
        print("N/A — AUTHENTICATED ODDS ACCESS UNAVAILABLE (no proxy, env key, key file, or --key)")
        sys.exit(2)

    if args.stage == "events":
        rec = None
        max_age = float(os.environ.get("ODDS_REUSE_CACHE_MAX_AGE", "0") or 0)
        ef = CACHE / "events.json"
        if max_age > 0 and ef.exists():
            try:
                r_ = json.loads(ef.read_text())
                if r_.get("class") == "OK" and time.time() - ef.stat().st_mtime <= max_age:
                    rec = r_; rec["reused_cache"] = ef.name
                    print("NOTE: reusing cached events.json; no request spent", file=sys.stderr)
            except Exception:
                rec = None
        if rec is None:
            rec = run_stage(cred, "events", cache_name="events.json")
        out = {k: rec[k] for k in ("stage", "retrieved_at_utc", "status", "class", "quota")}
        if rec["class"] == "OK":
            ev = rec["data"]
            out["events_returned"] = len(ev)
            if args.home or args.away:
                ev = [e for e in ev if (not args.home or e["home_team"] == args.home)
                      and (not args.away or e["away_team"] == args.away)]
            out["events"] = [{k: e[k] for k in ("id", "commence_time", "away_team", "home_team")}
                             for e in ev]
        print(json.dumps(out, indent=1))
        sys.exit(0 if rec["class"] == "OK" else 1)

    if not args.event_id:
        sys.exit("event_id required")

    if args.stage == "markets":
        rec = run_stage(cred, "markets", args.event_id, {"regions": "us"},
                        cache_name=f"markets_{args.event_id}.json")
        out = {k: rec[k] for k in ("stage", "retrieved_at_utc", "status", "class", "quota")}
        if rec["class"] == "OK":
            allow = set(ALLOWLIST)
            out["bookmakers"] = {
                b["key"]: {"n_markets": len(b["markets"]),
                           "allowlisted_present": sorted(allow & {m["key"] for m in b["markets"]})}
                for b in rec["data"].get("bookmakers", [])}
        else:
            out["body_head"] = rec.get("body_head")
        print(json.dumps(out, indent=1))
        sys.exit(0 if rec["class"] == "OK" else 1)

    # odds
    mk = [m.strip() for m in args.markets.split(",") if m.strip()]
    off = [m for m in mk if m not in ALLOWLIST]
    if off:
        print(f"WARNING: markets outside allowlist requested: {off}", file=sys.stderr)
    params = {"regions": "us", "markets": ",".join(mk), "oddsFormat": "american",
              "bookmakers": args.books}
    # Quota guard: ODDS_REUSE_CACHE_MAX_AGE=<seconds> reuses the newest successful
    # cached quote for this event if it is younger than that, instead of spending a
    # request. Off by default; a reused quote is labelled as such in the output.
    rec = None
    max_age = float(os.environ.get("ODDS_REUSE_CACHE_MAX_AGE", "0") or 0)
    if max_age > 0:
        for f in sorted(CACHE.glob(f"odds_{args.event_id}_*.json"), reverse=True):
            try:
                r_ = json.loads(f.read_text())
            except Exception:
                continue
            if r_.get("class") == "OK" and set(mk) <= {m["key"] for b in r_["data"]["bookmakers"] for m in b["markets"]}:
                age = time.time() - int(f.stem.rsplit("_", 1)[1])
                if age <= max_age:
                    rec = r_; rec["reused_cache"] = f.name; rec["cache_age_s"] = int(age)
                    print(f"NOTE: reusing cached quote {f.name} ({int(age)} s old); no request spent", file=sys.stderr)
                    break
    if rec is None:
        rec = run_stage(cred, "odds", args.event_id, params,
                        cache_name=f"odds_{args.event_id}_{int(time.time())}.json")
    out = {k: rec[k] for k in ("stage", "retrieved_at_utc", "status", "class", "quota")}
    for k in ("reused_cache", "cache_age_s"):
        if k in rec: out[k] = rec[k]
    if rec["class"] != "OK":
        out["body_head"] = rec.get("body_head")
        print(json.dumps(out, indent=1))
        sys.exit(1)
    d = rec["data"]
    out["event"] = {k: d[k] for k in ("id", "commence_time", "away_team", "home_team")}
    out["markets"] = {b["key"]: {m["key"]: {"n": len(m["outcomes"]), "last_update": m["last_update"]}
                                 for m in b["markets"]} for b in d.get("bookmakers", [])}
    if args.archive:
        season = args.season or int(d["commence_time"][:4])
        rows = archive_rows(rec, args.snapshot, season, args.week, cred["mode"])
        path = Path(args.archive_file or f"/mnt/user-data/outputs/line_archive_nfl_{season}.jsonl")
        n_local = append_jsonl(path, rows)
        out["archive"] = {"rows": len(rows), "new_local": n_local, "file": str(path)}
        token, repo = os.environ.get("GITHUB_TOKEN"), os.environ.get("LINE_ARCHIVE_REPO")
        if token and repo:
            try:
                n = github_append(rows, repo, token, f"line_archive_nfl_{season}.jsonl")
                out["archive"]["github"] = {"repo": repo, "new_rows": n}
            except Exception as e:  # noqa: BLE001
                out["archive"]["github"] = {"repo": repo, "error": redact(str(e), token)}
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
