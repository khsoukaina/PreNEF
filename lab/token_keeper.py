#!/usr/bin/env python3
"""Keep a fresh NEF OAuth2 token in one private file during long campaigns.

Your NRF issues tokens valid ~17 min. This loop re-runs YOUR renewal script
(148_renew_expired_token_using_original.py, the original NRF /oauth2/token
procedure) before expiry, copies the newest access_token into --out (mode 600,
atomic replace) and sleeps until `exp - margin`. NefClient reads the file on
every request when NEF_TOKEN_FILE points to it.

  python3 lab/token_keeper.py --out ~/.prenef/nef_token --approve-lab-http-token-acquisition &
  export NEF_TOKEN_FILE=~/.prenef/nef_token
The token value is never printed.
"""
from __future__ import annotations

import argparse
import base64
import glob
import json
import os
import subprocess
import sys
import time
from pathlib import Path

BASE = Path.home() / "prenef-experiments/prenef-next-stage"
RENEW = BASE / "scripts/148_renew_expired_token_using_original.py"


def newest_token() -> tuple[str, float] | None:
    files = sorted(glob.glob(str(BASE / "**/token.secret.json"), recursive=True), key=os.path.getmtime)
    for f in reversed(files):
        try:
            tok = json.load(open(f))["access_token"]
            pl = tok.split(".")[1]
            pl += "=" * (-len(pl) % 4)
            return tok, float(json.loads(base64.urlsafe_b64decode(pl))["exp"])
        except Exception:  # noqa: BLE001
            continue
    return None


def write_private(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    tmp = path.with_suffix(".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(value)
    os.replace(tmp, path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(Path.home() / ".prenef/nef_token"))
    ap.add_argument("--margin-s", type=float, default=240, help="renew this long before expiry")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--approve-lab-http-token-acquisition", action="store_true")
    a = ap.parse_args()
    if not a.approve_lab_http_token_acquisition:
        print("refusing: runs the NRF token procedure; pass --approve-lab-http-token-acquisition", file=sys.stderr)
        return 2
    out = Path(os.path.expanduser(a.out))
    while True:
        cur = newest_token()
        if not cur or cur[1] - time.time() < a.margin_s:
            p = subprocess.run([sys.executable, str(RENEW), "--approve-lab-http-token-acquisition"],
                               cwd=BASE, capture_output=True, text=True)
            ok = "SUCCEEDED" in p.stdout or "PASS" in p.stdout
            print(time.strftime("%H:%M:%S"), "renewal", "ok" if ok else f"FAILED rc={p.returncode}", flush=True)
            cur = newest_token()
        if not cur or cur[1] <= time.time():
            print(time.strftime("%H:%M:%S"), "no valid token available; retry in 30 s", flush=True)
            time.sleep(30)
            continue
        write_private(out, cur[0])
        left = cur[1] - time.time()
        print(time.strftime("%H:%M:%S"), f"token file updated, valid {left/60:.1f} min", flush=True)
        if a.once:
            return 0
        time.sleep(max(20.0, left - a.margin_s))


if __name__ == "__main__":
    sys.exit(main())
