"""AO-LACCP paired synthetic research demonstrator.

IMPORTANT RESEARCH LIMITATION
This application is a transparent, assumption-based simulator. It does not
independently prove real-world or production superiority. The baseline and
AO-LACCP prototype policies receive the same synthetic feature rows; ground
truth is reserved for evaluation. Outcome effectiveness and latency are
explicit model assumptions and must be calibrated/validated before making
empirical claims. Replace the illustrative policy functions with the actual
AO-LACCP implementation before describing results as tests of that artifact.

Run:
    pip install streamlit numpy pandas matplotlib scipy
    streamlit run ao_laccp_scientific_comparison.py
"""

import io
from typing import Dict, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from scipy import stats

st.set_page_config(page_title="AO-LACCP Paired Research Demonstrator", layout="wide")
st.title("AO-LACCP: Paired Comparative Research Demonstrator")
st.caption("Same scenarios for both policies • transparent assumptions • paired analysis")

st.warning(
    "Scientific-integrity notice: this app evaluates two explicitly coded policies on "
    "synthetic scenarios. It is not proof of production effectiveness. The outcome and "
    "latency models below are assumptions, not measurements from a live SOC or validated "
    "financial system. For a dissertation claim about the AO-LACCP artifact, verify that "
    "the AO policy function below matches your actual implemented decision logic."
)

# -----------------------------------------------------------------------------
# Experiment configuration
# -----------------------------------------------------------------------------
st.sidebar.header("Experiment configuration")
n_scenarios = st.sidebar.slider("Number of paired scenarios", 100, 5000, 1000, 100)
seed = st.sidebar.number_input("Random seed", min_value=0, max_value=999999, value=42, step=1)
scenario_mode = st.sidebar.selectbox(
    "Threat mix",
    ["Mixed threat population", "Normal operating conditions", "Latency spike",
     "Adversarial signal", "Compliance drift", "Combined multi-threat"],
)
crypto_mode = st.sidebar.selectbox("Configured cryptographic mode", ["RSA", "ECC", "PQC", "Hybrid"])
policy_note = st.sidebar.selectbox(
    "AO-LACCP policy profile",
    ["Adaptive (illustrative)", "Conservative (illustrative)"],
    help="This changes the prototype policy only. It is not a claim that a production AO-LACCP deployment uses this profile.",
)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Ground-truth labels are used only for scoring. Neither policy receives the label "
    "as an input. Both policies process identical feature values."
)

THREATS = ["benign", "brute_force", "phishing", "mitm", "data_exfiltration",
           "latency_spike", "compliance_drift", "combined_multi_threat"]
ATTACKS = set(THREATS) - {"benign"}
ACTION_LEVEL = {"Monitor": 0, "Mitigate": 1, "Isolate/Escalate": 2}

# All parameters in these tables are declared simulator assumptions.
# Replace/calibrate them from independent evidence before drawing empirical conclusions.
THREAT_SEVERITY = {
    "benign": 0.05, "brute_force": 0.70, "phishing": 0.60, "mitm": 0.82,
    "data_exfiltration": 0.90, "latency_spike": 0.55,
    "compliance_drift": 0.48, "combined_multi_threat": 0.95,
}
MIN_ACTION_FOR_MITIGATION = {
    "benign": 0, "brute_force": 1, "phishing": 1, "mitm": 2,
    "data_exfiltration": 2, "latency_spike": 1,
    "compliance_drift": 1, "combined_multi_threat": 2,
}
# Residual-risk multipliers by action level, applied equally to both policies.
RESIDUAL_MULTIPLIER = {"Monitor": 1.00, "Mitigate": 0.48, "Isolate/Escalate": 0.22}
ACTION_LATENCY_MS = {"Monitor": 5.0, "Mitigate": 22.0, "Isolate/Escalate": 40.0}


def generate_scenarios(n: int, random_seed: int, mode: str) -> pd.DataFrame:
    """Generate one feature table. Ground truth is retained only for evaluation."""
    rng = np.random.default_rng(random_seed)
    if mode == "Normal operating conditions":
        probs = [0.90, 0.02, 0.02, 0.01, 0.01, 0.02, 0.01, 0.01]
    elif mode == "Latency spike":
        probs = [0.50, 0.08, 0.06, 0.05, 0.06, 0.18, 0.02, 0.05]
    elif mode == "Adversarial signal":
        probs = [0.45, 0.14, 0.12, 0.10, 0.08, 0.03, 0.02, 0.06]
    elif mode == "Compliance drift":
        probs = [0.55, 0.06, 0.06, 0.04, 0.05, 0.04, 0.15, 0.05]
    elif mode == "Combined multi-threat":
        probs = [0.25, 0.12, 0.10, 0.10, 0.12, 0.08, 0.08, 0.15]
