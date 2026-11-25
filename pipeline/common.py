"""Shared helpers: .env loading, runs.jsonl logging, retries.
Nothing here talks to a model by itself."""
from __future__ import annotations

import json
import os
import random
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent


def _load_env() -> None:
    """Read KEY=VALUE lines from .env (never committed) without overriding real env vars."""
    p = ROOT / ".env"
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_env()

OUT = Path(os.environ.get("HERITAGE_OUT", ROOT / "outputs"))
RUNS = Path(os.environ.get("HERITAGE_RUNS", ROOT / "runs.jsonl"))


def log_call(**fields) -> None:
    """Append one line to runs.jsonl. Never put keys or tokens in `fields`."""
    rec = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), **fields}
    RUNS.parent.mkdir(parents=True, exist_ok=True)
    with RUNS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def redact(text: str) -> str:
    """Remove any secret that appears in an error message before it is logged."""
    for name in ("GEMINI_API_KEY", "CF_API_TOKEN", "CF_ACCOUNT_ID"):
        secret = os.environ.get(name)
        if secret:
            text = text.replace(secret, "<redacted>")
    return text


RETRYABLE_HTTP = {429, 500, 502, 503, 504}


def call_with_retries(stage: str, model: str, params: dict, fn, seed=None, attempts: int = 3, base_delay: float = 2.0):
    """Run fn(). Log every attempt to runs.jsonl. Retry rate limits, server errors and timeouts
    with exponential backoff. Other errors are logged and raised at once."""
    for attempt in range(1, attempts + 1):
        t0 = time.time()
        retry, err = False, ""
        try:
            result = fn()
            log_call(stage=stage, model=model, params=params, seed=seed, latency_s=round(time.time() - t0, 3),
                     cost_usd=0.0, status="ok", attempt=attempt)
            return result
        except requests.HTTPError as e:
            code = e.response.status_code if e.response is not None else None
            body = redact(e.response.text[:300]) if e.response is not None else ""
            retry, err = code in RETRYABLE_HTTP, f"HTTP {code}: {body}"
        except (requests.ConnectionError, requests.Timeout) as e:
            retry, err = True, type(e).__name__
        except Exception as e:  # parsing problems, missing fields: not worth retrying
            err = redact(f"{type(e).__name__}: {e}")
        log_call(stage=stage, model=model, params=params, seed=seed, latency_s=round(time.time() - t0, 3),
                 cost_usd=0.0, status="error", error=err, attempt=attempt)
        if not retry or attempt == attempts:
            raise RuntimeError(f"{stage} ({model}) failed after {attempt} attempt(s): {err}")
        time.sleep(base_delay * 2 ** (attempt - 1) + random.random())
