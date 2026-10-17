#!/usr/bin/env python3
"""Network QoS (latency, loss, reachability, throughput) per scenario phase, per UE and per arm.

  python3 bench/qos_metrics.py --campaign campaigns/final3
  python3 bench/qos_metrics.py --campaign campaigns/qos --tput campaigns/qos/tput.jsonl

CONDITIONS   what the network delivered to each UE in each scenario phase (identical across arms
             by design: same seed per block) -> sanity check + "what failed" picture.
EXPERIENCED  the same samples restricted to the time the application RELIED on the network
             (primary/remote mode). PReNEF cannot make the network faster; it keeps the application
             off a path that no longer meets its contract.
Phases per (AF, time): baseline | ue_ramp | ue_violated | srsu_ramp | srsu_outage
Writes <campaign>/paper/: figQ1_conditions, figQ2_tail, figQ3_per_ue, figQ4_goodput (with --tput),
qos_conditions.md/.csv, qos_experienced.md/.csv
"""
from __future__ import annotations

import argparse
import bisect
import csv
import glob
import math
import os
import sys
from collections import defaultdict

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from bench.analyze import bootstrap_ci  # noqa: E402
from bench.figures import load_contracts  # noqa: E402
from bench.metrics import episodes, load_agent_logs, mode_at, mode_timeline, obs_series  # noqa: E402
from bench.paper_figures import COL1, COL2, INK, INK2, save, setup  # noqa: E402
from prenef.common import read_json, read_jsonl  # noqa: E402

ARM_STYLE = {
    "direct_nef": ("Direct NEF (3GPP)", "#eda100", "^", (0, (4, 1.5))),
    "independent_pred": ("Per-AF predictor", "#eb6834", "s", (0, (1.5, 1.2))),
    "prenef_noai": ("PReNEF (no AI)", "#1baf7a", "D", (0, (5, 1.5, 1.5, 1.5))),
    "prenef_dtip": ("PReNEF + DTIP", "#2a78d6", "o", "-"),
}
PHASES = {"baseline": ("Baseline", "#b9bec7"), "ue_ramp": ("UE ramp (precursor)", "#f2c45a"),
          "ue_violated": ("UE degradation (contract violated)", "#e34948"),
          "srsu_ramp": ("sRSU ramp (precursor)", "#c3b5f2"), "srsu_outage": ("sRSU outage", "#6250d6")}
N6_PHASES = ["baseline", "ue_ramp", "ue_violated"]
SRSU_PHASES = ["baseline", "srsu_ramp", "srsu_outage"]
NOREPLY = 2000.0


def label(arm):
    return ARM_STYLE.get(arm, (arm,))[0]


def phase_of(af, t, eps):
    for e in eps:
        if af in e["afs"] and e["start"] - 0.01 <= t <= e["end"] + 1.0:
            on = e["onsets"].get(af)
            pre = "srsu" if e["kind"] == "shared" else "ue"
            if on is not None and t >= on:
                return "srsu_outage" if pre == "srsu" else "ue_violated"
            return f"{pre}_ramp"
    return "baseline"


def load_tput(path):
    if not path:
        return {}
    by_af = defaultdict(list)
    for r in read_jsonl(path):
        if r.get("kind") == "tput":
            by_af[r["af"]].append(r)
    for v in by_af.values():
        v.sort(key=lambda r: r["wall_s"])
    return by_af


def load(campaign, arms, tput):
    samples, tps = [], []
    for d in sorted(glob.glob(os.path.join(campaign, "b*-*"))):
        name = os.path.basename(d)
        arm = name.split("-", 1)[1]
        if arm not in arms or not os.path.exists(os.path.join(d, "journal.jsonl")):
            continue
        mp = os.path.join(d, "metrics.json")
        if os.path.exists(mp):
            m = read_json(mp)
            if m.get("audit_ok") is False or (m.get("meas_coverage_min") or 1) < 0.9:
                continue
        try:
            block = int(name[1:3])
            sp = os.path.join(d, "scenario.json")
            scen = read_json(sp) if os.path.exists(sp) else {}
            contracts = load_contracts(d)
            eps = episodes(d, scen.get("service_afs", {}), contracts, scen)
            agents = load_agent_logs(d)
        except (StopIteration, FileNotFoundError, ValueError) as ex:
            print("skip", d, ex)
            continue
        for af, recs in agents.items():
            c = contracts.get(af)
            if c is None:
                continue
            prim = max(c.modes, key=lambda m: c.modes[m].utility)
            req = c.modes[prim].requirements
            lat_max = req.get("max_latency_ms", math.inf)
            loss_max = req.get("max_loss_pct", math.inf)
            deps = list(c.modes[prim].dependencies)
            obs = [r for r in recs if r["kind"] == "observation"]
            series = obs_series(recs)
            for r, (_, _, dt, _) in zip(obs, series):
                o = r.get("obs", {})
                if o.get("loss_pct") is None:
                    continue
                n6 = o.get("latency_ms")
                n6 = math.inf if n6 is None else float(n6)
                sv = (o.get("services") or {}).get("sRSU") if "sRSU" in deps else None
                s_up = None if sv is None else sv.get("up")
                s_lat = None if sv is None else (math.inf if (s_up is False or sv.get("latency_ms") is None)
                                                  else float(sv["latency_ms"]))
                samples.append({"block": block, "arm": arm, "af": af, "t": r["wall_s"], "dt": dt,
                                "remote": r.get("mode") == prim, "phase": phase_of(af, r["wall_s"], eps),
                                "n6": n6, "loss": float(o["loss_pct"]), "srsu_up": s_up, "srsu": s_lat,
                                "n6_bad": n6 > lat_max or float(o["loss_pct"]) > loss_max,
                                "srsu_bad": s_lat is not None and (s_up is False or s_lat > lat_max)})
            if tput.get(af) and obs:
                t_lo, t_hi = obs[0]["wall_s"], obs[-1]["wall_s"]
                tl = mode_timeline(recs)
                rows = tput[af]
                i = bisect.bisect_left([x["wall_s"] for x in rows], t_lo)
                for x in rows[i:]:
                    if x["wall_s"] > t_hi:
                        break
                    tps.append({"block": block, "arm": arm, "af": af, "t": x["wall_s"],
                                "remote": mode_at(tl, x["wall_s"]) == prim,
                                "phase": phase_of(af, x["wall_s"], eps), "rx": x["rx_kbps"],
                                "offered": x["offered_kbps"], "lost": x.get("lost_pct")})
    return samples, tps


def ci(v):
    v = np.asarray([x for x in v if x is not None and not math.isnan(x)], float)
    if len(v) == 0:
        return None
    lo, hi = bootstrap_ci(v) if len(v) >= 3 else (v.min(), v.max())
    return float(v.mean()), float(lo), float(hi), len(v)


def fmt(c, d=1):
    return "–" if c is None else f"{c[0]:.{d}f} [{c[1]:.{d}f}, {c[2]:.{d}f}]"


def pct(v, q):
    v = np.asarray(v, float)
    return float(np.percentile(np.minimum(v, NOREPLY), q)) if len(v) else math.nan


def per_block(samples, arm, fn, af=None):
    acc = defaultdict(list)
    for s in samples:
        if s["arm"] == arm and (af is None or s["af"] == af):
            acc[s["block"]].append(s)
    return [fn(v) for v in acc.values()]


def af_hours(v):
    return sum(s["dt"] for s in v) / 3600.0


def viol_s_per_afh(v):
    h = af_hours(v)
    return sum(s["dt"] for s in v if s["remote"] and (s["n6_bad"] or s["srsu_bad"])) / h if h else math.nan


def n6_viol_s_per_afh(v):
    h = af_hours(v)
    return sum(s["dt"] for s in v if s["remote"] and s["n6_bad"]) / h if h else math.nan


def srsu_viol_s_per_afh(v):
    v = [s for s in v if s["srsu"] is not None]
    h = af_hours(v)
    return sum(s["dt"] for s in v if s["remote"] and s["srsu_bad"]) / h if h else math.nan


def remote_share(v):
    tot = sum(s["dt"] for s in v)
    return 100 * sum(s["dt"] for s in v if s["remote"]) / tot if tot else math.nan


def p99_remote(v):
    x = [s["n6"] for s in v if s["remote"]]
    return pct(x, 99) if x else math.nan


def box(ax, data, pos, col, width):
    if len(data) == 0:
        return
    bp = ax.boxplot([np.minimum(data, NOREPLY)], positions=[pos], widths=width, whis=(5, 95), showfliers=False,
                    patch_artist=True, medianprops={"color": INK, "lw": 0.9},
                    whiskerprops={"color": INK2, "lw": 0.6}, capprops={"color": INK2, "lw": 0.6})
    bp["boxes"][0].set(facecolor=col, edgecolor=INK2, linewidth=0.5)


def fig_conditions(plt, samples, tps, out, afs):
    has_t = bool(tps)
    n = 4 if has_t else 3
    fig, axes = plt.subplots(1, n, figsize=(COL2, 2.25),
                             gridspec_kw={"wspace": 0.42, "width_ratios": [1.25, 1.25, 0.8, 1.25][:n]})
    w = 0.26
    ax = axes[0]
    for i, af in enumerate(afs):
        for k, ph in enumerate(N6_PHASES):
            d = [s["n6"] for s in samples if s["af"] == af and s["phase"] == ph and math.isfinite(s["n6"])]
            box(ax, d, i + (k - 1) * w, PHASES[ph][1], w * 0.9)
    ax.set_yscale("log")
    ax.axhline(60, color=INK, lw=0.6, ls="--")
    ax.text(len(afs) - 0.5, 60, "contract 60 ms", ha="right", va="bottom", fontsize=5.8, color=INK)
    ax.set_title("(a) RTT UE$\\rightarrow$N6 (ms)", loc="left", fontsize=7.5, fontweight="bold")
    ax = axes[1]
    for i, af in enumerate(afs):
        for k, ph in enumerate(N6_PHASES):
            d = [s["loss"] for s in samples if s["af"] == af and s["phase"] == ph]
            if d:
                ax.bar(i + (k - 1) * w, float(np.mean(d)), w * 0.9, color=PHASES[ph][1], edgecolor=INK2, lw=0.4)
    ax.set_title("(b) Packet loss UE$\\rightarrow$N6 (%)", loc="left", fontsize=7.5, fontweight="bold")
    ax = axes[2]
    s_afs = [af for af in afs if any(s["af"] == af and s["srsu"] is not None for s in samples)]
    for i, af in enumerate(s_afs):
        for k, ph in enumerate(SRSU_PHASES):
            sel = [s for s in samples if s["af"] == af and s["phase"] == ph and s["srsu"] is not None]
            d = [s["srsu"] for s in sel if math.isfinite(s["srsu"])]
            x = i + (k - 1) * w
            box(ax, d, x, PHASES[ph][1], w * 0.9)
            if sel:
                reach = 100 * len(d) / len(sel)
                ax.text(x, 1.02, f"{reach:.0f}%", transform=ax.get_xaxis_transform(), ha="center", va="bottom",
                        fontsize=5.3, color=INK if reach > 50 else "#c0201f", rotation=90)
    ax.set_yscale("log")
    ax.axhline(60, color=INK, lw=0.6, ls="--")
    ax.set_xticks(range(len(s_afs)))
    ax.set_xticklabels(s_afs)
    ax.set_title("(c) RTT UE$\\rightarrow$sRSU (ms)", loc="left", fontsize=7.5, fontweight="bold", pad=24)
    ax.set_xlabel("top: % of probes answered", fontsize=6.0, color=INK2)
    if has_t:
        ax = axes[3]
        for i, af in enumerate(afs):
            for k, ph in enumerate(N6_PHASES):
                d = [x["rx"] / 1e3 for x in tps if x["af"] == af and x["phase"] == ph]
                box(ax, d, i + (k - 1) * w, PHASES[ph][1], w * 0.9)
        off = max(x["offered"] for x in tps) / 1e3
        ax.axhline(off, color=INK, lw=0.6, ls=":")
        ax.text(len(afs) - 0.5, off, f"offered {off:g} Mb/s", ha="right", va="bottom", fontsize=5.8)
        ax.set_ylim(0, off * 1.25)
        ax.set_title("(d) Uplink goodput (Mb/s)", loc="left", fontsize=7.5, fontweight="bold")
    for ax in [axes[0], axes[1]] + ([axes[3]] if has_t else []):
        ax.set_xticks(range(len(afs)))
        ax.set_xticklabels(afs)
    from matplotlib.patches import Patch
    phs = N6_PHASES + SRSU_PHASES[1:]
    fig.legend(handles=[Patch(facecolor=PHASES[p][1], edgecolor=INK2, lw=0.4, label=PHASES[p][0]) for p in phs],
               ncol=len(phs), loc="upper center", bbox_to_anchor=(0.5, 1.13), handlelength=1.0, columnspacing=0.9,
               fontsize=6.3)
    fig.text(0.5, -0.06, "Network conditions per UE and scenario phase, pooled over arms (identical by design). "
             "Boxes: median, IQR, whiskers 5–95 %.", ha="center", fontsize=6.0, color=INK2)
    save(fig, out, "figQ1_conditions")
    plt.close(fig)


def ccdf_panel(ax, samples, arms, key, title, vals):
    grid = np.logspace(0, math.log10(1200), 300)
    floor = 1e-3
    for arm in arms:
        sel = [s for s in samples if s["arm"] == arm and s[key] is not None]
        if not sel:
            continue
        tot = sum(s["dt"] for s in sel)
        v = np.array([s[key] for s in sel], float)
        w = np.array([s["dt"] for s in sel], float)
        r = np.array([s["remote"] for s in sel], bool)
        y = np.array([100 * w[r & (v > g)].sum() / tot for g in grid])
        y_inf = 100 * w[r & ~np.isfinite(v)].sum() / tot
        y60 = 100 * w[r & (v > 60)].sum() / tot
        lab, col, _, ls = ARM_STYLE.get(arm, (arm, INK, "o", "-"))
        ax.plot(grid, np.maximum(y, floor), color=col, ls=ls, lw=1.3 if arm == "prenef_dtip" else 1.0,
                label=f"{lab}: {y60:.2f} %")
        ax.plot([1300, 3000], [max(y_inf, floor)] * 2, color=col, ls=ls, lw=2.2, solid_capstyle="butt")
        vals[(key, arm)] = (y60, y_inf, 100 * w[r].sum() / tot)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(1, 3000)
    ax.set_ylim(floor * 0.8, 130)
    ax.axvline(60, color=INK, lw=0.6, ls="--")
    ax.text(62, 1.4e-3, "contract\n60 ms", fontsize=5.6, color=INK, va="bottom")
    ax.axvspan(1250, 3000, color="#f3f3f3", lw=0, zorder=0)
    ax.text(1950, 60, "no\nreply", ha="center", va="top", fontsize=5.6, color=INK2)
    ax.set_xticks([1, 10, 60, 100, 1000])
    ax.set_xticklabels(["1", "10", "60", "100", "1000"])
    ax.set_yticks([1e-3, 1e-2, 1e-1, 1, 10, 100])
    ax.set_yticklabels(["0.001", "0.01", "0.1", "1", "10", "100"])
    ax.grid(axis="both", visible=True)
    ax.set_xlabel("RTT threshold $x$ (ms)")
    ax.set_title(title, loc="left", fontsize=7.5, fontweight="bold")
    ax.legend(loc="lower left", fontsize=5.9, handlelength=2.2, title="time relying on RTT > 60 ms",
              title_fontsize=5.9)


def fig_tail(plt, samples, arms, out):
    vals = {}
    fig, axes = plt.subplots(1, 2, figsize=(COL2, 2.5), gridspec_kw={"wspace": 0.22})
    ccdf_panel(axes[0], samples, arms, "n6", "(a) Path UE$\\rightarrow$N6 server (all UEs)", vals)
    ccdf_panel(axes[1], [s for s in samples if s["srsu"] is not None], arms, "srsu",
               "(b) Path UE$\\rightarrow$sRSU (shared service, af1–af2)", vals)
    axes[0].set_ylabel("Share of operating time the app relied\non a path with RTT $> x$ (%)")
    fig.text(0.5, -0.07, "Left end of each curve = share of time in the network-dependent (remote) mode; "
             "lower tail = fewer seconds spent depending on an out-of-contract path.", ha="center",
             fontsize=6.0, color=INK2)
    save(fig, out, "figQ2_tail")
    plt.close(fig)
    return vals


def fig_per_ue(plt, samples, arms, afs, out):
    fig, axes = plt.subplots(1, len(afs), figsize=(COL2, 1.9), gridspec_kw={"wspace": 0.35})
    for ax, af in zip(np.atleast_1d(axes), afs):
        for k, arm in enumerate(arms):
            c = ci(per_block(samples, arm, viol_s_per_afh, af=af))
            if c is None:
                continue
            col = ARM_STYLE.get(arm, (arm, INK))[1]
            ax.bar(k, c[0], 0.72, color=col, edgecolor="white", lw=0.4)
            ax.errorbar(k, c[0], yerr=[[c[0] - c[1]], [c[2] - c[0]]], fmt="none", ecolor=INK, elinewidth=0.7,
                        capsize=1.5)
        deps = "sRSU + N6" if any(s["af"] == af and s["srsu"] is not None for s in samples) else "N6 only"
        ax.set_title(f"{af} ({deps})", loc="left", fontsize=7.2, fontweight="bold")
        ax.set_xticks([])
        ax.set_ylim(bottom=0)
    np.atleast_1d(axes)[0].set_ylabel("s per AF-hour relying on\nan out-of-contract path")
    from matplotlib.patches import Patch
    fig.legend(handles=[Patch(color=ARM_STYLE.get(a, (a, INK))[1], label=label(a)) for a in arms],
               ncol=len(arms), loc="upper center", bbox_to_anchor=(0.5, 1.12), handlelength=1.0, fontsize=6.5)
    save(fig, out, "figQ3_per_ue")
    plt.close(fig)


def goodput_metrics(tps, arm):
    acc = defaultdict(list)
    for x in tps:
        if x["arm"] == arm:
            acc[x["block"]].append(x)
    short, low = [], []
    for v in acc.values():
        h = len(v) / 3600.0
        short.append(sum(max(0.0, x["offered"] - x["rx"]) for x in v if x["remote"]) / 1e3 / h)
        low.append(sum(1 for x in v if x["remote"] and x["rx"] < 0.5 * x["offered"]) / h)
    return short, low


def fig_goodput(plt, tps, arms, out):
    fig, axes = plt.subplots(1, 2, figsize=(COL1, 1.9), gridspec_kw={"wspace": 0.6})
    for k, arm in enumerate(arms):
        col = ARM_STYLE.get(arm, (arm, INK))[1]
        for ax, v in zip(axes, goodput_metrics(tps, arm)):
            c = ci(v)
            if c is None:
                continue
            ax.barh(len(arms) - 1 - k, c[0], 0.7, color=col, edgecolor="white")
            ax.errorbar(c[0], len(arms) - 1 - k, xerr=[[c[0] - c[1]], [c[2] - c[0]]], fmt="none", ecolor=INK,
                        elinewidth=0.7, capsize=1.5)
    for ax in axes:
        ax.set_yticks(range(len(arms)))
        ax.grid(axis="x", visible=True)
        ax.grid(axis="y", visible=False)
    axes[0].set_yticklabels([label(a) for a in reversed(arms)], fontsize=6.5)
    axes[1].set_yticklabels([])
    axes[0].set_xlabel("Mbit not delivered\nper AF-hour (remote mode)", fontsize=6.5)
    axes[1].set_xlabel("s per AF-hour with goodput\n< 50 % (remote mode)", fontsize=6.5)
    save(fig, out, "figQ4_goodput")
    plt.close(fig)


def tables(samples, tps, arms, afs, out, tail_vals):
    C = [["af", "phase", "arm", "n_samples", "rtt_n6_p50_ms", "rtt_n6_p95_ms", "loss_n6_mean_pct",
          "srsu_reachable_pct", "rtt_srsu_p50_ms", "goodput_p50_mbps", "goodput_mean_mbps"]]
    md = ["# Network conditions per UE and scenario phase", "",
          "Pooled over arms (the scenario of a block is identical in every arm). RTT/loss from the AF probes "
          "(0.2 s ping), goodput from lab/tput_logger.py (receiver side).", "",
          "| UE | phase | samples | RTT N6 p50 / p95 (ms) | loss N6 (%) | sRSU reachable (%) | RTT sRSU p50 (ms) "
          "| goodput p50 (Mb/s) |", "|---|---|---|---|---|---|---|---|"]
    f = lambda x, d=1: "–" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{d}f}"  # noqa: E731
    chk = defaultdict(list)
    for af in afs:
        for ph in PHASES:
            for arm in [None] + arms:
                sel = [s for s in samples if s["af"] == af and s["phase"] == ph and (arm is None or s["arm"] == arm)]
                if not sel:
                    continue
                n6 = [s["n6"] for s in sel]
                sr = [s for s in sel if s["srsu"] is not None]
                srf = [s["srsu"] for s in sr if math.isfinite(s["srsu"])]
                tp = [x["rx"] / 1e3 for x in tps if x["af"] == af and x["phase"] == ph and (arm is None or x["arm"] == arm)]
                row = [af, ph, arm or "all", len(sel), pct(n6, 50), pct(n6, 95), float(np.mean([s["loss"] for s in sel])),
                       100 * len(srf) / len(sr) if sr else None, pct(srf, 50) if srf else None,
                       float(np.median(tp)) if tp else None, float(np.mean(tp)) if tp else None]
                C.append(row)
                if arm is None:
                    md.append(f"| {af} | {PHASES[ph][0]} | {len(sel)} | {f(row[4])} / {f(row[5])} | {f(row[6])} | "
                              f"{f(row[7], 0)} | {f(row[8])} | {f(row[9], 2)} |")
                elif ph in ("baseline", "ue_violated") and math.isfinite(row[4]):
                    chk[(af, ph)].append(row[4])
    worst = max((max(v) - min(v) for v in chk.values() if len(v) > 1), default=0.0)
    md += ["", f"Identical-conditions check: largest difference between arms of the median N6 RTT within a "
           f"(UE, phase) cell = {worst:.1f} ms.", ""]
    with open(os.path.join(out, "qos_conditions.csv"), "w", newline="") as fh:
        csv.writer(fh).writerows(C)
    with open(os.path.join(out, "qos_conditions.md"), "w") as fh:
        fh.write("\n".join(md) + "\n")

    E = [["scope", "metric", "arm", "mean", "ci_lo", "ci_hi", "n_blocks"]]
    base = arms[0]

    def row_of(name, values_by_arm, d):
        cells, b = [], None
        for arm in arms:
            c = ci(values_by_arm(arm))
            if c is None:
                cells.append("–")
                continue
            E.append(["all", name.strip(), arm, *c])
            if arm == base:
                b = c[0]
            rel = "" if arm == base or not b else f"<br>({100 * (c[0] - b) / b:+.0f} %)"
            cells.append(fmt(c, d) + rel)
        return f"| {name} | " + " | ".join(cells) + " |"

    md = ["# QoS experienced by the applications (only while they relied on the network)", "",
          f"Mean [95 % bootstrap CI over blocks]; percentage = relative change vs {label(base)}.", "",
          "| Metric | " + " | ".join(label(a) for a in arms) + " |", "|---|" + "---|" * len(arms)]
    for name, fn, d in [("Time in remote (network-dependent) mode (%)", remote_share, 1),
                        ("Relying on an out-of-contract path (s per AF-hour)", viol_s_per_afh, 1),
                        ("– N6 path: RTT > 60 ms, loss or no reply (s per AF-hour)", n6_viol_s_per_afh, 1),
                        ("– sRSU unreachable or RTT > 60 ms (s per AF-hour, af1–af2)", srsu_viol_s_per_afh, 1),
                        ("p99 N6 RTT experienced in remote mode (ms, no reply = 2000)", p99_remote, 0)]:
        md.append(row_of(name, lambda arm, fn=fn: per_block(samples, arm, fn), d))
    if tps:
        md.append(row_of("Uplink data not delivered in remote mode (Mbit per AF-hour)",
                         lambda arm: goodput_metrics(tps, arm)[0], 1))
        md.append(row_of("Remote-mode seconds with goodput < 50 % (s per AF-hour)",
                         lambda arm: goodput_metrics(tps, arm)[1], 1))
    md += ["", "## Per UE: seconds per AF-hour relying on an out-of-contract path", "",
           "| UE | " + " | ".join(label(a) for a in arms) + " |", "|---|" + "---|" * len(arms)]
    for af in afs:
        cells = []
        for arm in arms:
            c = ci(per_block(samples, arm, viol_s_per_afh, af=af))
            cells.append(fmt(c, 1))
            if c:
                E.append([af, "viol_s_per_afh", arm, *c])
        md.append(f"| {af} | " + " | ".join(cells) + " |")
    md += ["", "## Per scenario phase: % of the phase spent relying on the network (remote mode)", "",
           "| Phase | " + " | ".join(label(a) for a in arms) + " |", "|---|" + "---|" * len(arms)]
    for ph in ("ue_ramp", "ue_violated", "srsu_ramp", "srsu_outage"):
        def share(v, ph=ph):
            v = [s for s in v if s["phase"] == ph]
            tot = sum(s["dt"] for s in v)
            return 100 * sum(s["dt"] for s in v if s["remote"]) / tot if tot else math.nan
        cells = []
        for arm in arms:
            c = ci(per_block(samples, arm, share))
            cells.append(fmt(c, 0))
            if c:
                E.append([ph, "remote_share_pct", arm, *c])
        md.append(f"| {PHASES[ph][0]} | " + " | ".join(cells) + " |")
    md += ["", "## Tail (figQ2): % of operating time relying on the path with RTT > 60 ms / with no reply", "",
           "| Path | " + " | ".join(label(a) for a in arms) + " |", "|---|" + "---|" * len(arms)]
    for key, nm in (("n6", "UE→N6"), ("srsu", "UE→sRSU")):
        cells = [f"{tail_vals[(key, a)][0]:.2f} / {tail_vals[(key, a)][1]:.2f}" if (key, a) in tail_vals else "–"
                 for a in arms]
        md.append(f"| {nm} | " + " | ".join(cells) + " |")
    with open(os.path.join(out, "qos_experienced.csv"), "w", newline="") as fh:
        csv.writer(fh).writerows(E)
    with open(os.path.join(out, "qos_experienced.md"), "w") as fh:
        fh.write("\n".join(md) + "\n")
    return "\n".join(md)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign", required=True)
    ap.add_argument("--tput", default=None, help="JSONL from lab/tput_logger.py (optional)")
    ap.add_argument("--arms", default="direct_nef,independent_pred,prenef_noai,prenef_dtip",
                    help="first arm = reference for the relative changes")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = a.out or os.path.join(a.campaign, "paper")
    os.makedirs(out, exist_ok=True)
    arms = [x for x in a.arms.split(",") if x]
    print("reading run folders...")
    samples, tps = load(a.campaign, set(arms), load_tput(a.tput))
    if not samples:
        print("no samples found (check --campaign / --arms)")
        return 1
    arms = [x for x in arms if any(s["arm"] == x for s in samples)]
    afs = sorted({s["af"] for s in samples})
    print(f"{len(samples)} probe samples, {len(tps)} goodput seconds, arms: {', '.join(arms)}")
    if a.tput and not tps:
        print("WARNING: --tput given but no goodput record falls inside the runs")
    plt = setup()
    fig_conditions(plt, samples, tps, out, afs)
    vals = fig_tail(plt, samples, arms, out)
    fig_per_ue(plt, samples, arms, afs, out)
    if tps:
        fig_goodput(plt, tps, arms, out)
    print(tables(samples, tps, arms, afs, out, vals))
    print("\nwrote", out, ": figQ1_conditions, figQ2_tail, figQ3_per_ue" + (", figQ4_goodput" if tps else "") +
          " (.pdf/.png), qos_conditions.md/.csv, qos_experienced.md/.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
