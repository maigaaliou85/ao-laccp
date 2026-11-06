
import streamlit as st
from PIL import Image
import os
import importlib.util
import sys

# ==============================
# DASHBOARD CONFIGURATION
# ==============================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ==============================
# LOGO
# ==============================

logo_path = os.path.join(BASE_DIR, "marymount_logo.png")

if os.path.exists(logo_path):
    try:
        img = Image.open(logo_path)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(img, width=440)
    except Exception as e:
        st.warning(f"Cannot open logo: {e}")
else:
    st.warning(f"Logo not found: {logo_path}")

# ==============================
# DASHBOARD HEADER
# ==============================

st.markdown("""
<div style="text-align:center; padding:10px; background-color:#f5f5f5;">
    <h1 style="color:#10069F;">AO-LACCP Dashboard</h1>
</div>
""", unsafe_allow_html=True)


# ==============================
# TITLE PAGE
# ==============================

def show_title_page():

    st.markdown("""
    <div style="text-align:center;">

        <h4 style="color:#2c3e50;">
        AI-Orchestrated Latency-Aware Cryptographic Control Plane
        </h4>

        <p style="font-family:Arial; font-size:11pt; color:#8B0000;">
        <strong>
        TOPIC: AI-Orchestrated Cyber Resilience: An Adaptive Framework
        for Cyber Risk Management in Banking and FinTech Ecosystems
        </strong>
        </p>

        <p style="font-family:Arial; font-size:14pt; color:#8B0000;">
        <strong>AO-LACCP Artifact Simulation – Doctoral Research Demo</strong>
        </p>

        <p style="font-family:Arial; font-size:14px; color:#2c3e50; line-height:1.5;">
        By<br>
        <strong>Aliou Maiga</strong><br><br>

        MICHELLE LIU, PhD, Committee Chair<br>
        NATHAN GREEN, PhD, Committee Member<br>
        SEYEDAMIN POURIYEH, PhD, External Reader<br>
        ANNE MAGRO, PhD, Dean<br><br>

        College of Business, Innovation, Leadership, and Technology<br><br>

        A Dissertation Presented in Partial Fulfillment of the Requirements
        for the Degree of Doctor of Science<br><br>

        Marymount University<br>
        May 2027
        </p>

    </div>
    """, unsafe_allow_html=True)


# ==============================
# MODULE SELECTION
# ==============================

st.sidebar.header("Select Module to Run")

module_options = [
    "None",
    "Full Code 1: AO-LACCP Full Framework",
    "Full Code 2: AO-LACCP Multi-Agent",
    "Full Code 3: AO-LACCP Baseline",
    "Case Study Scenario: Threat Scenarios"
]

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
        st.rerun()


# ==============================
# MODULE LOADER
# ==============================

def run_module(folder_name):

    module_path = os.path.join(
        BASE_DIR,
        folder_name,
        "main.py"
    )

    if not os.path.isfile(module_path):
        st.error(f"Module not found: {module_path}")
        return

    module_name = f"{folder_name}_main"

    try:

        spec = importlib.util.spec_from_file_location(
            module_name,
            module_path
        )

        if spec is None or spec.loader is None:
            st.error(f"Cannot load module: {module_path}")
            return

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module

        spec.loader.exec_module(module)

        # Run main() only if the module does not
        # already execute it during import.
        if not getattr(module, "_APP_EXECUTED", False):
            if hasattr(module, "main"):
                module.main()
            else:
                st.error(f"No main() function found in {module_path}")

    except Exception as e:
        st.error(f"Error loading {folder_name}: {e}")
        st.exception(e)


# ==============================
# APPLICATION ROUTING
# ==============================

if st.session_state.module_choice == "None":

    show_title_page()

elif st.session_state.module_choice.startswith("Full Code 1"):

    run_module("FullCode1")

elif st.session_state.module_choice.startswith("Full Code 2"):

    run_module("FullCode2")

elif st.session_state.module_choice.startswith("Full Code 3"):

    run_module("FullCode3")

elif st.session_state.module_choice.startswith("Case Study Scenario"):

    run_module("CaseStudyScenario")
