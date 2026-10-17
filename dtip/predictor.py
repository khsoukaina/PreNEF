"""Online DTIP inference for the runtime (block E). Verifies the model card
hash before use and propagates the qualification flags into every Prediction:
an unqualified model is still *callable* (for shadow logging) but the planner
will abstain from AI-based ranking (eq. 19)."""
from __future__ import annotations

import hashlib
import os
import pickle
import time

import numpy as np

from dtip.features import FEATURE_NAMES, extract
from prenef.common import read_json
from prenef.planner import Prediction


class OnlinePredictor:
    def __init__(self, model_dir: str, p_horizon_s: float = 5.0):
        card = read_json(os.path.join(model_dir, "model_card.json"))
        mp = os.path.join(model_dir, "model.pkl")
        if hashlib.sha256(open(mp, "rb").read()).hexdigest() != card["model_sha256"]:
            raise RuntimeError("model.pkl does not match model_card.json")
        if card["feature_names"] != FEATURE_NAMES:
            raise RuntimeError("feature schema changed since training")
        with open(mp, "rb") as f:
            self.model = pickle.load(f)
        self.card = card
        self.qualified = bool(card["safe_time_qualified"] and card["uncertainty_qualified"])
        self.p_horizon_s = p_horizon_s

    def predict_many(self, items: list[tuple], now_wall_s: float | None = None) -> dict:
        """items: [(af, history, dependencies, n_shared)] -> {af: (Prediction, info)}.
        One model call for all AFs (sklearn per-call overhead dominates single rows)."""
        if not items:
            return {}
        t = now_wall_s or time.time()
        t0 = time.perf_counter()
        X = np.array([extract(h, t, d, n) for _, h, d, n in items], dtype=float)
        out = self.model.predict(X, self.p_horizon_s)
        dt = time.perf_counter() - t0
        res = {}
        for i, (af, *_rest) in enumerate(items):
            res[af] = (Prediction(p_inad=float(out["p_inad"][i]), t_safe_s=float(out["t_safe_s"][i]),
                                  u=float(out["u"][i]), qualified=self.qualified, horizon_s=self.p_horizon_s),
                       {"features": X[i].tolist(), "F": out["F"][i].tolist(), "l_pred_s": dt,
                        "u_max_card": self.model.u_max})
        return res

    def predict(self, history: list[dict], dependencies: list[str], n_shared: int,
                now_wall_s: float | None = None) -> tuple[Prediction, dict]:
        t = now_wall_s or time.time()
        t0 = time.perf_counter()
        x = np.array([extract(history, t, dependencies, n_shared)], dtype=float)
        out = self.model.predict(x, self.p_horizon_s)
        pred = Prediction(p_inad=float(out["p_inad"][0]), t_safe_s=float(out["t_safe_s"][0]),
                          u=float(out["u"][0]), qualified=self.qualified, horizon_s=self.p_horizon_s)
        return pred, {"features": x[0].tolist(), "F": out["F"][0].tolist(),
                      "l_pred_s": time.perf_counter() - t0, "u_max_card": self.model.u_max}
