import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from sklearn.linear_model import LinearRegression
from matplotlib.backends.backend_pdf import PdfPages
import io

# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="AO-LACCP Full Framework",
    layout="wide"
)

st.title(
    "🧠 AO-LACCP: AI-Orchestrated Adaptive Cryptographic Agility Framework"
)

st.caption(
    "AI-Orchestrated Latency-Aware Cryptographic Control Plane "
    "for Adaptive Cyber Resilience"
)

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("⚙️ AO-LACCP Governance & Security Control Panel")

download_data = st.sidebar.checkbox(
    "📥 Enable Dataset Download",
    value=False
)

save_output = st.sidebar.checkbox(
    "💾 Save Results",
    value=False
)

rl_enabled = st.sidebar.checkbox(
    "🔁 Enable Reinforcement Learning",
    value=True
)

# ============================================================
# CASE STUDY / THREAT SCENARIO
# ============================================================

threat_scenario = st.sidebar.selectbox(
    "🎯 Case Study / Threat Scenario",
    [
        "Normal Operating Conditions",
        "Latency Spike",
        "Adversarial Signal",
        "Compliance Drift",
        "Combined Multi-Threat"
    ]
)

st.sidebar.markdown("---")

# ============================================================
# GOVERNANCE
# ============================================================

governance = st.sidebar.multiselect(
    "🏛 Governance Frameworks",
    [
        "ISO 27001",
        "GDPR",
        "PCI DSS",
        "NIST CSF",
        "SOX"
    ],
    default=[
        "ISO 27001",
        "NIST CSF"
    ]
)

# ============================================================
# CRYPTOGRAPHIC MODEL
# ============================================================

crypto_model = st.sidebar.selectbox(
    "🔐 Cryptographic Model",
    [
        "RSA",
        "ECC",
        "PQC",
        "Hybrid"
    ]
)

# ============================================================
# COMPLIANCE
# ============================================================

compliance = st.sidebar.selectbox(
    "📜 Compliance Level",
    [
        "Low",
        "Medium",
        "High",
        "Very High"
    ]
)

# ============================================================
# DISPLAY SELECTED SCENARIO
# ============================================================

st.info(
    f"**Selected Case Study:** {threat_scenario}  \n"
    f"**Cryptographic Model:** {crypto_model}  \n"
    f"**Compliance Level:** {compliance}  \n"
    f"**Governance Frameworks:** "
    f"{', '.join(governance) if governance else 'None selected'}"
)

# ============================================================
# BUILT-IN SYNTHETIC DATASET
# ============================================================
#
# IMPORTANT:
# There is NO CSV upload functionality.
# The application always uses this controlled synthetic dataset.
#
# This prevents KeyError problems caused by uploaded datasets
# missing AO-LACCP analytical variables.
# ============================================================

np.random.seed(42)

n = 30

df = pd.DataFrame({
    "Baseline_Risk": np.random.normal(
        0.55,
        0.08,
        n
    ),

    "AO-LACCP_Risk": np.random.normal(
        0.32,
        0.05,
        n
    ),

    "Baseline_Latency": np.random.normal(
        210,
        25,
        n
    ),

    "AO-LACCP_Latency": np.random.normal(
        120,
        15,
        n
    ),

    "Baseline_Agility": np.random.normal(
        1.0,
        0.2,
        n
    ),

    "AO-LACCP_Agility": np.random.normal(
        1.8,
        0.25,
        n
    )
})

# ============================================================
# APPLY CASE-STUDY EFFECTS
# ============================================================

if threat_scenario == "Latency Spike":

    df["Baseline_Latency"] += 50
    df["AO-LACCP_Latency"] += 15

elif threat_scenario == "Adversarial Signal":

    df["Baseline_Risk"] += 0.08
    df["AO-LACCP_Risk"] += 0.03

elif threat_scenario == "Compliance Drift":

    df["Baseline_Agility"] -= 0.05
    df["AO-LACCP_Agility"] -= 0.02

elif threat_scenario == "Combined Multi-Threat":

    df["Baseline_Risk"] += 0.08
    df["AO-LACCP_Risk"] += 0.03

    df["Baseline_Latency"] += 50
    df["AO-LACCP_Latency"] += 15

    df["Baseline_Agility"] -= 0.05
    df["AO-LACCP_Agility"] -= 0.02

# ============================================================
# DESCRIPTIVE SAMPLE
# ============================================================

st.subheader("📌 Descriptive Sample")

st.dataframe(
    df.head(),
    use_container_width=True
)

st.caption(
    f"Synthetic demonstration dataset: {n} observations."
)

# ============================================================
# DESCRIPTIVE STATISTICS
# ============================================================

st.subheader("📊 Descriptive Statistics Table")

desc_table = pd.DataFrame({
    "Metric": [
        "Cyber Risk",
        "Cyber Risk",
        "Cryptographic Agility",
        "Cryptographic Agility",
        "Response Latency",
        "Response Latency"
    ],

    "Approach": [
        "AO-LACCP",
        "Baseline",
        "AO-LACCP",
        "Baseline",
        "AO-LACCP",
        "Baseline"
    ],

    "Mean": [
        df["AO-LACCP_Risk"].mean(),
        df["Baseline_Risk"].mean(),
        df["AO-LACCP_Agility"].mean(),
        df["Baseline_Agility"].mean(),
        df["AO-LACCP_Latency"].mean(),
        df["Baseline_Latency"].mean()
    ],

    "Std Dev": [
        df["AO-LACCP_Risk"].std(),
        df["Baseline_Risk"].std(),
        df["AO-LACCP_Agility"].std(),
        df["Baseline_Agility"].std(),
        df["AO-LACCP_Latency"].std(),
        df["Baseline_Latency"].std()
    ],

    "N": [
        n,
        n,
        n,
        n,
        n,
        n
    ]
})

st.dataframe(
    desc_table,
    use_container_width=True
)

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def cohens_d(x, y):
    """
    Calculate Cohen's d using pooled sample standard deviation.
    """

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    nx = len(x)
    ny = len(y)

    pooled_sd = np.sqrt(
        (
            (nx - 1) * np.var(x, ddof=1)
            +
            (ny - 1) * np.var(y, ddof=1)
        )
        /
        (nx + ny - 2)
    )

    if pooled_sd == 0:
        return 0.0

    return (
        np.mean(x) - np.mean(y)
    ) / pooled_sd


def eta_squared(f, df1, df2):

    denominator = (
        f * df1
        +
        df2
    )

    if denominator == 0:
        return 0.0

    return (
        f * df1
    ) / denominator


def decision(p):

    if p < 0.05:
        return "Reject H₀"

    return "Fail to Reject H₀"


def significance_text(p):

    if p < 0.001:
        return "p < .001"

    return f"p = {p:.5f}"


# ============================================================
# HYPOTHESIS TESTING FUNCTION
# ============================================================

def plot_h(
    title,
    ao_column,
    baseline_column,
    ylabel,
    fig_num
):

    ao_data = df[ao_column]
    baseline_data = df[baseline_column]

    # One-way ANOVA
    f_value, p_value = stats.f_oneway(
        ao_data,
        baseline_data
    )

    df1 = 1

    df2 = (
        len(ao_data)
        +
        len(baseline_data)
        -
        2
    )

    # Effect size
    d_value = cohens_d(
        ao_data,
        baseline_data
    )

    eta_value = eta_squared(
        f_value,
        df1,
        df2
    )

    # ========================================================
    # GRAPH
    # ========================================================

    fig, ax = plt.subplots(
        figsize=(7, 5)
    )

    ax.bar(
        ["Baseline", "AO-LACCP"],
        [
            baseline_data.mean(),
            ao_data.mean()
        ],
        yerr=[
            baseline_data.std(),
            ao_data.std()
        ],
        capsize=10
    )

    ax.set_title(
        f"Figure {fig_num}: {title}"
    )

    ax.set_ylabel(
        ylabel
    )

    ax.grid(
        axis="y",
        alpha=0.25
    )

    plt.tight_layout()

    st.pyplot(
        fig,
        clear_figure=False
    )

    # ========================================================
    # APA REPORTING
    # ========================================================

    st.markdown(
        f"""
### {title} — APA Reporting

**F({df1}, {df2}) = {f_value:.2f}, {significance_text(p_value)}**

**Cohen's d = {d_value:.2f}**

**Eta squared (η²) = {eta_value:.3f}**

**Decision:** {decision(p_value)}
"""
    )

    return (
        f_value,
        p_value,
        d_value,
        eta_value,
        fig
    )


# ============================================================
# HYPOTHESES
# ============================================================

st.header("🧪 Hypothesis Testing")

# ============================================================
# H1 — CYBER RISK
# ============================================================

h1_f, h1_p, d1, eta1, fig_h1 = plot_h(
    "Cyber Risk Comparison",
    "AO-LACCP_Risk",
    "Baseline_Risk",
    "Risk Score",
    "4.2"
)

# ============================================================
# H2 — CRYPTOGRAPHIC AGILITY
# ============================================================

h2_f, h2_p, d2, eta2, fig_h2 = plot_h(
    "Cryptographic Agility Comparison",
    "AO-LACCP_Agility",
    "Baseline_Agility",
    "Agility",
    "4.3"
)

# ============================================================
# H3 — RESPONSE LATENCY
# ============================================================

h3_f, h3_p, d3, eta3, fig_h3 = plot_h(
    "Response Latency Comparison",
    "AO-LACCP_Latency",
    "Baseline_Latency",
    "Latency (ms)",
    "4.4"
)

# ============================================================
# SUMMARY TABLE
# ============================================================

st.subheader("📋 Hypothesis Summary")

summary = pd.DataFrame({
    "Hypothesis": [
        "H1 Cyber Risk",
        "H2 Agility",
        "H3 Latency"
    ],

    "F-Value": [
        h1_f,
        h2_f,
        h3_f
    ],

    "P-Value": [
        h1_p,
        h2_p,
        h3_p
    ],

    "Cohen_d": [
        d1,
        d2,
        d3
    ],

    "Eta_Squared": [
        eta1,
        eta2,
        eta3
    ],

    "Decision": [
        decision(h1_p),
        decision(h2_p),
        decision(h3_p)
    ]
})

st.dataframe(
    summary,
    use_container_width=True
)

# ============================================================
# ONE-WAY ANOVA RESULTS
# ============================================================

st.subheader("📊 One-Way ANOVA Results")

def between_ss(x, y):

    mean_x = np.mean(x)
    mean_y = np.mean(y)

    grand_mean = (
        len(x) * mean_x
        +
        len(y) * mean_y
    ) / (
        len(x) + len(y)
    )

    return (
        len(x) * (mean_x - grand_mean) ** 2
        +
        len(y) * (mean_y - grand_mean) ** 2
    )


anova_table = pd.DataFrame({

    "Metric": [
        "Cyber Risk",
        "Cryptographic Agility",
        "Response Latency"
    ],

    "Between SS": [
        between_ss(
            df["AO-LACCP_Risk"],
            df["Baseline_Risk"]
        ),

        between_ss(
            df["AO-LACCP_Agility"],
            df["Baseline_Agility"]
        ),

        between_ss(
            df["AO-LACCP_Latency"],
            df["Baseline_Latency"]
        )
    ],

    "df (Between)": [
        1,
        1,
        1
    ],

    "F-Value": [
        h1_f,
        h2_f,
        h3_f
    ],

    "p-value": [
        h1_p,
        h2_p,
        h3_p
    ],

    "df (Within)": [
        2 * n - 2,
        2 * n - 2,
        2 * n - 2
    ]
})

st.dataframe(
    anova_table,
    use_container_width=True
)

# ============================================================
# REGRESSION
# ============================================================

st.subheader("📉 Regression Analysis")

X = df[
    [
        "AO-LACCP_Agility",
        "AO-LACCP_Latency"
    ]
]

y = df[
    "AO-LACCP_Risk"
]

model = LinearRegression()

model.fit(
    X,
    y
)

y_pred = model.predict(
    X
)

r2 = model.score(
    X,
    y
)

st.metric(
    "R² Score",
    f"{r2:.4f}"
)

# ============================================================
# REGRESSION COEFFICIENTS
# ============================================================

regression_results = pd.DataFrame({

    "Predictor": [
        "AO-LACCP Agility",
        "AO-LACCP Latency"
    ],

    "Coefficient": [
        model.coef_[0],
        model.coef_[1]
    ]
})

st.dataframe(
    regression_results,
    use_container_width=True
)

st.write(
    "Regression Intercept:",
    model.intercept_
)

# ============================================================
# ACTUAL VS PREDICTED GRAPH
# ============================================================

fig_regression, ax = plt.subplots(
    figsize=(7, 5)
)

ax.scatter(
    y,
    y_pred
)

minimum = min(
    y.min(),
    y_pred.min()
)

maximum = max(
    y.max(),
    y_pred.max()
)

ax.plot(
    [minimum, maximum],
    [minimum, maximum],
    "r--"
)

ax.set_title(
    "Regression: Actual vs Predicted Cyber Risk"
)

ax.set_xlabel(
    "Actual Risk"
)

ax.set_ylabel(
    "Predicted Risk"
)

ax.grid(
    alpha=0.25
)

plt.tight_layout()

st.pyplot(
    fig_regression
)

# ============================================================
# RL / MDP
# ============================================================

if rl_enabled:

    st.subheader(
        "🔁 Markov Decision Process "
        "(AO-LACCP Reinforcement Learning)"
    )

    states = [
        "Low",
        "Medium",
        "High"
    ]

    actions = [
        "Monitor",
        "Mitigate",
        "Escalate"
    ]

    transition = {

        "Low": [
            0.7,
            0.25,
            0.05
        ],

        "Medium": [
            0.3,
            0.5,
            0.2
        ],

        "High": [
            0.1,
            0.4,
            0.5
        ]
    }

    # ========================================================
    # REWARD FUNCTION
    # ========================================================

    def reward(
        state,
        action
    ):

        if (
            state == "Low"
            and
            action == "Monitor"
        ):
            return 10

        if (
            state == "Medium"
            and
            action == "Mitigate"
        ):
            return 20

        if (
            state == "High"
            and
            action == "Escalate"
        ):
            return 30

        return -5

    # ========================================================
    # Q TABLE
    # ========================================================

    Q = pd.DataFrame(
        0.0,
        index=states,
        columns=actions
    )

    alpha = 0.1
    gamma = 0.9
    epsilon = 0.2

    # ========================================================
    # NEXT STATE
    # ========================================================

    def next_state(state):

        return np.random.choice(
            states,
            p=transition[state]
        )

    # ========================================================
    # Q-LEARNING
    # ========================================================

    for episode in range(300):

        state = np.random.choice(
            states
        )

        for step in range(10):

            if np.random.rand() < epsilon:

                action = np.random.choice(
                    actions
                )

            else:

                action = Q.loc[
                    state
                ].idxmax()

            r = reward(
                state,
                action
            )

            new_state = next_state(
                state
            )

            Q.loc[
                state,
                action
            ] += alpha * (
                r
                +
                gamma
                *
                Q.loc[new_state].max()
                -
                Q.loc[state, action]
            )

            state = new_state

    # ========================================================
    # Q TABLE
    # ========================================================

    st.subheader(
        "🧠 Q-Table"
    )

    st.dataframe(
        Q,
        use_container_width=True
    )

    # ========================================================
    # POLICY
    # ========================================================

    st.subheader(
        "📈 Optimal Policy"
    )

    policy = Q.idxmax(
        axis=1
    )

    values = Q.max(
        axis=1
    )

    fig_policy, ax = plt.subplots(
        figsize=(7, 5)
    )

    ax.bar(
        states,
        values
    )

    for i, state in enumerate(states):

        ax.text(
            i,
            values[state],
            policy[state],
            ha="center",
            va="bottom",
            fontweight="bold"
        )

    ax.set_title(
        "Optimal Policy by Risk Level"
    )

    ax.set_ylabel(
        "Expected Utility"
    )

    ax.grid(
        axis="y",
        alpha=0.25
    )

    plt.tight_layout()

    st.pyplot(
        fig_policy
    )

else:

    st.info(
        "Reinforcement Learning is disabled. "
        "Enable it from the sidebar to display the Q-learning analysis."
    )

    fig_policy = None


# ============================================================
# FINAL INTERPRETATION
# ============================================================

st.subheader(
    "📘 APA Interpretation"
)

# ============================================================
# H1 INTERPRETATION
# ============================================================

risk_direction = (
    "reduces"
    if df["AO-LACCP_Risk"].mean()
    <
    df["Baseline_Risk"].mean()
    else
    "increases"
)

st.markdown(
    f"""
### H1: Cyber Risk

**F(1, {2*n-2}) = {h1_f:.2f}, {significance_text(h1_p)}**

The AO-LACCP framework **{risk_direction} cyber risk**
relative to the baseline condition.

**Decision:** {decision(h1_p)}
"""
)

# ============================================================
# H2 INTERPRETATION
# ============================================================

agility_direction = (
    "improves"
    if df["AO-LACCP_Agility"].mean()
    >
    df["Baseline_Agility"].mean()
    else
    "reduces"
)

st.markdown(
    f"""
### H2: Cryptographic Agility

**F(1, {2*n-2}) = {h2_f:.2f}, {significance_text(h2_p)}**

The AO-LACCP framework **{agility_direction}
cryptographic agility** relative to the baseline condition.

**Decision:** {decision(h2_p)}
"""
)

# ============================================================
# H3 INTERPRETATION
# ============================================================

latency_direction = (
    "reduces"
    if df["AO-LACCP_Latency"].mean()
    <
    df["Baseline_Latency"].mean()
    else
    "increases"
)

st.markdown(
    f"""
### H3: Response Latency

**F(1, {2*n-2}) = {h3_f:.2f}, {significance_text(h3_p)}**

The AO-LACCP framework **{latency_direction}
response latency** relative to the baseline condition.

**Decision:** {decision(h3_p)}
"""
)

# ============================================================
# PERFORMANCE SUMMARY
# ============================================================

st.subheader(
    "📊 AO-LACCP Performance Summary"
)

risk_reduction = (
    (
        df["Baseline_Risk"].mean()
        -
        df["AO-LACCP_Risk"].mean()
    )
    /
    df["Baseline_Risk"].mean()
) * 100

latency_reduction = (
    (
        df["Baseline_Latency"].mean()
        -
        df["AO-LACCP_Latency"].mean()
    )
    /
    df["Baseline_Latency"].mean()
) * 100

agility_improvement = (
    (
        df["AO-LACCP_Agility"].mean()
        -
        df["Baseline_Agility"].mean()
    )
    /
    df["Baseline_Agility"].mean()
) * 100

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "Cyber Risk Reduction",
        f"{risk_reduction:.2f}%"
    )

with col2:

    st.metric(
        "Latency Reduction",
        f"{latency_reduction:.2f}%"
    )

with col3:

    st.metric(
        "Agility Improvement",
        f"{agility_improvement:.2f}%"
    )

# ============================================================
# PDF GENERATOR
# ============================================================

def generate_pdf(
    df,
    desc_table,
    summary,
    anova_table,
    fig_h1,
    fig_h2,
    fig_h3,
    fig_policy,
    threat_scenario
):

    buffer = io.BytesIO()

    with PdfPages(buffer) as pdf:

        # ====================================================
        # TITLE PAGE
        # ====================================================

        fig, ax = plt.subplots(
            figsize=(8.5, 11)
        )

        ax.axis("off")

        ax.text(
            0.5,
            0.65,
            "AO-LACCP Full Dissertation Report",
            ha="center",
            fontsize=18,
            fontweight="bold"
        )

        ax.text(
            0.5,
            0.57,
            "AI-Orchestrated Latency-Aware "
            "Cryptographic Control Plane",
            ha="center",
            fontsize=12
        )

        ax.text(
            0.5,
            0.49,
            f"Case Study: {threat_scenario}",
            ha="center",
            fontsize=11
        )

        ax.text(
            0.5,
            0.43,
            f"Cryptographic Model: {crypto_model}",
            ha="center",
            fontsize=11
        )

        ax.text(
            0.5,
            0.37,
            f"Compliance Level: {compliance}",
            ha="center",
            fontsize=11
        )

        pdf.savefig(
            fig,
            bbox_inches="tight"
        )

        plt.close()

        # ====================================================
        # DATASET SAMPLE
        # ====================================================

        fig, ax = plt.subplots(
            figsize=(11, 8)
        )

        ax.axis("off")

        table = ax.table(
            cellText=df.head(10).round(4).values,
            colLabels=df.columns,
            loc="center"
        )

        table.auto_set_font_size(
            False
        )

        table.set_fontsize(
            8
        )

        table.scale(
            1,
            1.5
        )

        ax.set_title(
            "Synthetic Dataset Sample"
        )

        pdf.savefig(
            fig,
            bbox_inches="tight"
        )

        plt.close()

        # ====================================================
        # HYPOTHESIS FIGURES
        # ====================================================

        pdf.savefig(
            fig_h1
        )

        pdf.savefig(
            fig_h2
        )

        pdf.savefig(
            fig_h3
        )

        # ====================================================
        # POLICY FIGURE
        # ====================================================

        if fig_policy is not None:

            pdf.savefig(
                fig_policy
            )

        # ====================================================
        # DESCRIPTIVE STATISTICS
        # ====================================================

        fig, ax = plt.subplots(
            figsize=(11, 8)
        )

        ax.axis("off")

        table = ax.table(
            cellText=desc_table.round(4).values,
            colLabels=desc_table.columns,
            loc="center"
        )

        table.auto_set_font_size(
            False
        )

        table.set_fontsize(
            8
        )

        table.scale(
            1,
            1.5
        )

        ax.set_title(
            "Descriptive Statistics"
        )

        pdf.savefig(
            fig,
            bbox_inches="tight"
        )

        plt.close()

        # ====================================================
        # HYPOTHESIS SUMMARY
        # ====================================================

        fig, ax = plt.subplots(
            figsize=(11, 8)
        )

        ax.axis("off")

        table = ax.table(
            cellText=summary.round(5).values,
            colLabels=summary.columns,
            loc="center"
        )

        table.auto_set_font_size(
            False
        )

        table.set_fontsize(
            7
        )

        table.scale(
            1,
            1.5
        )

        ax.set_title(
            "Hypothesis Summary"
        )

        pdf.savefig(
            fig,
            bbox_inches="tight"
        )

        plt.close()

        # ====================================================
        # ANOVA RESULTS
        # ====================================================

        fig, ax = plt.subplots(
            figsize=(11, 8)
        )

        ax.axis("off")

        table = ax.table(
            cellText=anova_table.round(5).values,
            colLabels=anova_table.columns,
            loc="center"
        )

        table.auto_set_font_size(
            False
        )

        table.set_fontsize(
            7
        )

        table.scale(
            1,
            1.5
        )

        ax.set_title(
            "One-Way ANOVA Results"
        )

        pdf.savefig(
            fig,
            bbox_inches="tight"
        )

        plt.close()

    buffer.seek(0)

    return buffer


# ============================================================
# DOWNLOAD SYNTHETIC DATASET
# ============================================================

if download_data:

    st.download_button(
        label="⬇ Download Synthetic Dataset",
        data=df.to_csv(
            index=False
        ),
        file_name="AO_LACCP_synthetic_dataset.csv",
        mime="text/csv"
    )

# ============================================================
# GENERATE PDF
# ============================================================

if st.button(
    "📄 Generate PDF Report"
):

    pdf_file = generate_pdf(
        df,
        desc_table,
        summary,
        anova_table,
        fig_h1,
        fig_h2,
        fig_h3,
        fig_policy if rl_enabled else None,
        threat_scenario
    )

    st.download_button(
        label="⬇ Download AO-LACCP PDF",
        data=pdf_file,
        file_name="AO-LACCP_Report.pdf",
        mime="application/pdf"
    )

# ============================================================
# SAVE RESULTS
# ============================================================

if save_output:

    summary.to_csv(
        "AO-LACCP_results.csv",
        index=False
    )

    st.success(
        "AO-LACCP results have been saved."
    )

# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <p style="
        color: darkred;
        font-family: Arial, sans-serif;
        font-size: 24px;
        text-align: center;
    ">
        <br>
        AO_LACCP Artifact Simulation –
        Doctoral Research Demo | Any Questions?
    </p>
    """,
    unsafe_allow_html=True
)