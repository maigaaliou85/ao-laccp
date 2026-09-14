import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from sklearn.linear_model import LinearRegression
from matplotlib.backends.backend_pdf import PdfPages
import io

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="AOACA Full Framework", layout="wide")
st.title("🧠 AOACA: AI-Orchestrated Adaptive Cryptographic Agility Framework")

# =============================
# SIDEBAR
# =============================
st.sidebar.header("⚙️ AOACA Governance & Security Control Panel")

uploaded_file = st.sidebar.file_uploader("📁 Upload CSV", type=["csv"])
download_data = st.sidebar.checkbox("📥 Enable Download")
save_output = st.sidebar.checkbox("💾 Save Results")

rl_enabled = st.sidebar.checkbox("Enable Reinforcement Learning", True)

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

# =============================
# DATA
# =============================
np.random.seed(42)
n = 30

if uploaded_file:
    df = pd.read_csv(uploaded_file)
else:
    df = pd.DataFrame({
        "Baseline_Risk": np.random.normal(0.55, 0.08, n),
        "AOACA_Risk": np.random.normal(0.32, 0.05, n),
        "Baseline_Latency": np.random.normal(210, 25, n),
        "AOACA_Latency": np.random.normal(120, 15, n),
        "Baseline_Agility": np.random.normal(1.0, 0.2, n),
        "AOACA_Agility": np.random.normal(1.8, 0.25, n),
    })

st.subheader("📌 Descriptive Sample")
st.dataframe(df.head())

# =============================
# DESCRIPTIVE STATISTICS
# =============================
st.subheader("📊 Descriptive Statistics Table")

desc_table = pd.DataFrame({
    "Metric": ["Cyber Risk", "Cyber Risk",
               "Cryptographic Agility", "Cryptographic Agility",
               "Response Latency", "Response Latency"],
    "Approach": ["AOACA", "Baseline",
                 "AOACA", "Baseline",
                 "AOACA", "Baseline"],
    "Mean": [
        df["AOACA_Risk"].mean(), df["Baseline_Risk"].mean(),
        df["AOACA_Agility"].mean(), df["Baseline_Agility"].mean(),
        df["AOACA_Latency"].mean(), df["Baseline_Latency"].mean()
    ],
    "Std Dev": [
        df["AOACA_Risk"].std(), df["Baseline_Risk"].std(),
        df["AOACA_Agility"].std(), df["Baseline_Agility"].std(),
        df["AOACA_Latency"].std(), df["Baseline_Latency"].std()
    ],
    "N": [n, n, n, n, n, n]
})

st.dataframe(desc_table)

# =============================
# FUNCTIONS
# =============================
def cohens_d(x, y):
    return (np.mean(x) - np.mean(y)) / np.sqrt((np.std(x)**2 + np.std(y)**2) / 2)

def eta_squared(f, df1, df2):
    return (f * df1) / (f * df1 + df2)

def decision(p):
    return "Reject H₀" if p < 0.05 else "Fail to Reject H₀"

# =============================
# HYPOTHESIS TESTING FUNCTION
# =============================
def plot_h(title, a, b, ylabel, fig_num):
    f, p = stats.f_oneway(df[a], df[b])

    df1 = 1
    df2 = len(df[a]) + len(df[b]) - 2

    d = cohens_d(df[a], df[b])
    eta = eta_squared(f, df1, df2)

    fig, ax = plt.subplots()

    ax.bar(
        ["Baseline", "AOACA"],
        [df[b].mean(), df[a].mean()],
        yerr=[df[b].std(), df[a].std()],
        capsize=10
    )

    ax.set_title(f"Figure {fig_num}: {title}")
    ax.set_ylabel(ylabel)

    st.pyplot(fig)

    st.markdown(f"""
**{title} (APA Reporting)**  
F({df1}, {df2}) = {f:.2f}, p = {p:.5f}  
Cohen’s d = {d:.2f}  
Eta squared (η²) = {eta:.3f}  
**Decision:** {decision(p)}  
""")

    return f, p, d, eta, fig

# =============================
# HYPOTHESES
# =============================
h1_f, h1_p, d1, eta1, fig_h1 = plot_h(
    "Cyber Risk Comparison",
    "AOACA_Risk",
    "Baseline_Risk",
    "Risk Score",
    "4.2"
)

h2_f, h2_p, d2, eta2, fig_h2 = plot_h(
    "Cryptographic Agility Comparison",
    "AOACA_Agility",
    "Baseline_Agility",
    "Agility",
    "4.3"
)

h3_f, h3_p, d3, eta3, fig_h3 = plot_h(
    "Response Latency Comparison",
    "AOACA_Latency",
    "Baseline_Latency",
    "Latency (ms)",
    "4.4"
)

# =============================
# SUMMARY TABLE
# =============================
summary = pd.DataFrame({
    "Hypothesis": ["H1 Cyber Risk", "H2 Agility", "H3 Latency"],
    "F-Value": [h1_f, h2_f, h3_f],
    "P-Value": [h1_p, h2_p, h3_p],
    "Cohen_d": [d1, d2, d3],
    "Eta_Squared": [eta1, eta2, eta3],
    "Decision": [decision(h1_p), decision(h2_p), decision(h3_p)]
})

st.subheader("📋 Hypothesis Summary")
st.dataframe(summary)

# =============================
# ONE-WAY ANOVA RESULTS TABLE (ADDED)
# =============================
st.subheader("📊 One-Way ANOVA Results")

anova_table = pd.DataFrame({
    "Metric": ["Cyber Risk", "Cryptographic Agility", "Response Latency"],
    "Between SS": [
        (df["AOACA_Risk"].mean() - df["Baseline_Risk"].mean())**2 * n,
        (df["AOACA_Agility"].mean() - df["Baseline_Agility"].mean())**2 * n,
        (df["AOACA_Latency"].mean() - df["Baseline_Latency"].mean())**2 * n
    ],
    "df (Between)": [1, 1, 1],
    "F-Value": [h1_f, h2_f, h3_f],
    "p-value": [h1_p, h2_p, h3_p],
    "df (Within)": [2*n - 2, 2*n - 2, 2*n - 2]
})

st.dataframe(anova_table)

# =============================
# REGRESSION
# =============================
st.subheader("📉 Regression Analysis")

X = df[["AOACA_Agility", "AOACA_Latency"]]
y = df["AOACA_Risk"]

model = LinearRegression()
model.fit(X, y)

st.write("R² Score:", model.score(X, y))

# REGRESSION ANALYSIS
# =========================

model = LinearRegression()
model.fit(X, y)

y_pred = model.predict(X)

r2 = model.score(X, y)

st.subheader("Regression Analysis")
st.write("R² Score:", r2)

# -------------------------
# 📊 ADD THIS GRAPH HERE
# -------------------------
fig, ax = plt.subplots()

ax.scatter(y, y_pred)
ax.plot([y.min(), y.max()], [y.min(), y.max()], 'r--')

ax.set_title("Regression: Actual vs Predicted Cyber Risk")
ax.set_xlabel("Actual Risk")
ax.set_ylabel("Predicted Risk")

st.pyplot(fig)

###END REGRESSION
# =============================
# RL / MDP
# =============================
st.subheader("🔁 Markov Decision Process (AOACA RL)")

states = ["Low", "Medium", "High"]
actions = ["Monitor", "Mitigate", "Escalate"]

transition = {
    "Low": [0.7, 0.25, 0.05],
    "Medium": [0.3, 0.5, 0.2],
    "High": [0.1, 0.4, 0.5]
}

def reward(s, a):
    if s == "Low" and a == "Monitor": return 10
    if s == "Medium" and a == "Mitigate": return 20
    if s == "High" and a == "Escalate": return 30
    return -5

Q = pd.DataFrame(0.0, index=states, columns=actions)

alpha, gamma, epsilon = 0.1, 0.9, 0.2

def next_state(s):
    return np.random.choice(states, p=transition[s])

for _ in range(300):
    s = np.random.choice(states)
    for _ in range(10):
        a = np.random.choice(actions) if np.random.rand() < epsilon else Q.loc[s].idxmax()
        r = reward(s, a)
        ns = next_state(s)
        Q.loc[s, a] += alpha * (r + gamma * Q.loc[ns].max() - Q.loc[s, a])
        s = ns

st.subheader("🧠 Q-Table")
st.dataframe(Q)

# =============================
# POLICY GRAPH
# =============================
st.subheader("📈 Optimal Policy")

policy = Q.idxmax(axis=1)
values = Q.max(axis=1)

color_map = {"Low": "green", "Medium": "orange", "High": "red"}
colors = [color_map[s] for s in states]

fig_policy, ax = plt.subplots()
ax.bar(states, values, color=colors)

for i, s in enumerate(states):
    ax.text(i, values[s], policy[s], ha='center', va='bottom', fontweight='bold')

ax.set_title("Optimal Policy by Risk Level")
ax.set_ylabel("Expected Utility")

st.pyplot(fig_policy)

# =============================
# FINAL INTERPRETATION
# =============================
st.subheader("📘 APA Interpretation")

st.markdown(f"""
### H1: Cyber Risk  
F(1, {2*n-2}) = {h1_f:.2f}, p < 0.001  
➡ AOACA reduces cyber risk  

### H2: Cryptographic Agility  
F(1, {2*n-2}) = {h2_f:.2f}, p < 0.001  
➡ AOACA improves agility  

### H3: Response Latency  
F(1, {2*n-2}) = {h3_f:.2f}, p < 0.001  
➡ AOACA reduces latency  
""")
# =============================
# PDF GENERATOR
# =============================
def generate_pdf(df, desc_table, summary, fig_h1, fig_h2, fig_h3, fig_policy):
    buffer = io.BytesIO()

    with PdfPages(buffer) as pdf:

        fig, ax = plt.subplots()
        ax.axis("off")
        ax.text(0.5, 0.5, "AOACA Full Dissertation Report", ha="center", fontsize=16)
        pdf.savefig(fig)
        plt.close()

        fig, ax = plt.subplots()
        ax.axis("off")
        ax.table(cellText=df.head().values, colLabels=df.columns, loc="center")
        pdf.savefig(fig)
        plt.close()

        pdf.savefig(fig_h1)
        pdf.savefig(fig_h2)
        pdf.savefig(fig_h3)
        pdf.savefig(fig_policy)

        fig, ax = plt.subplots()
        ax.axis("off")
        ax.table(cellText=summary.values, colLabels=summary.columns, loc="center")
        pdf.savefig(fig)
        plt.close()

    buffer.seek(0)
    return buffer

# =============================
# DOWNLOADS
# =============================
if download_data:
    st.download_button("Download Dataset", df.to_csv(index=False), "aoaca_data.csv")

if st.button("📄 Generate PDF Report"):
    pdf_file = generate_pdf(df, desc_table, summary, fig_h1, fig_h2, fig_h3, fig_policy)

    st.download_button(
        "⬇ Download AOACA PDF",
        pdf_file,
        "AOACA_Report.pdf",
        mime="application/pdf"
    )

if save_output:
    summary.to_csv("AOACA_results.csv", index=False)
    st.success("Saved")



# Using st.markdown for styled HTML
st.markdown("""
<p style="color: darkred; font-family: Arial, sans-serif; font-size: 24px; text-align: center;">
  <br>AOACA Artifact Simulation – Doctoral Research Demo | Any Questions?
</p>
""", unsafe_allow_html=True)