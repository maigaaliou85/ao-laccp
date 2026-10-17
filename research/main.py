from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from typing import Dict, List, Tuple

import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from scipy import stats

try:
    from cryptography.hazmat.primitives.asymmetric import rsa, ec, padding
    from cryptography.hazmat.primitives import hashes

    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


# ============================================================
# STREAMLIT CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AO-LACCP Scientific Paired Evaluation",
    page_icon="🛡️",
    layout="wide",
)


# ============================================================
# MODEL CONFIGURATION
# ============================================================

ACTIONS = ("Monitor", "Mitigate", "Escalate")

ACTION_MAP = {
    "Monitor": "monitor",
    "Mitigate": "rate_limit",
    "Escalate": "isolate",
}

ACTION_COST = {
    "monitor": 0.00,
    "rate_limit": 0.12,
    "isolate": 0.32,
}

ACTION_LATENCY_MS = {
    "monitor": 2.0,
    "rate_limit": 8.0,
    "isolate": 18.0,
}

ACTION_MITIGATION = {
    "monitor": 0.04,
    "rate_limit": 0.22,
    "isolate": 0.52,
}

THREAT_TYPES = (
    "benign",
    "brute_force",
    "phishing",
    "data_exfiltration",
    "mitm",
    "zero_day",
)

THREAT_PROBS = np.array(
    [0.28, 0.18, 0.16, 0.14, 0.13, 0.11]
)

PERSISTENCE = {
    "benign": 0.10,
    "brute_force": 0.72,
    "phishing": 0.66,
    "data_exfiltration": 0.82,
    "mitm": 0.78,
    "zero_day": 0.88,
}

ACTION_MATCH = {
    "benign": {
        "monitor": 0.75,
        "rate_limit": 0.60,
        "isolate": 0.45,
    },
    "brute_force": {
        "monitor": 0.08,
        "rate_limit": 0.82,
        "isolate": 0.90,
    },
    "phishing": {
        "monitor": 0.12,
        "rate_limit": 0.35,
        "isolate": 0.70,
    },
    "data_exfiltration": {
        "monitor": 0.05,
        "rate_limit": 0.50,
        "isolate": 0.92,
    },
    "mitm": {
        "monitor": 0.08,
        "rate_limit": 0.25,
        "isolate": 0.78,
    },
    "zero_day": {
        "monitor": 0.08,
        "rate_limit": 0.25,
        "isolate": 0.80,
    },
}

# Illustrative state-only transition probabilities.
# They are assumptions unless empirically calibrated.
ARTIFACT_TRANSITIONS = {
    "Low": np.array([0.70, 0.25, 0.05]),
    "Medium": np.array([0.30, 0.50, 0.20]),
    "High": np.array([0.10, 0.40, 0.50]),
}

ARTIFACT_REWARDS = {
    ("Low", "Monitor"): 10.0,
    ("Medium", "Mitigate"): 20.0,
    ("High", "Escalate"): 30.0,
}

BASE_REWARD_FALLBACK = -5.0

POLICY_BASELINE = "Baseline"
POLICY_AO = "AO-LACCP Q-learning"


# ============================================================
# SCENARIO STRUCTURE
# ============================================================

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


def clip01(value: float) -> float:
    """Restrict a numeric value to the interval [0, 1]."""
    return float(np.clip(value, 0.0, 1.0))


# ============================================================
# SYNTHETIC SCENARIO GENERATION
# ============================================================

def generate_scenarios(
    seed: int,
    run_id: int,
    n: int,
) -> List[Scenario]:
    """Generate synthetic scenarios using declared distributions."""

    rng = np.random.default_rng(seed)

    severity_ranges = {
        "benign": (0.02, 0.22),
        "brute_force": (0.45, 0.95),
        "phishing": (0.35, 0.88),
        "data_exfiltration": (0.55, 0.98),
        "mitm": (0.48, 0.96),
        "zero_day": (0.60, 1.00),
    }

    scenarios = []

    for i in range(n):

        threat = str(
            rng.choice(THREAT_TYPES, p=THREAT_PROBS)
        )

        low, high = severity_ranges[threat]

        severity = float(
            rng.uniform(low, high)
        )

        initial_risk = clip01(
            0.45 * severity
            + 0.25 * rng.beta(2.0, 2.2)
            + 0.15
        )

        threat_signal = clip01(
            0.72 * severity
            + rng.normal(0, 0.12)
        )

        crypto_pressure = clip01(
            (
                0.75
                if threat in ("mitm", "zero_day")
                else 0.25
            )
            + rng.normal(0, 0.15)
        )

        scenarios.append(
            Scenario(
                run_id=run_id,
                scenario_id=i,
                threat_type=threat,
                threat_severity=severity,
                initial_risk=initial_risk,
                workload=float(
                    rng.uniform(0.20, 1.0)
                ),
                network_load=float(
                    rng.uniform(0.15, 1.0)
                ),
                network_noise=float(
                    rng.normal(0, 1)
                ),
                threat_signal=threat_signal,
                crypto_pressure=crypto_pressure,
                service_capacity=float(
                    rng.uniform(0.75, 1.0)
                ),
            )
        )

    return scenarios


# ============================================================
# STATE MAPPING AND BASELINE POLICY
# ============================================================

def state_of(scenario: Scenario) -> str:
    """Map scenario characteristics to Low, Medium, or High."""

    risk_proxy = clip01(
        0.55 * scenario.initial_risk
        + 0.30 * scenario.threat_signal
        + 0.15 * scenario.threat_severity
    )

    if risk_proxy < 0.35:
        return "Low"

    if risk_proxy < 0.65:
        return "Medium"

    return "High"


def baseline_policy(scenario: Scenario) -> str:
    """
    Fixed-threshold comparator.

    This is an explicitly defined research baseline,
    not a claim to represent every production SOC.
    """

    if (
        scenario.initial_risk >= 0.72
        or scenario.threat_signal >= 0.82
    ):
        return "Escalate"

    if scenario.threat_signal >= 0.58:
        return "Mitigate"

    return "Monitor"


# ============================================================
# SHARED SYNTHETIC OUTCOME MODEL
# ============================================================

def outcome(
    scenario: Scenario,
    action_name: str,
    effectiveness_scale: float = 1.0,
    noise_scale: float = 1.0,
    calibration_factors: Dict[str, float] | None = None,
) -> Dict[str, float]:
    """
    Calculate modeled outcomes for either policy.

    These equations are assumptions. They are not empirically
    validated unless supported by suitable calibration data.
    """

    action = ACTION_MAP[action_name]

    calibration_factors = calibration_factors or {}

    factor = float(
        calibration_factors.get(action, 1.0)
    )

    mitigation = np.clip(
        ACTION_MITIGATION[action]
        * ACTION_MATCH[scenario.threat_type][action]
        * effectiveness_scale
        * factor,
        0.0,
        0.95,
    )

    disturbance = (
        0.035
        * scenario.network_noise
        * noise_scale
        + 0.045
        * max(0.0, scenario.network_load - 0.70)
        + 0.035 * scenario.workload
    )

    residual_threat = (
        scenario.threat_severity
        * PERSISTENCE[scenario.threat_type]
        * (1.0 - mitigation)
    )

    risk = clip01(
        0.48 * scenario.initial_risk
        + 0.44 * residual_threat
        + disturbance
    )

    base_latency = (
        35.0
        + 85.0 * scenario.network_load
        + 42.0 * scenario.workload
        + 18.0
        * (
            1.0
            / max(scenario.service_capacity, 0.50)
            - 1.0
        )
        + 2.5 * scenario.network_noise
    )

    latency = max(
        1.0,
        base_latency
        + ACTION_LATENCY_MS[action]
        + 18.0 * ACTION_COST[action],
    )

    service_impact = clip01(
        0.10 * scenario.workload
        + 0.42 * ACTION_COST[action]
        + 0.10
        * max(
            0.0,
            scenario.network_load
            - scenario.service_capacity,
        )
    )

    return {
        "resulting_risk": risk,
        "simulated_latency_ms": latency,
        "service_impact_proxy": service_impact,
        "action_cost_proxy": ACTION_COST[action],
        "residual_threat_proxy": residual_threat,
    }


# ============================================================
# Q-LEARNING
# ============================================================

def reward_for(
    state: str,
    action: str,
    reward_scale: float = 1.0,
) -> float:

    return float(
        ARTIFACT_REWARDS.get(
            (state, action),
            BASE_REWARD_FALLBACK,
        )
        * reward_scale
    )


def mdp_transition(
    state: str,
    rng: np.random.Generator,
    transition_mix: float = 1.0,
) -> str:
    """
    Sample the next state from the declared transition row.

    IMPORTANT:
    Transitions depend on the current state, not on the action.
    """

    probabilities = ARTIFACT_TRANSITIONS[state].astype(float)

    uniform = np.ones(3) / 3.0

    mix = float(
        np.clip(transition_mix, 0.0, 1.0)
    )

    probabilities = (
        mix * probabilities
        + (1.0 - mix) * uniform
    )

    probabilities /= probabilities.sum()

    return str(
        rng.choice(
            ["Low", "Medium", "High"],
            p=probabilities,
        )
    )


def train_q_policy(
    seed: int,
    episodes: int,
    steps_per_episode: int,
    alpha: float,
    gamma: float,
    epsilon: float,
    transition_mix: float = 1.0,
) -> pd.DataFrame:
    """Train a tabular Q-learning policy."""

    rng = np.random.default_rng(seed)

    states = ["Low", "Medium", "High"]

    q = pd.DataFrame(
        0.0,
        index=states,
        columns=ACTIONS,
    )

    for _ in range(episodes):

        state = str(
            rng.choice(states)
        )

        for _ in range(steps_per_episode):

            # Epsilon-greedy exploration during training.
            if rng.random() < epsilon:

                action = str(
                    rng.choice(ACTIONS)
                )

            else:

                values = q.loc[state].to_numpy(
                    dtype=float
                )

                best = np.flatnonzero(
                    np.isclose(
                        values,
                        values.max(),
                    )
                )

                action = ACTIONS[
                    int(rng.choice(best))
                ]

            reward = reward_for(
                state,
                action,
            )

            next_state = mdp_transition(
                state,
                rng,
                transition_mix,
            )

            old_value = float(
                q.loc[state, action]
            )

            q.loc[state, action] = (
                old_value
                + alpha
                * (
                    reward
                    + gamma
                    * float(q.loc[next_state].max())
                    - old_value
                )
            )

            state = next_state

    return q


def q_policy(
    scenario: Scenario,
    q: pd.DataFrame,
) -> str:
    """Choose the highest-Q-value action for the scenario state."""

    return str(
        q.loc[state_of(scenario)].idxmax()
    )


# ============================================================
# PAIRED EVALUATION
# ============================================================

def evaluate(
    seed: int,
    n_runs: int,
    n_per_run: int,
    q: pd.DataFrame,
    effectiveness_scale: float = 1.0,
    noise_scale: float = 1.0,
    calibration_factors: Dict[str, float] | None = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Evaluate baseline and Q-learning on identical scenarios.

    The same scenario is passed to both policies. Pairing is
    verified before the detailed and wide dataframes are returned.
    """

    rows = []

    input_columns = [
        "threat_type",
        "threat_severity",
        "initial_risk",
        "workload",
        "network_load",
        "network_noise",
        "threat_signal",
        "crypto_pressure",
        "service_capacity",
    ]

    for run in range(1, n_runs + 1):

        scenarios = generate_scenarios(
            seed + run * 100_003,
            run,
            n_per_run,
        )

        for scenario in scenarios:

            policies = [
                (
                    POLICY_BASELINE,
                    baseline_policy(scenario),
                ),
                (
                    POLICY_AO,
                    q_policy(scenario, q),
                ),
            ]

            for policy_name, action in policies:

                modeled_outcome = outcome(
                    scenario,
                    action,
                    effectiveness_scale,
                    noise_scale,
                    calibration_factors,
                )

                rows.append(
                    {
                        **asdict(scenario),
                        "policy": policy_name,
                        "selected_action": action,
                        **modeled_outcome,
                    }
                )

    detail = pd.DataFrame(rows)

    keys = ["run_id", "scenario_id"]

    # Verify that both policies were evaluated for every scenario.
    policy_counts = (
        detail.groupby(keys)["policy"].nunique()
    )

    if not policy_counts.eq(2).all():
        raise RuntimeError(
            "Pairing check failed: every scenario must have both policies."
        )

    # Verify that paired scenarios have identical input values.
    for column in input_columns:

        counts = (
            detail.groupby(keys)[column].nunique()
        )

        if counts.max() != 1:
            raise RuntimeError(
                f"Pairing check failed for input: {column}"
            )

    metrics = [
        "resulting_risk",
        "simulated_latency_ms",
        "service_impact_proxy",
        "action_cost_proxy",
    ]

    wide = detail.pivot(
        index=keys,
        columns="policy",
        values=metrics,
    )

    wide.columns = [
        f"{metric}__{policy}"
        for metric, policy in wide.columns
    ]

    wide = wide.reset_index()

    for metric in metrics:

        ao_col = f"{metric}__{POLICY_AO}"
        baseline_col = f"{metric}__{POLICY_BASELINE}"

        wide[
            f"{metric}__diff_AO_minus_baseline"
        ] = wide[ao_col] - wide[baseline_col]

    return detail, wide


# ============================================================
# STATISTICAL ANALYSIS
# ============================================================

def holm_adjust(
    p_values: List[float],
) -> List[float]:
    """Holm step-down correction for multiple hypothesis tests."""

    p = np.asarray(
        p_values,
        dtype=float,
    )

    adjusted = np.full(
        len(p),
        np.nan,
    )

    valid = np.flatnonzero(
        np.isfinite(p)
    )

    if len(valid) == 0:
        return adjusted.tolist()

    order = valid[
        np.argsort(p[valid])
    ]

    running_max = 0.0
    number_tests = len(order)

    for rank, index in enumerate(order):

        corrected = min(
            1.0,
            (number_tests - rank) * p[index],
        )

        running_max = max(
            running_max,
            corrected,
        )

        adjusted[index] = running_max

    return adjusted.tolist()


def summarize_runs(
    wide: pd.DataFrame,
) -> pd.DataFrame:
    """
    Perform inference on independent run-level paired differences.

    Scenarios within a run are not treated as independent replicates.
    """

    metric_definitions = [
        (
            "resulting_risk",
            "Risk (lower is better)",
        ),
        (
            "simulated_latency_ms",
            "Simulated latency (ms; lower is better)",
        ),
        (
            "service_impact_proxy",
            "Service-impact proxy (lower is better)",
        ),
        (
            "action_cost_proxy",
            "Action-cost proxy (lower is better)",
        ),
    ]

    difference_columns = [
        f"{metric}__diff_AO_minus_baseline"
        for metric, _ in metric_definitions
    ]

    run_means = (
        wide.groupby("run_id")[difference_columns]
        .mean()
        .reset_index()
    )

    rows = []
    raw_p_values = []

    for metric, label in metric_definitions:

        differences = run_means[
            f"{metric}__diff_AO_minus_baseline"
        ].to_numpy(dtype=float)

        n = len(differences)

        mean_difference = float(
            np.mean(differences)
        )

        sd = (
            float(np.std(differences, ddof=1))
            if n > 1
            else np.nan
        )

        se = (
            sd / np.sqrt(n)
            if n > 1
            else np.nan
        )

        critical = (
            float(stats.t.ppf(0.975, n - 1))
            if n > 1
            else np.nan
        )

        if n > 1:

            ci_low = (
                mean_difference
                - critical * se
            )

            ci_high = (
                mean_difference
                + critical * se
            )

        else:

            ci_low = np.nan
            ci_high = np.nan

        if n > 1 and sd > 0:

            t_statistic, p_value = (
                stats.ttest_1samp(
                    differences,
                    0.0,
                )
            )

            cohens_dz = mean_difference / sd

        else:

            t_statistic = np.nan
            p_value = np.nan
            cohens_dz = np.nan

        # Bootstrap the independent run-level differences.
        if n > 1:

            rng = np.random.default_rng(
                81_000 + len(rows)
            )

            bootstrap_means = np.mean(
                rng.choice(
                    differences,
                    size=(10_000, n),
                    replace=True,
                ),
                axis=1,
            )

            bootstrap_low, bootstrap_high = (
                np.quantile(
                    bootstrap_means,
                    [0.025, 0.975],
                )
            )

        else:

            bootstrap_low = np.nan
            bootstrap_high = np.nan

        raw_p_values.append(
            float(p_value)
            if np.isfinite(p_value)
            else np.nan
        )

        rows.append(
            {
                "Metric": label,
                "Independent runs (N)": n,
                "Mean paired difference (AO - baseline)": mean_difference,
                "95% t CI low": ci_low,
                "95% t CI high": ci_high,
                "95% run-bootstrap CI low": bootstrap_low,
                "95% run-bootstrap CI high": bootstrap_high,
                "Run-level Cohen dz": cohens_dz,
                "Paired run-level t statistic": t_statistic,
                "Raw p-value": p_value,
            }
        )

    adjusted_p_values = holm_adjust(
        raw_p_values
    )

    for row, adjusted_p in zip(
        rows,
        adjusted_p_values,
    ):
        row["Holm-adjusted p-value"] = adjusted_p

    return pd.DataFrame(rows)


def repeated_measures_results(
    detail: pd.DataFrame,
) -> pd.DataFrame:
    """
    For two paired policy conditions, repeated-measures ANOVA
    is equivalent to a paired t-test, with F = t squared.
    """

    rows = []

    for metric, label in [
        ("resulting_risk", "Cyber risk"),
        ("simulated_latency_ms", "Simulated latency"),
    ]:

        run_means = (
            detail.groupby(
                ["run_id", "policy"]
            )[metric]
            .mean()
            .unstack("policy")
        )

        if (
            POLICY_BASELINE not in run_means.columns
            or POLICY_AO not in run_means.columns
        ):
            continue

        paired = run_means[
            [POLICY_BASELINE, POLICY_AO]
        ].dropna()

        if len(paired) < 2:
            continue

        t_statistic, p_value = stats.ttest_rel(
            paired[POLICY_AO],
            paired[POLICY_BASELINE],
        )

        rows.append(
            {
                "Outcome": label,
                "Independent run pairs": len(paired),
                "F statistic": float(t_statistic ** 2),
                "df1": 1,
                "df2": len(paired) - 1,
                "p-value": float(p_value),
                "Note": (
                    "Run-level paired test on synthetic modeled outcomes."
                ),
            }
        )

    return pd.DataFrame(rows)


def exploratory_risk_regression(
    detail: pd.DataFrame,
    wide: pd.DataFrame,
) -> Tuple[pd.DataFrame, float]:
    """
    Exploratory OLS fit for paired scenario-level risk differences.

    This descriptive model is not a causal analysis. Its R-squared
    does not establish scientific validity of the simulator.
    """

    baseline_inputs = detail.loc[
        detail["policy"] == POLICY_BASELINE,
        [
            "run_id",
            "scenario_id",
            "threat_severity",
            "initial_risk",
            "workload",
            "network_load",
            "threat_signal",
            "crypto_pressure",
        ],
    ].copy()

    differences = wide[
        [
            "run_id",
            "scenario_id",
            "resulting_risk__diff_AO_minus_baseline",
        ]
    ]

    data = baseline_inputs.merge(
        differences,
        on=["run_id", "scenario_id"],
        validate="one_to_one",
    ).dropna()

    features = [
        "threat_severity",
        "initial_risk",
        "workload",
        "network_load",
        "threat_signal",
        "crypto_pressure",
    ]

    x = data[features].to_numpy(dtype=float)

    x = np.column_stack(
        [np.ones(len(x)), x]
    )

    y = data[
        "resulting_risk__diff_AO_minus_baseline"
    ].to_numpy(dtype=float)

    coefficients, *_ = np.linalg.lstsq(
        x,
        y,
        rcond=None,
    )

    predictions = x @ coefficients

    residual_ss = float(
        np.sum((y - predictions) ** 2)
    )

    total_ss = float(
        np.sum((y - y.mean()) ** 2)
    )

    r_squared = (
        float(1.0 - residual_ss / total_ss)
        if total_ss > 0
        else float("nan")
    )

    table = pd.DataFrame(
        {
            "Term": ["Intercept"] + features,
            "Coefficient": coefficients,
        }
    )

    return table, r_squared


# ============================================================
# OPTIONAL EMPIRICAL CALIBRATION
# ============================================================

def parse_calibration_csv(
    uploaded_file,
) -> Tuple[Dict[str, float], pd.DataFrame, str]:
    """
    Expected columns:
        action, observed_mitigation_fraction

    Actions:
        Monitor / Mitigate / Escalate
        or monitor / rate_limit / isolate

    Only use documented, comparable observations.
    """

    df = pd.read_csv(uploaded_file)

    required = {
        "action",
        "observed_mitigation_fraction",
    }

    if not required.issubset(df.columns):
        raise ValueError(
            "CSV must contain action and observed_mitigation_fraction."
        )

    df = df.copy()

    df["observed_mitigation_fraction"] = pd.to_numeric(
        df["observed_mitigation_fraction"],
        errors="coerce",
    )

    values = df[
        "observed_mitigation_fraction"
    ]

    if (
        values.isna().any()
        or not values.between(0, 1).all()
    ):
        raise ValueError(
            "Mitigation fractions must be numeric values from 0 to 1."
        )

    action_mapping = {
        "monitor": "monitor",
        "mitigate": "rate_limit",
        "rate_limit": "rate_limit",
        "escalate": "isolate",
        "isolate": "isolate",
    }

    df["action_normalized"] = (
        df["action"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map(action_mapping)
    )

    if df["action_normalized"].isna().any():
        raise ValueError(
            "Unrecognized action. Use Monitor, Mitigate, Escalate, "
            "monitor, rate_limit, or isolate."
        )

    grouped = (
        df.groupby("action_normalized")[
            "observed_mitigation_fraction"
        ]
        .agg(["mean", "std", "count"])
        .reset_index()
    )

    factors = {}

    for _, row in grouped.iterrows():

        action = row["action_normalized"]

        factors[action] = float(
            row["mean"]
            / max(ACTION_MITIGATION[action], 1e-9)
        )

    note = (
        "Calibration factors depend on the quality and comparability "
        "of uploaded observations. This process does not calibrate "
        "transition probabilities or latency."
    )

    return factors, grouped, note


# ============================================================
# SENSITIVITY ANALYSIS
# ============================================================

def run_sensitivity_analysis(
    seed: int,
    episodes: int,
    steps: int,
    alpha: float,
    gamma: float,
    epsilon: float,
    n_runs: int,
    n_per_run: int,
    calibration_factors: Dict[str, float] | None,
) -> pd.DataFrame:
    """Retrain and reevaluate for each declared parameter variant."""

    variants = [
        ("Reference assumptions", 1.00, 1.00, 1.00),
        ("Transition rows 50% toward uniform", 0.50, 1.00, 1.00),
        ("Transition rows fully uniform", 0.00, 1.00, 1.00),
        ("Action effectiveness -25%", 1.00, 0.75, 1.00),
        ("Action effectiveness +25%", 1.00, 1.25, 1.00),
        ("Network-noise effect -25%", 1.00, 1.00, 0.75),
        ("Network-noise effect +25%", 1.00, 1.00, 1.25),
    ]

    results = []

    # Reuse test scenario seeds across conditions for comparability.
    common_test_seed = seed + 202_000

    for index, (
        label,
        transition_mix,
        effectiveness_scale,
        noise_scale,
    ) in enumerate(variants):

        q = train_q_policy(
            seed + 101_000 + index * 17,
            episodes,
            steps,
            alpha,
            gamma,
            epsilon,
            transition_mix=transition_mix,
        )

        _, wide = evaluate(
            common_test_seed,
            n_runs,
            n_per_run,
            q,
            effectiveness_scale=effectiveness_scale,
            noise_scale=noise_scale,
            calibration_factors=calibration_factors,
        )

        run_differences = (
            wide.groupby("run_id")[
                [
                    "resulting_risk__diff_AO_minus_baseline",
                    "simulated_latency_ms__diff_AO_minus_baseline",
                ]
            ]
            .mean()
        )

        risk_difference = float(
            run_differences[
                "resulting_risk__diff_AO_minus_baseline"
            ].mean()
        )

        latency_difference = float(
            run_differences[
                "simulated_latency_ms__diff_AO_minus_baseline"
            ].mean()
        )

        results.append(
            {
                "Sensitivity condition": label,
                "Transition mix": transition_mix,
                "Action-effect scale": effectiveness_scale,
                "Network-noise scale": noise_scale,
                "Mean risk difference (AO - baseline)": risk_difference,
                "Mean latency difference ms (AO - baseline)": latency_difference,
                "Risk direction favors AO?": risk_difference < 0,
                "Latency direction favors AO?": latency_difference < 0,
            }
        )

    return pd.DataFrame(results)


# ============================================================
# SEPARATE RSA/ECDSA BENCHMARK
# ============================================================

def benchmark_crypto(
    seed: int,
    n_events: int = 30,
) -> Tuple[pd.DataFrame, pd.DataFrame, str]:
    """
    Execute real RSA/ECDSA signing and verification.

    This separate test harness does not validate original-dashboard
    switching behavior and does not test post-quantum cryptography.
    """

    if not CRYPTO_AVAILABLE:

        return (
            pd.DataFrame(),
            pd.DataFrame(),
            "The cryptography package is unavailable.",
        )

    rng = np.random.default_rng(seed)

    events = []

    for i in range(n_events):

        pressure = float(
            rng.random()
        )

        threat = str(
            rng.choice(
                ["benign", "brute_force", "mitm", "zero_day"]
            )
        )

        if threat in ("mitm", "zero_day") or pressure >= 0.70:
            suite = "Hybrid (RSA+ECDSA)"

        elif pressure >= 0.35:
            suite = "ECDSA"

        else:
            suite = "RSA"

        events.append(
            {
                "event_id": i + 1,
                "threat_type": threat,
                "crypto_pressure": pressure,
                "selected_suite": suite,
            }
        )

    rsa_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    ec_key = ec.generate_private_key(
        ec.SECP256R1()
    )

    payload = b"AO-LACCP crypto benchmark payload"

    rows = []
    previous_suite = None

    for event in events:

        suite = event["selected_suite"]

        switched = (
            previous_suite is not None
            and suite != previous_suite
        )

        start = time.perf_counter()

        success = True

        try:

            if suite in ("RSA", "Hybrid (RSA+ECDSA)"):

                signature = rsa_key.sign(
                    payload,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH,
                    ),
                    hashes.SHA256(),
                )

                rsa_key.public_key().verify(
                    signature,
                    payload,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH,
                    ),
                    hashes.SHA256(),
                )

            if suite in ("ECDSA", "Hybrid (RSA+ECDSA)"):

                signature = ec_key.sign(
                    payload,
                    ec.ECDSA(hashes.SHA256()),
                )

                ec_key.public_key().verify(
                    signature,
                    payload,
                    ec.ECDSA(hashes.SHA256()),
                )

        except Exception:
            success = False

        elapsed_ms = (
            time.perf_counter() - start
        ) * 1000.0

        rows.append(
            {
                **event,
                "suite_changed_from_previous_event": switched,
                "operation_success": success,
                "sign_verify_elapsed_ms": elapsed_ms,
                "operations_performed": (
                    4
                    if suite == "Hybrid (RSA+ECDSA)"
                    else 2
                ),
            }
        )

        previous_suite = suite

    trace = pd.DataFrame(rows)

    switch_count = int(
        trace["suite_changed_from_previous_event"].sum()
    )

    summary = pd.DataFrame(
        [
            {
                "Events": len(trace),
                "Suite transitions observed": switch_count,
                "Transition rate": (
                    switch_count / max(1, len(trace) - 1)
                ),
                "Successful events": int(
                    trace["operation_success"].sum()
                ),
                "Operation success rate": float(
                    trace["operation_success"].mean()
                ),
                "Mean operation time ms": float(
                    trace["sign_verify_elapsed_ms"].mean()
                ),
                "PQC tested": False,
            }
        ]
    )

    note = (
        "This is a separate benchmark using real RSA-2048 and ECDSA P-256 "
        "operations. The suite-selection rule is illustrative. It does not "
        "prove dynamic switching in the original dashboard, and PQC is not tested."
    )

    return trace, summary, note


# ============================================================
# CHARTS
# ============================================================

def make_outcome_plot(
    detail: pd.DataFrame,
) -> plt.Figure:

    metric_specs = [
        ("resulting_risk", "Cyber risk"),
        ("simulated_latency_ms", "Simulated latency (ms)"),
        ("service_impact_proxy", "Service impact proxy"),
        ("action_cost_proxy", "Action cost proxy"),
    ]

    fig, axes = plt.subplots(
        2,
        2,
        figsize=(12, 8),
    )

    for ax, (metric, title) in zip(
        axes.flat,
        metric_specs,
    ):

        values = [
            detail.loc[
                detail["policy"] == POLICY_BASELINE,
                metric,
            ].to_numpy(dtype=float),

            detail.loc[
                detail["policy"] == POLICY_AO,
                metric,
            ].to_numpy(dtype=float),
        ]

        ax.boxplot(
            values,
            labels=["Baseline", "AO-LACCP Q-learning"],
            showmeans=True,
        )

        ax.set_title(title)
        ax.grid(axis="y", alpha=0.25)

    fig.suptitle(
        "Held-out synthetic scenario outcome distributions"
    )

    fig.tight_layout()

    return fig


# ============================================================
# MAIN STREAMLIT APPLICATION
# ============================================================

def main() -> None:

    st.title(
        "🛡️ AO-LACCP: Scientific Paired Evaluation"
    )

    st.caption(
        "Synthetic research prototype | Reproducible paired comparisons "
        "| Not a production validation"
    )

    st.warning(
        "Results are conditional on synthetic scenarios and assumed outcome "
        "equations. They do not prove real-world banking, FinTech, or SOC superiority."
    )

    with st.expander(
        "Study protocol and limitations",
        expanded=True,
    ):

        st.markdown(
            """
**Evaluation design:** Q-learning is trained first and then frozen.
Both policies receive the same held-out synthetic scenario inputs.

**Baseline:** A declared fixed-threshold comparator, not a representation
of every production SOC.

**MDP:** Three states (Low, Medium, High), three actions
(Monitor, Mitigate, Escalate), configured state-only transition rows,
matching-action rewards of +10, +20, +30, and -5 otherwise.

**Outcome bridge:** The mapping from selected actions to risk, latency,
service-impact, and cost is an assumed evaluation model. It is not
established as the original dashboard's metric-generation logic.

**Statistics:** Primary confidence intervals and hypothesis tests use
independent run-level means and paired differences. Scenarios within
a run are not treated as independent replicates.

**Calibration:** Sensitivity analysis tests how findings respond to
assumptions; it does not itself calibrate the model.

**Cryptography:** The optional RSA/ECDSA benchmark is separate and does
not test PQC or prove switching in the original AO-LACCP dashboard.
"""
        )

    # --------------------------------------------------------
    # Evaluation parameters
    # --------------------------------------------------------

    st.subheader("Evaluation settings")

    c1, c2, c3 = st.columns(3)

    with c1:

        seed = int(
            st.number_input(
                "Random seed",
                min_value=0,
                max_value=2_000_000_000,
                value=20261017,
                step=1,
            )
        )

    with c2:

        n_runs = int(
            st.number_input(
                "Independent test runs",
                min_value=10,
                max_value=200,
                value=40,
                step=10,
            )
        )

    with c3:

        n_per_run = int(
            st.number_input(
                "Scenarios per run",
                min_value=25,
                max_value=2000,
                value=200,
                step=25,
            )
        )

    st.subheader("Q-learning training")

    a, b, c, d = st.columns(4)

    with a:

        episodes = int(
            st.number_input(
                "Training episodes",
                min_value=100,
                max_value=10000,
                value=1500,
                step=100,
            )
        )

    with b:

        steps = int(
            st.number_input(
                "Steps per episode",
                min_value=5,
                max_value=100,
                value=20,
                step=5,
            )
        )

    with c:

        alpha = float(
            st.slider(
                "Learning rate α",
                min_value=0.01,
                max_value=1.0,
                value=0.10,
                step=0.01,
            )
        )

    with d:

        gamma = float(
            st.slider(
                "Discount factor γ",
                min_value=0.0,
                max_value=0.99,
                value=0.80,
                step=0.01,
            )
        )

    epsilon = float(
        st.slider(
            "Exploration ε during training",
            min_value=0.01,
            max_value=1.0,
            value=0.15,
            step=0.01,
        )
    )

    # --------------------------------------------------------
    # Optional calibration upload
    # --------------------------------------------------------

    st.subheader(
        "Optional empirical action-effect calibration"
    )

    st.write(
        "Upload a CSV containing `action` and "
        "`observed_mitigation_fraction`. Use only documented observations "
        "measured under comparable conditions."
    )

    uploaded_file = st.file_uploader(
        "Calibration CSV (optional)",
        type=["csv"],
    )

    calibration_factors = {}

    if uploaded_file is not None:

        try:

            (
                calibration_factors,
                calibration_table,
                calibration_note,
            ) = parse_calibration_csv(
                uploaded_file
            )

            st.dataframe(
                calibration_table.round(5),
                use_container_width=True,
                hide_index=True,
            )

            st.caption(calibration_note)

        except Exception as exc:

            st.error(
                f"Calibration was not applied: {exc}"
            )

            calibration_factors = {}

    # --------------------------------------------------------
    # Train and evaluate
    # --------------------------------------------------------

    if st.button(
        "Train policy and run held-out evaluation",
        type="primary",
        use_container_width=True,
    ):

        with st.spinner(
            "Training Q-learning and evaluating paired scenarios..."
        ):

            q = train_q_policy(
                seed + 7_000_001,
                episodes,
                steps,
                alpha,
                gamma,
                epsilon,
            )

            detail, wide = evaluate(
                seed + 19_000_003,
                n_runs,
                n_per_run,
                q,
                calibration_factors=calibration_factors,
            )

            summary = summarize_runs(wide)

            config = {
                "seed": seed,
                "independent_test_runs": n_runs,
                "scenarios_per_run": n_per_run,
                "training_episodes": episodes,
                "steps_per_episode": steps,
                "alpha": alpha,
                "gamma": gamma,
                "epsilon": epsilon,
                "baseline": "fixed-threshold policy",
                "AO_policy": "tabular Q-learning on declared synthetic MDP",
                "outcome_model": "shared assumed synthetic outcome equations",
                "calibration_factors": calibration_factors,
                "PQC_tested": False,
            }

            st.session_state["detail"] = detail
            st.session_state["wide"] = wide
            st.session_state["summary"] = summary
            st.session_state["q"] = q
            st.session_state["config"] = config

            st.session_state.pop(
                "sensitivity",
                None,
            )

            st.session_state.pop(
                "crypto_summary",
                None,
            )

            st.session_state.pop(
                "crypto_trace",
                None,
            )

    # Do not display analysis until evaluation has run.
    if "summary" not in st.session_state:

        st.info(
            "Choose the settings above, then run the evaluation."
        )

        return

    detail = st.session_state["detail"]
    wide = st.session_state["wide"]
    summary = st.session_state["summary"]
    q = st.session_state["q"]
    config = st.session_state["config"]

    # --------------------------------------------------------
    # Q-table and statistical summary
    # --------------------------------------------------------

    st.subheader(
        "Learned Q-table — frozen before evaluation"
    )

    st.dataframe(
        q.round(4),
        use_container_width=True,
    )

    optimal_policy = pd.DataFrame(
        {
            "State": q.index,
            "Selected action": [
                q.loc[state].idxmax()
                for state in q.index
            ],
            "Best estimated Q-value": [
                float(q.loc[state].max())
                for state in q.index
            ],
        }
    )

    st.subheader(
        "Policy derived from learned Q-table"
    )

    st.dataframe(
        optimal_policy.round(4),
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "The selected action is optimal only relative to this declared "
        "synthetic MDP and reward function."
    )

    st.subheader(
        "Primary run-level paired statistical summary"
    )

    st.dataframe(
        summary.round(5),
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "Negative AO-minus-baseline differences favor AO-LACCP only for "
        "metrics where lower is better. Statistical significance does not "
        "validate the model assumptions."
    )

    # --------------------------------------------------------
    # Outcome distributions
    # --------------------------------------------------------

    st.subheader(
        "Held-out outcome distributions"
    )

    fig = make_outcome_plot(detail)

    st.pyplot(fig)

    plt.close(fig)

    # --------------------------------------------------------
    # Run-level mean confidence intervals
    # --------------------------------------------------------

    st.subheader(
        "Mean outcomes and 95% confidence intervals"
    )

    metric_specs = [
        ("resulting_risk", "Risk"),
        ("simulated_latency_ms", "Simulated latency (ms)"),
        ("service_impact_proxy", "Service impact"),
        ("action_cost_proxy", "Action cost"),
    ]

    mean_rows = []

    for metric, label in metric_specs:

        for policy in (
            POLICY_BASELINE,
            POLICY_AO,
        ):

            per_run = (
                detail.loc[
                    detail["policy"] == policy
                ]
                .groupby("run_id")[metric]
                .mean()
                .to_numpy(dtype=float)
            )

            n = len(per_run)

            mean_value = float(
                np.mean(per_run)
            )

            if n > 1:

                standard_error = float(
                    stats.sem(per_run)
                )

                critical = float(
                    stats.t.ppf(
                        0.975,
                        n - 1,
                    )
                )

                ci_low = (
                    mean_value
                    - critical * standard_error
                )

                ci_high = (
                    mean_value
                    + critical * standard_error
                )

            else:

                ci_low = np.nan
                ci_high = np.nan

            mean_rows.append(
                {
                    "Metric": label,
                    "Policy": policy,
                    "Mean": mean_value,
                    "95% CI low": ci_low,
                    "95% CI high": ci_high,
                }
            )

    mean_df = pd.DataFrame(mean_rows)

    st.dataframe(
        mean_df.round(5),
        use_container_width=True,
        hide_index=True,
    )

    # --------------------------------------------------------
    # Action counts
    # --------------------------------------------------------

    st.subheader(
        "Action selection counts"
    )

    action_counts = (
        detail.groupby(
            ["policy", "selected_action"]
        )
        .size()
        .rename("Scenario count")
        .reset_index()
    )

    action_counts["Share within policy"] = (
        action_counts["Scenario count"]
        / action_counts.groupby(
            "policy"
        )["Scenario count"].transform("sum")
    )

    st.dataframe(
        action_counts,
        use_container_width=True,
        hide_index=True,
    )

    # --------------------------------------------------------
    # MDP transition table
    # --------------------------------------------------------

    st.subheader(
        "Configured MDP transition probabilities"
    )

    transition_rows = []

    for state, probabilities in ARTIFACT_TRANSITIONS.items():

        for next_state, probability in zip(
            ["Low", "Medium", "High"],
            probabilities,
        ):

            transition_rows.append(
                {
                    "Current state": state,
                    "Next state": next_state,
                    "Transition probability": float(probability),
                    "Model note": (
                        "Illustrative; action-independent"
                    ),
                }
            )

    transition_df = pd.DataFrame(
        transition_rows
    )

    st.dataframe(
        transition_df.round(4),
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "The configured transition probabilities depend on the current "
        "state, not on the selected action. They are assumptions unless "
        "supported by empirical evidence."
    )

    # --------------------------------------------------------
    # Repeated-measures results
    # --------------------------------------------------------

    st.subheader(
        "Repeated-measures ANOVA comparison"
    )

    st.write(
        "Because the policies receive the same scenarios, an independent-groups "
        "ANOVA would ignore pairing. With two conditions, repeated-measures ANOVA "
        "is equivalent to a paired t-test, with F = t², on the independent run means."
    )

    anova_df = repeated_measures_results(
        detail
    )

    st.dataframe(
        anova_df.round(5),
        use_container_width=True,
        hide_index=True,
    )

    # --------------------------------------------------------
    # Exploratory regression
    # --------------------------------------------------------

    st.subheader(
        "Exploratory regression analysis"
    )

    st.write(
        "This descriptive OLS model examines how scenario inputs relate to "
        "the paired AO-minus-baseline risk difference. R² is not proof of "
        "causality, model validity, or real-world efficacy."
    )

    regression_table, r_squared = (
        exploratory_risk_regression(
            detail,
            wide,
        )
    )

    left, right = st.columns([1, 2])

    with left:

        st.metric(
            "Exploratory R²",
            (
                f"{r_squared:.4f}"
                if np.isfinite(r_squared)
                else "Unavailable"
            ),
        )

    with right:

        st.dataframe(
            regression_table.round(6),
            use_container_width=True,
            hide_index=True,
        )

    # --------------------------------------------------------
    # Sensitivity analysis
    # --------------------------------------------------------

    st.subheader(
        "Sensitivity analysis"
    )

    st.caption(
        "Each condition retrains Q-learning and reruns the evaluation. "
        "The same test scenario seeds are reused across variants. These "
        "tests assess sensitivity to assumptions; they are not calibration."
    )

    if st.button(
        "Run sensitivity analysis (7 evaluations)",
        use_container_width=True,
    ):

        with st.spinner(
            "Retraining and rerunning sensitivity conditions..."
        ):

            sensitivity = run_sensitivity_analysis(
                seed + 303_001,
                episodes,
                steps,
                alpha,
                gamma,
                epsilon,
                min(n_runs, 20),
                min(n_per_run, 150),
                calibration_factors,
            )

            st.session_state["sensitivity"] = sensitivity

    if "sensitivity" in st.session_state:

        sensitivity = st.session_state[
            "sensitivity"
        ]

        st.dataframe(
            sensitivity.round(5),
            use_container_width=True,
            hide_index=True,
        )

        fig, ax = plt.subplots(
            figsize=(10, 4.5)
        )

        ax.bar(
            sensitivity["Sensitivity condition"],
            sensitivity[
                "Mean risk difference (AO - baseline)"
            ],
        )

        ax.axhline(
            0,
            linestyle="--",
            linewidth=1,
        )

        ax.set_ylabel(
            "Mean risk difference (AO - baseline)"
        )

        ax.set_title(
            "Sensitivity of risk comparison to model assumptions"
        )

        ax.tick_params(
            axis="x",
            labelrotation=25,
        )

        ax.grid(
            axis="y",
            alpha=0.25,
        )

        fig.tight_layout()

        st.pyplot(fig)

        plt.close(fig)

        st.download_button(
            "Download sensitivity CSV",
            sensitivity.to_csv(
                index=False
            ).encode("utf-8"),
            "ao_laccp_sensitivity_analysis.csv",
            "text/csv",
        )

    # --------------------------------------------------------
    # Separate cryptographic benchmark
    # --------------------------------------------------------

    st.subheader(
        "Separate RSA/ECDSA cryptographic benchmark"
    )

    st.warning(
        "This separate harness executes actual RSA/ECDSA signing and verification. "
        "The suite-selection rule is illustrative and does not establish that the "
        "original AO-LACCP dashboard implements dynamic switching. PQC is not tested."
    )

    if not CRYPTO_AVAILABLE:

        st.info(
            "Install the cryptography package to enable this optional benchmark."
        )

    if st.button(
        "Run RSA/ECDSA benchmark",
        use_container_width=True,
    ):

        with st.spinner(
            "Executing cryptographic signing and verification..."
        ):

            trace, crypto_summary, crypto_note = (
                benchmark_crypto(
                    seed + 404_001,
                    30,
                )
            )

            st.session_state["crypto_trace"] = trace
            st.session_state["crypto_summary"] = crypto_summary
            st.session_state["crypto_note"] = crypto_note

    if "crypto_summary" in st.session_state:

        crypto_summary = st.session_state[
            "crypto_summary"
        ]

        trace = st.session_state[
            "crypto_trace"
        ]

        st.dataframe(
            crypto_summary.round(5),
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            st.session_state["crypto_note"]
        )

        if not trace.empty:

            st.dataframe(
                trace.round(5),
                use_container_width=True,
                hide_index=True,
            )

            fig, ax = plt.subplots(
                figsize=(9, 3.5)
            )

            ax.step(
                trace["event_id"],
                trace[
                    "suite_changed_from_previous_event"
                ].astype(int),
                where="mid",
            )

            ax.set_yticks(
                [0, 1],
                labels=["No switch", "Switch"],
            )

            ax.set_xlabel(
                "Event number"
            )

            ax.set_title(
                "Suite changes in separate cryptographic benchmark"
            )

            ax.grid(
                axis="x",
                alpha=0.25,
            )

            fig.tight_layout()

            st.pyplot(fig)

            plt.close(fig)

            st.download_button(
                "Download cryptographic trace CSV",
                trace.to_csv(
                    index=False
                ).encode("utf-8"),
                "ao_laccp_crypto_switch_trace.csv",
                "text/csv",
            )

    # --------------------------------------------------------
    # Reproducibility record and exports
    # --------------------------------------------------------

    st.subheader(
        "Reproducibility record"
    )

    config_json = json.dumps(
        config,
        indent=2,
        sort_keys=True,
    )

    st.code(
        config_json,
        language="json",
    )

    config_hash = hashlib.sha256(
        config_json.encode("utf-8")
    ).hexdigest()

    st.write(
        "Configuration SHA-256:",
        config_hash,
    )

    st.download_button(
        "Download detailed scenario results",
        detail.to_csv(
            index=False
        ).encode("utf-8"),
        "ao_laccp_validation_detailed.csv",
        "text/csv",
    )

    st.download_button(
        "Download paired outcomes",
        wide.to_csv(
            index=False
        ).encode("utf-8"),
        "ao_laccp_validation_paired.csv",
        "text/csv",
    )

    st.download_button(
        "Download statistical summary",
        summary.to_csv(
            index=False
        ).encode("utf-8"),
        "ao_laccp_validation_statistics.csv",
        "text/csv",
    )

    st.download_button(
        "Download learned Q-table",
        q.to_csv().encode("utf-8"),
        "ao_laccp_learned_q_table.csv",
        "text/csv",
    )

    st.warning(
        "Interpret all findings conditionally. The simulation uses assumed "
        "outcome equations and synthetic inputs. It does not establish production "
        "effectiveness, validated post-quantum cryptographic agility, or superiority "
        "outside the declared model."
    )


if __name__ == "__main__":
    main()
