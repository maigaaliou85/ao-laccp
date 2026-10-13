"""AO-LACCP Full Framework — fair-comparison simulation scaffold.

IMPORTANT RESEARCH LIMITATION
This is a transparent synthetic simulation, not a validated model of a deployed
cybersecurity system. The policy rules and outcome coefficients are illustrative
assumptions. Replace the AO-LACCP policy function with the actual artifact logic,
justify/calibrate coefficients, and run sensitivity/validation studies before using
outputs as dissertation evidence of effectiveness.
"""
from __future__ import annotations

import io
from typing import Dict, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from matplotlib.backends.backend_pdf import PdfPages
from scipy import stats

# -----------------------------------------------------------------------------
# Page and controls
# -----------------------------------------------------------------------------
st.set_page_config(page_title="AO-LACCP Full Framework — Fair Comparison", layout="wide")
st.title("AO-LACCP: AI-Orchestrated Latency-Aware Cryptographic Control Plane")
st.caption("Fair-comparison simulation scaffold for Design Science Research (DSR) evaluation")
st.warning(
    "Research integrity notice: this dashboard uses synthetic inputs and explicitly configured "
    "policy/outcome assumptions. It does not establish real-world effectiveness. The AO-LACCP "
    "policy below is a transparent adaptive rule-based placeholder—not a trained AI model and "
    "not the separate Q-learning demonstration."
)

with st.sidebar:
    st.header("Simulation Controls")
    random_seed = int(st.number_input("Random seed", min_value=0, max_value=2_147_483_647, value=42, step=1))
    n = int(st.number_input("Observations per run", min_value=10, max_value=5000, value=100, step=10))
    n_repeats = int(st.number_input("Repeated simulation runs", min_value=2, max_value=500, value=30, step=1))
    threat_scenario = st.selectbox(
        "Threat scenario",
        ["Normal Operating Conditions", "Latency Spike", "Adversarial Signal", "Compliance Drift", "Combined Multi-Threat"],
    )
    compliance_level = st.selectbox("Compliance-pressure setting", ["Low", "Medium", "High", "Very High"], index=1)
    crypto_model = st.selectbox("Cryptographic mode (shared by both policies)", ["RSA", "ECC", "PQC", "Hybrid"], index=1)
    governance = st.multiselect(
        "Governance references (metadata only)",
        ["ISO 27001", "GDPR", "PCI DSS", "NIST CSF", "SOX"],
        default=["ISO 27001", "NIST CSF"],
    )
    rl_enabled = st.checkbox("Show separate illustrative Q-learning demo", value=False)
    show_raw = st.checkbox("Show synthetic observation-level data", value=False)

st.info(
    f"**Scenario:** {threat_scenario}  |  **Seed:** {random_seed}  |  **Observations/run:** {n}  |  "
    f"**Repeated runs:** {n_repeats}  |  **Cryptographic mode:** {crypto_model}"
)

# -----------------------------------------------------------------------------
# Transparent assumptions — intentionally visible in the app/report
# -----------------------------------------------------------------------------
SCENARIO_ADJUSTMENTS: Dict[str, Dict[str, float]] = {
    "Normal Operating Conditions": {"threat": 0.00, "latency_pressure": 0.00, "compliance_pressure": 0.00},
    "Latency Spike": {"threat": 0.00, "latency_pressure": 0.35, "compliance_pressure": 0.00},
    "Adversarial Signal": {"threat": 0.25, "latency_pressure": 0.00, "compliance_pressure": 0.00},
    "Compliance Drift": {"threat": 0.00, "latency_pressure": 0.00, "compliance_pressure": 0.30},
    "Combined Multi-Threat": {"threat": 0.25, "latency_pressure": 0.35, "compliance_pressure": 0.30},
}
COMPLIANCE_LEVEL_PRESSURE = {"Low": 0.10, "Medium": 0.30, "High": 0.55, "Very High": 0.75}
CRYPTO_LATENCY_OVERHEAD_MS = {"RSA": 4.0, "ECC": 3.0, "PQC": 12.0, "Hybrid": 8.0}

st.subheader("Model assumptions and operational definitions")
st.markdown(
    "- **Shared inputs:** each synthetic observation is generated once and passed to both policies.\n"
    "- **Baseline policy:** fixed thresholds based only on threat intensity.\n"
    "- **AO-LACCP placeholder policy:** transparent rule-based score using threat intensity, latency pressure, and compliance pressure.\n"
    "- **Common outcome equations:** both policies use the same risk, latency, and agility-proxy formulas; only the selected action differs.\n"
    "- **Agility metric:** an illustrative response/agility proxy, not measured cryptographic switching time or proof of PQC readiness.\n"
    "- **Governance selectors:** recorded as report metadata; this prototype does not perform ISO/NIST/GDPR/PCI DSS/SOX compliance validation."
)
assumptions_table = pd.DataFrame([
    {"Parameter": "Risk mitigation — Monitor", "Value": 0.02, "Meaning": "Illustrative reduction in normalized risk score"},
    {"Parameter": "Risk mitigation — Mitigate", "Value": 0.10, "Meaning": "Illustrative reduction in normalized risk score"},
    {"Parameter": "Risk mitigation — Escalate", "Value": 0.18, "Meaning": "Illustrative reduction in normalized risk score"},
    {"Parameter": "Latency cost — Monitor", "Value": 2.0, "Meaning": "Added milliseconds"},
    {"Parameter": "Latency cost — Mitigate", "Value": 10.0, "Meaning": "Added milliseconds"},
    {"Parameter": "Latency cost — Escalate", "Value": 22.0, "Meaning": "Added milliseconds"},
    {"Parameter": "Crypto-mode overhead", "Value": CRYPTO_LATENCY_OVERHEAD_MS[crypto_model], "Meaning": f"Shared overhead for {crypto_model} mode (ms)"},
])
st.dataframe(assumptions_table, use_container_width=True, hide_index=True)

# -----------------------------------------------------------------------------
# Scenario generator: one common row per experimental case
# -----------------------------------------------------------------------------
def make_shared_scenarios(seed: int, scenario: str, observations: int, compliance_setting: str) -> pd.DataFrame:
    """Generate the shared synthetic cases; no system-specific outcome is generated here."""
    rng = np.random.default_rng(seed)
    adj = SCENARIO_ADJUSTMENTS[scenario]
    threat = np.clip(rng.beta(2.2, 2.0, observations) + adj["threat"], 0.0, 1.0)
    latency_pressure = np.clip(rng.beta(1.8, 3.2, observations) + adj["latency_pressure"], 0.0, 1.0)
    compliance_pressure = np.clip(
        0.55 * rng.beta(2.0, 2.5, observations)
        + 0.45 * COMPLIANCE_LEVEL_PRESSURE[compliance_setting]
        + adj["compliance_pressure"], 0.0, 1.0
    )
    initial_risk = np.clip(
        0.12 + 0.48 * threat + 0.20 * compliance_pressure + rng.normal(0.0, 0.035, observations),
        0.0, 1.0,
    )
    base_latency = np.clip(rng.normal(180.0, 22.0, observations), 80.0, None)
    # The same disturbance terms are reused for both policies to preserve pairing.
    risk_noise = rng.normal(0.0, 0.018, observations)
    latency_noise = rng.normal(0.0, 4.0, observations)
    return pd.DataFrame({
        "Case_ID": np.arange(1, observations + 1),
        "Initial_Risk": initial_risk,
        "Threat_Intensity": threat,
        "Latency_Pressure": latency_pressure,
        "Compliance_Pressure": compliance_pressure,
        "Base_Latency_ms": base_latency,
        "Shared_Risk_Noise": risk_noise,
        "Shared_Latency_Noise_ms": latency_noise,
    })

# -----------------------------------------------------------------------------
# Policies and shared outcome model
# -----------------------------------------------------------------------------
ACTION_LEVEL = {"Monitor": 0, "Mitigate": 1, "Escalate": 2}
RISK_MITIGATION = {"Monitor": 0.02, "Mitigate": 0.10, "Escalate": 0.18}
ACTION_LATENCY_MS = {"Monitor": 2.0, "Mitigate": 10.0, "Escalate": 22.0}
AGILITY_PROXY = {"Monitor": 0.25, "Mitigate": 0.60, "Escalate": 0.90}


def baseline_policy(row: pd.Series) -> str:
    """Simple fixed-threshold baseline; intentionally transparent."""
    if row["Threat_Intensity"] >= 0.70:
        return "Escalate"
    if row["Threat_Intensity"] >= 0.40:
        return "Mitigate"
    return "Monitor"


def ao_laccp_adaptive_rule_policy(row: pd.Series) -> str:
    """Rule-based adaptive placeholder; replace with the actual artifact decision logic."""
    score = (
        0.50 * row["Threat_Intensity"]
        + 0.20 * row["Latency_Pressure"]
        + 0.30 * row["Compliance_Pressure"]
    )
    # Latency pressure is an input to the policy, but the same latency costs are
    # charged to both systems by the shared outcome function below.
    if score >= 0.67:
        return "Escalate"
    if score >= 0.38:
        return "Mitigate"
    return "Monitor"


def evaluate_policy(shared: pd.DataFrame, policy_fn, crypto_mode: str, label: str) -> pd.DataFrame:
    """Apply one policy to common cases, then compute outcomes with common equations."""
    out = shared.copy()
    out["Action"] = out.apply(policy_fn, axis=1)
    crypto_overhead = CRYPTO_LATENCY_OVERHEAD_MS[crypto_mode]
    out[f"{label}_Risk"] = np.clip(
        out["Initial_Risk"] - out["Action"].map(RISK_MITIGATION) + out["Shared_Risk_Noise"], 0.0, 1.0
    )
    out[f"{label}_Latency_ms"] = np.clip(
        out["Base_Latency_ms"]
        + 45.0 * out["Latency_Pressure"]
        + out["Action"].map(ACTION_LATENCY_MS)
        + crypto_overhead
        + out["Shared_Latency_Noise_ms"],
        0.0, None,
    )
    out[f"{label}_Agility_Proxy"] = out["Action"].map(AGILITY_PROXY).astype(float)
    return out


def run_paired_simulation(seed: int, scenario: str, observations: int, compliance_setting: str, crypto_mode: str) -> pd.DataFrame:
    shared = make_shared_scenarios(seed, scenario, observations, compliance_setting)
    baseline = evaluate_policy(shared, baseline_policy, crypto_mode, "Baseline")
    ao = evaluate_policy(shared, ao_laccp_adaptive_rule_policy, crypto_mode, "AO_LACCP")
    # Assemble one row per shared case, preserving matched case IDs.
    result = shared[["Case_ID", "Initial_Risk", "Threat_Intensity", "Latency_Pressure", "Compliance_Pressure", "Base_Latency_ms"]].copy()
    result["Baseline_Action"] = baseline["Action"].to_numpy()
    result["AO_LACCP_Action"] = ao["Action"].to_numpy()
    for metric in ["Risk", "Latency_ms", "Agility_Proxy"]:
        result[f"Baseline_{metric}"] = baseline[f"Baseline_{metric}"].to_numpy()
        result[f"AO_LACCP_{metric}"] = ao[f"AO_LACCP_{metric}"].to_numpy()
    return result


df = run_paired_simulation(random_seed, threat_scenario, n, compliance_level, crypto_model)

# -----------------------------------------------------------------------------
# Statistics: paired differences and 95% t confidence intervals
# -----------------------------------------------------------------------------
def paired_statistics(baseline: pd.Series, ao: pd.Series, metric: str, favorable_direction: str) -> dict:
    b = np.asarray(baseline, dtype=float)
    a = np.asarray(ao, dtype=float)
    raw_diff = a - b  # always AO-LACCP minus baseline
    test = stats.ttest_rel(a, b, nan_policy="omit")
    valid = raw_diff[np.isfinite(raw_diff)]
    count = len(valid)
    mean_raw = float(np.mean(valid)) if count else np.nan
    sd_diff = float(np.std(valid, ddof=1)) if count > 1 else np.nan
    se = sd_diff / np.sqrt(count) if count > 1 and np.isfinite(sd_diff) else np.nan
    crit = stats.t.ppf(0.975, df=count - 1) if count > 1 else np.nan
    raw_low = mean_raw - crit * se if np.isfinite(se) else np.nan
    raw_high = mean_raw + crit * se if np.isfinite(se) else np.nan
    # Positive oriented difference means favorable to AO-LACCP for every metric.
    sign = -1.0 if favorable_direction == "lower" else 1.0
    oriented = sign * valid
    oriented_mean = float(np.mean(oriented)) if count else np.nan
    oriented_low, oriented_high = (sign * raw_low, sign * raw_high) if sign > 0 else (-raw_high, -raw_low)
    paired_d = mean_raw / sd_diff if np.isfinite(sd_diff) and not np.isclose(sd_diff, 0) else np.nan
    return {
        "Metric": metric,
        "Baseline_Mean": float(np.mean(b)),
        "Baseline_SD": float(np.std(b, ddof=1)),
        "AO_LACCP_Mean": float(np.mean(a)),
        "AO_LACCP_SD": float(np.std(a, ddof=1)),
        "AO_minus_Baseline": mean_raw,
        "Favorable_Difference": oriented_mean,
        "Favorable_95CI_Lower": oriented_low,
        "Favorable_95CI_Upper": oriented_high,
        "Paired_t": float(test.statistic),
        "p_raw": float(test.pvalue),
        "Paired_dz": paired_d,
        "N_Pairs": count,
    }


metric_specs = [
    ("Cyber Risk", "Baseline_Risk", "AO_LACCP_Risk", "lower", "Risk score (0–1)"),
    ("Response Latency", "Baseline_Latency_ms", "AO_LACCP_Latency_ms", "lower", "Latency (ms)"),
    ("Cryptographic Agility Proxy", "Baseline_Agility_Proxy", "AO_LACCP_Agility_Proxy", "higher", "Illustrative index"),
]
results = pd.DataFrame([
    paired_statistics(df[bcol], df[acol], name, direction)
    for name, bcol, acol, direction, _ in metric_specs
])

# Holm adjustment for the three primary comparisons.
def holm_adjust(p_values) -> np.ndarray:
    p = np.asarray(p_values, dtype=float)
    adjusted = np.full(len(p), np.nan)
    valid_idx = np.where(np.isfinite(p))[0]
    if not len(valid_idx):
        return adjusted
    order = valid_idx[np.argsort(p[valid_idx])]
    m = len(order)
    running = 0.0
    for rank, idx in enumerate(order):
        candidate = min(1.0, (m - rank) * p[idx])
        running = max(running, candidate)
        adjusted[idx] = running
    return adjusted

results["p_Holm"] = holm_adjust(results["p_raw"].to_numpy())
results["Decision_Holm_alpha_0.05"] = np.where(results["p_Holm"] < 0.05, "Statistically significant", "Not statistically significant")


def p_format(value: float) -> str:
    if not np.isfinite(value):
        return "not estimable"
    if value < 0.001:
        return "< .001"
    return f"= {value:.3f}"


def describe_difference(row: pd.Series) -> str:
    return (
        f"Mean AO-LACCP − baseline difference = {row['AO_minus_Baseline']:.4f}; "
        f"95% CI for favorable-oriented difference = "
        f"[{row['Favorable_95CI_Lower']:.4f}, {row['Favorable_95CI_Upper']:.4f}]; "
        f"paired t({int(row['N_Pairs']) - 1}) = {row['Paired_t']:.3f}, "
        f"raw p {p_format(row['p_raw'])}, Holm-adjusted p {p_format(row['p_Holm'])}."
    )

# -----------------------------------------------------------------------------
# Dashboard results
# -----------------------------------------------------------------------------
st.header("1. Shared-input paired comparison")
st.caption(
    "Every row is the same synthetic case evaluated by both policies. The paired t-test is used "
    "because observations are matched by Case_ID. Holm adjustment controls family-wise error across "
    "the three displayed primary metrics. Statistical significance does not validate the assumptions."
)

summary_rows = []
for _, row in results.iterrows():
    summary_rows.append({
        "Metric": row["Metric"],
        "Baseline mean": row["Baseline_Mean"],
        "Baseline SD": row["Baseline_SD"],
        "AO-LACCP mean": row["AO_LACCP_Mean"],
        "AO-LACCP SD": row["AO_LACCP_SD"],
        "AO − Baseline": row["AO_minus_Baseline"],
        "Favorable 95% CI lower": row["Favorable_95CI_Lower"],
        "Favorable 95% CI upper": row["Favorable_95CI_Upper"],
        "Paired d_z": row["Paired_dz"],
        "Raw p": row["p_raw"],
        "Holm-adjusted p": row["p_Holm"],
        "N paired cases": row["N_Pairs"],
    })
summary_table = pd.DataFrame(summary_rows)
st.dataframe(summary_table.round(4), use_container_width=True, hide_index=True)

cols = st.columns(3)
for col, (_, row) in zip(cols, results.iterrows()):
    with col:
        label = row["Metric"]
        favorable = row["Favorable_Difference"]
        col.metric(label, f"{favorable:.4f}", help="Positive means favorable to AO-LACCP under the configured outcome model.")
        st.caption(f"Holm-adjusted p {p_format(row['p_Holm'])}")

st.subheader("Paired outcome distributions")
figures = {}
for name, bcol, acol, direction, ylabel in metric_specs:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    positions = [1, 2]
    ax.boxplot([df[bcol].to_numpy(), df[acol].to_numpy()], positions=positions, labels=["Baseline", "AO-LACCP"])
    ax.set_title(f"{name}: matched synthetic cases")
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    figures[name] = fig
    st.pyplot(fig, clear_figure=False)
    row = results.loc[results["Metric"] == name].iloc[0]
    st.write(describe_difference(row))

if show_raw:
    st.subheader("Synthetic observation-level dataset")
    st.dataframe(df, use_container_width=True, hide_index=True)

st.subheader("Action distribution")
action_table = pd.concat([
    df["Baseline_Action"].value_counts().rename("Baseline count"),
    df["AO_LACCP_Action"].value_counts().rename("AO-LACCP count"),
], axis=1).fillna(0).astype(int).rename_axis("Action").reset_index()
st.dataframe(action_table, use_container_width=True, hide_index=True)

# -----------------------------------------------------------------------------
# Repeated simulation runs: use one paired comparison per run
# -----------------------------------------------------------------------------
st.header("2. Repeated simulation robustness check")
st.caption(
    "Each replication generates new shared cases and compares both policies within that replication. "
    "The replication-level table describes sensitivity to random draws; replications are not human participants."
)
rep_records = []
for run_idx in range(n_repeats):
    run_df = run_paired_simulation(random_seed + run_idx, threat_scenario, n, compliance_level, crypto_model)
    rec = {"Run": run_idx + 1, "Seed": random_seed + run_idx}
    for metric, bcol, acol, direction, _ in metric_specs:
        row = paired_statistics(run_df[bcol], run_df[acol], metric, direction)
        rec[f"{metric}_FavorableDifference"] = row["Favorable_Difference"]
        rec[f"{metric}_p_raw"] = row["p_raw"]
    rep_records.append(rec)
replications = pd.DataFrame(rep_records)
rep_summary = []
for metric, *_ in metric_specs:
    values = replications[f"{metric}_FavorableDifference"]
    rep_summary.append({
        "Metric": metric,
        "Mean favorable difference across runs": values.mean(),
        "SD across runs": values.std(ddof=1),
        "Runs": n_repeats,
        "Runs favoring AO-LACCP": int((values > 0).sum()),
    })
rep_summary_df = pd.DataFrame(rep_summary)
st.dataframe(rep_summary_df.round(4), use_container_width=True, hide_index=True)

# -----------------------------------------------------------------------------
# Separate, explicitly disconnected Q-learning demonstration
# -----------------------------------------------------------------------------
fig_q = None
if rl_enabled:
    st.header("3. Separate illustrative Q-learning demonstration")
    st.warning(
        "This toy Q-learning example is not connected to the policy actions, outcomes, or statistical "
        "comparisons above. Do not describe it as the controller that produced these results."
    )
    states = ["Low", "Medium", "High"]
    actions = ["Monitor", "Mitigate", "Escalate"]
    transition = {"Low": [0.70, 0.25, 0.05], "Medium": [0.30, 0.50, 0.20], "High": [0.10, 0.40, 0.50]}
    reward_map = {
        ("Low", "Monitor"): 10, ("Medium", "Mitigate"): 20, ("High", "Escalate"): 30,
    }
    rng = np.random.default_rng(random_seed + 100_000)
    q = pd.DataFrame(0.0, index=states, columns=actions)
    alpha, gamma, epsilon = 0.10, 0.90, 0.20
    for _ in range(300):
        state = rng.choice(states)
        for _ in range(10):
            if rng.random() < epsilon:
                action = rng.choice(actions)
            else:
                qvals = q.loc[state].to_numpy()
                best = np.flatnonzero(np.isclose(qvals, qvals.max()))
                action = actions[int(rng.choice(best))]
            reward = reward_map.get((state, action), -5)
            next_state = rng.choice(states, p=transition[state])
            q.loc[state, action] += alpha * (reward + gamma * q.loc[next_state].max() - q.loc[state, action])
            state = next_state
    st.dataframe(q.round(3), use_container_width=True)
    learned_policy = q.idxmax(axis=1)
    fig_q, ax = plt.subplots(figsize=(7, 4))
    vals = q.max(axis=1)
    ax.bar(states, vals)
    for i, state in enumerate(states):
        ax.text(i, vals[state], learned_policy[state], ha="center", va="bottom")
    ax.set_title("Toy Q-learning policy (not connected to primary comparison)")
    ax.set_ylabel("Estimated Q-value")
    ax.grid(axis="y", alpha=0.25)
    fig_q.tight_layout()
    st.pyplot(fig_q)

# -----------------------------------------------------------------------------
# Interpretation and downloads
# -----------------------------------------------------------------------------
st.header("4. Interpretation and limitations")
st.markdown(
    "**What this comparison can support:** reproducible, paired comparison of two explicitly defined "
    "policies under the same synthetic cases and the same outcome equations.\n\n"
    "**What it cannot support by itself:** a claim that the deployed AO-LACCP artifact has achieved "
    "these risk, latency, or cryptographic-agility gains in real banking/FinTech systems. The numerical "
    "results depend on illustrative action thresholds, mitigation values, latency costs, and synthetic distributions.\n\n"
    "**Required next step for dissertation use:** replace `ao_laccp_adaptive_rule_policy()` with the actual "
    "AO-LACCP decision logic, define the baseline from a defensible reference method, justify or calibrate "
    "the outcome model independently, perform sensitivity analysis, and validate on held-out or external data "
    "where feasible. Report the results as simulation evidence, not production evidence."
)

metadata = pd.DataFrame([
    {"Item": "Scenario", "Value": threat_scenario},
    {"Item": "Compliance-pressure setting", "Value": compliance_level},
    {"Item": "Cryptographic mode", "Value": crypto_model},
    {"Item": "Governance references (metadata only)", "Value": ", ".join(governance) if governance else "None selected"},
    {"Item": "Random seed", "Value": random_seed},
    {"Item": "Observations per run", "Value": n},
    {"Item": "Repeated runs", "Value": n_repeats},
    {"Item": "Policy evaluated", "Value": "Transparent rule-based placeholder; not trained AI"},
    {"Item": "Outcome model", "Value": "Synthetic illustrative assumptions; not empirically calibrated"},
])

st.download_button(
    "Download paired synthetic dataset (CSV)",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name="AO_LACCP_paired_synthetic_dataset.csv",
    mime="text/csv",
)
st.download_button(
    "Download paired comparison results (CSV)",
    data=results.to_csv(index=False).encode("utf-8"),
    file_name="AO_LACCP_paired_comparison_statistics.csv",
    mime="text/csv",
)
st.download_button(
    "Download repeated-run results (CSV)",
    data=replications.to_csv(index=False).encode("utf-8"),
    file_name="AO_LACCP_repeated_run_results.csv",
    mime="text/csv",
)

# PDF report generated on request
if st.button("Prepare PDF report"):
    buffer = io.BytesIO()
    with PdfPages(buffer) as pdf:
        cover, ax = plt.subplots(figsize=(8.5, 11))
        ax.axis("off")
        ax.text(0.5, 0.82, "AO-LACCP Paired Simulation Report", ha="center", fontsize=18, fontweight="bold")
        ax.text(0.5, 0.75, "Synthetic comparison scaffold — not validated real-world performance", ha="center", fontsize=10)
        lines = [
            f"Scenario: {threat_scenario}", f"Compliance-pressure setting: {compliance_level}",
            f"Cryptographic mode: {crypto_model}", f"Governance metadata: {', '.join(governance) if governance else 'None'}",
            f"Seed: {random_seed}", f"Observations per run: {n}", f"Repeated runs: {n_repeats}",
            "AO-LACCP policy: transparent rule-based placeholder, not trained AI",
            "Outcome coefficients: illustrative assumptions requiring calibration/validation",
        ]
        for i, line in enumerate(lines):
            ax.text(0.10, 0.64 - i * 0.045, line, fontsize=10)
        pdf.savefig(cover, bbox_inches="tight")
        plt.close(cover)
        for fig in figures.values():
            pdf.savefig(fig, bbox_inches="tight")
        if fig_q is not None:
            pdf.savefig(fig_q, bbox_inches="tight")
        for table, title in [(summary_table, "Paired comparison statistics"), (rep_summary_df, "Repeated-run summary"), (action_table, "Action distribution"), (metadata, "Configuration and limitations")]:
            fig, ax = plt.subplots(figsize=(11, 8.5))
            ax.axis("off")
            ax.set_title(title)
            tab = ax.table(cellText=table.round(4).astype(str).values, colLabels=table.columns, loc="center")
            tab.auto_set_font_size(False)
            tab.set_fontsize(7)
            tab.scale(1, 1.4)
            pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)
    buffer.seek(0)
    st.download_button(
        "Download AO-LACCP PDF report", data=buffer.getvalue(),
        file_name="AO_LACCP_Paired_Simulation_Report.pdf", mime="application/pdf",
    )

st.caption("AO-LACCP DSR prototype • Synthetic simulation only • Reproducible seed • Paired case design")
