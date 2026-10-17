"""AO-LACCP scientific paired-evaluation prototype.

This is a transparent synthetic simulation harness, NOT a production validation.
It trains a tabular Q-learning policy on training scenarios, freezes it, and
compares it with a fixed-threshold baseline on independent held-out scenarios.
Both policies receive the same scenario inputs and share one outcome simulator.

IMPORTANT: action effectiveness, scenario distributions, latency equation, and
reward weights are explicit assumptions. Justify/calibrate them and conduct
sensitivity analyses before using results as dissertation evidence.

Run:
    pip install streamlit pandas numpy scipy matplotlib
    streamlit run ao_laccp_scientific_validation_research_ready.py
"""
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
    return "Low" if risk_proxy < .35 else ("Medium" if risk_proxy < .65 else "High")


def baseline_policy(s: Scenario) -> str:
    """Explicit fixed-threshold baseline; this baseline is not defined by the original artifact."""
    if s.initial_risk >= .72 or s.threat_signal >= .82:
        return "Escalate"
    if s.threat_signal >= .58:
        return "Mitigate"
    return "Monitor"


def outcome(s: Scenario, action_name: str, effectiveness_scale: float = 1.0,
            transition_noise_scale: float = 1.0,
            calibration_factors: Dict[str, float] | None = None) -> Dict[str, float]:
    """Shared synthetic outcome equations; effect sizes are assumptions, not calibrated efficacy."""
    action = ACTION_MAP.get(action_name, action_name)
    persistence = PERSISTENCE[s.threat_type]
    calibration_factors = calibration_factors or {}
    factor = float(calibration_factors.get(action, 1.0))
    mitigation = np.clip(ACTION_MITIGATION[action] * ACTION_MATCH[s.threat_type][action] * effectiveness_scale * factor, 0, .95)
    disturbance = .035 * s.network_noise * transition_noise_scale + .045 * max(0.0, s.network_load - .70) + .035 * s.workload
    residual = s.threat_severity * persistence * (1.0 - mitigation)
    risk = clip01(.48 * s.initial_risk + .44 * residual + disturbance)
    base_latency = (35.0 + 85.0 * s.network_load + 42.0 * s.workload
                    + 18.0 * (1.0 / max(s.service_capacity, .50) - 1.0) + 2.5 * s.network_noise)
    latency = max(1.0, base_latency + ACTION_LATENCY_MS[action] + 18.0 * ACTION_COST[action])
    service_impact = clip01(.10 * s.workload + .42 * ACTION_COST[action]
                            + .10 * max(0.0, s.network_load - s.service_capacity))
    return {"resulting_risk": risk, "simulated_latency_ms": latency,
            "service_impact_proxy": service_impact, "action_cost_proxy": ACTION_COST[action],
            "selected_action_code": float(ACTIONS.index(action_name)),
            "residual_threat_proxy": residual}


def reward_for(state: str, action: str, reward_scale: float = 1.0) -> float:
    """Original artifact reward table, optionally scaled for predeclared sensitivity tests."""
    return float(ARTIFACT_REWARDS.get((state, action), BASE_REWARD_FALLBACK) * reward_scale)


def mdp_transition(state: str, rng: np.random.Generator, transition_mix: float = 1.0) -> str:
    """Original artifact transition model: state-based probabilities, action-independent.

    transition_mix=1 uses original rows exactly; values below 1 blend rows toward a
    uniform distribution for sensitivity analysis. This is a model assumption, not calibration.
    """
    p = ARTIFACT_TRANSITIONS[state].astype(float)
    uniform = np.ones(3) / 3.0
    mix = float(np.clip(transition_mix, 0.0, 1.0))
    p = mix * p + (1.0 - mix) * uniform
    p = p / p.sum()
    return str(rng.choice(["Low", "Medium", "High"], p=p))


def representative_scenario(state: str, seed: int) -> Scenario:
    rng = np.random.default_rng(seed)
    risk = {"Low": .20, "Medium": .50, "High": .82}[state]
    threat = {"Low": "benign", "Medium": "brute_force", "High": "zero_day"}[state]
    severity = {"benign": .12, "brute_force": .70, "zero_day": .88}[threat]
    return Scenario(0, 0, threat, severity, risk, float(rng.uniform(.3, .8)),
                    float(rng.uniform(.2, .8)), 0.0, clip01(risk), .30, .90)


def train_q_policy(seed: int, episodes: int, steps_per_episode: int,
                   weights: Dict[str, float], alpha: float, gamma: float, epsilon: float,
                   transition_mix: float = 1.0, reward_scale: float = 1.0) -> pd.DataFrame:
    """Reproduce original artifact's state/action/reward/transition structure.

    The original artifact uses 3 risk states, Monitor/Mitigate/Escalate,
    state-only transitions, reward +10/+20/+30 for matching actions and -5 otherwise.
    Defaults in its code are 300 episodes x 10 steps, alpha=.1, gamma=.9, epsilon=.2.
    """
    rng = np.random.default_rng(seed)
    states = ["Low", "Medium", "High"]
    q = pd.DataFrame(0.0, index=states, columns=ACTIONS)
    for episode in range(episodes):
        state = str(rng.choice(states))
        for step in range(steps_per_episode):
            if rng.random() < epsilon:
                action = str(rng.choice(ACTIONS))
            else:
                values = q.loc[state].to_numpy(dtype=float)
                best = np.flatnonzero(np.isclose(values, values.max()))
                action = ACTIONS[int(rng.choice(best))]
            reward = reward_for(state, action, reward_scale)
            next_state = mdp_transition(state, rng, transition_mix)
            old = float(q.loc[state, action])
            q.loc[state, action] = old + alpha * (reward + gamma * float(q.loc[next_state].max()) - old)
            state = next_state
    return q


def mdp_transition_table(transition_mix: float = 1.0) -> pd.DataFrame:
    rows = []
    for state, probs in ARTIFACT_TRANSITIONS.items():
        uniform = np.ones(3) / 3.0
        p = transition_mix * probs + (1.0 - transition_mix) * uniform
        p = p / p.sum()
        for nxt, prob in zip(["Low", "Medium", "High"], p):
            rows.append({"Current state": state, "Next state": nxt, "Transition probability": float(prob),
                         "Source": "Original artifact configured row" if transition_mix == 1.0 else "Sensitivity perturbation"})
    return pd.DataFrame(rows)


def q_policy(s: Scenario, q: pd.DataFrame) -> str:
    return str(q.loc[state_of(s)].idxmax())


def evaluate(seed: int, n_runs: int, n_per_run: int, q: pd.DataFrame,
             effectiveness_scale: float = 1.0, transition_noise_scale: float = 1.0,
             calibration_factors: Dict[str, float] | None = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for run in range(1, n_runs + 1):
        scenarios = generate_scenarios(seed + run * 100_003, run, n_per_run)
        for s in scenarios:
            for name, action in (("Baseline", baseline_policy(s)), ("AO-LACCP artifact-aligned Q-learning", q_policy(s, q))):
                rows.append({**asdict(s), "policy": name, "selected_action": action,
                             **outcome(s, action, effectiveness_scale, transition_noise_scale, calibration_factors)})
    detail = pd.DataFrame(rows)
    key = ["run_id", "scenario_id"]
    counts = detail.groupby(key)["policy"].nunique()
    if not counts.eq(2).all():
        raise RuntimeError("Pairing check failed: each scenario must have both policies.")
    inputs = ["threat_type", "threat_severity", "initial_risk", "workload", "network_load", "network_noise", "threat_signal", "crypto_pressure", "service_capacity"]
    for col in inputs:
        if detail.groupby(key)[col].nunique().max() != 1:
            raise RuntimeError(f"Pairing check failed: input {col} differs within a pair.")
    metrics = ["resulting_risk", "simulated_latency_ms", "service_impact_proxy", "action_cost_proxy", "selected_action_code"]
    wide = detail.pivot(index=key, columns="policy", values=metrics)
    wide.columns = [f"{m}__{p}" for m, p in wide.columns]
    wide = wide.reset_index()
    for m in metrics:
        wide[f"{m}__diff_AO_minus_baseline"] = wide[f"{m}__AO-LACCP artifact-aligned Q-learning"] - wide[f"{m}__Baseline"]
    return detail, wide


def holm_adjust(p_values: List[float]) -> List[float]:
    """Holm step-down family-wise error correction; preserves input order."""
    p = np.asarray(p_values, dtype=float)
    out = np.full(len(p), np.nan)
    valid = np.flatnonzero(np.isfinite(p))
    if len(valid) == 0:
        return out.tolist()
    order = valid[np.argsort(p[valid])]
    running = 0.0
    m = len(order)
    for rank, idx in enumerate(order):
        adj = min(1.0, (m - rank) * p[idx])
        running = max(running, adj)
        out[idx] = running
    return out.tolist()


def summarize_runs(wide: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Primary inference uses independent run-level means, avoiding scenario pseudoreplication."""
    metrics = [
        ("resulting_risk", "Risk (lower is better)"),
        ("simulated_latency_ms", "Simulated latency (ms; lower is better)"),
        ("service_impact_proxy", "Service-impact proxy (lower is better)"),
        ("action_cost_proxy", "Action-cost proxy (lower is better)"),
    ]
    diff_cols = [f"{m}__diff_AO_minus_baseline" for m, _ in metrics]
    run_means = wide.groupby("run_id")[diff_cols].mean().reset_index()
    rows = []
    raw_ps = []
    for m, label in metrics:
        d = run_means[f"{m}__diff_AO_minus_baseline"].to_numpy(float)
        n = len(d)
        mean = float(np.mean(d))
        sd = float(np.std(d, ddof=1)) if n > 1 else np.nan
        se = sd / np.sqrt(n) if n > 1 else np.nan
        crit = float(stats.t.ppf(.975, n - 1)) if n > 1 else np.nan
        lo, hi = (mean - crit * se, mean + crit * se) if n > 1 else (np.nan, np.nan)
        if n > 1 and sd > 0:
            t_stat, p = stats.ttest_1samp(d, 0.0)
            dz = mean / sd
        else:
            t_stat, p, dz = np.nan, np.nan, np.nan
        # Paired bootstrap over independent run-level mean differences.
        brng = np.random.default_rng(81000 + len(rows))
        if n > 1:
            boot = np.mean(brng.choice(d, size=(10000, n), replace=True), axis=1)
            blo, bhi = np.quantile(boot, [.025, .975])
        else:
            blo, bhi = np.nan, np.nan
        raw_ps.append(float(p) if np.isfinite(p) else np.nan)
        rows.append({"Metric": label, "Independent runs (N)": n, "Mean run-level paired difference (AO - baseline)": mean,
                     "95% t CI low": lo, "95% t CI high": hi, "95% run-bootstrap CI low": blo,
                     "95% run-bootstrap CI high": bhi, "Run-level Cohen dz": dz, "Paired run-level t statistic": t_stat,
                     "Raw p-value": p})
    adjusted = holm_adjust(raw_ps)
    for row, p_adj in zip(rows, adjusted):
        row["Holm-adjusted p-value"] = p_adj
    return pd.DataFrame(rows), run_means



def paired_repeated_measures_anova(detail: pd.DataFrame) -> pd.DataFrame:
    """Two-policy repeated-measures ANOVA equivalent (F=t^2) on independent run means.

    A conventional independent-groups one-way ANOVA is not appropriate because both
    policies are evaluated on the same scenarios. With exactly two repeated conditions,
    the repeated-measures ANOVA test is equivalent to the paired t-test.
    """
    rows = []
    for metric, label in [("resulting_risk", "Cyber risk"),
                          ("simulated_latency_ms", "Response latency")]:
        rm = detail.groupby(["run_id", "policy"])[metric].mean().unstack("policy")
        if "Baseline" not in rm or "AO-LACCP artifact-aligned Q-learning" not in rm:
            continue
        paired = rm[["Baseline", "AO-LACCP artifact-aligned Q-learning"]].dropna()
        if len(paired) < 2:
            continue
        diffs = paired["AO-LACCP artifact-aligned Q-learning"] - paired["Baseline"]
        t_stat, p_value = stats.ttest_rel(paired["AO-LACCP artifact-aligned Q-learning"], paired["Baseline"])
        rows.append({"Outcome": label, "Independent run pairs": len(paired),
                     "F statistic (repeated-measures; 1, N-1 df)": float(t_stat ** 2),
                     "df1": 1, "df2": len(paired) - 1, "p-value": float(p_value),
                     "Interpretation note": "Run-level paired analysis; model-based synthetic outcome."})
    return pd.DataFrame(rows)


def exploratory_risk_regression(detail: pd.DataFrame, wide: pd.DataFrame) -> Tuple[pd.DataFrame, float]:
    """OLS R² for scenario-level paired risk difference; descriptive/exploratory only."""
    base = detail.loc[detail["policy"] == "Baseline",
                      ["run_id", "scenario_id", "threat_severity", "initial_risk", "workload",
                       "network_load", "threat_signal", "crypto_pressure"]].copy()
    diffs = wide[["run_id", "scenario_id", "resulting_risk__diff_AO_minus_baseline"]]
    df = base.merge(diffs, on=["run_id", "scenario_id"], validate="one_to_one").dropna()
    features = ["threat_severity", "initial_risk", "workload", "network_load", "threat_signal", "crypto_pressure"]
    X = df[features].to_numpy(float)
    X = np.column_stack([np.ones(len(X)), X])
    y = df["resulting_risk__diff_AO_minus_baseline"].to_numpy(float)
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    pred = X @ coef
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else float("nan")
    table = pd.DataFrame({"Term": ["Intercept"] + features, "Coefficient": coef})
    return table, r2



def parse_action_calibration(uploaded_file) -> Tuple[Dict[str, float], pd.DataFrame, str]:
    """Derive action-effect multipliers from user-supplied comparable empirical observations.

    Required CSV columns: action, observed_mitigation_fraction. Actions may be
    Monitor/Mitigate/Escalate or monitor/rate_limit/isolate. Values must be 0..1.
    """
    df = pd.read_csv(uploaded_file)
    required = {"action", "observed_mitigation_fraction"}
    if not required.issubset(df.columns):
        raise ValueError("Calibration CSV must contain columns: action, observed_mitigation_fraction")
    df = df.copy()
    df["observed_mitigation_fraction"] = pd.to_numeric(df["observed_mitigation_fraction"], errors="coerce")
    if df["observed_mitigation_fraction"].isna().any() or not df["observed_mitigation_fraction"].between(0, 1).all():
        raise ValueError("observed_mitigation_fraction must be numeric and between 0 and 1")
    mapping = {"monitor": "monitor", "mitigate": "rate_limit", "rate_limit": "rate_limit",
               "escalate": "isolate", "isolate": "isolate"}
    df["action_normalized"] = df["action"].astype(str).str.strip().str.lower().map(mapping)
    if df["action_normalized"].isna().any():
        raise ValueError("action values must be Monitor/Mitigate/Escalate or monitor/rate_limit/isolate")
    means = df.groupby("action_normalized")["observed_mitigation_fraction"].agg(["mean", "std", "count"]).reset_index()
    factors = {}
    for _, row in means.iterrows():
        action = row["action_normalized"]
        factors[action] = float(row["mean"] / max(ACTION_MITIGATION[action], 1e-9))
    note = ("Calibration multipliers were derived from the uploaded observed mitigation fractions. "
            "Use only observations measured under comparable conditions with a documented outcome definition. "
            "This does not calibrate transition probabilities or latency unless those are separately observed and modeled.")
    return factors, means, note

def run_sensitivity_analysis(seed: int, episodes: int, steps: int, weights: Dict[str, float],
                             alpha: float, gamma: float, epsilon: float, n_runs: int, n_per_run: int,
                             calibration_factors: Dict[str, float] | None = None) -> pd.DataFrame:
    """Genuine one-factor-at-a-time reruns: retrain and reevaluate for each assumption set."""
    variants = [
        ("Reference assumptions", 1.00, 1.00, 1.00),
        ("Transition rows blended 50% toward uniform", 0.50, 1.00, 1.00),
        ("Transition rows blended 100% toward uniform", 0.00, 1.00, 1.00),
        ("Action effectiveness -25%", 1.00, 0.75, 1.00),
        ("Action effectiveness +25%", 1.00, 1.25, 1.00),
        ("Network-noise effect -25%", 1.00, 1.00, 0.75),
        ("Network-noise effect +25%", 1.00, 1.00, 1.25),
    ]
    rows = []
    for i, (label, trans_mix, eff_scale, noise_scale) in enumerate(variants):
        q = train_q_policy(seed + 101_000 + i * 17, episodes, steps, weights, alpha, gamma, epsilon,
                           transition_mix=trans_mix)
        detail, wide = evaluate(seed + 202_000 + i * 31, n_runs, n_per_run, q, eff_scale, noise_scale, calibration_factors)
        run_diff = wide.groupby("run_id")[["resulting_risk__diff_AO_minus_baseline",
                                            "simulated_latency_ms__diff_AO_minus_baseline"]].mean()
        rows.append({"Sensitivity condition": label, "Transition mix": trans_mix,
                     "Action-effect scale": eff_scale, "Network-noise scale": noise_scale,
                     "Mean paired risk difference (AO - baseline)": run_diff["resulting_risk__diff_AO_minus_baseline"].mean(),
                     "Mean paired latency difference ms (AO - baseline)": run_diff["simulated_latency_ms__diff_AO_minus_baseline"].mean(),
                     "Risk direction favors AO?": bool(run_diff["resulting_risk__diff_AO_minus_baseline"].mean() < 0),
                     "Latency direction favors AO?": bool(run_diff["simulated_latency_ms__diff_AO_minus_baseline"].mean() < 0)})
    return pd.DataFrame(rows)


def benchmark_real_crypto_switching(seed: int, n_events: int = 30) -> Tuple[pd.DataFrame, pd.DataFrame, str]:
    """Run real RSA/ECDSA signing+verification and record actual suite-selection transitions.

    The suite selector is a transparent test policy, not present in the original dashboard.
    This benchmark measures actual operations for RSA/ECC/Hybrid where cryptography is installed.
    PQC is deliberately excluded unless a validated PQC backend is integrated.
    """
    if not CRYPTO_BACKEND_AVAILABLE:
        return pd.DataFrame(), pd.DataFrame(), "The Python cryptography package is unavailable; no cryptographic operations were run."
    rng = np.random.default_rng(seed)
    # Deterministic, reproducible event stream. Mode selection is a test rule, not claimed to be
    # the original AO-LACCP behavior. It allows measurement of actual suite changes/operations.
    events = []
    for i in range(n_events):
        pressure = float(rng.random())
        threat = str(rng.choice(["benign", "brute_force", "mitm", "zero_day"]))
        if threat in ("mitm", "zero_day") or pressure >= .70:
            suite = "Hybrid (RSA+ECDSA)"
        elif pressure >= .35:
            suite = "ECDSA"
        else:
            suite = "RSA"
        events.append({"event_id": i + 1, "threat_type": threat, "crypto_pressure": pressure, "selected_suite": suite})
    # Generate real keys once; per-event signing and verification use the selected suite.
    rsa_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    ec_key = ec.generate_private_key(ec.SECP256R1())
    payload = b"AO-LACCP crypto-switch benchmark payload"
    rows = []
    previous = None
    for ev in events:
        suite = ev["selected_suite"]
        switched = previous is not None and suite != previous
        t0 = time.perf_counter()
        ok = True
        try:
            if suite in ("RSA", "Hybrid (RSA+ECDSA)"):
                sig_rsa = rsa_key.sign(payload, padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                                    salt_length=padding.PSS.MAX_LENGTH), hashes.SHA256())
                rsa_key.public_key().verify(sig_rsa, payload, padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                                    salt_length=padding.PSS.MAX_LENGTH), hashes.SHA256())
            if suite in ("ECDSA", "Hybrid (RSA+ECDSA)"):
                sig_ec = ec_key.sign(payload, ec.ECDSA(hashes.SHA256()))
                ec_key.public_key().verify(sig_ec, payload, ec.ECDSA(hashes.SHA256()))
        except Exception:
            ok = False
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        rows.append({**ev, "suite_changed_from_previous_event": bool(switched),
                     "operation_success": bool(ok), "sign_verify_elapsed_ms": elapsed_ms,
                     "operations_performed": 2 if suite != "Hybrid (RSA+ECDSA)" else 4})
        previous = suite
    trace = pd.DataFrame(rows)
    total_switches = int(trace["suite_changed_from_previous_event"].sum())
    success_rate = float(trace["operation_success"].mean()) if len(trace) else float("nan")
    summary = pd.DataFrame([{"Events": len(trace), "Suite transitions observed": total_switches,
                             "Transition rate (excluding first event)": total_switches / max(1, len(trace)-1),
                             "Successful sign/verify events": int(trace["operation_success"].sum()),
                             "Operation success rate": success_rate,
                             "Mean sign/verify elapsed ms": float(trace["sign_verify_elapsed_ms"].mean()),
                             "PQC tested": False}])
    note = ("This executes real RSA-2048 and ECDSA P-256 signing/verification and counts suite-selection changes. "
            "It is a separate benchmark harness, not evidence that the original AO-LACCP dashboard performs these switches. "
            "PQC is not tested because no PQC backend is integrated; do not claim PQC agility from these results.")
    return trace, summary, note

def main() -> None:
    st.title("AO-LACCP: Scientific Paired Evaluation Prototype")
    st.warning("Synthetic model only. This app can test reproducibility and conditional behavior; it cannot by itself validate real-world banking efficacy or justify uncalibrated simulation assumptions.")
    with st.expander("Protocol, policy and limitations", expanded=True):
        st.markdown("""
**Design:** Q-learning is trained on synthetic training scenarios and then frozen. Evaluation uses independent held-out scenarios. Each held-out scenario is passed unchanged to the baseline and AO-LACCP policy.

**Baseline:** fixed thresholds on initial risk, threat signal and cryptographic pressure. This is one explicit comparator, not a claim to represent all production SOCs.

**Policy alignment audit:** the Q-learning state/action/reward/transition structure below now reproduces the current `ao_laccp_full_framework_updated.py` illustrative MDP: Low/Medium/High; Monitor/Mitigate/Escalate; configured state-only transition rows; matching-action rewards +10/+20/+30 and -5 otherwise. The original artifact does NOT connect this Q-table to its generated risk/latency/agility outcomes. The mapping from actions to outcome effects in this evaluation is therefore an explicitly added bridge assumption, not verified original behavior.

**Shared outputs:** both policies use the same synthetic outcome equations. The action-effect bridge and scenario generator are not empirically calibrated. A separate cryptographic benchmark below performs real RSA/ECDSA signing and verification and records suite transitions, but it does not validate the original dashboard or PQC switching.

**Inference:** scenarios are nested within independent simulation runs. The primary statistical summaries therefore use run-level mean differences, with confidence intervals, effect sizes and Holm correction across the displayed metrics.

**Before dissertation use:** pre-specify primary outcomes and reward weights; justify/calibrate scenario and action-effect parameters; perform sensitivity analyses; and verify the evaluated policy matches the artifact you claim to evaluate.
""")
    c1, c2, c3 = st.columns(3)
    with c1: seed = int(st.number_input("Random seed", min_value=0, max_value=2_000_000_000, value=20261017, step=1))
    with c2: n_runs = int(st.number_input("Independent test runs", min_value=10, max_value=200, value=40, step=10))
    with c3: n_per_run = int(st.number_input("Scenarios per run", min_value=25, max_value=2000, value=200, step=25))
    st.subheader("Training protocol")
    a, b, c, d = st.columns(4)
    with a: episodes = int(st.number_input("Training episodes", min_value=100, max_value=10000, value=1500, step=100))
    with b: steps = int(st.number_input("Steps per episode", min_value=5, max_value=100, value=20, step=5))
    with c: alpha = float(st.slider("Learning rate α", 0.01, 1.0, 0.10, 0.01))
    with d: gamma = float(st.slider("Discount γ", 0.0, 0.99, 0.80, 0.01))
    epsilon = float(st.slider("Exploration ε during training", 0.01, 1.0, 0.15, 0.01))
    st.markdown("**Predeclared reward weights** (must be justified and sensitivity-tested)")
    w1, w2, w3, w4 = st.columns(4)
    with w1: wrisk = float(st.number_input("Risk weight (reported; artifact reward uses fixed +10/+20/+30/-5)", min_value=0.0, max_value=1.0, value=0.55, step=0.05))
    with w2: wlat = float(st.number_input("Latency weight", min_value=0.0, max_value=1.0, value=0.15, step=0.05))
    with w3: wserv = float(st.number_input("Service impact weight", min_value=0.0, max_value=1.0, value=0.20, step=0.05))
    with w4: wcost = float(st.number_input("Action cost weight", min_value=0.0, max_value=1.0, value=0.10, step=0.05))
    weights = {"risk": wrisk, "latency": wlat, "service": wserv, "cost": wcost}
    if sum(weights.values()) <= 0:
        st.error("At least one reward weight must be positive.")
        return
    st.caption(f"Reward weights sum to {sum(weights.values()):.2f}; note that the artifact-aligned Q learner uses the original fixed +10/+20/+30/-5 reward table; these weights are retained for sensitivity-report context only.")
    st.subheader("Optional empirical action-effect calibration")
    st.write("Upload a CSV with columns `action,observed_mitigation_fraction`, where action is Monitor/Mitigate/Escalate (or monitor/rate_limit/isolate) and the fraction is an observed, documented mitigation proportion from comparable experiments. Do not upload invented values and label them empirical.")
    calibration_upload = st.file_uploader("Empirical action-effect calibration CSV (optional)", type=["csv"], key="action_calibration_csv")
    calibration_factors = {}
    if calibration_upload is not None:
        try:
            calibration_factors, calibration_table, calibration_note = parse_action_calibration(calibration_upload)
            st.dataframe(calibration_table.round(5), use_container_width=True, hide_index=True)
            st.caption(calibration_note)
        except Exception as exc:
            st.error(f"Calibration file was not applied: {exc}")
            calibration_factors = {}
    if st.button("Train policy and run held-out paired evaluation", type="primary", use_container_width=True):
        with st.spinner("Training Q-learning on training scenarios, freezing the policy, and evaluating on held-out scenarios..."):
            q = train_q_policy(seed + 7_000_001, episodes, steps, weights, alpha, gamma, epsilon)
            detail, wide = evaluate(seed + 19_000_003, n_runs, n_per_run, q, calibration_factors=calibration_factors)
            summary, run_means = summarize_runs(wide)
            config = {"seed": seed, "independent_test_runs": n_runs, "scenarios_per_run": n_per_run,
                      "training_episodes": episodes, "steps_per_episode": steps, "alpha": alpha, "gamma": gamma,
                      "epsilon": epsilon, "reward_weights": weights, "baseline": "fixed-threshold policy",
                      "AO-LACCP policy": "state/action/reward/transition structure aligned to current original artifact MDP",
                      "policy_outcome_bridge": "new, assumed mapping from original actions to common outcome equations",
                      "mdp_transition_model": "original artifact configured state-only transition rows; not calibrated",
                      "sensitivity_analysis": "separate retraining and reevaluation across parameter variants",
                      "empirical_action_calibration_factors": calibration_factors,
                      "calibration_note": "No action-effect calibration applied unless a valid empirical CSV was uploaded"}
            st.session_state["eval_detail"] = detail
            st.session_state["eval_wide"] = wide
            st.session_state["eval_summary"] = summary
            st.session_state["eval_runs"] = run_means
            st.session_state["eval_q"] = q
            st.session_state["eval_config"] = config
    if "eval_summary" not in st.session_state:
        st.info("Set the protocol values, then run the held-out paired evaluation.")
        return
    detail = st.session_state["eval_detail"]
    wide = st.session_state["eval_wide"]
    summary = st.session_state["eval_summary"]
    run_means = st.session_state["eval_runs"]
    q = st.session_state["eval_q"]
    config = st.session_state["eval_config"]
    st.subheader("Learned Q-table — frozen before test evaluation")
    st.dataframe(q.round(4), use_container_width=True)
    st.subheader("Primary statistical summary")
    st.dataframe(summary.round(5), use_container_width=True, hide_index=True)
    st.caption("Negative AO-minus-baseline differences favor AO-LACCP only for metrics where lower is better. Action codes are categorical and are excluded from hypothesis tests.")
    st.subheader("Mean outcomes with 95% confidence intervals")
    means = []
    for metric, label in [("resulting_risk", "Risk"), ("simulated_latency_ms", "Simulated latency"), ("service_impact_proxy", "Service impact"), ("action_cost_proxy", "Action cost")]:
        for pol, name in [("Baseline", "Baseline"), ("AO-LACCP artifact-aligned Q-learning", "AO-LACCP artifact-aligned Q-learning")]:
            # Use independent run-level means for intervals; scenarios within a run are not treated as independent replicates.
            per_run = detail.loc[detail.policy == pol].groupby("run_id")[metric].mean().to_numpy(float)
            n_run = len(per_run)
            mean = float(per_run.mean())
            se = float(stats.sem(per_run)) if n_run > 1 else np.nan
            crit = float(stats.t.ppf(.975, n_run - 1)) if n_run > 1 else np.nan
            means.append({"Metric": label, "Policy": name, "Mean": mean,
                          "CI_low": mean - crit * se if n_run > 1 else np.nan,
                          "CI_high": mean + crit * se if n_run > 1 else np.nan})
    mean_df = pd.DataFrame(means)
    fig, ax = plt.subplots(figsize=(10, 4.5))
    metrics_labels = list(mean_df.Metric.drop_duplicates())
    x = np.arange(len(metrics_labels)); width = .36
    for j, pol in enumerate(["Baseline", "AO-LACCP artifact-aligned Q-learning"]):
        sub = mean_df[mean_df.Policy == pol].set_index("Metric").loc[metrics_labels]
        yerr = np.vstack([sub.Mean.to_numpy() - sub.CI_low.to_numpy(), sub.CI_high.to_numpy() - sub.Mean.to_numpy()])
        ax.bar(x + (j - .5) * width, sub.Mean, width, yerr=yerr, capsize=4, label=pol)
    ax.set_xticks(x); ax.set_xticklabels(metrics_labels, rotation=10); ax.set_ylabel("Mean (95% CI across independent runs)")
    ax.set_title("Descriptive policy outcomes with run-level 95% confidence intervals"); ax.legend(); ax.grid(axis="y", alpha=.25)
    fig.tight_layout(); st.pyplot(fig); plt.close(fig)
    st.subheader("Run-level paired differences with 95% confidence intervals")
    # Match each plotted outcome to its actual summary label. The summary uses
    # "Service-impact" and "Action-cost" (hyphens), so shorter labels such as
    # "Service impact" would return an empty DataFrame and make .iloc[0] fail.
    diff_metrics = [
        ("resulting_risk", "Risk (lower is better)"),
        ("simulated_latency_ms", "Simulated latency (ms; lower is better)"),
        ("service_impact_proxy", "Service-impact proxy (lower is better)"),
        ("action_cost_proxy", "Action-cost proxy (lower is better)"),
    ]
    fig, ax = plt.subplots(figsize=(10, 5))
    y_positions = np.arange(len(diff_metrics))
    for y, (metric, summary_label) in zip(y_positions, diff_metrics):
        matches = summary.loc[summary["Metric"].eq(summary_label)]
        if matches.empty:
            st.warning(
                f"Cannot plot paired differences for '{metric}': "
                f"summary row '{summary_label}' was not found. "
                f"Available metrics: {', '.join(summary['Metric'].astype(str).tolist())}"
            )
            continue
        row = matches.iloc[0]
        m = float(row["Mean run-level paired difference (AO - baseline)"])
        lo, hi = float(row["95% t CI low"]), float(row["95% t CI high"])
        if np.isfinite(m) and np.isfinite(lo) and np.isfinite(hi):
            ax.errorbar(m, y, xerr=[[max(0.0, m-lo)], [max(0.0, hi-m)]], fmt="o", capsize=4)
        else:
            ax.plot(m, y, "o")
            ax.annotate("CI unavailable", (m, y), xytext=(5, 5), textcoords="offset points", fontsize=8)
    ax.axvline(0, linestyle="--", linewidth=1); ax.set_yticks(y_positions); ax.set_yticklabels(["Risk", "Simulated latency", "Service impact", "Action cost"])
    ax.set_xlabel("AO-LACCP minus baseline (run-level mean difference)"); ax.set_title("Paired effects and 95% t confidence intervals")
    ax.grid(axis="x", alpha=.25); fig.tight_layout(); st.pyplot(fig); plt.close(fig)
    st.subheader("Paired outcome distributions")
    selected = st.selectbox("Select metric", ["resulting_risk", "simulated_latency_ms", "service_impact_proxy", "action_cost_proxy"])
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.boxplot([detail.loc[detail.policy == "Baseline", selected], detail.loc[detail.policy == "AO-LACCP artifact-aligned Q-learning", selected]], labels=["Baseline", "AO-LACCP artifact-aligned Q-learning"], showmeans=True)
    ax.set_ylabel(selected); ax.set_title("Held-out scenario outcome distributions"); ax.grid(axis="y", alpha=.25)
    fig.tight_layout(); st.pyplot(fig); plt.close(fig)
    st.subheader("Hypothesis-testing comparison graphs")
    st.caption("Only quantitative modeled outcomes are plotted here. Cryptographic suite switching is measured separately by executing real RSA/ECDSA operations; it is not inferred from action codes.")
    chart_specs = [
        ("resulting_risk", "Cyber risk comparison", "Risk score (lower is better)"),
        ("simulated_latency_ms", "Response latency comparison", "Simulated latency (ms; lower is better)"),
    ]
    for metric, title, ylabel in chart_specs:
        plot_df = detail.groupby(["run_id", "policy"])[metric].mean().reset_index()
        fig, ax = plt.subplots(figsize=(8, 4))
        data = [plot_df.loc[plot_df.policy == pol, metric].to_numpy(float)
                for pol in ["Baseline", "AO-LACCP artifact-aligned Q-learning"]]
        ax.boxplot(data, labels=["Baseline", "AO-LACCP artifact-aligned Q-learning"], showmeans=True)
        ax.set_title(title + " (independent run means)")
        ax.set_ylabel(ylabel)
        ax.grid(axis="y", alpha=.25)
        fig.tight_layout(); st.pyplot(fig); plt.close(fig)

    st.subheader("Policy action selection counts (descriptive only)")
    action_counts = detail.groupby(["policy", "selected_action"]).size().rename("Scenario count").reset_index()
    action_counts["Share within policy"] = action_counts["Scenario count"] / action_counts.groupby("policy")["Scenario count"].transform("sum")
    st.dataframe(action_counts, use_container_width=True, hide_index=True)

    st.subheader("Repeated-measures ANOVA results")
    st.write("Because both policies receive the same scenarios, an independent-groups one-way ANOVA would ignore pairing. For two policies, the appropriate repeated-measures ANOVA test is equivalent to the paired t-test on independent run-level means (F = t²).")
    anova_table = paired_repeated_measures_anova(detail)
    st.dataframe(anova_table.round(5), use_container_width=True, hide_index=True)

    st.subheader("Exploratory regression analysis (R²)")
    st.write("This OLS model describes how scenario inputs relate to the paired AO-minus-baseline cyber-risk difference. R² is descriptive, not proof of causality or model validity; coefficients and fit depend on the assumed synthetic outcome model.")
    reg_table, reg_r2 = exploratory_risk_regression(detail, wide)
    rcol1, rcol2 = st.columns([1, 2])
    with rcol1:
        st.metric("Exploratory R²", f"{reg_r2:.4f}" if np.isfinite(reg_r2) else "Unavailable")
    with rcol2:
        st.dataframe(reg_table.round(6), use_container_width=True, hide_index=True)

    st.subheader("Markov decision process (MDP)")
    st.markdown("The tabular Q-learning policy now uses an explicit action-dependent synthetic transition rule. The transition probabilities are assumed for demonstration and must be justified or calibrated before dissertation claims. The crypto-pressure band is modelled as an external condition, not as cryptographic posture.")
    transition_table = mdp_transition_table(transition_mix=1.0)
    st.dataframe(transition_table.round(3), use_container_width=True, hide_index=True)

    st.subheader("Optimal policy derived from the learned Q-table")
    optimal = q.copy()
    optimal["Optimal action"] = [str(q.loc[idx].idxmax()) for idx in q.index]
    optimal["Best estimated Q-value"] = [float(q.loc[idx].max()) for idx in q.index]
    st.dataframe(optimal.round(4), use_container_width=True)
    st.caption("The optimal action is optimal only relative to this declared synthetic MDP, reward function, and training setup; it is not established as globally optimal for real financial systems.")

    st.subheader("Policy-to-artifact alignment audit")
    st.markdown("The current original framework code uses three states (Low/Medium/High), three actions (Monitor/Mitigate/Escalate), transition rows Low=[0.70, 0.25, 0.05], Medium=[0.30, 0.50, 0.20], High=[0.10, 0.40, 0.50], and rewards +10/+20/+30 for the matching state/action, otherwise -5. The evaluation reproduces that MDP structure. These transitions are sourced from the code, not empirically calibrated. The original artifact does not connect these actions to separately generated risk/latency/agility values. This app adds an explicit action-to-outcome bridge; therefore the outcome comparison is not a direct validation of the original dashboard's metric generation. Upload comparable observed mitigation data to calibrate action-effect multipliers; absent such data, values remain assumptions.")
    st.dataframe(mdp_transition_table(1.0), use_container_width=True, hide_index=True)

    st.subheader("Genuine sensitivity analysis: retrain and rerun")
    st.caption("Each row retrains the Q policy and reruns the paired held-out evaluation under a different transition or outcome-model assumption. These are stress tests, not empirical calibration.")
    if st.button("Run sensitivity analysis (7 complete reruns)", use_container_width=True):
        with st.spinner("Retraining and reevaluating all sensitivity conditions..."):
            sens = run_sensitivity_analysis(seed + 303_001, episodes, steps, weights, alpha, gamma, epsilon,
                                            min(n_runs, 20), min(n_per_run, 150), calibration_factors)
            st.session_state["eval_sensitivity"] = sens
    if "eval_sensitivity" in st.session_state:
        sens = st.session_state["eval_sensitivity"]
        st.dataframe(sens.round(5), use_container_width=True, hide_index=True)
        fig, ax = plt.subplots(figsize=(10, 4.5))
        ax.bar(sens["Sensitivity condition"], sens["Mean paired risk difference (AO - baseline)"])
        ax.axhline(0, linestyle="--", linewidth=1)
        ax.set_ylabel("Mean paired risk difference (AO - baseline)")
        ax.set_title("Sensitivity of risk comparison to assumed parameters")
        ax.tick_params(axis="x", labelrotation=25); ax.grid(axis="y", alpha=.25); fig.tight_layout()
        st.pyplot(fig); plt.close(fig)
        st.download_button("Download sensitivity analysis CSV", sens.to_csv(index=False).encode(),
                            "ao_laccp_sensitivity_analysis.csv", "text/csv")

    st.subheader("Real cryptographic operation and switching benchmark (RSA/ECDSA/Hybrid)")
    st.warning("This separate test performs actual cryptographic signing/verification and measures suite transitions in a generated event sequence. The original AO-LACCP dashboard currently exposes a static crypto-model selector and does not implement or log dynamic switching. This benchmark therefore measures a test harness, not original-artifact behavior; PQC is not included.")
    if st.button("Run real cryptographic switching benchmark", use_container_width=True):
        with st.spinner("Executing RSA/ECDSA/Hybrid signing and verification operations..."):
            crypto_trace, crypto_summary, crypto_note = benchmark_real_crypto_switching(seed + 404_001, 30)
            st.session_state["crypto_trace"] = crypto_trace
            st.session_state["crypto_summary"] = crypto_summary
            st.session_state["crypto_note"] = crypto_note
    if "crypto_summary" in st.session_state:
        st.dataframe(st.session_state["crypto_summary"].round(5), use_container_width=True, hide_index=True)
        st.caption(st.session_state["crypto_note"])
        crypto_trace = st.session_state["crypto_trace"]
        st.dataframe(crypto_trace.round(5), use_container_width=True, hide_index=True)
        fig, ax = plt.subplots(figsize=(9, 3.5))
        ax.step(crypto_trace["event_id"], crypto_trace["suite_changed_from_previous_event"].astype(int), where="mid")
        ax.set_yticks([0, 1], labels=["No switch", "Switch"])
        ax.set_xlabel("Event number"); ax.set_title("Observed cryptographic suite changes in the benchmark trace")
        ax.grid(axis="x", alpha=.25); fig.tight_layout(); st.pyplot(fig); plt.close(fig)
        st.download_button("Download cryptographic operation trace CSV",
                            st.session_state["crypto_trace"].to_csv(index=False).encode(),
                            "ao_laccp_crypto_switch_trace.csv", "text/csv")

    st.subheader("Independent run-level results (not a sensitivity analysis)")
    st.dataframe(run_means.round(5), use_container_width=True, hide_index=True)
    st.warning("This run-to-run table measures variability, not parameter sensitivity. A true sensitivity analysis must rerun the complete evaluation under predeclared alternative transition probabilities, action-effectiveness values, scenario distributions, and reward weights.")
    st.subheader("Reproducibility record")
    config_json = json.dumps(config, indent=2, sort_keys=True)
    st.code(config_json, language="json")
    st.write("Configuration SHA-256:", hashlib.sha256(config_json.encode("utf-8")).hexdigest())
    st.download_button("Download detailed scenario results CSV", detail.to_csv(index=False).encode(), "ao_laccp_validation_detailed.csv", "text/csv")
    st.download_button("Download paired outcomes CSV", wide.to_csv(index=False).encode(), "ao_laccp_validation_paired.csv", "text/csv")
    st.download_button("Download statistical summary CSV", summary.to_csv(index=False).encode(), "ao_laccp_validation_statistics.csv", "text/csv")
    st.warning("The MDP logic is aligned to the current original code, but its outputs are not directly linked to the original dashboard metrics. The action-effect bridge remains assumed; sensitivity results test robustness to assumptions but do not calibrate them. The crypto benchmark executes RSA/ECDSA/Hybrid operations in a separate harness; it does not establish original-artifact switching or PQC agility.")

if __name__ == "__main__":
    main()
