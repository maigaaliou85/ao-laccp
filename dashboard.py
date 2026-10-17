
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


# ============================================================
# LOGO
# ============================================================

if os.path.isfile(LOGO_PATH):
    try:
        logo = Image.open(LOGO_PATH)

        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            st.image(logo, width=440)

    except Exception as exc:
        st.warning(f"Cannot open logo: {exc}")
else:
    st.warning(f"Logo not found: {LOGO_PATH}")


# ============================================================
# DASHBOARD HEADER
# ============================================================

st.markdown(
    """
    <div style="
        text-align: center;
        padding: 10px;
        background-color: #f5f5f5;
        border-radius: 8px;
    ">
        <h1 style="color: #10069F;">
            AO-LACCP Dashboard
        </h1>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()


# ============================================================
# TITLE PAGE
# ============================================================

def show_title_page():
    """Display the AO-LACCP doctoral research title page."""

    st.markdown(
        """
        <div style="text-align: center;">

            <h3 style="color: #2c3e50;">
                AI-Orchestrated Latency-Aware Cryptographic Control Plane
            </h3>

            <p style="
                font-family: Arial, sans-serif;
                font-size: 16px;
                color: #8B0000;
            ">
                <strong>
                    TOPIC: AI-Orchestrated Cyber Resilience:
                    An Adaptive Framework for Cyber Risk Management
                    in Banking and FinTech Ecosystems
                </strong>
            </p>

            <p style="
                font-family: Arial, sans-serif;
                font-size: 16px;
                color: #8B0000;
            ">
                <strong>
                    AO-LACCP Artifact Simulation – Doctoral Research Demo
                </strong>
            </p>

            <p style="
                font-family: Arial, sans-serif;
                font-size: 14px;
                color: #2c3e50;
                line-height: 1.7;
            ">
                By<br>
                <strong>Aliou Maiga</strong><br><br>

                Michelle Liu, PhD — Committee Chair<br>
                Nathan Green, PhD — Committee Member<br>
                Seyedamin Pouriyeh, PhD — External Reader<br>
                Anne Magro, PhD — Dean<br><br>

                College of Business, Innovation, Leadership,
                and Technology<br><br>

                A Dissertation Proposal Presented in Partial
                Fulfillment of the Requirements for the Degree
                of Doctor of Science<br><br>

                Marymount University<br>
                May 2027
            </p>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.subheader("Research Demonstration")

    st.write(
        "Use the sidebar to select an AO-LACCP module. "
        "Each module provides its own simulation, analysis, "
        "or evaluation interface."
    )

    st.info(
        "Choose a module from the sidebar to open it. "
        "Select None or use Close Module to return to this page."
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


# ============================================================
# MODULE LOADER
# ============================================================

def run_module(folder_name):
    """
    Load a module from:
        <dashboard directory>/<folder_name>/main.py

    If main.py defines main(), call it after importing.
    Otherwise, its top-level code executes during import.
    """

    module_dir = os.path.join(BASE_DIR, folder_name)
    module_path = os.path.join(module_dir, "main.py")

    st.subheader(folder_name)

    if not os.path.isdir(module_dir):
        st.error(f"Module folder not found: {module_dir}")
        st.code(f"{folder_name}/main.py")
        return

    if not os.path.isfile(module_path):
        st.error(f"Module file not found: {module_path}")
        return

    module_name = f"ao_laccp_{folder_name.lower()}"
    added_path = module_dir not in sys.path

    try:
        if added_path:
            sys.path.insert(0, module_dir)

        spec = importlib.util.spec_from_file_location(
            module_name,
            module_path,
        )

        if spec is None or spec.loader is None:
            st.error(f"Could not load module: {module_path}")
            return

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module

        with st.spinner(f"Loading {folder_name}..."):
            spec.loader.exec_module(module)

        module_main = getattr(module, "main", None)

        if callable(module_main):
            module_main()

    except Exception as exc:
        st.error(f"An error occurred while running {folder_name}.")
        st.exception(exc)

    finally:
        if added_path and module_dir in sys.path:
            sys.path.remove(module_dir)


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

st.sidebar.header("Select Module to Run")

# Do not assign to st.session_state["module_choice"] after
# creating this widget. The callback below handles resetting it.
selected_module = st.sidebar.radio(
    "Choose Module",
    options=MODULE_OPTIONS,
    key="module_choice",
)

if selected_module != "None":
    st.sidebar.button(
        "Close Module",
        key="close_module_button",
        on_click=close_module,
        use_container_width=True,
    )


# ============================================================
# DISPLAY HOME PAGE OR SELECTED MODULE
# ============================================================

if selected_module == "None":
    show_title_page()
else:
    folder_name = MODULES[selected_module]
    run_module(folder_name)
