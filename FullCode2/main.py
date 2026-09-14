import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import seaborn as sns
import matplotlib.pyplot as plt

st.set_page_config(page_title="AO-LACCP Multi-Agent Dashboard", layout="wide")
st.title("AO-LACCP: AI-Orchestrated Latency-Aware Cryptographic Control Plane")

# ----------------------------
# Sidebar: Simulation Settings
# ----------------------------
st.sidebar.header("Simulation Settings")
num_agents = st.sidebar.slider("Number of Agents", 1, 10, 5)
num_samples = st.sidebar.slider("Posterior Samples per Iteration", 100, 5000, 1000)
iterations = st.sidebar.slider("Number of Iterations", 1, 20, 10)
scenario_choice = st.sidebar.selectbox(
    "Threat Scenario", ["Normal", "Latency Spike", "Adversarial Signal", "Quantum Attack"]
)
epsilon = st.sidebar.slider("Convergence Threshold (ε)", 0.0001, 0.01, 0.001)

# ----------------------------
# Sidebar: User Override Options
# ----------------------------
crypto_choices_user = st.sidebar.multiselect(
    "Override Cryptography Actions (optional)", ["Hybrid", "PQC", "RSA"]
)
policy_choices_user = st.sidebar.multiselect(
    "Override Compliance/Policy Actions (optional)", ["ISO 27001", "NIST", "GDPR"]
)

# ----------------------------
# Threat Response Mapping
# ----------------------------
# Predefined recommended actions per threat scenario
threat_response = {
    "Normal": {"crypto": ["RSA"], "policy": ["ISO 27001"], "reason": "System operating under normal conditions."},
    "Latency Spike": {"crypto": ["Hybrid"], "policy": ["ISO 27001"], "reason": "Latency spikes; hybrid crypto + ISO recommended to maintain stability."},
    "Adversarial Signal": {"crypto": ["Hybrid", "PQC"], "policy": ["NIST"], "reason": "Detected adversarial signals; PQC + hybrid crypto + NIST compliance recommended."},
    "Quantum Attack": {"crypto": ["PQC", "Hybrid"], "policy": ["GDPR", "NIST"], "reason": "Quantum attack threat; post-quantum crypto + hybrid + strong compliance recommended."}
}

# ----------------------------
# Initialize Session State
# ----------------------------
if "history" not in st.session_state:
    st.session_state.history = {}
if "history_actions" not in st.session_state:
    st.session_state.history_actions = {}

# Initialize dictionaries for selected scenario
if scenario_choice not in st.session_state.history:
    st.session_state.history[scenario_choice] = {i: [] for i in range(num_agents)}
if scenario_choice not in st.session_state.history_actions:
    st.session_state.history_actions[scenario_choice] = {i: [] for i in range(num_agents)}

# ----------------------------
# Helper Functions
# ----------------------------
def bayesian_posterior(prior, ai_score, pqc_score, samples=num_samples, weight=0.5):
    likelihood = np.random.beta(ai_score*10+1, (1-ai_score)*10+1, size=samples) * \
                 np.random.beta(pqc_score*10+1, (1-pqc_score)*10+1, size=samples)
    posterior = prior*(1-weight) + likelihood*weight
    return np.clip(posterior, 0, 1)

def get_recommended_actions(mean_risk, scenario):
    # If user overrides, use them; else use threat mapping
    if crypto_choices_user or policy_choices_user:
        return crypto_choices_user or ["RSA"], policy_choices_user or ["ISO 27001"], "User override applied"
    return threat_response[scenario]["crypto"], threat_response[scenario]["policy"], threat_response[scenario]["reason"]

def policy_color(mean_risk):
    if mean_risk > 0.7:
        return "#ff4c4c"  # Red
    elif mean_risk > 0.5:
        return "#ffa500"  # Orange
    else:
        return "#90ee90"  # Green

# ----------------------------
# Run Simulation for Each Agent
# ----------------------------
for agent in range(num_agents):
    prior = st.session_state.history[scenario_choice][agent][-1].mean() if st.session_state.history[scenario_choice][agent] else 0.5
    ai_score_default = 0.6 if scenario_choice=="Normal" else 0.5
    pqc_score_default = 0.7 if scenario_choice=="Normal" else 0.6
    posterior_samples = bayesian_posterior(prior, ai_score_default, pqc_score_default, samples=num_samples)
    
    st.session_state.history[scenario_choice][agent].append(posterior_samples)
    rec_crypto, rec_policy, reason = get_recommended_actions(posterior_samples.mean(), scenario_choice)
    st.session_state.history_actions[scenario_choice][agent].append({
        "crypto": rec_crypto,
        "policy": rec_policy,
        "reason": reason
    })

# ----------------------------
# Convergence Check
# ----------------------------
converged = all(
    len(st.session_state.history[scenario_choice][agent]) > 1 and
    abs(st.session_state.history[scenario_choice][agent][-1].mean() - st.session_state.history[scenario_choice][agent][-2].mean()) < epsilon
    for agent in range(num_agents)
)

st.subheader("Simulation Summary")
st.write(f"Scenario: {scenario_choice}")
st.write(f"Number of Agents: {num_agents}")
st.write(f"Converged Across All Agents: {'✅ Yes' if converged else '❌ No'}")

# ----------------------------
# Heatmap
# ----------------------------
st.subheader("Interactive Multi-Agent Heatmap")
max_iters = max(len(st.session_state.history[scenario_choice][0]), 1)
z_data, hover_text = [], []

for agent in range(num_agents):
    row, hover_row = [], []
    for idx, posterior in enumerate(st.session_state.history[scenario_choice][agent]):
        mean_risk = posterior.mean()
        row.append(mean_risk)
        action_info = st.session_state.history_actions[scenario_choice][agent][idx]
        hover_row.append(f"Agent {agent+1}<br>Iter {idx+1}<br>Mean Risk: {mean_risk:.2f}<br>"
                         f"Crypto: {', '.join(action_info['crypto'])}<br>"
                         f"Policy: {', '.join(action_info['policy'])}<br>"
                         f"Reason: {action_info['reason']}")
    while len(row) < max_iters:
        row.append(None)
        hover_row.append("")
    z_data.append(row)
    hover_text.append(hover_row)

fig = go.Figure(data=go.Heatmap(
    z=z_data,
    text=hover_text,
    hoverinfo='text',
    colorscale=[[0, "#90ee90"], [0.5, "#ffa500"], [1, "#ff4c4c"]],
    zmin=0, zmax=1
))
fig.update_layout(
    xaxis=dict(title="Iteration", dtick=1),
    yaxis=dict(title="Agent", dtick=1, autorange="reversed"),
    height=600 + num_agents*20,
    width=1000
)
st.plotly_chart(fig, use_container_width=True)

# ----------------------------
# Individual Agent What-If
# ----------------------------
st.subheader("Agent-Specific What-If Analysis")
for agent in range(num_agents):
    agent_iters = len(st.session_state.history[scenario_choice][agent])
    iter_sel = st.slider(
        f"Iteration for Agent {agent+1}",
        1,
        max(agent_iters,2),
        1
    )
    posterior_data = st.session_state.history[scenario_choice][agent][iter_sel-1]

    # Agent-specific adjustments
    ai_score = st.slider(f"AI Score Agent {agent+1}", 0.0, 1.0, float(np.mean(posterior_data)), key=f"ai_{agent}")
    pqc_score = st.slider(f"PQC Score Agent {agent+1}", 0.0, 1.0, float(np.mean(posterior_data)), key=f"pqc_{agent}")
    posterior_whatif = bayesian_posterior(posterior_data.mean(), ai_score, pqc_score, samples=num_samples)

    # Histogram
    fig_agent, ax_agent = plt.subplots(figsize=(5,2.5))
    sns.histplot(posterior_whatif + np.random.normal(0,0.01,len(posterior_whatif)), bins=30, kde=True, color="skyblue", ax=ax_agent)
    ax_agent.axvline(posterior_whatif.mean(), color='r', linestyle='--', label=f"Mean: {posterior_whatif.mean():.4f}")
    ax_agent.set_xlabel("Risk")
    ax_agent.set_ylabel("Frequency")
    ax_agent.set_title(f"Agent {agent+1} Posterior Iter {iter_sel}")
    ax_agent.legend(fontsize=6)
    st.pyplot(fig_agent, use_container_width=True)

    # Update chosen crypto/policy if user overrides
    chosen_crypto = st.multiselect("Choose Crypto", ["Hybrid", "PQC", "RSA"], default=st.session_state.history_actions[scenario_choice][agent][iter_sel-1]["crypto"], key=f"crypto_{agent}")
    chosen_policy = st.multiselect("Choose Policy", ["ISO 27001", "NIST", "GDPR"], default=st.session_state.history_actions[scenario_choice][agent][iter_sel-1]["policy"], key=f"policy_{agent}")
    st.session_state.history_actions[scenario_choice][agent][iter_sel-1]["crypto"] = chosen_crypto
    st.session_state.history_actions[scenario_choice][agent][iter_sel-1]["policy"] = chosen_policy

    # Explanation
    st.write("**Reason for Recommended Actions:**")
    st.info(st.session_state.history_actions[scenario_choice][agent][iter_sel-1]["reason"])

# ----------------------------
# AO-LACCP Final Results
# ----------------------------
st.subheader("AO-LACCP Results")
final_table = []
for agent in range(num_agents):
    posterior = st.session_state.history[scenario_choice][agent][-1]
    actions = st.session_state.history_actions[scenario_choice][agent][-1]
    final_table.append({
        "Agent": agent+1,
        "Mean Risk": posterior.mean(),
        "Crypto": ", ".join(actions["crypto"]),
        "Policy": ", ".join(actions["policy"]),
        "Reason": actions["reason"]
    })
df_final = pd.DataFrame(final_table)
st.dataframe(df_final)

st.markdown("""
**Note on Design Science Research (DSR):**  
AO-LACCP demonstrates operational integration of cryptography and compliance actions in real-time.  
By combining Bayesian risk estimation with adaptive policy recommendations per threat scenario, it provides traceable, actionable measures per agent and scenario — showing how DSR enables orchestrated cybersecurity decisions in a FinTech environment.
""")

# Using st.markdown for styled HTML
st.markdown("""
<p style="color: darkred; font-family: Arial, sans-serif; font-size: 24px; text-align: center;">
  <br>AO-LACCP Artifact Simulation – Doctoral Research Demo | Any Questions?
</p>
""", unsafe_allow_html=True)
