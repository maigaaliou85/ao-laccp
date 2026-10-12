
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
    "Design Science Research (DSR) Artifact | "
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
    "Cryptographic Options",
    ["RSA", "Hybrid", "PQC"],
    default=["RSA"]
)

policy_choice = st.sidebar.multiselect(
    "Compliance Framework",
    ["ISO 27001", "NIST", "GDPR"],
    default=["ISO 27001"]
)

st.sidebar.info(
    "The agent count and iteration count control the number "
    "of simulated observations. Cryptographic and compliance "
    "selections are configuration inputs in this version."
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
    The model represents the conceptual relationship between
    risk assessment, security actions, latency, cryptographic
    choices, and policy constraints. The equations are a
    conceptual model; the statistical distributions below are
    the assumptions used in this simulation.
    """
)

# ============================================================
# 4. SIMULATION PARAMETERS
# ============================================================

# Risk is bounded between 0 and 1.
# The baseline SD of 0.15 is provisional; validate it
# against your research design before reporting findings.

BASELINE_RISK_MEAN = 0.55
BASELINE_RISK_SD = 0.15

AO_RISK_MEAN = 0.32
AO_RISK_SD = 0.05

# Latency measured in milliseconds.

BASELINE_LATENCY_MEAN = 210.0
BASELINE_LATENCY_SD = 25.0

AO_LATENCY_MEAN = 120.0
AO_LATENCY_SD = 15.0

# Cryptographic agility index.
# These are simulated index values, not physical units.

BASELINE_AGILITY_MEAN = 1.0
BASELINE_AGILITY_SD = 0.20

AO_AGILITY_MEAN = 1.8
AO_AGILITY_SD = 0.25

# ============================================================
# 5. DISTRIBUTION HELPERS
# ============================================================

def beta_parameters(mean, sd):
    """
    Convert a feasible mean and standard deviation into
    beta-distribution parameters for values in [0, 1].
    """

    variance = sd ** 2

    common = (
        mean * (1.0 - mean) / variance
    ) - 1.0

    if common <= 0:
        raise ValueError(
            "The specified mean and standard deviation "
            "are not feasible for a beta distribution."
        )

    alpha = mean * common
    beta = (1.0 - mean) * common

    return alpha, beta


def generate_risk(mean, sd, size):
    """Generate bounded synthetic risk scores."""

    alpha, beta = beta_parameters(mean, sd)

    return np.random.beta(
        alpha, beta, size=size
    )


def generate_positive_values(mean, sd, size):
    """Generate positive latency or agility observations."""

    values = np.random.normal(
        loc=mean,
        scale=sd,
        size=size
    )

    return np.maximum(values, 0.01)


# ============================================================
# 6. DATA SIMULATION
# ============================================================

# Fixed seed makes results reproducible for a fixed configuration.
np.random.seed(42)

n = num_agents * iterations

# Generate baseline and AO-LACCP risk.
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

# Generate latency in milliseconds.
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

# Generate cryptographic agility index values.
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
# 7. THREAT SCENARIO ADJUSTMENTS
# ============================================================

# These multipliers are illustrative scenario assumptions.
# They are not measured threat-response effects.
#
# They are applied to the generated observations so that
# selecting a scenario changes the simulated conditions.

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

    "Scenario": scenario,

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
    "Baseline and AO-LACCP observations are independently "
    "generated synthetic samples. They are not paired "
    "measurements from identical experimental runs."
)

# ============================================================
# 10. STATISTICAL TESTING
# ============================================================

st.header("3. Hypothesis Testing")

st.markdown(
    """
    Welch's independent-samples t-test is used to compare
    group means without assuming equal variances.

    The significance threshold is 0.05. Cohen's d is reported
    as a standardized effect-size estimate.
    """
)


def hypothesis_test(
    title,
    ao_values,
    baseline_values,
    direction
):
    """
    Compare independent synthetic samples using Welch's t-test.

    direction:
        'lower' means lower AO-LACCP values are desirable.
        'higher' means higher AO-LACCP values are desirable.
    """

    ao_values = np.asarray(ao_values, dtype=float)
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

    # Pooled-SD Cohen's d.
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

    # Mean direction and statistical significance
    # are evaluated separately.
    if direction == "lower":
        favors_ao = ao_mean < baseline_mean
    else:
        favors_ao = ao_mean > baseline_mean

    statistically_significant = (
        test.pvalue < 0.05
    )

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

    if statistically_significant and favors_ao:

        st.success(
            "The difference is statistically significant "
            "at the 0.05 level, and the observed mean "
            "favors AO-LACCP."
        )

    elif statistically_significant and not favors_ao:

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
        "Significant (p < 0.05)": statistically_significant,
        "Direction Favors AO-LACCP": favors_ao
    }


# H1: Risk reduction
h1 = hypothesis_test(
    "H1: Cyber Risk Reduction",
    df["Risk_AO_LACCP"],
    df["Risk_Baseline"],
    "lower"
)

# H2: Cryptographic agility
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


make_boxplot(
    "Risk_Baseline",
    "Risk_AO_LACCP",
    "Cyber Risk Comparison",
    "Risk Score (0–1)"
)

make_boxplot(
    "Latency_Baseline",
    "Latency_AO_LACCP",
    "Latency (milliseconds)"
)

make_boxplot(
    "Agility_Baseline",
    "Agility_AO_LACCP",
    "Cryptographic Agility Index"
)

# ============================================================
# 12. STATISTICAL SUMMARY TABLE
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
    "Baseline risk SD: "
    f"{df['Risk_Baseline'].std(ddof=1):.4f}"
)

st.write(
    "AO-LACCP risk SD: "
    f"{df['Risk_AO_LACCP'].std(ddof=1):.4f}"
)

# ============================================================
# 14. SCENARIO AND CONFIGURATION SUMMARY
# ============================================================

st.header("7. Scenario and Configuration")

st.write(f"**Selected scenario:** {scenario}")

st.write(
    "**Cryptographic options:** "
    + (", ".join(crypto_choice) if crypto_choice else "None selected")
)

st.write(
    "**Compliance frameworks:** "
    + (", ".join(policy_choice) if policy_choice else "None selected")
)

st.warning(
    "Cryptographic and compliance selections are currently "
    "displayed as configuration inputs. They do not yet "
    "change the simulation's cryptographic operations or "
    "enforce compliance controls."
)

# ============================================================
# 15. SECURITY RECOMMENDATIONS
# ============================================================

st.header("8. AO-LACCP Security Recommendations")

if scenario == "Quantum Attack":

    st.error(
        "Recommendation: evaluate post-quantum cryptography "
        "(PQC) or hybrid cryptography, test interoperability, "
        "and develop a cryptographic migration plan."
    )

elif scenario == "Adversarial Signal":

    st.warning(
        "Recommendation: strengthen threat validation, "
        "monitoring, model robustness, and incident response."
    )

elif scenario == "Latency Spike":

    st.info(
        "Recommendation: evaluate latency-aware policy "
        "selection and measure end-to-end processing delays."
    )

else:

    st.success(
        "Recommendation: maintain continuous monitoring, "
        "review access controls, and validate security policies."
    )

if not crypto_choice:
    st.warning("No cryptographic option has been selected.")

if not policy_choice:
    st.warning("No compliance framework has been selected.")

# ============================================================
# 16. AO-LACCP CONTRIBUTIONS AND DESIGN TRACEABILITY
# ============================================================

st.header("9. AO-LACCP Contributions and Design Traceability")

st.markdown(
    """
    **Integrated Architecture**

    Conceptual integration of AI-orchestrated decision logic,
    cryptographic agility, Zero Trust, and governance.

    **Adaptive Risk Intelligence**

    Simulation of baseline and AO-LACCP risk-score distributions.

    **Latency-Aware Decisions**

    Comparison of simulated processing latency in milliseconds.

    **Cryptographic Agility**

    Comparison of baseline and AO-LACCP agility-index values.

    **Post-Quantum Readiness**

    The Quantum Attack scenario illustrates a possible evaluation
    context for PQC migration and hybrid cryptography. It does
    not demonstrate resistance to actual quantum attacks.

    **Explainable AI**

    Explainability should be validated using documented decision
    logic, traceable inputs, and explanations of security actions.

    **Zero Trust**

    Zero Trust enforcement requires explicit access-control,
    identity, device, and contextual-policy logic to be implemented
    and tested.

    **Governance Integration**

    The interface provides ISO 27001, NIST, and GDPR selections.
    These selections alone do not establish compliance.

    **System Evaluation**

    Simulation outputs, statistical comparisons, and limitations
    provide evidence for evaluating the research artifact.

    **Continuous Adaptation**

    A genuine feedback loop requires implemented logic that uses
    observed outcomes to update subsequent decisions.
    """
)

# ============================================================
# 17. DESIGN SCIENCE RESEARCH JUSTIFICATION
# ============================================================

st.header("10. Design Science Research (DSR) Justification")

st.markdown(
    """
    AO-LACCP is presented as a Design Science Research artifact
    intended to address cybersecurity risk management challenges
    in banking and FinTech environments.

    Its evaluation follows four broad activities:

    1. **Problem identification:** identify limitations in
       adaptive cyber-risk management.

    2. **Artifact design:** specify the architecture, constructs,
       decision logic, and evaluation metrics.

    3. **Implementation:** implement the computational prototype
       and configurable simulation.

    4. **Evaluation:** compare simulated risk, latency, and
       cryptographic-agility metrics under documented assumptions.

    The results displayed here are synthetic computational
    results. They should not be represented as live financial
    institution measurements or as proof of production readiness.
    """
)

# ============================================================
# 18. EXPORT SIMULATION DATA
# ============================================================

st.header("11. Export Results")

csv_data = df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Simulation Dataset (CSV)",
    data=csv_data,
    file_name="ao_laccp_simulation_results.csv",
    mime="text/csv"
)

summary_csv = summary.to_csv(index=False).encode("utf-8")

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
    "Evaluation results depend on the specified simulation "
    "assumptions, selected scenario, and random seed."
)
