"""Shared utilities: durable JSON, hash-chained audit journal, clocks.

Stdlib only. Python >= 3.10.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Iterable, Iterator


def now_wall() -> float:
    return time.time()


def now_mono() -> float:
    return time.monotonic()


def new_correlation_id(prefix: str = "pn") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:16]}"


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def durable_json(path: str | Path, value: Any) -> None:
    """Atomic write: tmp file + fsync + rename."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp-{os.getpid()}")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(value, f, indent=2, sort_keys=True, default=str)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def read_jsonl(path: str | Path, strict: bool = False) -> Iterator[dict]:
    with open(path, "r", encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                if strict:
                    raise ValueError(f"{path}:{n}: invalid JSON line")


def _canonical(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode()


class AuditJournal:
    """Append-only, hash-chained JSONL journal (Table 2, block I).

    Each record carries `seq`, `prev_hash` and `hash` so that any later
    modification or deletion of a line is detectable by `verify_chain`.
    Thread-safe within one process. One journal per run.
    """

    GENESIS = "0" * 64

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._seq = 0
        self._prev = self.GENESIS
        if self.path.exists():
            for rec in read_jsonl(self.path):
                self._seq = rec.get("seq", self._seq)
                self._prev = rec.get("hash", self._prev)

    def append(self, kind: str, **fields: Any) -> dict:
        with self._lock:
            self._seq += 1
            rec = {
                "seq": self._seq,
                "kind": kind,
                "wall_s": now_wall(),
                "mono_s": now_mono(),
                **fields,
                "prev_hash": self._prev,
            }
            rec["hash"] = hashlib.sha256(_canonical(rec)).hexdigest()
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, sort_keys=True, default=str) + "\n")
                f.flush()
                os.fsync(f.fileno())
            self._prev = rec["hash"]
            return rec


def verify_chain(path: str | Path) -> tuple[bool, str]:
    prev = AuditJournal.GENESIS
    expected_seq = 0
    for rec in read_jsonl(path, strict=True):
        expected_seq += 1
        if rec.get("seq") != expected_seq:
            return False, f"sequence gap at seq={rec.get('seq')} (expected {expected_seq})"
        if rec.get("prev_hash") != prev:
            return False, f"broken link at seq={rec['seq']}"
        body = {k: v for k, v in rec.items() if k != "hash"}
        if hashlib.sha256(_canonical(body)).hexdigest() != rec.get("hash"):
            return False, f"hash mismatch at seq={rec['seq']}"
        prev = rec["hash"]
    return True, f"ok ({expected_seq} records)"


def percentile(values: Iterable[float], q: float) -> float | None:
    vals = sorted(v for v in values if v is not None)
    if not vals:
        return None
    if len(vals) == 1:
        return vals[0]
    pos = (len(vals) - 1) * q
    lo, hi = int(pos), min(int(pos) + 1, len(vals) - 1)
    return vals[lo] + (vals[hi] - vals[lo]) * (pos - lo)
