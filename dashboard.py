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
            st.warning(f"The Marymount logo could not be opened: {exc}")
    else:
        st.warning(
            "Marymount logo not found. Expected location: "
            f"{LOGO_PATH}"
        )

st.title("AO-LACCP Dashboard")
st.divider()


# ============================================================
# TITLE PAGE — NATIVE STREAMLIT ONLY
# No HTML tags are used in this function.
# ============================================================

def show_title_page():
    """Display the doctoral research title page."""

    st.title(
        "AI-Orchestrated Latency-Aware Cryptographic Control Plane"
    )

    st.divider()

    st.subheader("Doctoral Research Topic")

    st.markdown(
        "**AI-Orchestrated Cyber Resilience: An Adaptive Framework "
        "for Cyber Risk Management in Banking and FinTech Ecosystems**"
    )

    st.info("AO-LACCP Artifact Simulation – Doctoral Research Demo")

    st.divider()

    # Center the author and dissertation information.
    left_col, center_col, right_col = st.columns([1, 3, 1])

    with center_col:
        st.markdown("### By")
        st.header("Aliou Maiga")

        st.markdown("#### Dissertation Committee")
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

    # Research demonstration instructions.
    st.header("Research Demonstration")

    st.write(
        "Use the sidebar to open an AO-LACCP module. "
        "Each module provides its own simulation, analysis, "
        "or evaluation interface."
    )

    st.info(
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


# ============================================================
# MODULE LOADER
# ============================================================

def run_module(folder_name):
    """
    Load a module from:
        <dashboard directory>/<folder_name>/main.py

    If the module defines main(), call it after importing.
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
        st.error(f"Module entry point not found: {module_path}")
        st.info(
            f"Create a main.py file inside the {folder_name} folder."
        )
        return

    module_name = f"ao_laccp_{folder_name.lower()}"
    added_path = module_dir not in sys.path

    try:
        # Allow imports of files located inside the module folder.
        if added_path:
            sys.path.insert(0, module_dir)

        spec = importlib.util.spec_from_file_location(
            module_name,
            module_path,
        )

        if spec is None or spec.loader is None:
            st.error(f"Unable to load module: {module_path}")
            return

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module

        with st.spinner(f"Loading {folder_name}..."):
            spec.loader.exec_module(module)

        module_main = getattr(module, "main", None)

        if callable(module_main):
            module_main()

    except Exception as exc:
        st.error(f"Could not run module: {folder_name}")
        st.exception(exc)

    finally:
        # Remove only the path added by this function.
        if added_path and module_dir in sys.path:
            sys.path.remove(module_dir)


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

st.sidebar.title("AO-LACCP Navigation")
st.sidebar.caption("Doctoral Research Demonstration")

selected_module = st.sidebar.radio(
    "Select a module",
    options=SELECTION_OPTIONS,
    key="module_choice",
)

st.sidebar.divider()
st.sidebar.caption("Module Controls")

st.sidebar.button(
    "Return to Home",
    key="return_home_button",
    on_click=return_to_home,
    use_container_width=True,
)

st.sidebar.caption(
    "If a module does not open, check its folder structure "
    "and review the error displayed on the main page."
)


# ============================================================
# MAIN CONTENT
# ============================================================

if selected_module == "Home":
    show_title_page()
else:
    folder_name = MODULES[selected_module]
    run_module(folder_name)
