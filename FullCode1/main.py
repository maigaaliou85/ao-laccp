import io
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from sklearn.linear_model import LinearRegression
from matplotlib.backends.backend_pdf import PdfPages

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(page_title="AO-LACCP Full Framework", layout="wide")
st.title("🧠 AO-LACCP: AI-Orchestrated Adaptive Cryptographic Agility Framework")
st.caption("AI-Orchestrated Latency-Aware Cryptographic Control Plane for Adaptive Cyber Resilience")

# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.header("⚙️ AO-LACCP Governance & Security Control Panel")
download_data = st.sidebar.checkbox("📥 Enable Dataset Download", value=False)
save_output = st.sidebar.checkbox("💾 Enable Results Download", value=False)
rl_enabled = st.sidebar.checkbox("🔁 Enable Illustrative Q-Learning Demonstration", value=True)
random_seed = int(st.sidebar.number_input("🎲 Random Seed", min_value=0, max_value=2_147_483_647, value=42, step=1))
n = int(st.sidebar.number_input("📊 Observations per simulation", min_value=10, max_value=1000, value=30, step=10))
n_repeats = int(st.sidebar.number_input("🔁 Repeated simulation runs", min_value=1, max_value=100, value=30, step=1,
    help="Repeated synthetic simulation replications; these are not additional human participants."))

threat_scenario = st.sidebar.selectbox("🎯 Case Study / Threat Scenario", [
    "Normal Operating Conditions", "Latency Spike", "Adversarial Signal",
    "Compliance Drift", "Combined Multi-Threat"
])
st.sidebar.markdown("---")
governance = st.sidebar.multiselect("🏛 Governance Frameworks", ["ISO 27001", "GDPR", "PCI DSS", "NIST CSF", "SOX"], default=["ISO 27001", "NIST CSF"])
crypto_model = st.sidebar.selectbox("🔐 Cryptographic Model", ["RSA", "ECC", "PQC", "Hybrid"])
compliance = st.sidebar.selectbox("📜 Compliance Level", ["Low", "Medium", "High", "Very High"])

st.info(
    f"**Selected Case Study:** {threat_scenario}  \n"
    f"**Cryptographic Model:** {crypto_model}  \n"
    f"**Compliance Level:** {compliance}  \n"
    f"**Governance Frameworks:** {', '.join(governance) if governance else 'None selected'}  \n"
    f"**Random seed:** {random_seed} | **Observations/run:** {n} | **Repeated runs:** {n_repeats}"
)

# ============================================================
# SYNTHETIC THREAT MODEL
# Same scenario adjustments are applied to both approaches.
# These are illustrative assumptions, not empirically measured effects.
# ============================================================
THREAT_ADJUSTMENTS = {
    "Normal Operating Conditions": {"risk": 0.00, "latency_ms": 0.0, "agility": 0.00},
    "Latency Spike": {"risk": 0.00, "latency_ms": 50.0, "agility": 0.00},
    "Adversarial Signal": {"risk": 0.08, "latency_ms": 0.0, "agility": 0.00},
    "Compliance Drift": {"risk": 0.00, "latency_ms": 0.0, "agility": -0.05},
    "Combined Multi-Threat": {"risk": 0.08, "latency_ms": 50.0, "agility": -0.05},
}

adjustment = THREAT_ADJUSTMENTS[threat_scenario]
st.subheader("🧭 Simulation Assumptions")
st.write("The selected scenario applies the same configured adjustment to both systems. Values are synthetic assumptions and should be justified/calibrated before formal dissertation reporting.")
st.dataframe(pd.DataFrame([
    {"Metric": "Risk score adjustment", "Applied equally to both": adjustment["risk"]},
    {"Metric": "Latency adjustment (ms)", "Applied equally to both": adjustment["latency_ms"]},
    {"Metric": "Agility adjustment", "Applied equally to both": adjustment["agility"]},
]), use_container_width=True, hide_index=True)

# ============================================================
# DATA GENERATION
# ============================================================
def generate_simulation(seed: int, scenario: str, observations: int) -> pd.DataFrame:
    """Create one reproducible synthetic run with equal scenario penalties."""
    rng = np.random.default_rng(seed)
    data = pd.DataFrame({
        "Baseline_Risk": rng.normal(0.55, 0.08, observations),
        "AO-LACCP_Risk": rng.normal(0.32, 0.05, observations),
        "Baseline_Latency": rng.normal(210, 25, observations),
        "AO-LACCP_Latency": rng.normal(120, 15, observations),
        "Baseline_Agility": rng.normal(1.0, 0.2, observations),
        "AO-LACCP_Agility": rng.normal(1.8, 0.25, observations),
    })
    effects = THREAT_ADJUSTMENTS[scenario]
    for col in ["Baseline_Risk", "AO-LACCP_Risk"]:
        data[col] += effects["risk"]
        data[col] = data[col].clip(0, 1)  # risk is assumed normalized to [0, 1]
    for col in ["Baseline_Latency", "AO-LACCP_Latency"]:
        data[col] = (data[col] + effects["latency_ms"]).clip(lower=0)
    # Agility is an index in this model, not a probability; do not clip to [0, 1].
    for col in ["Baseline_Agility", "AO-LACCP_Agility"]:
        data[col] += effects["agility"]
    return data

# Current run used for dashboard tables and plots.
df = generate_simulation(random_seed, threat_scenario, n)

# Repeated, reproducible runs with deterministic distinct seeds.
replicate_records = []
for run_index in range(n_repeats):
    run_df = generate_simulation(random_seed + run_index, threat_scenario, n)
    br, ar = run_df["Baseline_Risk"].mean(), run_df["AO-LACCP_Risk"].mean()
    bl, al = run_df["Baseline_Latency"].mean(), run_df["AO-LACCP_Latency"].mean()
    ba, aa = run_df["Baseline_Agility"].mean(), run_df["AO-LACCP_Agility"].mean()
    replicate_records.append({
        "Run": run_index + 1,
        "Seed": random_seed + run_index,
        "Baseline_Mean_Risk": br,
        "AO-LACCP_Mean_Risk": ar,
        "Risk_Difference_Baseline_minus_AO": br - ar,
        "Baseline_Mean_Latency_ms": bl,
        "AO-LACCP_Mean_Latency_ms": al,
        "Latency_Difference_Baseline_minus_AO_ms": bl - al,
        "Baseline_Mean_Agility": ba,
        "AO-LACCP_Mean_Agility": aa,
        "Agility_Difference_AO_minus_Baseline": aa - ba,
    })
replications = pd.DataFrame(replicate_records)

# ============================================================
# DESCRIPTIVE SAMPLE / STATISTICS
# ============================================================
st.subheader("📌 Descriptive Sample")
st.dataframe(df.head(), use_container_width=True)
st.caption(f"Synthetic demonstration dataset: {n} observations in this run; {n_repeats} repeated simulation runs.")

st.subheader("📊 Descriptive Statistics Table")
desc_rows = []
for metric, ao_col, base_col in [
    ("Cyber Risk", "AO-LACCP_Risk", "Baseline_Risk"),
    ("Cryptographic Agility", "AO-LACCP_Agility", "Baseline_Agility"),
    ("Response Latency (ms)", "AO-LACCP_Latency", "Baseline_Latency"),
]:
    for approach, col in [("AO-LACCP", ao_col), ("Baseline", base_col)]:
        desc_rows.append({"Metric": metric, "Approach": approach, "Mean": df[col].mean(), "Std Dev": df[col].std(ddof=1), "N": len(df)})
desc_table = pd.DataFrame(desc_rows)
st.dataframe(desc_table, use_container_width=True, hide_index=True)

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def cohens_d(x, y):
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    nx, ny = len(x), len(y)
    if nx < 2 or ny < 2:
        return np.nan
    pooled_var = (((nx - 1) * np.var(x, ddof=1)) + ((ny - 1) * np.var(y, ddof=1))) / (nx + ny - 2)
    pooled_sd = np.sqrt(pooled_var)
    return 0.0 if pooled_sd == 0 else (np.mean(x) - np.mean(y)) / pooled_sd


def eta_squared(f, df1, df2):
    denom = f * df1 + df2
    return np.nan if not np.isfinite(denom) or denom == 0 else (f * df1) / denom


def decision(p):
    if not np.isfinite(p):
        return "Not estimable"
    return "Reject H₀" if p < 0.05 else "Fail to Reject H₀"


def significance_text(p):
    if not np.isfinite(p):
        return "p not estimable"
    return "p < .001" if p < 0.001 else f"p = {p:.5f}"


def safe_f_oneway(x, y):
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if len(x) < 2 or len(y) < 2:
        return np.nan, np.nan
    with np.errstate(invalid="ignore", divide="ignore"):
        f_value, p_value = stats.f_oneway(x, y)
    return float(f_value), float(p_value)


def between_ss(x, y):
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    mx, my = np.mean(x), np.mean(y)
    grand = (len(x) * mx + len(y) * my) / (len(x) + len(y))
    return len(x) * (mx - grand) ** 2 + len(y) * (my - grand) ** 2

# ============================================================
# HYPOTHESIS TESTING
# ============================================================
st.header("🧪 Hypothesis Testing")
st.warning(
    "Statistical note: this generator draws separate samples for the two approaches, "
    "so the current one-way ANOVA treats them as independent groups. If your formal "
    "experiment uses matched trials or paired inputs, use paired tests or a repeated-measures "
    "design. These synthetic-data p-values are not participant-study findings."
)


def plot_h(title, ao_column, baseline_column, ylabel, fig_num):
    ao_data = df[ao_column].to_numpy()
    baseline_data = df[baseline_column].to_numpy()
    f_value, p_value = safe_f_oneway(ao_data, baseline_data)
    df1, df2 = 1, len(ao_data) + len(baseline_data) - 2
    d_value = cohens_d(ao_data, baseline_data)
    eta_value = eta_squared(f_value, df1, df2)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.bar(["Baseline", "AO-LACCP"], [baseline_data.mean(), ao_data.mean()],
           yerr=[baseline_data.std(ddof=1), ao_data.std(ddof=1)], capsize=10)
    ax.set_title(f"Figure {fig_num}: {title}")
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.25)
    plt.tight_layout()
    st.pyplot(fig, clear_figure=False)
    st.markdown(f"""
### {title} — APA-Style Reporting

**F({df1}, {df2}) = {f_value:.2f}, {significance_text(p_value)}**

**Cohen's d = {d_value:.2f}**

**Eta squared (η²) = {eta_value:.3f}**

**Decision:** {decision(p_value)}
""")
    return f_value, p_value, d_value, eta_value, fig

h1_f, h1_p, d1, eta1, fig_h1 = plot_h("Cyber Risk Comparison", "AO-LACCP_Risk", "Baseline_Risk", "Risk Score", "4.2")
h2_f, h2_p, d2, eta2, fig_h2 = plot_h("Cryptographic Agility Comparison", "AO-LACCP_Agility", "Baseline_Agility", "Agility Index", "4.3")
h3_f, h3_p, d3, eta3, fig_h3 = plot_h("Response Latency Comparison", "AO-LACCP_Latency", "Baseline_Latency", "Latency (ms)", "4.4")

# ============================================================
# HYPOTHESIS SUMMARY / ANOVA TABLE
# ============================================================
st.subheader("📋 Hypothesis Summary")
summary = pd.DataFrame({
    "Hypothesis": ["H1 Cyber Risk", "H2 Agility", "H3 Latency"],
    "F-Value": [h1_f, h2_f, h3_f],
    "P-Value": [h1_p, h2_p, h3_p],
    "Cohen_d": [d1, d2, d3],
    "Eta_Squared": [eta1, eta2, eta3],
    "Decision": [decision(h1_p), decision(h2_p), decision(h3_p)],
})
st.dataframe(summary, use_container_width=True, hide_index=True)

st.subheader("📊 One-Way ANOVA Results")
anova_table = pd.DataFrame({
    "Metric": ["Cyber Risk", "Cryptographic Agility", "Response Latency"],
    "Between SS": [between_ss(df["AO-LACCP_Risk"], df["Baseline_Risk"]),
                   between_ss(df["AO-LACCP_Agility"], df["Baseline_Agility"]),
                   between_ss(df["AO-LACCP_Latency"], df["Baseline_Latency"])],
    "df (Between)": [1, 1, 1],
    "F-Value": [h1_f, h2_f, h3_f],
    "p-value": [h1_p, h2_p, h3_p],
    "df (Within)": [2 * n - 2] * 3,
})
st.dataframe(anova_table, use_container_width=True, hide_index=True)

# ============================================================
# REPEATED-RUN RESULTS
# ============================================================
st.subheader("🔁 Repeated Simulation Results")
repeat_summary = pd.DataFrame([
    {"Metric": "Risk difference (Baseline − AO-LACCP)", "Mean across runs": replications["Risk_Difference_Baseline_minus_AO"].mean(), "SD across runs": replications["Risk_Difference_Baseline_minus_AO"].std(ddof=1), "Runs": n_repeats},
    {"Metric": "Latency difference (Baseline − AO-LACCP), ms", "Mean across runs": replications["Latency_Difference_Baseline_minus_AO_ms"].mean(), "SD across runs": replications["Latency_Difference_Baseline_minus_AO_ms"].std(ddof=1), "Runs": n_repeats},
    {"Metric": "Agility difference (AO-LACCP − Baseline)", "Mean across runs": replications["Agility_Difference_AO_minus_Baseline"].mean(), "SD across runs": replications["Agility_Difference_AO_minus_Baseline"].std(ddof=1), "Runs": n_repeats},
])
st.dataframe(repeat_summary, use_container_width=True, hide_index=True)
st.caption("Repeated runs summarize variability in the synthetic simulation. They are not additional human participants or independent real-world experiments.")

# ============================================================
# REGRESSION
# ============================================================
st.subheader("📉 Regression Analysis")
X = df[["AO-LACCP_Agility", "AO-LACCP_Latency"]]
y = df["AO-LACCP_Risk"]
model = LinearRegression().fit(X, y)
y_pred = model.predict(X)
r2 = model.score(X, y)
st.metric("In-sample R² Score", f"{r2:.4f}")
st.caption("This is an in-sample fit to synthetic data, not out-of-sample predictive validation.")
regression_results = pd.DataFrame({"Predictor": ["AO-LACCP Agility", "AO-LACCP Latency"], "Coefficient": model.coef_})
st.dataframe(regression_results, use_container_width=True, hide_index=True)
st.write("Regression Intercept:", model.intercept_)
fig_regression, ax = plt.subplots(figsize=(7, 5))
ax.scatter(y, y_pred)
minimum, maximum = min(y.min(), y_pred.min()), max(y.max(), y_pred.max())
ax.plot([minimum, maximum], [minimum, maximum], "r--")
ax.set_title("Regression: Actual vs Predicted Cyber Risk")
ax.set_xlabel("Actual Risk")
ax.set_ylabel("Predicted Risk")
ax.grid(alpha=0.25)
plt.tight_layout()
st.pyplot(fig_regression)

# ============================================================
# ILLUSTRATIVE Q-LEARNING / MDP
# ============================================================
fig_policy = None
if rl_enabled:
    st.subheader("🔁 Illustrative Markov Decision Process (Q-Learning)")
    st.caption("This simplified demonstration uses configured transition probabilities and rewards. It is not a validated production reinforcement-learning controller.")
    states, actions = ["Low", "Medium", "High"], ["Monitor", "Mitigate", "Escalate"]
    transition = {"Low": [0.7, 0.25, 0.05], "Medium": [0.3, 0.5, 0.2], "High": [0.1, 0.4, 0.5]}

    def reward(state, action):
        if state == "Low" and action == "Monitor": return 10
        if state == "Medium" and action == "Mitigate": return 20
        if state == "High" and action == "Escalate": return 30
        return -5

    Q = pd.DataFrame(0.0, index=states, columns=actions)
    alpha, gamma, epsilon = 0.1, 0.9, 0.2
    rl_rng = np.random.default_rng(random_seed + 100_000)

    def next_state(state):
        return rl_rng.choice(states, p=transition[state])

    for episode in range(300):
        state = rl_rng.choice(states)
        for step in range(10):
            if rl_rng.random() < epsilon:
                action = rl_rng.choice(actions)
            else:
                values = Q.loc[state].to_numpy(dtype=float)
                best = np.flatnonzero(np.isclose(values, values.max()))
                action = actions[int(rl_rng.choice(best))]
            r = reward(state, action)
            new_state = next_state(state)
            Q.loc[state, action] += alpha * (r + gamma * Q.loc[new_state].max() - Q.loc[state, action])
            state = new_state
    st.subheader("🧠 Q-Table")
    st.dataframe(Q, use_container_width=True)
    st.subheader("📈 Learned Policy")
    policy, values = Q.idxmax(axis=1), Q.max(axis=1)
    fig_policy, ax = plt.subplots(figsize=(7, 5))
    ax.bar(states, values)
    for i, state in enumerate(states):
        ax.text(i, values[state], policy[state], ha="center", va="bottom", fontweight="bold")
    ax.set_title("Learned Policy by Illustrative Risk Level")
    ax.set_ylabel("Estimated Q-Value")
    ax.grid(axis="y", alpha=0.25)
    plt.tight_layout()
    st.pyplot(fig_policy)
else:
    st.info("Q-learning demonstration is disabled. Enable it in the sidebar to display the Q-table and policy.")

# ============================================================
# APA-STYLE INTERPRETATION
# ============================================================
st.subheader("📘 APA-Style Interpretation")
risk_direction = "lower mean risk" if df["AO-LACCP_Risk"].mean() < df["Baseline_Risk"].mean() else "higher or equal mean risk"
agility_direction = "higher mean cryptographic agility" if df["AO-LACCP_Agility"].mean() > df["Baseline_Agility"].mean() else "lower or equal mean cryptographic agility"
latency_direction = "lower mean response latency" if df["AO-LACCP_Latency"].mean() < df["Baseline_Latency"].mean() else "higher or equal mean response latency"
st.markdown(f"""### H1: Cyber Risk

**F(1, {2*n-2}) = {h1_f:.2f}, {significance_text(h1_p)}**

In this synthetic run, AO-LACCP has **{risk_direction}** than the baseline. This describes the configured simulation and is not proof of real-world causal impact.

**Decision:** {decision(h1_p)}""")
st.markdown(f"""### H2: Cryptographic Agility

**F(1, {2*n-2}) = {h2_f:.2f}, {significance_text(h2_p)}**

In this synthetic run, AO-LACCP has **{agility_direction}** than the baseline.

**Decision:** {decision(h2_p)}""")
st.markdown(f"""### H3: Response Latency

**F(1, {2*n-2}) = {h3_f:.2f}, {significance_text(h3_p)}**

In this synthetic run, AO-LACCP has **{latency_direction}** than the baseline.

**Decision:** {decision(h3_p)}""")

# ============================================================
# PERFORMANCE SUMMARY
# ============================================================
st.subheader("📊 AO-LACCP Performance Summary")
base_risk, ao_risk = df["Baseline_Risk"].mean(), df["AO-LACCP_Risk"].mean()
base_latency, ao_latency = df["Baseline_Latency"].mean(), df["AO-LACCP_Latency"].mean()
base_agility, ao_agility = df["Baseline_Agility"].mean(), df["AO-LACCP_Agility"].mean()
risk_reduction = (base_risk - ao_risk) / abs(base_risk) * 100 if not np.isclose(base_risk, 0) else np.nan
latency_reduction = (base_latency - ao_latency) / abs(base_latency) * 100 if not np.isclose(base_latency, 0) else np.nan
agility_improvement = (ao_agility - base_agility) / abs(base_agility) * 100 if not np.isclose(base_agility, 0) else np.nan
col1, col2, col3 = st.columns(3)
with col1: st.metric("Relative Risk Difference", f"{risk_reduction:.2f}%")
with col2: st.metric("Relative Latency Difference", f"{latency_reduction:.2f}%")
with col3: st.metric("Relative Agility Difference", f"{agility_improvement:.2f}%")
st.caption("Positive values indicate lower risk/latency or higher agility for AO-LACCP under these formulas. These are descriptive synthetic comparisons, not proof of causality.")

# ============================================================
# PDF REPORT HELPERS
# ============================================================
def add_table_page(pdf, dataframe, title, font_size=8):
    fig, ax = plt.subplots(figsize=(11, 8))
    ax.axis("off")
    table = ax.table(cellText=dataframe.round(4).astype(str).values, colLabels=dataframe.columns, loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(font_size)
    table.scale(1, 1.4)
    ax.set_title(title)
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def generate_pdf(data, descriptive_table, hypothesis_summary, anova_results,
                 repeated_summary, repeated_data, figure_h1, figure_h2,
                 figure_h3, figure_reg, figure_policy, scenario,
                 selected_crypto, selected_compliance, selected_governance,
                 seed, observations, repeated_runs):
    buffer = io.BytesIO()
    with PdfPages(buffer) as pdf:
        fig, ax = plt.subplots(figsize=(8.5, 11))
        ax.axis("off")
        ax.text(0.5, 0.72, "AO-LACCP Synthetic Simulation Report", ha="center", fontsize=18, fontweight="bold")
        ax.text(0.5, 0.64, "AI-Orchestrated Latency-Aware Cryptographic Control Plane", ha="center", fontsize=11)
        ax.text(0.5, 0.56, f"Scenario: {scenario}", ha="center", fontsize=11)
        ax.text(0.5, 0.51, f"Cryptographic model: {selected_crypto}", ha="center", fontsize=10)
        ax.text(0.5, 0.46, f"Compliance level: {selected_compliance}", ha="center", fontsize=10)
        ax.text(0.5, 0.41, f"Governance frameworks: {', '.join(selected_governance) if selected_governance else 'None'}", ha="center", fontsize=9)
        ax.text(0.5, 0.35, f"Random seed: {seed}", ha="center", fontsize=10)
        ax.text(0.5, 0.30, f"Observations per run: {observations}", ha="center", fontsize=10)
        ax.text(0.5, 0.25, f"Repeated simulation runs: {repeated_runs}", ha="center", fontsize=10)
        ax.text(0.5, 0.14, "Synthetic demonstration only; configured parameters are not empirical estimates.", ha="center", fontsize=9, wrap=True)
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)
        add_table_page(pdf, data.head(10), "Synthetic Dataset Sample")
        pdf.savefig(figure_h1)
        pdf.savefig(figure_h2)
        pdf.savefig(figure_h3)
        pdf.savefig(figure_reg)
        if figure_policy is not None:
            pdf.savefig(figure_policy)
        add_table_page(pdf, descriptive_table, "Descriptive Statistics")
        add_table_page(pdf, hypothesis_summary, "Hypothesis Summary", 7)
        add_table_page(pdf, anova_results, "One-Way ANOVA Results", 7)
        add_table_page(pdf, repeated_summary, "Repeated Simulation Summary", 7)
        add_table_page(pdf, repeated_data.head(30), "Repeated Simulation Run-Level Results", 6)
    buffer.seek(0)
    return buffer

# ============================================================
# DOWNLOAD DATA / RESULTS
# ============================================================
if download_data:
    st.download_button("⬇ Download Current Synthetic Dataset", data=df.to_csv(index=False), file_name="AO_LACCP_synthetic_dataset.csv", mime="text/csv")
if save_output:
    st.download_button("⬇ Download Repeated Simulation Results", data=replications.to_csv(index=False), file_name="AO_LACCP_repeated_simulation_results.csv", mime="text/csv")
    st.download_button("⬇ Download Hypothesis Summary", data=summary.to_csv(index=False), file_name="AO_LACCP_hypothesis_summary.csv", mime="text/csv")

# ============================================================
# GENERATE PDF
# ============================================================
if st.button("📄 Prepare PDF Report"):
    pdf_file = generate_pdf(
        df, desc_table, summary, anova_table, repeat_summary, replications,
        fig_h1, fig_h2, fig_h3, fig_regression,
        fig_policy if rl_enabled else None, threat_scenario, crypto_model,
        compliance, governance, random_seed, n, n_repeats
    )
    st.download_button("⬇ Download AO-LACCP PDF", data=pdf_file, file_name="AO-LACCP_Report.pdf", mime="application/pdf")

# ============================================================
# FOOTER
# ============================================================
st.markdown("""
<p style="color: darkred; font-family: Arial, sans-serif; font-size: 24px; text-align: center;">
AO-LACCP Artifact Simulation – Doctoral Research Demo | Any Questions?
</p>
""", unsafe_allow_html=True)

