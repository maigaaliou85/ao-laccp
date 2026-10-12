
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import stats

# ============================================================
# 1. CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AO-LACCP | Computational Evaluation",
    page_icon="🛡️",
    layout="wide"
)

st.title(
    "AO-LACCP: AI-Orchestrated Latency-Aware "
    "Cryptographic Control Plane"
)

st.caption(
    "Design Science Research Artifact | "
    "Computational Simulation and Evaluation"
)

# ============================================================
# 2. SIDEBAR CONTROL PANEL
# ============================================================

st.sidebar.header("AO-LACCP Control Panel")

num_agents = st.sidebar.slider(
    "Number of Agents", 2, 10, 5
)

iterations = st.sidebar.slider(
    "Iterations per Agent", 5, 30, 10
)

scenario = st.sidebar.selectbox(
    "Threat Scenario",
    [
        "Normal",
        "Latency Spike",
        "Adversarial Signal",
        "Quantum Attack"
    ]
)

crypto_choice = st.sidebar.multiselect(
    "Cryptography",
    ["RSA", "Hybrid", "PQC"],
    default=["RSA"]
)

policy_choice = st.sidebar.multiselect(
    "Compliance Framework",
    ["ISO 27001", "NIST", "GDPR"],
    default=["ISO 27001"]
)

st.sidebar.info(
    "Configure the simulation population, threat scenario, "
    "cryptographic options, and governance selections."
)

# ============================================================
# 3. MATHEMATICAL MODEL
# ============================================================

st.header("1. AO-LACCP Mathematical Model")

st.latex(
    r"F_{\mathrm{AO-LACCP}}="
    r"\langle S,A,P,U,G,C,\Phi\rangle"
)

st.latex(
    r"R_t=\sigma("
    r"\beta_0+\beta_1X_t+\beta_2V_t+\beta_3L_t)"
)

st.latex(
    r"U(A_t)=\alpha(1-R_t)"
    r"-\lambda C(A_t)-\delta L(A_t)"
)

st.markdown(
    """
    The equations describe the conceptual framework for
    adaptive cyber-risk assessment and security decisions.
    The experiment below uses synthetic distributions to
    compare baseline and AO-LACCP performance.
    """
)

# ============================================================
# 4. SIMULATION PARAMETERS
# ============================================================

# Risk scores must remain between 0 and 1.
# The baseline risk SD of 0.15 is provisional.
# A normal distribution with mean 0.55 and SD 0.88 is
# not appropriate for a variable bounded between 0 and 1.

BASELINE_RISK_MEAN = 0.55
BASELINE_RISK_SD = 0.15

AO_RISK_MEAN = 0.32
AO_RISK_SD = 0.05

BASELINE_LATENCY_MEAN = 210.0
BASELINE_LATENCY_SD = 25.0

AO_LATENCY_MEAN = 120.0
AO_LATENCY_SD = 15.0

BASELINE_AGILITY_MEAN = 1.0
BASELINE_AGILITY_SD = 0.20

AO_AGILITY_MEAN = 1.8
AO_AGILITY_SD = 0.25

# ============================================================
# 5. DISTRIBUTION HELPERS
# ============================================================

def beta_parameters(mean, sd):
    """Calculate beta-distribution parameters."""

    variance = sd ** 2

    common = (
        mean * (1.0 - mean) / variance
    ) - 1.0

    if common <= 0:
        raise ValueError(
            "Invalid mean and standard deviation "
            "for a beta distribution."
        )

    alpha = mean * common
    beta = (1.0 - mean) * common

    return alpha, beta


def generate_risk(mean, sd, size):
    """Generate risk scores in the interval [0, 1]."""

    alpha, beta = beta_parameters(mean, sd)

    return np.random.beta(
        alpha, beta, size=size
    )


def generate_positive_values(mean, sd, size):
    """Generate positive synthetic measurements."""

    values = np.random.normal(
        loc=mean,
        scale=sd,
        size=size
    )

    return np.maximum(values, 0.01)


# ============================================================
# 6. GENERATE SYNTHETIC DATA
# ============================================================

# A fixed seed provides reproducibility for a given configuration.
np.random.seed(42)

n = num_agents * iterations

risk_baseline = generate_risk(
    BASELINE_RISK_MEAN,
    BASELINE_RISK_SD,
    n
)

risk_ao = generate_risk(
    AO_RISK_MEAN,
    AO_RISK_SD,
    n
)

latency_baseline = generate_positive_values(
    BASELINE_LATENCY_MEAN,
    BASELINE_LATENCY_SD,
    n
)

latency_ao = generate_positive_values(
    AO_LATENCY_MEAN,
    AO_LATENCY_SD,
    n
)

agility_baseline = generate_positive_values(
    BASELINE_AGILITY_MEAN,
    BASELINE_AGILITY_SD,
    n
)

agility_ao = generate_positive_values(
    AO_AGILITY_MEAN,
    AO_AGILITY_SD,
    n
)

# ============================================================
# 7. THREAT SCENARIOS
# ============================================================

# These scenario adjustments are illustrative assumptions.
# They are not empirically measured effects.

if scenario == "Latency Spike":

    latency_baseline *= 1.30
    latency_ao *= 1.15

elif scenario == "Adversarial Signal":

    risk_baseline = np.clip(
        risk_baseline * 1.15, 0.0, 1.0
    )

    risk_ao = np.clip(
        risk_ao * 1.10, 0.0, 1.0
    )

elif scenario == "Quantum Attack":

    risk_baseline = np.clip(
        risk_baseline * 1.25, 0.0, 1.0
    )

    risk_ao = np.clip(
        risk_ao * 0.95, 0.0, 1.0
    )

# ============================================================
# 8. CREATE DATAFRAME
# ============================================================

df = pd.DataFrame({
    "Agent": np.repeat(
        np.arange(1, num_agents + 1),
        iterations
    ),

    "Iteration": np.tile(
        np.arange(1, iterations + 1),
        num_agents
    ),

    "Scenario": [scenario] * n,

    "Risk_Baseline": risk_baseline,
    "Risk_AO_LACCP": risk_ao,

    "Latency_Baseline": latency_baseline,
    "Latency_AO_LACCP": latency_ao,

    "Agility_Baseline": agility_baseline,
    "Agility_AO_LACCP": agility_ao
})

# ============================================================
# 9. SIMULATION OVERVIEW
# ============================================================

st.header("2. Simulation Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Agents", num_agents)
col2.metric("Iterations per Agent", iterations)
col3.metric("Observations per Group", n)
col4.metric("Threat Scenario", scenario)

st.caption(
    "Each group contains synthetic observations. "
    "The baseline and AO-LACCP samples are independently "
    "generated and are not paired experimental measurements."
)

# ============================================================
# 10. HYPOTHESIS TESTING
# ============================================================

st.header("3. Hypothesis Testing")

st.markdown(
    """
    Welch's independent-samples t-test compares group means
    without assuming equal population variances.

    The significance threshold is 0.05. Cohen's d provides
    a standardized effect-size estimate.
    """
)


def hypothesis_test(
    title,
    ao_values,
    baseline_values,
    direction
):
    """Compare independent samples and report their statistics."""

    ao_values = np.asarray(
        ao_values, dtype=float
    )

    baseline_values = np.asarray(
        baseline_values, dtype=float
    )

    test = stats.ttest_ind(
        ao_values,
        baseline_values,
        equal_var=False
    )

    ao_mean = np.mean(ao_values)
    baseline_mean = np.mean(baseline_values)

    ao_sd = np.std(ao_values, ddof=1)
    baseline_sd = np.std(
        baseline_values, ddof=1
    )

    pooled_variance = (
        (len(ao_values) - 1) * ao_sd ** 2
        + (len(baseline_values) - 1)
        * baseline_sd ** 2
    ) / (
        len(ao_values) + len(baseline_values) - 2
    )

    pooled_sd = np.sqrt(pooled_variance)

    if pooled_sd > 0:
        cohen_d = (
            ao_mean - baseline_mean
        ) / pooled_sd
    else:
        cohen_d = np.nan

    if baseline_mean != 0:
        relative_change = (
            (ao_mean - baseline_mean)
            / baseline_mean
        ) * 100.0
    else:
        relative_change = np.nan

    if direction == "lower":
        favors_ao = ao_mean < baseline_mean
    else:
        favors_ao = ao_mean > baseline_mean

    significant = test.pvalue < 0.05

    st.subheader(title)

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Baseline Mean",
        f"{baseline_mean:.4f}"
    )

    c2.metric(
        "AO-LACCP Mean",
        f"{ao_mean:.4f}"
    )

    c3.metric(
        "Relative Change",
        f"{relative_change:.2f}%"
    )

    st.write(
        f"Welch t-statistic: {test.statistic:.4f}"
    )

    st.write(
        f"P-value: {test.pvalue:.6f}"
    )

    st.write(
        f"Cohen's d: {cohen_d:.4f}"
    )

    if significant and favors_ao:
        st.success(
            "The difference is statistically significant "
            "at the 0.05 level, and the observed mean "
            "favors AO-LACCP."
        )

    elif significant and not favors_ao:
        st.warning(
            "The difference is statistically significant, "
            "but the observed mean does not favor AO-LACCP."
        )

    else:
        st.info(
            "The difference did not reach the "
            "0.05 significance threshold."
        )

    return {
        "Hypothesis": title,
        "Baseline Mean": baseline_mean,
        "AO-LACCP Mean": ao_mean,
        "Welch t-statistic": test.statistic,
        "p-value": test.pvalue,
        "Cohen's d": cohen_d,
        "Relative Change (%)": relative_change,
        "Significant (p < 0.05)": significant,
        "Direction Favors AO-LACCP": favors_ao
    }


# H1: Cyber risk reduction
h1 = hypothesis_test(
    "H1: Cyber Risk Reduction",
    df["Risk_AO_LACCP"],
    df["Risk_Baseline"],
    "lower"
)

# H2: Cryptographic agility improvement
h2 = hypothesis_test(
    "H2: Cryptographic Agility",
    df["Agility_AO_LACCP"],
    df["Agility_Baseline"],
    "higher"
)

# H3: Latency reduction
h3 = hypothesis_test(
    "H3: Latency Reduction",
    df["Latency_AO_LACCP"],
    df["Latency_Baseline"],
    "lower"
)

# ============================================================
# 11. VISUALIZATION
# ============================================================

st.header("4. Results Visualization")


def make_boxplot(
    baseline_column,
    ao_column,
    title,
    y_label
):
    """Display baseline and AO-LACCP distributions."""

    fig = go.Figure()

    fig.add_trace(
        go.Box(
            y=df[baseline_column],
            name="Baseline",
            boxpoints="outliers"
        )
    )

    fig.add_trace(
        go.Box(
            y=df[ao_column],
            name="AO-LACCP",
            boxpoints="outliers"
        )
    )

    fig.update_layout(
        title=title,
        yaxis_title=y_label,
        boxmode="group",
        template="plotly_white",
        height=450
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# IMPORTANT: Each call supplies all four required arguments.

make_boxplot(
    "Risk_Baseline",
    "Risk_AO_LACCP",
    "Cyber Risk Comparison",
    "Risk Score (0–1)"
)

make_boxplot(
    "Latency_Baseline",
    "Latency_AO_LACCP",
    "Latency Comparison",
    "Latency (milliseconds)"
)

make_boxplot(
    "Agility_Baseline",
    "Agility_AO_LACCP",
    "Cryptographic Agility Comparison",
    "Cryptographic Agility Index"
)

# ============================================================
# 12. STATISTICAL SUMMARY
# ============================================================

st.header("5. Statistical Summary")

summary = pd.DataFrame([
    h1,
    h2,
    h3
])

st.dataframe(
    summary,
    use_container_width=True
)

# ============================================================
# 13. DESCRIPTIVE STATISTICS
# ============================================================

st.header("6. Descriptive Analysis")

descriptive_columns = [
    "Risk_Baseline",
    "Risk_AO_LACCP",
    "Latency_Baseline",
    "Latency_AO_LACCP",
    "Agility_Baseline",
    "Agility_AO_LACCP"
]

descriptive = df[
    descriptive_columns
].describe().T

descriptive = descriptive.rename(
    columns={
        "mean": "Mean",
        "std": "Standard Deviation",
        "min": "Minimum",
        "25%": "25th Percentile",
        "50%": "Median",
        "75%": "75th Percentile",
        "max": "Maximum"
    }
)

st.dataframe(
    descriptive,
    use_container_width=True
)

st.subheader("Risk Variability")

st.write(
    "Baseline risk standard deviation: "
    f"{df['Risk_Baseline'].std(ddof=1):.4f}"
)

st.write(
    "AO-LACCP risk standard deviation: "
    f"{df['Risk_AO_LACCP'].std(ddof=1):.4f}"
)

# ============================================================
# 14. SCENARIO AND CONFIGURATION
# ============================================================

st.header("7. Scenario and Configuration")

st.write(f"**Selected scenario:** {scenario}")

st.write(
    "**Cryptographic options:** "
    + (
        ", ".join(crypto_choice)
        if crypto_choice else "None selected"
    )
)

st.write(
    "**Compliance frameworks:** "
    + (
        ", ".join(policy_choice)
        if policy_choice else "None selected"
    )
)

st.warning(
    "The cryptographic and compliance selections are currently "
    "displayed as configuration inputs. They do not yet change "
    "the simulated cryptographic operations or enforce compliance."
)

# ============================================================
# 15. SECURITY RECOMMENDATIONS
# ============================================================

st.header("8. AO-LACCP Security Recommendations")

if scenario == "Quantum Attack":

    st.error(
        "Evaluate post-quantum cryptography (PQC) or hybrid "
        "cryptography, interoperability, and migration readiness."
    )

elif scenario == "Adversarial Signal":

    st.warning(
        "Strengthen threat validation, monitoring, model "
        "robustness, and incident response."
    )

elif scenario == "Latency Spike":

    st.info(
        "Evaluate latency-aware policy selection and measure "
        "end-to-end processing delays."
    )

else:

    st.success(
        "Maintain continuous monitoring, review access controls, "
        "and validate security policies."
    )

if not crypto_choice:
    st.warning(
        "No cryptographic option has been selected."
    )

if not policy_choice:
    st.warning(
        "No compliance framework has been selected."
    )

# ============================================================
# 16. AO-LACCP CONTRIBUTIONS
# ============================================================

st.header(
    "9. AO-LACCP Contributions and Design Traceability"
)

with st.expander(
    "Integrated Architecture",
    expanded=True
):
    st.write(
        "Conceptual integration of AI-orchestrated decision "
        "logic, cryptographic agility, Zero Trust, and governance."
    )

with st.expander("Adaptive Risk Intelligence"):
    st.write(
        "Comparison of simulated baseline and AO-LACCP "
        "cyber-risk score distributions."
    )

with st.expander("Latency-Aware Decisions"):
    st.write(
        "Comparison of simulated processing latency in milliseconds."
    )

with st.expander("Cryptographic Agility"):
    st.write(
        "Comparison of baseline and AO-LACCP agility-index values. "
        "This index requires a documented operational definition."
    )

with st.expander("Post-Quantum Readiness"):
    st.write(
        "The Quantum Attack scenario illustrates a possible "
        "evaluation context for PQC migration. It does not "
        "demonstrate resistance to actual quantum attacks."
    )

with st.expander("Explainable AI and Zero Trust"):
    st.write(
        "These capabilities require implemented decision "
        "explanations, traceable inputs, identity checks, and "
        "contextual access-control logic to be validated."
    )

with st.expander("Governance and Continuous Adaptation"):
    st.write(
        "Framework selections alone do not establish compliance. "
        "Continuous adaptation requires implemented feedback "
        "logic that updates subsequent decisions."
    )

# ============================================================
# 17. DESIGN SCIENCE RESEARCH JUSTIFICATION
# ============================================================

st.header(
    "10. Design Science Research (DSR) Justification"
)

st.markdown(
    """
    AO-LACCP is presented as a Design Science Research artifact
    intended to address adaptive cyber-risk management challenges
    in banking and FinTech environments.

    **Problem identification:** Identify limitations in adaptive
    cyber-risk management.

    **Artifact design:** Specify the architecture, constructs,
    decision logic, and evaluation metrics.

    **Implementation:** Implement the computational prototype
    and configurable simulation.

    **Evaluation:** Compare simulated risk, latency, and
    cryptographic-agility metrics under documented assumptions.

    The results displayed here are synthetic computational
    results. They are not live financial-institution measurements
    or proof of production readiness.
    """
)

# ============================================================
# 18. EXPORT RESULTS
# ============================================================

st.header("11. Export Results")

csv_data = df.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    label="Download Simulation Dataset (CSV)",
    data=csv_data,
    file_name="ao_laccp_simulation_results.csv",
    mime="text/csv"
)

summary_csv = summary.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    label="Download Statistical Summary (CSV)",
    data=summary_csv,
    file_name="ao_laccp_statistical_summary.csv",
    mime="text/csv"
)

# ============================================================
# 19. FOOTER
# ============================================================

st.divider()

st.caption(
    "AO-LACCP Artifact Simulation | Doctoral Research Demo"
)

st.caption(
    "Results depend on the specified simulation assumptions, "
    "selected scenario, and random seed."
)
