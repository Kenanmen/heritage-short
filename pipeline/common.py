"""Shared helpers: .env loading, runs.jsonl logging, retries.
Nothing here talks to a model by itself."""
from __future__ import annotations

import hashlib
import json
import os
import random
import re
import time
import wave
from datetime import datetime, timezone
from pathlib import Path

import requests
from jsonschema import Draft202012Validator

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
STORYBOARD = Path(os.environ.get("HERITAGE_STORYBOARD", ROOT / "storyboard.json"))
SCHEMA = ROOT / "schema" / "storyboard.schema.json"


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
        retry, err, wait = False, "", None
        try:
            result = fn()
            log_call(stage=stage, model=model, params=params, seed=seed, latency_s=round(time.time() - t0, 3),
                     cost_usd=0.0, status="ok", attempt=attempt)
            return result
        except requests.HTTPError as e:
            code = e.response.status_code if e.response is not None else None
            full = redact(e.response.text) if e.response is not None else ""
            body = full[:300]
            retry, err = code in RETRYABLE_HTTP, f"HTTP {code}: {body}"
            m = re.search(r'retryDelay"?\s*:\s*"(\d+(?:\.\d+)?)s', full)  # Google says how long to wait
            if m:
                wait = min(float(m.group(1)) + 1, 90.0)
        except (requests.ConnectionError, requests.Timeout) as e:
            retry, err = True, type(e).__name__
        except Exception as e:  # parsing problems, missing fields: not worth retrying
            err = redact(f"{type(e).__name__}: {e}")
        log_call(stage=stage, model=model, params=params, seed=seed, latency_s=round(time.time() - t0, 3),
                 cost_usd=0.0, status="error", error=err, attempt=attempt)
        if not retry or attempt == attempts:
            raise RuntimeError(f"{stage} ({model}) failed after {attempt} attempt(s): {err}")
        time.sleep(wait if wait is not None else base_delay * 2 ** (attempt - 1) + random.random())


# --------------------------------------------------------------------------- storyboard
def nominal_total(sb: dict) -> float:
    return sum(s["duration_s"] for s in sb["shots"]) + sb["end_card"]["duration_s"]


def validation_errors(sb: dict) -> list[str]:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    errs = []
    for e in sorted(Draft202012Validator(schema).iter_errors(sb), key=lambda e: [str(p) for p in e.absolute_path]):
        where = "/".join(str(p) for p in e.absolute_path) or "<root>"
        errs.append(f"{where}: {e.message}")
    if errs:
        return errs
    ids = [s["id"] for s in sb["shots"]]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        errs.append(f"duplicate shot ids: {dup}")
    for s in sb["shots"]:
        n = s["narration"]
        if n and n["speaker"] not in sb["voices"]:
            errs.append(f"{s['id']}: speaker '{n['speaker']}' has no entry in voices")
    for c in sb["music"]["cues"]:
        for ref in (c["from_shot"], c["to_shot"]):
            if ref not in ids:
                errs.append(f"music cue '{c['id']}' refers to unknown shot {ref}")
    total = nominal_total(sb)
    if not 60 <= total <= 90:
        errs.append(f"nominal total {total:.1f}s (shots + end card) is outside the 60-90 s target")
    return errs


def load_storyboard() -> dict:
    sb = json.loads(STORYBOARD.read_text(encoding="utf-8"))
    errs = validation_errors(sb)
    if errs:
        raise SystemExit("storyboard.json is invalid:\n - " + "\n - ".join(errs))
    return sb


# --------------------------------------------------------------------------- cache
def input_hash(obj) -> str:
    """Stable hash of a stage's inputs. If it matches the stored hash, the output is reused."""
    blob = json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16]


def meta_path(p: Path) -> Path:
    return p.with_name(p.name + ".meta.json")


def is_fresh(p: Path, h: str) -> bool:
    m = meta_path(p)
    if not (p.exists() and m.exists()):
        return False
    try:
        return json.loads(m.read_text(encoding="utf-8"))["input_hash"] == h
    except (ValueError, KeyError):
        return False


def write_meta(p: Path, h: str, **extra) -> None:
    meta_path(p).write_text(json.dumps({"input_hash": h, **extra}, indent=2, ensure_ascii=False), encoding="utf-8")


# --------------------------------------------------------------------------- timing
def wav_seconds(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / float(w.getframerate())


def save_audio(path, data: bytes, sample_rate: int = 24000) -> None:
    """Save what the TTS API returned. Gemini returns a complete WAV file (RIFF header, audio, and a
    C2PA content-credentials chunk after the audio). Keep it exactly as sent. Wrapping it in a second
    WAV header made the header and the C2PA chunk play as noise (the glitch in the first clips).
    If the reply is raw 16-bit mono PCM instead, wrap it in a WAV header."""
    path = Path(path)
    if data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        path.write_bytes(data)
        return
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(data)


def repair_wrapped_wav(path) -> bool:
    """Undo the double wrapping from the early version of the pipeline: an outer 44-byte WAV header
    around a complete inner WAV file. Returns True if the file was repaired. Safe to run again."""
    path = Path(path)
    b = path.read_bytes()
    if len(b) > 56 and b[:4] == b"RIFF" and b[44:48] == b"RIFF" and b[52:56] == b"WAVE":
        path.write_bytes(b[44:])
        return True
    return False


def narration_lengths() -> dict:
    p = OUT / "narration" / "timing.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def effective_duration(shot: dict, lengths: dict) -> float:
    """Storyboard duration is a floor: if the narration does not fit, the shot gets longer."""
    d = float(shot["duration_s"])
    n, length = shot["narration"], lengths.get(shot["id"])
    if n and length:
        d = max(d, n.get("delay_s", 0.5) + length + 0.4)
    return d
