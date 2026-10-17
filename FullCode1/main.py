import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from sklearn.linear_model import LinearRegression
from matplotlib.backends.backend_pdf import PdfPages
import io
import os
import inspect

# ============================================================
# CONFIGURATION
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

governance = st.sidebar.multiselect(
    "🏛 Governance Frameworks",
    ["ISO 27001", "GDPR", "PCI DSS", "NIST CSF", "SOX"],
    default=["ISO 27001", "NIST CSF"]
)

crypto_model = st.sidebar.selectbox(
    "🔐 Cryptographic Model",
    ["RSA", "ECC", "PQC", "Hybrid"]
)

compliance = st.sidebar.selectbox(
    "📜 Compliance Level",
    ["Low", "Medium", "High", "Very High"]
)

st.info(
    f"**Selected Case Study:** {threat_scenario}\n\n"
    f"**Cryptographic Model:** {crypto_model}\n\n"
    f"**Compliance Level:** {compliance}\n\n"
    f"**Governance Frameworks:** "
    f"{', '.join(governance) if governance else 'None selected'}"
)

# ============================================================
# SYNTHETIC DATA
# ============================================================
# Reproducible demonstration data; not live financial data.
# Each row is a synthetic observation. Baseline and AO-LACCP
# samples are independently generated, not paired observations.
# ============================================================

np.random.seed(42)

n = 30

df = pd.DataFrame({
    "Baseline_Risk": np.random.normal(0.55, 0.08, n),
    "AO-LACCP_Risk": np.random.normal(0.32, 0.05, n),
    "Baseline_Latency": np.random.normal(210, 25, n),
    "AO-LACCP_Latency": np.random.normal(120, 15, n),
    "Baseline_Agility": np.random.normal(1.0, 0.2, n),
    "AO-LACCP_Agility": np.random.normal(1.8, 0.25, n)
})

# Keep simulated risk scores within a meaningful range.
for column in ["Baseline_Risk", "AO-LACCP_Risk"]:
    df[column] = df[column].clip(0, 1)

# ============================================================
# SCENARIO EFFECTS
# ============================================================

if threat_scenario == "Latency Spike":
    df["Baseline_Latency"] += 50
    df["AO-LACCP_Latency"] += 15

elif threat_scenario == "Adversarial Signal":
    df["Baseline_Risk"] = (df["Baseline_Risk"] + 0.08).clip(0, 1)
    df["AO-LACCP_Risk"] = (df["AO-LACCP_Risk"] + 0.03).clip(0, 1)

elif threat_scenario == "Compliance Drift":
    df["Baseline_Agility"] -= 0.05
    df["AO-LACCP_Agility"] -= 0.02

elif threat_scenario == "Combined Multi-Threat":
    df["Baseline_Risk"] = (df["Baseline_Risk"] + 0.08).clip(0, 1)
    df["AO-LACCP_Risk"] = (df["AO-LACCP_Risk"] + 0.03).clip(0, 1)

    df["Baseline_Latency"] += 50
    df["AO-LACCP_Latency"] += 15

    df["Baseline_Agility"] -= 0.05
    df["AO-LACCP_Agility"] -= 0.02

# ============================================================
# DATASET PREVIEW
# ============================================================

st.subheader("📌 Descriptive Sample")
st.dataframe(df.head(), use_container_width=True)

st.caption(
    f"Synthetic demonstration dataset: {n} observations. "
    "Results depend on the selected scenario and stated assumptions."
)

# ============================================================
# DESCRIPTIVE STATISTICS
# ============================================================

metric_definitions = [
    ("Cyber Risk", "AO-LACCP_Risk", "AO-LACCP"),
    ("Cyber Risk", "Baseline_Risk", "Baseline"),
    ("Cryptographic Agility", "AO-LACCP_Agility", "AO-LACCP"),
    ("Cryptographic Agility", "Baseline_Agility", "Baseline"),
    ("Response Latency", "AO-LACCP_Latency", "AO-LACCP"),
    ("Response Latency", "Baseline_Latency", "Baseline")
]

desc_table = pd.DataFrame([
    {
        "Metric": metric,
        "Approach": approach,
        "Mean": df[column].mean(),
        "Std Dev": df[column].std(ddof=1),
        "N": df[column].count()
    }
    for metric, column, approach in metric_definitions
])

st.subheader("📊 Descriptive Statistics Table")
st.dataframe(desc_table, use_container_width=True)

# ============================================================
# STATISTICAL HELPER FUNCTIONS
# ============================================================

def cohens_d(x, y):
    """Cohen's d using pooled sample standard deviation."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    nx, ny = len(x), len(y)

    if nx < 2 or ny < 2:
        return np.nan

    pooled_variance = (
        (nx - 1) * np.var(x, ddof=1)
        + (ny - 1) * np.var(y, ddof=1)
    ) / (nx + ny - 2)

    pooled_sd = np.sqrt(pooled_variance)

    if pooled_sd == 0:
        return 0.0

    return (np.mean(x) - np.mean(y)) / pooled_sd


def eta_squared(f_value, df1, df2):
    denominator = f_value * df1 + df2

    if not np.isfinite(denominator) or denominator == 0:
        return np.nan

    return (f_value * df1) / denominator


def decision(p_value):
    if not np.isfinite(p_value):
        return "Inconclusive"

    return "Reject H₀" if p_value < 0.05 else "Fail to Reject H₀"


def significance_text(p_value):
    if not np.isfinite(p_value):
        return "p unavailable"

    if p_value < 0.001:
        return "p < .001"

    return f"p = {p_value:.5f}"


def between_ss(x, y):
    """Between-group sum of squares for two independent groups."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    grand_mean = (
        len(x) * np.mean(x) + len(y) * np.mean(y)
    ) / (len(x) + len(y))

    return (
        len(x) * (np.mean(x) - grand_mean) ** 2
        + len(y) * (np.mean(y) - grand_mean) ** 2
    )


# ============================================================
# HYPOTHESIS TESTING AND VISUALIZATION
# ============================================================

figures = {}


def plot_h(title, ao_column, baseline_column, ylabel, fig_num):
    ao_data = pd.to_numeric(
        df[ao_column], errors="coerce"
    ).replace([np.inf, -np.inf], np.nan).dropna().to_numpy()

    baseline_data = pd.to_numeric(
        df[baseline_column], errors="coerce"
    ).replace([np.inf, -np.inf], np.nan).dropna().to_numpy()

    if len(ao_data) < 2 or len(baseline_data) < 2:
        st.warning(f"{title}: insufficient valid data for statistical testing.")
        return np.nan, np.nan, np.nan, np.nan, None

    # Independent-samples one-way ANOVA.
    f_value, p_value = stats.f_oneway(
        ao_data, baseline_data
    )

    df1 = 1
    df2 = len(ao_data) + len(baseline_data) - 2

    d_value = cohens_d(ao_data, baseline_data)
    eta_value = eta_squared(f_value, df1, df2)

    # Summary bar chart.
    fig, ax = plt.subplots(figsize=(7, 5))

    means = [np.mean(baseline_data), np.mean(ao_data)]
    stds = [
        np.std(baseline_data, ddof=1),
        np.std(ao_data, ddof=1)
    ]

    ax.bar(
        ["Baseline", "AO-LACCP"],
        means,
        yerr=stds,
        capsize=8
    )

    ax.set_title(f"Figure {fig_num}: {title}")
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()

    st.pyplot(fig)
    figures[f"hypothesis_{fig_num}"] = fig

    # Boxplot using the Matplotlib version's supported argument.
    # This directly addresses the reported labels/tick_labels error.
    box_fig, box_ax = plt.subplots(figsize=(7, 5))

    boxplot_parameters = inspect.signature(box_ax.boxplot).parameters
    label_parameter = (
        "tick_labels"
        if "tick_labels" in boxplot_parameters
        else "labels"
    )

    boxplot_options = {
        "positions": [1, 2],
        "showmeans": True,
        "patch_artist": True
    }
    boxplot_options[label_parameter] = ["Baseline", "AO-LACCP"]

    box_result = box_ax.boxplot(
        [baseline_data, ao_data],
        **boxplot_options
    )

    for patch, color in zip(
        box_result["boxes"], ["lightgray", "lightblue"]
    ):
        patch.set_facecolor(color)

    box_ax.set_title(f"Distribution: {title}")
    box_ax.set_ylabel(ylabel)
    box_ax.grid(axis="y", alpha=0.25)
    box_fig.tight_layout()

    st.pyplot(box_fig)
    figures[f"boxplot_{fig_num}"] = box_fig

    st.markdown(
        f"""
### {title} — Statistical Reporting

- **F({df1}, {df2}) = {f_value:.3f}, {significance_text(p_value)}**
- **Cohen's d = {d_value:.3f}**
- **Eta squared (η²) = {eta_value:.3f}**
- **Decision:** {decision(p_value)}

These are results from the synthetic demonstration dataset. Statistical
significance does not by itself establish real-world effectiveness.
"""
    )

    return f_value, p_value, d_value, eta_value, fig


st.header("🧪 Hypothesis Testing")

h1_f, h1_p, d1, eta1, fig_h1 = plot_h(
    "Cyber Risk Comparison",
    "AO-LACCP_Risk",
    "Baseline_Risk",
    "Risk Score",
    "4.2"
)

h2_f, h2_p, d2, eta2, fig_h2 = plot_h(
    "Cryptographic Agility Comparison",
    "AO-LACCP_Agility",
    "Baseline_Agility",
    "Agility",
    "4.3"
)

h3_f, h3_p, d3, eta3, fig_h3 = plot_h(
    "Response Latency Comparison",
    "AO-LACCP_Latency",
    "Baseline_Latency",
    "Latency (ms)",
    "4.4"
)

# ============================================================
# HYPOTHESIS SUMMARY
# ============================================================

st.subheader("📋 Hypothesis Summary")

summary = pd.DataFrame({
    "Hypothesis": [
        "H1 Cyber Risk",
        "H2 Agility",
        "H3 Latency"
    ],
    "F-Value": [h1_f, h2_f, h3_f],
    "P-Value": [h1_p, h2_p, h3_p],
    "Cohen_d": [d1, d2, d3],
    "Eta_Squared": [eta1, eta2, eta3],
    "Decision": [decision(h1_p), decision(h2_p), decision(h3_p)]
})

st.dataframe(summary, use_container_width=True)

# ============================================================
# ANOVA RESULTS
# ============================================================

st.subheader("📊 One-Way ANOVA Results")

anova_table = pd.DataFrame({
    "Metric": [
        "Cyber Risk",
        "Cryptographic Agility",
        "Response Latency"
    ],
    "Between SS": [
        between_ss(df["AO-LACCP_Risk"], df["Baseline_Risk"]),
        between_ss(df["AO-LACCP_Agility"], df["Baseline_Agility"]),
        between_ss(df["AO-LACCP_Latency"], df["Baseline_Latency"])
    ],
    "df (Between)": [1, 1, 1],
    "F-Value": [h1_f, h2_f, h3_f],
    "p-value": [h1_p, h2_p, h3_p],
    "df (Within)": [2 * n - 2] * 3
})

st.dataframe(anova_table, use_container_width=True)

# ============================================================
# REGRESSION ANALYSIS
# ============================================================

st.subheader("📉 Regression Analysis")

X = df[["AO-LACCP_Agility", "AO-LACCP_Latency"]]
y = df["AO-LACCP_Risk"]

model = LinearRegression()
model.fit(X, y)

y_pred = model.predict(X)
r2 = model.score(X, y)

st.metric("R² Score", f"{r2:.4f}")
st.caption(
    "This is an in-sample R² from synthetic data, not an independent "
    "test-set performance estimate."
)

regression_results = pd.DataFrame({
    "Predictor": ["AO-LACCP Agility", "AO-LACCP Latency"],
    "Coefficient": model.coef_
})

st.dataframe(regression_results, use_container_width=True)
st.write("Regression Intercept:", model.intercept_)

fig_regression, ax = plt.subplots(figsize=(7, 5))
ax.scatter(y, y_pred)

minimum = min(float(y.min()), float(y_pred.min()))
maximum = max(float(y.max()), float(y_pred.max()))

ax.plot([minimum, maximum], [minimum, maximum], "r--")
ax.set_title("Regression: Actual vs Predicted Cyber Risk")
ax.set_xlabel("Actual Risk")
ax.set_ylabel("Predicted Risk")
ax.grid(alpha=0.25)
fig_regression.tight_layout()

st.pyplot(fig_regression)
figures["regression"] = fig_regression

# ============================================================
# REINFORCEMENT LEARNING / MDP DEMONSTRATION
# ============================================================

fig_policy = None
Q = None
policy = None

if rl_enabled:
    st.subheader(
        "🔁 Markov Decision Process (AO-LACCP Reinforcement Learning)"
    )

    states = ["Low", "Medium", "High"]
    actions = ["Monitor", "Mitigate", "Escalate"]

    transition = {
        "Low": [0.7, 0.25, 0.05],
        "Medium": [0.3, 0.5, 0.2],
        "High": [0.1, 0.4, 0.5]
    }

    def reward(state, action):
        if state == "Low" and action == "Monitor":
            return 10
        if state == "Medium" and action == "Mitigate":
            return 20
        if state == "High" and action == "Escalate":
            return 30
        return -5

    Q = pd.DataFrame(0.0, index=states, columns=actions)

    alpha = 0.1
    gamma = 0.9
    epsilon = 0.2

    def next_state(state):
        return np.random.choice(states, p=transition[state])

    # Demonstration Q-learning. The transition model and rewards
    # are illustrative assumptions, not learned from real incidents.
    for episode in range(300):
        state = np.random.choice(states)

        for step in range(10):
            if np.random.rand() < epsilon:
                action = np.random.choice(actions)
            else:
                action = Q.loc[state].idxmax()

            r = reward(state, action)
            new_state = next_state(state)

            Q.loc[state, action] += alpha * (
                r + gamma * Q.loc[new_state].max() - Q.loc[state, action]
            )

            state = new_state

    st.subheader("🧠 Q-Table")
    st.dataframe(Q, use_container_width=True)

    st.subheader("📈 Optimal Policy")
    policy = Q.idxmax(axis=1)
    values = Q.max(axis=1)

    fig_policy, ax = plt.subplots(figsize=(7, 5))
    ax.bar(states, values)

    for i, state in enumerate(states):
        ax.text(
            i, values[state], policy[state],
            ha="center", va="bottom", fontweight="bold"
        )

    ax.set_title("Optimal Policy by Risk Level")
    ax.set_ylabel("Expected Utility")
    ax.grid(axis="y", alpha=0.25)
    fig_policy.tight_layout()

    st.pyplot(fig_policy)
    figures["policy"] = fig_policy

else:
    st.info(
        "Reinforcement Learning is disabled. Enable it from the sidebar "
        "to display the Q-learning analysis."
    )

# ============================================================
# APA INTERPRETATION
# ============================================================

st.subheader("📘 APA Interpretation")

def direction_text(ao_mean, baseline_mean, lower_is_better=True):
    if lower_is_better:
        return "reduces" if ao_mean < baseline_mean else "does not reduce"
    return "improves" if ao_mean > baseline_mean else "does not improve"


risk_direction = direction_text(
    df["AO-LACCP_Risk"].mean(),
    df["Baseline_Risk"].mean()
)

agility_direction = direction_text(
    df["AO-LACCP_Agility"].mean(),
    df["Baseline_Agility"].mean(),
    lower_is_better=False
)

latency_direction = direction_text(
    df["AO-LACCP_Latency"].mean(),
    df["Baseline_Latency"].mean()
)

st.markdown(
    f"""
### H1: Cyber Risk

**F(1, {2*n-2}) = {h1_f:.2f}, {significance_text(h1_p)}**

In the synthetic scenario, AO-LACCP {risk_direction} cyber risk
relative to the baseline.

**Decision:** {decision(h1_p)}

### H2: Cryptographic Agility

**F(1, {2*n-2}) = {h2_f:.2f}, {significance_text(h2_p)}**

In the synthetic scenario, AO-LACCP {agility_direction} cryptographic
agility relative to the baseline.

**Decision:** {decision(h2_p)}

### H3: Response Latency

**F(1, {2*n-2}) = {h3_f:.2f}, {significance_text(h3_p)}**

In the synthetic scenario, AO-LACCP {latency_direction} response latency
relative to the baseline.

**Decision:** {decision(h3_p)}
"""
)

# ============================================================
# PERFORMANCE SUMMARY
# ============================================================

st.subheader("📊 AO-LACCP Performance Summary")

baseline_risk_mean = df["Baseline_Risk"].mean()
ao_risk_mean = df["AO-LACCP_Risk"].mean()

baseline_latency_mean = df["Baseline_Latency"].mean()
ao_latency_mean = df["AO-LACCP_Latency"].mean()

baseline_agility_mean = df["Baseline_Agility"].mean()
ao_agility_mean = df["AO-LACCP_Agility"].mean()

risk_reduction = (
    (baseline_risk_mean - ao_risk_mean) / abs(baseline_risk_mean) * 100
    if baseline_risk_mean != 0 else np.nan
)

latency_reduction = (
    (baseline_latency_mean - ao_latency_mean)
    / abs(baseline_latency_mean) * 100
    if baseline_latency_mean != 0 else np.nan
)

agility_improvement = (
    (ao_agility_mean - baseline_agility_mean)
    / abs(baseline_agility_mean) * 100
    if baseline_agility_mean != 0 else np.nan
)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Cyber Risk Reduction", f"{risk_reduction:.2f}%")

with col2:
    st.metric("Latency Reduction", f"{latency_reduction:.2f}%")

with col3:
    st.metric("Agility Improvement", f"{agility_improvement:.2f}%")

# ============================================================
# PDF REPORT GENERATOR
# ============================================================

def add_table_page(pdf, data, title, figsize=(11, 8), font_size=8):
    fig, ax = plt.subplots(figsize=figsize)
    ax.axis("off")

    display_data = data.copy()

    for column in display_data.columns:
        if pd.api.types.is_numeric_dtype(display_data[column]):
            display_data[column] = display_data[column].round(4)

    table = ax.table(
        cellText=display_data.astype(str).values,
        colLabels=display_data.columns,
        loc="center"
    )

    table.auto_set_font_size(False)
    table.set_fontsize(font_size)
    table.scale(1, 1.5)
    ax.set_title(title)

    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def generate_pdf(
    data,
    descriptive,
    hypothesis_summary,
    anova_results,
    figure_dict,
    scenario,
    selected_crypto,
    selected_compliance,
    selected_governance
):
    buffer = io.BytesIO()

    with PdfPages(buffer) as pdf:
        # Title page
        fig, ax = plt.subplots(figsize=(8.5, 11))
        ax.axis("off")

        ax.text(
            0.5, 0.70,
            "AO-LACCP Simulation Report",
            ha="center", fontsize=18, fontweight="bold"
        )

        ax.text(
            0.5, 0.62,
            "AI-Orchestrated Latency-Aware Cryptographic Control Plane",
            ha="center", fontsize=11
        )

        ax.text(
            0.5, 0.54,
            f"Case Study: {scenario}",
            ha="center", fontsize=12
        )

        ax.text(
            0.5, 0.49,
            f"Cryptographic Model: {selected_crypto}",
            ha="center", fontsize=11
        )

        ax.text(
            0.5, 0.44,
            f"Compliance Level: {selected_compliance}",
            ha="center", fontsize=11
        )

        ax.text(
            0.5, 0.39,
            f"Governance: {', '.join(selected_governance) or 'None selected'}",
            ha="center", fontsize=10
        )

        ax.text(
            0.5, 0.28,
            "Synthetic demonstration results; not live financial-system evidence.",
            ha="center", fontsize=9
        )

        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

        # Dataset sample
        add_table_page(
            pdf,
            data.head(10),
            "Synthetic Dataset Sample",
            font_size=7
        )

        # Hypothesis figures and boxplots
        for key in [
            "hypothesis_4.2", "boxplot_4.2",
            "hypothesis_4.3", "boxplot_4.3",
            "hypothesis_4.4", "boxplot_4.4",
            "regression", "policy"
        ]:
            fig = figure_dict.get(key)

            if fig is not None:
                pdf.savefig(fig, bbox_inches="tight")

        add_table_page(
            pdf, descriptive, "Descriptive Statistics", font_size=8
        )

        add_table_page(
            pdf, hypothesis_summary, "Hypothesis Summary", font_size=7
        )

        add_table_page(
            pdf, anova_results, "One-Way ANOVA Results", font_size=7
        )

    buffer.seek(0)
    return buffer

# ============================================================
# DATASET DOWNLOAD
# ============================================================

if download_data:
    st.download_button(
        label="⬇ Download Synthetic Dataset",
        data=df.to_csv(index=False),
        file_name="AO_LACCP_synthetic_dataset.csv",
        mime="text/csv"
    )

# ============================================================
# PDF GENERATION
# ============================================================

if st.button("📄 Generate PDF Report"):
    pdf_file = generate_pdf(
        df,
        desc_table,
        summary,
        anova_table,
        figures,
        threat_scenario,
        crypto_model,
        compliance,
        governance
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
    try:
        output_file = "AO-LACCP_results.csv"
        summary.to_csv(output_file, index=False)

        st.success(f"Results saved to {os.path.abspath(output_file)}")

        st.download_button(
            label="⬇ Download Hypothesis Results",
            data=summary.to_csv(index=False),
            file_name="AO-LACCP_results.csv",
            mime="text/csv"
        )

    except OSError as exc:
        st.error(f"Could not save results: {exc}")

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
        AO-LACCP Artifact Simulation –
        Doctoral Research Demo | Any Questions?
    </p>
    """,
    unsafe_allow_html=True
)
when i run the full code, i don't see anything beside this

