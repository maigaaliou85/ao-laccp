
no good again. it shows the samething
The fact that the same problem persists suggests the issue may not be the HTML itself. We need to make the title page independent of HTML rendering so Streamlit displays the text correctly even if HTML is being escaped or handled unexpectedly.

My recommendation is to remove the HTML entirely from the title page. Streamlit has native functions for titles, headings, centered content, and text. This also makes the page easier to maintain.

1. Replace show_title_page() completely
Delete your existing function and replace it with this version. This version contains no HTML tags and does not use unsafe_allow_html=True.



    st.info("AO-LACCP Artifact Simulation – Doctoral Research Demo")

    # Author information
    st.divider()

    left_col, center_col, right_col = st.columns([1, 3, 1])

    with center_col:
        st.markdown("### Aliou Maiga")

        st.write("**Dissertation Committee**")
        st.write("Michelle Liu, PhD — Committee Chair")
        st.write("Nathan Green, PhD — Committee Member")
        st.write("Seyedamin Pouriyeh, PhD — External Reader")
        st.write("Anne Magro, PhD — Dean")

        st.divider()

        st.write(
            "College of Business, Innovation, Leadership, "
            "and Technology"
        )

        st.write(
            "A Dissertation Proposal Presented in Partial Fulfillment "
            "of the Requirements for the Degree of Doctor of Science"
        )

        st.markdown("**Marymount University**")
        st.write("May 2027")

    st.divider()

    # Navigation instructions
    st.header("Research Demonstration")

    st.write(
        "Use the sidebar to access the AO-LACCP framework, "
        "multi-agent orchestration, threat scenarios, and "
        "scientific research evaluation modules."
    )

    st.success(
        "Select a module from the sidebar to open its interface. "
        "Choose Home to return to this page."
    )

    st.subheader("Available Modules")

    st.markdown(
        """
        - **Full Code 1:** AO-LACCP Full Framework
        - **Full Code 2:** AO-LACCP Multi-Agent
        - **Case Study Scenario:** Threat Scenarios
        - **Full Code 3:** AO-LACCP Scientific Research Evaluation
        """
    )


2. If the same HTML still appears
Because this replacement contains no HTML, seeing the same literal <p> or <br> tags means the deployed page is likely rendering old code or displaying that content from another location.

Check these three things:

In GitHub, open the exact dashboard.py file used by Streamlit and confirm that the old show_title_page() function is gone.

Search the repository for TOPIC: AI-Orchestrated Cyber Resilience and Michelle Liu, PhD. Check whether another file contains the old HTML.

In Streamlit Community Cloud, open Manage app and review the app's deployment logs. Confirm that it is deploying the repository, branch, and entry-point file you edited.

Please do not replace the entire dashboard again yet. First replace only this function and redeploy. If the HTML tags still appear, send me the URL of your deployed Streamlit app, and I can help identify whether the problem is in the entry-point file or one of the imported modules.

full code
Here is the complete dashboard.py with the title page rewritten using native Streamlit elements. This version removes HTML from the title page entirely and retains your four modules and the corrected navigation callback.

Replace the entire contents of your existing dashboard.py with this code.


import os
import sys
import importlib.util

import streamlit as st
from PIL import Image

# ============================================================
# AO-LACCP DASHBOARD CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AO-LACCP Dashboard",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "marymount_logo.png")

# Sidebar labels and corresponding module directories.
MODULES = {
    "Full Code 1: AO-LACCP Full Framework": "FullCode1",
    "Full Code 2: AO-LACCP Multi-Agent": "FullCode2",
    "Case Study Scenario: Threat Scenarios": "CaseStudyScenario",
    "Full Code 3: AO-LACCP Scientific Research Evaluation": "FullCode3",
}

SELECTION_OPTIONS = ["Home"] + list(MODULES.keys())

# ============================================================
# NAVIGATION STATE
# ============================================================

# Initialize state before creating the radio widget.
if "module_choice" not in st.session_state:
    st.session_state["module_choice"] = "Home"

if st.session_state["module_choice"] not in SELECTION_OPTIONS:
    st.session_state["module_choice"] = "Home"


def return_to_home():
    """Set navigation state before Streamlit reruns."""
    st.session_state["module_choice"] = "Home"


# ============================================================
# LOGO AND DASHBOARD HEADER
# ============================================================

logo_col1, logo_col2, logo_col3 = st.columns([1, 2, 1])

with logo_col2:
    if os.path.isfile(LOGO_PATH):
        try:
            logo = Image.open(LOGO_PATH)
            st.image(logo, width=400)
        except Exception as exc:

Deployment checklist
Open your GitHub repository and replace the entire dashboard.py file.

Commit the changes to the branch used by Streamlit Community Cloud.

Wait for the deployment to finish, then refresh the app.

If the old HTML still appears, verify that Streamlit's configured entry point is this dashboard.py, not another dashboard file.

Important: This fixes the title page in the dashboard file shown here. If one of the four child modules renders the old title or contains its own HTML, that module will need a separate correction.

i used now this below, but give me errors (ValueError: This app has encountered an error. The original error message is redacted to prevent data leaks. Full error details have been recorded in the logs (if you're on Streamlit Cloud, click on 'Manage app' in the lower right of your app).
Traceback:
File "/mount/src/ao-laccp/dashboard.py", line 85, in <module>     index=module_options.index(st.session_state.module_choice)):
import streamlit as st
from PIL import Image
import os
import importlib.util
import sys

# ==============================
# DASHBOARD TITLE PAGE
# ==============================

# ------------------------------
# Logo Path
# ------------------------------
logo_path = os.path.join(os.path.dirname(__file__), "marymount_logo.png")

# ------------------------------
# Display Logo Centered
# ------------------------------
if os.path.exists(logo_path):
    try:
        img = Image.open(logo_path)
        # Center the image using st.image inside a column
        col1, col2, col3 = st.columns([1,2,1])  # middle column is wider
        with col2:
            st.image(img, width=440, use_container_width=False)
    except Exception as e:
        st.warning(f"Cannot open logo: {e}")
else:
    st.warning(f"Logo not found: {logo_path}")

# ------------------------------
# HTML Header Centered and Colored
# ------------------------------
st.markdown("""
<div style="text-align: center; padding: 10px; background-color: #f5f5f5;">
    <h1 style="color: #10069F;">AO-LACCP Dashboard</h1>
</div>
""", unsafe_allow_html=True)

# ------------------------------
# Function to Show Title Page (Centered)
# ------------------------------
def show_title_page():
    st.markdown("""
    <div style="text-align: center;">
        <h4 style="color: #2c3e50;">AI-Orchestrated Latency-Aware Cryptographic Control Plane</h4>
    
<p style="text-align: center; font-family: Arial; font-size: 11pt; color: #8B0000; text-transform: capitalize;">
    <strong><b>TOPIC: AI-Orchestrated Cyber Resilience: An Adaptive Framework For Cyber Risk Management In  Banking And Fintech Ecosystems</b></strong>
</p>
<p style="text-align: center; font-family: Arial; font-size: 14pt; color: #8B0000; text-transform: capitalize;">
    <strong><b>AO-LACCP Artifact Simulation – Doctoral Research Demo</b></strong>
</p>
  

  <p style="text-align: center; font-family: Arial; font-size: 14px; color: #2c3e50; line-height:1.5;">
    By<br>
    <strong>Aliou Maiga</strong><br><br>
    MICHELLE LIU, PhD, Committee Chair<br>
    NATHAN GREEN, PhD, Committee Member<br>
    SEYEDAMIN POURIYEH, PhD, External Reader<br>
   ANNE MAGRO, PhD, Dean<br><br>
    College of Business, Innovation, Leadership, and Technology<br><br>
    A Dissertation Proposal Presented in Partial Fulfillment of the Requirements for the Degree Doctor of Science<br><br>
    Marymount University<br>
    May 2027
</p>
    </div>
    """, unsafe_allow_html=True)

# ==============================
# Sidebar Module Selection
# ==============================
st.sidebar.header("Select Module to Run")
module_options = ["None", "Full Code 1: AO-LACCP Full Framework", 
                  "Full Code 2: AO-LACCP Multi-Agent", 
                  "Case Study Scenario: Threat Scenarios", "Full Code 3: AO-LACCP Scientific Research Evaluation"]

if "module_choice" not in st.session_state:
    st.session_state.module_choice = "None"

st.session_state.module_choice = st.sidebar.radio(
    "Choose Module",
    module_options,
    index=module_options.index(st.session_state.module_choice)
)

if st.session_state.module_choice != "None":
    if st.sidebar.button("Close Module"):
        st.session_state.module_choice = "None"
        st.experimental_rerun = True

# ==============================
# Function to Import and Run a Module
# ==============================
def run_module(folder_name):
    module_path = os.path.join(folder_name, "main.py")
    if os.path.exists(module_path):
        spec = importlib.util.spec_from_file_location("module_main", module_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules["module_main"] = module
        spec.loader.exec_module(module)
    else:
        st.error(f"Module not found: {module_path}")

# ==============================
# Run Title Page or Module
# ==============================
if st.session_state.module_choice == "None":
    show_title_page()
else:
    if st.session_state.module_choice.startswith("Full Code 1"):
        run_module("FullCode1")
    elif st.session_state.module_choice.startswith("Full Code 2"):
        run_module("FullCode2")
    elif st.session_state.module_choice.startswith("Case Study Scenario"):
        run_module("CaseStudyScenario")
    elif st.session_state.module_choice.startswith("Full Code 3"):
        run_module("FullCode3")

…
The ValueError happens because st.session_state.module_choice contains a value that is not in module_options. Therefore, this expression fails:

module_options.index(st.session_state.module_choice)

Your code also has two other issues: it assigns a value to the radio widget's state after widget creation, and st.experimental_rerun = True does not rerun the app.

I'll fix all three issues in the full code below. I'll also keep your title page, logo, four modules, and HTML formatting.

Replace your entire dashboard.py with this corrected version. The main fix is to validate the saved selection before creating the radio widget and use a callback for the Close Module button.


import os
import sys
import importlib.util

import streamlit as st
from PIL import Image

# ============================================================
# AO-LACCP DASHBOARD CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "marymount_logo.png")

MODULES = {
    "Full Code 1: AO-LACCP Full Framework": "FullCode1",
    "Full Code 2: AO-LACCP Multi-Agent": "FullCode2",
    "Case Study Scenario: Threat Scenarios": "CaseStudyScenario",
    "Full Code 3: AO-LACCP Scientific Research Evaluation": "FullCode3",
}

MODULE_OPTIONS = ["None"] + list(MODULES.keys())

# ============================================================
# INITIALIZE SESSION STATE BEFORE CREATING THE RADIO WIDGET
# ============================================================

# Fix stale or invalid values left in the session.
if st.session_state.get("module_choice") not in MODULE_OPTIONS:
    st.session_state["module_choice"] = "None"


def close_module():
    """Reset the selection before Streamlit reruns the script."""
    st.session_state["module_choice"] = "None"

What this fixes
ValueError: invalid saved selections are reset to "None" before the radio widget is created.

StreamlitWidgetAlreadyInstantiatedError: the radio widget's state is changed through a callback rather than directly after the widget is rendered.

Close Module: uses on_click=close_module instead of the incorrect st.experimental_rerun = True.

Module paths: uses absolute paths based on the dashboard's directory, which is more reliable on Streamlit Cloud.

Deploy it
Replace the complete dashboard.py in your GitHub repository.

Commit and push your changes.

Wait for Streamlit Cloud to redeploy, then refresh the app.

If a new error appears inside one of the four modules, share its traceback separately. A child module may have its own issue, such as calling st.set_page_config() again or accessing a missing file.

when i run Full Code 3 there is any ouput
If you select Full Code 3: AO-LACCP Scientific Research Evaluation and nothing appears, the most likely issue is in how dashboard.py loads FullCode3/main.py.

Your current loader executes the module's top-level code and then calls main() if it exists. If Full Code 3 uses a different entry point, or its Streamlit interface is not inside main(), the dashboard may not display the expected results.

Step 1 — Check FullCode3/main.py
Open the file and look at its bottom. If it contains:

if __name__ == "__main__":
    main()

that is fine: the dashboard loader explicitly calls main() after importing the file.

However, if the file defines a function with a different name, such as run_app(), the current loader will not call it automatically.

Step 2 — Add diagnostic messages to the module loader
In dashboard.py, inside run_module(), replace this section:

module_main = getattr(module, "main", None)

if callable(module_main):
    module_main()

with:

module_main = getattr(module, "main", None)

if callable(module_main):
    st.write(f"Starting {folder_name}...")
    module_main()
    st.success(f"{folder_name} finished running.")
else:
    st.warning(
        f"{folder_name}/main.py loaded, but no main() function was found."
    )

This will tell us whether the loader is actually reaching the module's entry point.

Step 3 — Check the Streamlit Cloud logs
If you see an error, open Manage app → Logs in Streamlit Community Cloud. Look for a traceback mentioning FullCode3/main.py.

One thing I need from you
Please paste the last 40–60 lines of FullCode3/main.py, including the main() function and the code at the bottom of the file. I can then correct the loader or entry point specifically so that Full Code 3 displays its evaluation tables, charts, and research outputs.


Pasted text(20261017-193255).txt
Document
here is the full code 3, please fix and provide me the fix full code in text:

Worked for 32s

I reviewed your full Code 3. I found a likely reason it produces no output when launched from your main dashboard.

The main problem is st.set_page_config(). Full Code 3 calls this when it is imported by dashboard.py, but the dashboard has already issued Streamlit commands. Streamlit can then raise an exception before Full Code 3 displays anything.

I corrected that issue and made the Matplotlib boxplot arguments more compatible with different installed versions.

1. Download the complete corrected Code 3
Download FullCode3_fixed.py

The corrected file contains the full 1,749-line program, including the paired evaluation, Q-learning, statistical tables, plots, sensitivity analysis, cryptographic benchmark, and CSV exports.

2. The main correction
Replace the original page-configuration block near the top of FullCode3/main.py:

st.set_page_config(
    page_title="AO-LACCP Scientific Paired Evaluation",
    page_icon="🛡️",
    layout="wide",
)

with this corrected version:

# Configure the page only when this file runs independently.
# When dashboard.py imports this module, the root dashboard
# has already started issuing Streamlit commands.
if __name__ == "__main__":
    st.set_page_config(
        page_title="AO-LACCP Scientific Paired Evaluation",
        page_icon="🛡️",
        layout="wide",
    )

I also changed tick_labels= to labels= in the two boxplot calls for broader Matplotlib compatibility.

3. Install the corrected code
Open your project folder.

Open FullCode3.

Back up your existing main.py.

Copy the complete contents of FullCode3_fixed.py into FullCode3/main.py.

Save the file and restart the Streamlit app.

Your root dashboard should continue loading Full Code 3 through its existing module loader.

Important: This correction addresses the likely rendering failure; it does not guarantee that every runtime issue is resolved. The code's synthetic outcome assumptions and Q-learning evaluation still need scientific justification and sensitivity testing before you use the results as evidence of AO-LACCP's superiority.


FullCode3_fixed.py
Code



"""AO-LACCP scientific paired-evaluation prototype.

This is a transparent synthetic simulation harness, NOT a production validation.
It trains a tabular Q-learning policy on training scenarios, freezes it, and
compares it with a fixed-threshold baseline on independent held-out scenarios.
Both policies receive the same scenario inputs and share one outcome simulator.

IMPORTANT: action effectiveness, scenario distributions, latency equation, and
reward weights are explicit assumptions. Justify/calibrate them and conduct
sensitivity analyses before using results as dissertation evidence.

Run:
    pip install streamlit pandas numpy scipy matplotlib cryptography
    streamlit run main.py
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from scipy import stats

try:
    from cryptography.hazmat.primitives.asymmetric import rsa, ec, padding
    from cryptography.hazmat.primitives import hashes
    CRYPTO_BACKEND_AVAILABLE = True
except Exception:
    CRYPTO_BACKEND_AVAILABLE = False

# When this module is loaded by the root dashboard, that dashboard has already
# emitted Streamlit commands. Calling st.set_page_config() here would raise a
# StreamlitAPIException and prevent Full Code 3 from rendering. Configure the
# page only when this file is launched directly with `streamlit run main.py`.
if __name__ == "__main__":
    st.set_page_config(
        page_title="AO-LACCP Scientific Paired Evaluation",
        page_icon="🛡️",
        layout="wide",
    )

# Actions and MDP values copied from the current AO-LACCP full-framework code.
# Outcome effects below are an explicit evaluation bridge, not present in the original artifact.
ACTIONS = ("Monitor", "Mitigate", "Escalate")
ACTION_MAP = {
    "Monitor": "monitor",
    "Mitigate": "rate_limit",
    "Escalate": "isolate",
}
ACTION_COST = {
    "monitor": 0.00,
    "rate_limit": 0.12,
    "isolate": 0.32,
    "crypto_harden": 0.20,
}
ACTION_LATENCY_MS = {
    "monitor": 2.0,
    "rate_limit": 8.0,
    "isolate": 18.0,
    "crypto_harden": 12.0,
}
ACTION_MITIGATION = {
    "monitor": 0.04,
    "rate_limit": 0.22,
    "isolate": 0.52,
    "crypto_harden": 0.30,
}
THREAT_TYPES = (
    "benign",
    "brute_force",
    "phishing",
    "data_exfiltration",
    "mitm",
    "zero_day",
)
THREAT_PROBS = np.array([0.28, 0.18, 0.16, 0.14, 0.13, 0.11])
PERSISTENCE = {
    "benign": 0.10,
    "brute_force": 0.72,
    "phishing": 0.66,
    "data_exfiltration": 0.82,
    "mitm": 0.78,
    "zero_day": 0.88,
}
ACTION_MATCH = {
    "benign": {
        "monitor": 0.75, "rate_limit": 0.60,
        "isolate": 0.45, "crypto_harden": 0.50,
    },
    "brute_force": {
