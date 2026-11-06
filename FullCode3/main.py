from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple

import streamlit as st
import plotly.graph_objects as go
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from scipy import stats
import time
import secrets

try:
    from cryptography.hazmat.primitives.asymmetric import rsa, ec, padding
    from cryptography.hazmat.primitives import hashes
    from cryptography.exceptions import InvalidSignature
    CRYPTO_BACKEND_AVAILABLE = True
except Exception:
    CRYPTO_BACKEND_AVAILABLE = False

st.set_page_config(page_title="AO-LACCP Scientific Research Evaluation", layout="wide")
st.title("AO-LACCP: AI-Orchestrated Latency-Aware Cryptographic Control Plane")

# Actions and MDP values copied from the current AO-LACCP full-framework code.
# Outcome effects below are an explicit evaluation bridge, not present in the original artifact.
ACTIONS = ("Monitor", "Mitigate", "Escalate")
ACTION_MAP = {"Monitor": "monitor", "Mitigate": "rate_limit", "Escalate": "isolate"}
ACTION_COST = {"monitor": 0.00, "rate_limit": 0.12, "isolate": 0.32, "crypto_harden": 0.20}
ACTION_LATENCY_MS = {"monitor": 2.0, "rate_limit": 8.0, "isolate": 18.0, "crypto_harden": 12.0}
ACTION_MITIGATION = {"monitor": 0.04, "rate_limit": 0.22, "isolate": 0.52, "crypto_harden": 0.30}
THREAT_TYPES = ("benign", "brute_force", "phishing", "data_exfiltration", "mitm", "zero_day")
THREAT_PROBS = np.array([0.28, 0.18, 0.16, 0.14, 0.13, 0.11])
PERSISTENCE = {"benign": 0.10, "brute_force": 0.72, "phishing": 0.66, "data_exfiltration": 0.82, "mitm": 0.78, "zero_day": 0.88}
ACTION_MATCH = {
    "benign": {"monitor": 0.75, "rate_limit": 0.60, "isolate": 0.45, "crypto_harden": 0.50},
    "brute_force": {"monitor": 0.08, "rate_limit": 0.82, "isolate": 0.90, "crypto_harden": 0.10},
    "phishing": {"monitor": 0.12, "rate_limit": 0.35, "isolate": 0.70, "crypto_harden": 0.10},
    "data_exfiltration": {"monitor": 0.05, "rate_limit": 0.50, "isolate": 0.92, "crypto_harden": 0.15},
    "mitm": {"monitor": 0.08, "rate_limit": 0.25, "isolate": 0.78, "crypto_harden": 0.86},
    "zero_day": {"monitor": 0.08, "rate_limit": 0.25, "isolate": 0.80, "crypto_harden": 0.72},
}
# Exact illustrative transition matrix in ao_laccp_full_framework_updated.py.
ARTIFACT_TRANSITIONS = {"Low": np.array([0.70, 0.25, 0.05]),
                        "Medium": np.array([0.30, 0.50, 0.20]),
                        "High": np.array([0.10, 0.40, 0.50])}
ARTIFACT_REWARDS = {("Low", "Monitor"): 10.0, ("Medium", "Mitigate"): 20.0,
                    ("High", "Escalate"): 30.0}
BASE_REWARD_FALLBACK = -5.0

@dataclass(frozen=True)
class Scenario:
    run_id: int
    scenario_id: int
    threat_type: str
    threat_severity: float
    initial_risk: float
    workload: float
    network_load: float
    network_noise: float
    threat_signal: float
    crypto_pressure: float
    service_capacity: float


def clip01(x: float) -> float:
    return float(np.clip(x, 0.0, 1.0))


def generate_scenarios(seed: int, run_id: int, n: int) -> List[Scenario]:
    rng = np.random.default_rng(seed)
    out = []
    ranges = {"benign": (0.02, 0.22), "brute_force": (0.45, 0.95), "phishing": (0.35, 0.88),
              "data_exfiltration": (0.55, 0.98), "mitm": (0.48, 0.96), "zero_day": (0.60, 1.00)}
    for i in range(n):
        threat = str(rng.choice(THREAT_TYPES, p=THREAT_PROBS))
        lo, hi = ranges[threat]
        sev = float(rng.uniform(lo, hi))
        initial = clip01(0.45 * sev + 0.25 * rng.beta(2.0, 2.2) + 0.15)
        out.append(Scenario(
            run_id=run_id, scenario_id=i, threat_type=threat, threat_severity=sev,
            initial_risk=initial, workload=float(rng.uniform(.20, 1.0)),
            network_load=float(rng.uniform(.15, 1.0)), network_noise=float(rng.normal(0, 1)),
            threat_signal=clip01(.72 * sev + rng.normal(0, .12)),
            crypto_pressure=clip01((.75 if threat in ("mitm", "zero_day") else .25) + rng.normal(0, .15)),
            service_capacity=float(rng.uniform(.75, 1.0))))
    return out


def state_of(s: Scenario) -> str:
    """Map scenario features to the original artifact's Low/Medium/High risk states."""
    risk_proxy = clip01(.55 * s.initial_risk + .30 * s.threat_signal + .15 * s.threat_severity)
