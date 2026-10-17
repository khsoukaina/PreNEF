#!/usr/bin/env python3
"""Impact view of a campaign: per-episode outcomes in units a reader feels.

  python3 bench/impact.py --campaign campaigns/final3 [--speed-kmh 30]

Per (failure episode, affected AF) it classifies the outcome:
  absorbed      0 s in an inadequate mode   (the fallback was in place before the contract broke)
  short         0 < exposure <= 1 s
  unprotected   exposure > 1 s
and converts exposure into distance driven blind at --speed-kmh (shuttle use case).
Writes <campaign>/paper/: figH_outcomes (.pdf/.png), impact.md, impact.csv
"""
from __future__ import annotations

import argparse
import csv
import glob
import os
import sys
from collections import defaultdict

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from bench.analyze import bootstrap_ci  # noqa: E402
from bench.figures import load_contracts  # noqa: E402
from bench.metrics import episodes, load_agent_logs, mode_at, mode_timeline, obs_series  # noqa: E402
from bench.paper_figures import COL1, INK, INK2, save, setup  # noqa: E402
from prenef.common import read_json  # noqa: E402

ARMS = [("direct_nef", "Direct NEF (3GPP)"), ("independent_pred", "Per-AF predictor"),
        ("prenef_noai", "PReNEF (no AI)"), ("prenef_dtip", "PReNEF + DTIP")]
LBL = dict(ARMS)
KINDS = [("shared", "Shared-service failures (sRSU)"), ("ue", "Single-UE failures")]
CLASSES = [("absorbed", "absorbed (0 s)", "#2a78d6"),
           ("short", "short (≤ 1 s)", "#a9c8ee"),
           ("unprotected", "unprotected (> 1 s)", "#e34948")]


def classify(x):
    return "absorbed" if x <= 1e-6 else ("short" if x <= 1.0 else "unprotected")


def run_episodes(run_dir):
    scen_p = os.path.join(run_dir, "scenario.json")
    scen = read_json(scen_p) if os.path.exists(scen_p) else {}
    contracts = load_contracts(run_dir)
    agents = load_agent_logs(run_dir)
    eps = episodes(run_dir, scen.get("service_afs", {}), contracts, scen)
    out, hours = [], 0.0
    for af, recs in agents.items():
        obs = [r for r in recs if r["kind"] == "observation"]
        if not obs:
            continue
        hours += (obs[-1]["wall_s"] - obs[0]["wall_s"]) / 3600.0
        tl = mode_timeline(recs)
        primary = tl[0][1] if tl else None
        series = obs_series(recs)
        fallbacks = [w for w, m, prev, _ in tl if prev == primary and m != primary]
        for e in eps:
            onset = e["onsets"].get(af)
            if af not in e["afs"] or onset is None or mode_at(tl, e["start"]) != primary:
                continue
            exp_s = sum(dt for w, a, dt, _ in series if a == 0 and e["start"] <= w <= e["end"] + 3.0)
            fb = [w for w in fallbacks if e["start"] - 1.0 <= w <= e["end"]]
            out.append({"af": af, "episode": e["episode"], "kind": e["kind"], "exposure_s": exp_s,
                        "anticipated": int(bool(fb) and fb[0] <= onset), "outcome": classify(exp_s)})
    return out, hours


def load(campaign):
    rows, hours = [], defaultdict(float)
    for d in sorted(glob.glob(os.path.join(campaign, "b*-*"))):
        name = os.path.basename(d)
        arm = name.split("-", 1)[1]
        if arm not in LBL or not os.path.exists(os.path.join(d, "journal.jsonl")):
            continue
        m = os.path.join(d, "metrics.json")
        if os.path.exists(m):
            mm = read_json(m)
            if mm.get("audit_ok") is False or (mm.get("meas_coverage_min") or 1) < 0.9:
                continue
        try:
            eps, h = run_episodes(d)
        except (StopIteration, FileNotFoundError, ValueError) as ex:
            print("skip", d, ex)
            continue
        block = int(name[1:3])
        hours[(block, arm)] += h
        rows += [dict(r, block=block, arm=arm) for r in eps]
    return rows, hours


def by_block(rows, arm, kind, fn):
    acc = defaultdict(list)
    for r in rows:
        if r["arm"] == arm and (kind is None or r["kind"] == kind):
            acc[r["block"]].append(r)
    return np.array([fn(v) for v in acc.values()], float)


def ci(v):
    if len(v) == 0:
        return None
    lo, hi = bootstrap_ci(v) if len(v) >= 3 else (v.min(), v.max())
    return float(v.mean()), float(lo), float(hi), len(v)


def fig_outcomes(plt, rows, out):
    fig, axes = plt.subplots(len(KINDS), 1, figsize=(COL1, 2.55), sharex=True, gridspec_kw={"hspace": 0.55})
    for ax, (kind, klabel) in zip(axes, KINDS):
        ax.grid(False)
        for k, (arm, label) in enumerate(ARMS):
            sel = [r for r in rows if r["arm"] == arm and r["kind"] == kind]
            if not sel:
                continue
            y = len(ARMS) - 1 - k
            left = 0.0
            for cls, _, col in CLASSES:
                share = sum(r["outcome"] == cls for r in sel) / len(sel)
                ax.barh(y, share, left=left, color=col, height=0.66, edgecolor="white", linewidth=0.5)
                if share >= 0.09:
                    ax.text(left + share / 2, y, f"{100 * share:.0f}%", ha="center", va="center", fontsize=6.3,
                            color="white" if cls != "short" else INK)
                left += share
            ax.text(1.01, y, f"n={len(sel)}", va="center", fontsize=5.8, color=INK2,
                    transform=ax.get_yaxis_transform())
        ax.set_yticks(range(len(ARMS)))
        ax.set_yticklabels([l for _, l in reversed(ARMS)], fontsize=6.8)
        ax.tick_params(axis="y", length=0)
        ax.set_title(klabel, loc="left", fontsize=7.5, fontweight="bold", pad=3)
        for s in ("left", "bottom"):
            ax.spines[s].set_visible(False)
        ax.set_xlim(0, 1)
    axes[-1].set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    axes[-1].set_xticklabels(["0", "25", "50", "75", "100 %"])
    axes[-1].spines["bottom"].set_visible(True)
    axes[-1].set_xlabel("Share of failure episodes, by time spent in an inadequate mode")
    from matplotlib.patches import Patch
    fig.legend(handles=[Patch(color=c, label=l) for _, l, c in CLASSES], ncol=3, loc="upper center",
               bbox_to_anchor=(0.5, 1.05), handlelength=1.0, columnspacing=0.8, fontsize=6.5)
    save(fig, out, "figH_outcomes")
    plt.close(fig)


def write_md(rows, hours, out, speed):
    v = speed / 3.6
    L = [f"# Impact summary ({len({r['block'] for r in rows})} blocks; mean [95% CI over blocks])", "",
         f"Distance driven blind = exposure x {speed:g} km/h ({v:.1f} m/s). "
         "'Absorbed' = 0 s in an inadequate mode.", ""]
    for kind, klabel in KINDS:
        L += [f"## {klabel}", "",
              "| Arm | episodes | absorbed (%) | anticipated (%) | exposure / episode (s) | blind distance / episode (m) |",
              "|---|---|---|---|---|---|"]
        for arm, label in ARMS:
            n = sum(1 for r in rows if r["arm"] == arm and r["kind"] == kind)
            if n == 0:
                continue
            ab = ci(by_block(rows, arm, kind, lambda e: 100 * np.mean([x["outcome"] == "absorbed" for x in e])))
            an = ci(by_block(rows, arm, kind, lambda e: 100 * np.mean([x["anticipated"] for x in e])))
            ex = ci(by_block(rows, arm, kind, lambda e: np.mean([x["exposure_s"] for x in e])))
            f = lambda c, s=1.0, d=1: f"{c[0] * s:.{d}f} [{c[1] * s:.{d}f}, {c[2] * s:.{d}f}]"  # noqa: E731
            L.append(f"| {label} | {n} | {f(ab, d=0)} | {f(an, d=0)} | {f(ex, d=2)} | {f(ex, v, 1)} |")
        L.append("")
    L += ["## Unsafe time per hour of operation (all episodes, per AF)", "",
          "| Arm | inadequate-mode seconds per AF-hour |", "|---|---|"]
    for arm, label in ARMS:
        per_block = defaultdict(float)
        for r in rows:
            if r["arm"] == arm:
                per_block[r["block"]] += r["exposure_s"]
        vals = np.array([per_block[b] / hours[(b, arm)] for b in per_block if hours.get((b, arm))], float)
        c = ci(vals)
        if c:
            L.append(f"| {label} | {c[0]:.0f} [{c[1]:.0f}, {c[2]:.0f}] s per hour |")
    with open(os.path.join(out, "impact.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign", required=True)
    ap.add_argument("--out", default=None, help="default: <campaign>/paper")
    ap.add_argument("--speed-kmh", type=float, default=30.0, help="shuttle speed used for the blind distance")
    a = ap.parse_args()
    out = a.out or os.path.join(a.campaign, "paper")
    os.makedirs(out, exist_ok=True)
    print("reading run folders (about 1 min)...")
    rows, hours = load(a.campaign)
    if not rows:
        print("no episodes found")
        return 1
    with open(os.path.join(out, "impact.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["block", "arm", "episode", "af", "kind", "exposure_s", "anticipated",
                                           "outcome"])
        w.writeheader()
        w.writerows(rows)
    plt = setup()
    fig_outcomes(plt, rows, out)
    print(write_md(rows, hours, out, a.speed_kmh))
    print("\nwrote", out, ": figH_outcomes.pdf/.png, impact.md, impact.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
