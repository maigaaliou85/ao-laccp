
import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from scipy import stats

# ============================================================
# AO-LACCP: AI-Orchestrated Latency-Aware Cryptographic Control
# Plane — Scenario Simulation and Security Recommendations
# ============================================================

st.set_page_config(
    page_title="AO-LACCP | Cyber Resilience",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ AO-LACCP: AI-Orchestrated Cyber Resilience")
st.caption(
    "Design Science Research artifact for adaptive cyber risk "
    "management in banking and FinTech environments."
)

# ============================================================
# 1. SCENARIO RECOMMENDATION ENGINE
# ============================================================

SCENARIO_POLICIES = {
    "Normal": {
        "crypto": ["RSA"],
        "compliance": ["ISO 27001"],
        "reason": (
            "Maintain approved cryptographic controls, continuous "
            "monitoring, and documented security governance."
        ),
        "risk_adjustment": 0.00,
        "latency_adjustment": 0.00,
    },
    "Latency Spike": {
        "crypto": ["Hybrid"],
        "compliance": ["ISO 27001"],
        "reason": (
            "Investigate latency bottlenecks and evaluate approved "
            "cryptographic configurations without weakening security."
        ),
        "risk_adjustment": 0.06,
        "latency_adjustment": 65.0,
    },
    "Adversarial Signal": {
        "crypto": ["Hybrid", "PQC"],
        "compliance": ["ISO 27001", "NIST CSF"],
        "reason": (
            "Strengthen threat detection, incident response, risk "
            "assessment, and cryptographic agility. ISO 27001 supports "
            "the information security management system; NIST CSF "
            "helps structure cybersecurity risk management."
        ),
        "risk_adjustment": 0.12,
        "latency_adjustment": 15.0,
    },
    "Quantum Attack": {
        "crypto": ["PQC", "Hybrid"],
        "compliance": ["ISO 27001", "NIST CSF"],
        "reason": (
            "Assess quantum-related exposure, inventory cryptographic "
            "dependencies, and plan a controlled post-quantum "
            "cryptography migration."
        ),
        "risk_adjustment": 0.15,
        "latency_adjustment": 25.0,
    },
}


def update_security_recommendations():
    """Update sidebar selections when the threat scenario changes."""
    selected = st.session_state["threat_scenario"]
    recommendation = SCENARIO_POLICIES[selected]

    st.session_state["crypto_selection"] = (
        recommendation["crypto"].copy()
    )
    st.session_state["policy_selection"] = (
        recommendation["compliance"].copy()
    )


# ============================================================
# 2. INITIALIZE SESSION STATE
# ============================================================

if "threat_scenario" not in st.session_state:
    st.session_state["threat_scenario"] = "Normal"

if "crypto_selection" not in st.session_state:
    st.session_state["crypto_selection"] = ["RSA"]

if "policy_selection" not in st.session_state:
    st.session_state["policy_selection"] = ["ISO 27001"]

# ============================================================
# 3. SIDEBAR CONTROLS
# ============================================================

st.sidebar.title("AO-LACCP Configuration")

agents = st.sidebar.slider(
    "Number of Agents",
    min_value=2,
    max_value=10,
    value=5,
    help="Simulation configuration parameter.",
)

iterations = st.sidebar.slider(
    "Simulation Iterations",
    min_value=5,
    max_value=30,
    value=10,
    help="Controls the number of synthetic observations.",
)

scenario = st.sidebar.selectbox(
    "Threat Scenario",
    options=list(SCENARIO_POLICIES.keys()),
    key="threat_scenario",
    on_change=update_security_recommendations,
)

crypto_choice = st.sidebar.multiselect(
    "Cryptographic Options",
    options=["RSA", "Hybrid", "PQC"],
    key="crypto_selection",
    help="Automatically populated from the selected threat scenario.",
)

policy_choice = st.sidebar.multiselect(
    "Compliance Frameworks",
    options=["ISO 27001", "NIST CSF", "GDPR"],
    key="policy_selection",
    help="Automatically populated from the selected threat scenario.",
)

recommendation = SCENARIO_POLICIES[scenario]

st.sidebar.divider()
st.sidebar.subheader("Scenario Recommendations")

st.sidebar.write(
    "**Recommended cryptography:** "
    + ", ".join(recommendation["crypto"])
)

st.sidebar.write(
    "**Recommended frameworks:** "
    + ", ".join(recommendation["compliance"])
)

st.sidebar.info(recommendation["reason"])

# ============================================================
# 4. SIMULATION SETTINGS
# ============================================================

st.header("1. Simulation Configuration")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Threat Scenario", scenario)

with col2:
    st.metric("Agents", agents)

with col3:
    st.metric("Iterations", iterations)

st.markdown("**Selected cryptography:** " +
            (", ".join(crypto_choice) if crypto_choice else "None"))

st.markdown("**Selected frameworks:** " +
            (", ".join(policy_choice) if policy_choice else "None"))

st.caption(
    "The selections above are scenario-based recommendations. "
    "This prototype does not automatically deploy cryptographic "
    "controls or certify regulatory compliance."
)

# ============================================================
# 5. SYNTHETIC DATA GENERATION
# ============================================================

# Reproducible demonstration seed; this is not a security key.
rng = np.random.default_rng(42)

# Use at least 30 observations for a more useful demonstration.
# The observations are synthetic, not real financial-system events.
n = max(30, iterations * agents)

scenario_risk_adjustment = recommendation["risk_adjustment"]
scenario_latency_adjustment = recommendation["latency_adjustment"]

# Risk values are bounded between 0 and 1.
baseline_risk = np.clip(
    rng.normal(loc=0.55, scale=0.15, size=n),
    0.0,
    1.0,
)

ao_risk = np.clip(
    rng.normal(loc=0.32, scale=0.05, size=n),
    0.0,
    1.0,
)

# Add scenario pressure to both architectures.
baseline_risk = np.clip(
    baseline_risk + scenario_risk_adjustment,
    0.0,
    1.0,
)

ao_risk = np.clip(
    ao_risk + scenario_risk_adjustment * 0.45,
    0.0,
    1.0,
)

# Latency is expressed in milliseconds.
baseline_latency = np.maximum(
    1.0,
    rng.normal(loc=210.0, scale=25.0, size=n)
    + scenario_latency_adjustment,
)

ao_latency = np.maximum(
    1.0,
    rng.normal(loc=120.0, scale=15.0, size=n)
    + scenario_latency_adjustment * 0.55,
)

# Agility is an illustrative index, not a standardized unit.
baseline_agility = np.maximum(
    0.0,
    rng.normal(loc=1.0, scale=0.20, size=n),
)

ao_agility = np.maximum(
    0.0,
    rng.normal(loc=1.8, scale=0.25, size=n),
)

# Make selected configuration choices affect the illustrative
# agility metric. These adjustments are explicit model assumptions.
if "Hybrid" in crypto_choice:
    ao_agility += 0.05

if "PQC" in crypto_choice:
    ao_agility += 0.10

if not crypto_choice:
    ao_agility = np.maximum(0.0, ao_agility - 0.10)

# A selected framework is not a compliance certification.
# These selections are recorded in the dashboard and export.

df = pd.DataFrame({
    "Observation": np.arange(1, n + 1),
    "Risk_Baseline": baseline_risk,
    "Risk_AO_LACCP": ao_risk,
    "Latency_Baseline_ms": baseline_latency,
    "Latency_AO_LACCP_ms": ao_latency,
    "Agility_Baseline": baseline_agility,
    "Agility_AO_LACCP": ao_agility,
    "Threat_Scenario": scenario,
    "Crypto_Selection": ", ".join(crypto_choice),
    "Compliance_Selection": ", ".join(policy_choice),
})

# ============================================================
# 6. STATISTICAL HELPERS
# ============================================================

def cohens_d(group1, group2):
    """Calculate Cohen's d using the pooled sample standard deviation."""
    a = np.asarray(group1, dtype=float)
    b = np.asarray(group2, dtype=float)

    if len(a) < 2 or len(b) < 2:
        return np.nan

    pooled_variance = (
        ((len(a) - 1) * np.var(a, ddof=1))
        + ((len(b) - 1) * np.var(b, ddof=1))
    ) / (len(a) + len(b) - 2)

    if pooled_variance <= 0:
        return 0.0

    return (np.mean(a) - np.mean(b)) / np.sqrt(pooled_variance)


def compare_groups(baseline, ao_laccp, metric_name, direction):
    """Welch t-test and descriptive comparison."""
    baseline = np.asarray(baseline, dtype=float)
    ao_laccp = np.asarray(ao_laccp, dtype=float)

    test = stats.ttest_ind(
        baseline,
        ao_laccp,
        equal_var=False,
        nan_policy="omit",
    )

    mean_baseline = float(np.mean(baseline))
    mean_ao = float(np.mean(ao_laccp))

    if direction == "lower":
        improvement = (
            (mean_baseline - mean_ao) / abs(mean_baseline) * 100
            if mean_baseline != 0 else np.nan
        )
        favorable = mean_ao < mean_baseline
    else:
        improvement = (
            (mean_ao - mean_baseline) / abs(mean_baseline) * 100
            if mean_baseline != 0 else np.nan
        )
        favorable = mean_ao > mean_baseline

    return {
        "Metric": metric_name,
        "Baseline Mean": mean_baseline,
        "AO-LACCP Mean": mean_ao,
        "Change (%)": improvement,
        "Welch t-statistic": float(test.statistic),
        "p-value": float(test.pvalue),
        "Cohen's d": float(cohens_d(baseline, ao_laccp)),
        "Direction Favorable": favorable,
    }


# ============================================================
# 7. METRIC SUMMARY
# ============================================================

risk_result = compare_groups(
    df["Risk_Baseline"],
    df["Risk_AO_LACCP"],
    "Cyber Risk",
    "lower",
)

latency_result = compare_groups(
    df["Latency_Baseline_ms"],
    df["Latency_AO_LACCP_ms"],
    "Latency (ms)",
    "lower",
)

agility_result = compare_groups(
    df["Agility_Baseline"],
    df["Agility_AO_LACCP"],
    "Cryptographic Agility Index",
    "higher",
)

results = pd.DataFrame([
    risk_result,
    latency_result,
    agility_result,
])

st.header("2. Simulation Results")

m1, m2, m3 = st.columns(3)

with m1:
    st.metric(
        "Mean Baseline Risk",
        f"{df['Risk_Baseline'].mean():.3f}",
    )
    st.metric(
        "Mean AO-LACCP Risk",
        f"{df['Risk_AO_LACCP'].mean():.3f}",
    )

with m2:
    st.metric(
        "Baseline Latency",
        f"{df['Latency_Baseline_ms'].mean():.1f} ms",
    )
    st.metric(
        "AO-LACCP Latency",
        f"{df['Latency_AO_LACCP_ms'].mean():.1f} ms",
    )

with m3:
    st.metric(
        "Baseline Agility",
        f"{df['Agility_Baseline'].mean():.2f}",
    )
    st.metric(
        "AO-LACCP Agility",
        f"{df['Agility_AO_LACCP'].mean():.2f}",
    )

st.subheader("Statistical Comparison")
st.dataframe(
    results.style.format({
        "Baseline Mean": "{:.4f}",
        "AO-LACCP Mean": "{:.4f}",
        "Change (%)": "{:.2f}%",
        "Welch t-statistic": "{:.3f}",
        "p-value": "{:.4f}",
        "Cohen's d": "{:.3f}",
    }),
    use_container_width=True,
)

st.caption(
    "These p-values describe comparisons within this synthetic "
    "simulation. They are not evidence of real-world effectiveness. "
    "The simulation assumptions and generated data should be "
    "validated before reporting inferential conclusions."
)

# ============================================================
# 8. VISUALIZATIONS
# ============================================================

st.header("3. Baseline vs. AO-LACCP Visualizations")


def make_boxplot(baseline_column, ao_column, title, y_label):
    plot_df = pd.DataFrame({
        "Architecture": (
            ["Baseline"] * len(df)
            + ["AO-LACCP"] * len(df)
        ),
        y_label: (
            df[baseline_column].tolist()
            + df[ao_column].tolist()
        ),
    })

    fig = px.box(
        plot_df,
        x="Architecture",
        y=y_label,
        color="Architecture",
        points="outliers",
        title=title,
    )

    fig.update_layout(
        showlegend=False,
        height=400,
    )

    st.plotly_chart(fig, use_container_width=True)


plot_col1, plot_col2 = st.columns(2)

with plot_col1:
    make_boxplot(
        "Risk_Baseline",
        "Risk_AO_LACCP",
        "Cyber Risk Comparison",
        "Risk Score (0–1)",
    )

with plot_col2:
    make_boxplot(
        "Latency_Baseline_ms",
        "Latency_AO_LACCP_ms",
        "Latency Comparison",
        "Latency (ms)",
    )

make_boxplot(
    "Agility_Baseline",
    "Agility_AO_LACCP",
    "Cryptographic Agility Comparison",
    "Agility Index",
)

st.subheader("Risk Values by Observation")

risk_line = df.melt(
    id_vars=["Observation"],
    value_vars=["Risk_Baseline", "Risk_AO_LACCP"],
    var_name="Architecture",
    value_name="Risk Score",
)

fig_risk = px.line(
    risk_line,
    x="Observation",
    y="Risk Score",
    color="Architecture",
    title="Synthetic Cyber Risk Across Observations",
)

st.plotly_chart(fig_risk, use_container_width=True)

# ============================================================
# 9. DYNAMIC SECURITY RECOMMENDATIONS
# ============================================================

st.header("4. Scenario-Driven Security Recommendations")

st.subheader(f"Selected Threat: {scenario}")
st.write(recommendation["reason"])

rec_col1, rec_col2 = st.columns(2)

with rec_col1:
    st.markdown("#### Recommended Cryptography")
    for item in recommendation["crypto"]:
        st.write(f"- {item}")

with rec_col2:
    st.markdown("#### Recommended Compliance Frameworks")
    for item in recommendation["compliance"]:
        st.write(f"- {item}")

st.markdown("#### Recommended Actions")

if scenario == "Normal":
    st.write(
        "1. Maintain an approved cryptographic inventory.\n"
        "2. Review access controls and security monitoring.\n"
        "3. Periodically assess security risks and control effectiveness."
    )

elif scenario == "Latency Spike":
    st.write(
        "1. Identify the source of increased latency.\n"
        "2. Benchmark approved cryptographic configurations.\n"
        "3. Preserve required security controls while optimizing performance."
    )

elif scenario == "Adversarial Signal":
    st.write(
        "1. Investigate and validate the threat signal.\n"
        "2. Review detection, escalation, and incident-response procedures.\n"
        "3. Assess cryptographic agility and the suitability of hybrid options.\n"
        "4. Map applicable controls to ISO 27001 and NIST CSF."
    )

elif scenario == "Quantum Attack":
    st.write(
        "1. Inventory cryptographic assets and dependencies.\n"
        "2. Identify systems requiring post-quantum readiness planning.\n"
        "3. Evaluate standardized post-quantum algorithms and migration risks.\n"
        "4. Test hybrid migration approaches for interoperability and latency."
    )

st.warning(
    "These are prototype recommendations, not automatic enforcement. "
    "ISO 27001 and NIST CSF support governance and risk management; "
    "selecting them in this dashboard does not establish compliance."
)

# ============================================================
# 10. DESCRIPTIVE STATISTICS
# ============================================================

st.header("5. Descriptive Statistics")

descriptive = df[
    [
        "Risk_Baseline",
        "Risk_AO_LACCP",
        "Latency_Baseline_ms",
        "Latency_AO_LACCP_ms",
        "Agility_Baseline",
        "Agility_AO_LACCP",
    ]
].describe().T

st.dataframe(
    descriptive.style.format("{:.4f}"),
    use_container_width=True,
)

# ============================================================
# 11. EXPORT SIMULATION DATA
# ============================================================

st.header("6. Export Results")

csv_data = df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Simulation Dataset (CSV)",
    data=csv_data,
    file_name="ao_laccp_scenario_simulation.csv",
    mime="text/csv",
)

results_csv = results.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Statistical Results (CSV)",
    data=results_csv,
    file_name="ao_laccp_statistical_results.csv",
    mime="text/csv",
)

# ============================================================
# 12. RESEARCH AND MODEL LIMITATIONS
# ============================================================

with st.expander("Research Methodology and Limitations"):
    st.markdown(
        """
        **Artifact purpose**

        This dashboard is a research prototype for exploring
        scenario-driven cyber resilience in banking and FinTech.

        **Data**

        The values are synthetic and generated with a fixed random
        seed for reproducibility. They are not observations from
        live banking systems or production deployments.

        **Model assumptions**

        The baseline and AO-LACCP distributions are illustrative
        assumptions. Scenario adjustments and cryptographic-agility
        adjustments are transparent demonstration rules, not
        independently validated causal effects.

        **Statistical interpretation**

        Welch's t-test and Cohen's d summarize differences between
        generated samples. Statistical significance in synthetic
        data does not establish real-world effectiveness.

        **Compliance**

        Framework selections provide guidance for further control
        mapping. They do not perform an audit or establish
        ISO 27001 certification, NIST CSF conformance, or GDPR compliance.

        **Cryptography**

        RSA, Hybrid, and PQC are simplified interface labels.
        A real implementation must specify algorithms, key sizes,
        protocol support, migration constraints, and performance
        requirements. PQC should be selected based on current
        standards and implementation requirements.
        """
    )

st.divider()
st.caption(
    "AO-LACCP | Research simulation prototype | "
    "Synthetic data only | Not for production security decisions"
)
