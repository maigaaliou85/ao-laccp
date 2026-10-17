import os
import sys
import importlib.util
import streamlit as st
from PIL import Image

# ============================================================
# AO-LACCP DASHBOARD
# ============================================================

# Configure the page before other Streamlit commands.
st.set_page_config(
    page_title="AO-LACCP Dashboard",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# PATHS AND MODULE CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LOGO_PATH = os.path.join(BASE_DIR, "marymount_logo.png")

MODULES = {
    "Full Code 1: AO-LACCP Full Framework": "FullCode1",
    "Full Code 2: AO-LACCP Multi-Agent": "FullCode2",
    "Case Study Scenario: Threat Scenarios": "CaseStudyScenario",
    "Full Code 3: AO-LACCP Scientific Research Evaluation": "FullCode3",
}

selection_options = ["Home"] + list(MODULES.keys())

# ============================================================
# INITIALIZE NAVIGATION STATE
# ============================================================
# IMPORTANT:
# Initialize the widget state before creating the radio widget.
# Do not assign to module_choice later in the main script.
# Use the callback below when returning to Home.

if "module_choice" not in st.session_state:
    st.session_state["module_choice"] = "Home"

if st.session_state["module_choice"] not in selection_options:
    st.session_state["module_choice"] = "Home"


def return_to_home():
    """Set navigation state before Streamlit reruns the app."""
    st.session_state["module_choice"] = "Home"


# ============================================================
# LOGO AND HEADER
# ============================================================

logo_col1, logo_col2, logo_col3 = st.columns([1, 2, 1])

with logo_col2:
    if os.path.isfile(LOGO_PATH):
        try:
            logo = Image.open(LOGO_PATH)
            st.image(logo, width=400)
        except Exception as exc:
            st.warning(f"The logo could not be opened: {exc}")
    else:
        st.warning(
            "Marymount logo not found. Expected location: "
            f"{LOGO_PATH}"
        )

st.markdown(
    """
    <div style="
        text-align: center;
        padding: 12px;
        background-color: #f5f5f5;
        border-radius: 8px;
    ">
        <h1 style="color: #10069F; margin: 0;">
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
    """Display the AO-LACCP research title page."""

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
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style="
            text-align: center;
            font-family: Arial, sans-serif;
            font-size: 15px;
            color: #2c3e50;
            line-height: 1.8;
        ">
            By<br>
            <strong>Aliou Maiga</strong><br><br>

            Michelle Liu, PhD — Committee Chair<br>
            Nathan Green, PhD — Committee Member<br>
            Seyedamin Pouriyeh, PhD — External Reader<br>
            Anne Magro, PhD — Dean<br><br>

            College of Business, Innovation, Leadership, and Technology
            <br><br>

            A Dissertation Proposal Presented in Partial Fulfillment
            of the Requirements for the Degree of Doctor of Science
            <br><br>

            Marymount University<br>
            May 2027
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.subheader("Research Demonstration")

    st.write(
        "Use the sidebar to open an AO-LACCP module. "
        "Each module should contain its own simulation, analysis, "
        "or evaluation interface."
    )

    st.info(
        "Select a module from the sidebar to open its interface. "
        "Use Return to Home to return to this page."
    )

    st.markdown("### Available modules")

    st.markdown(
        """
        - **Full Framework:** AO-LACCP framework and simulation.
        - **Multi-Agent:** Multi-agent orchestration demonstration.
        - **Threat Scenarios:** Case-study threat scenarios.
        - **Scientific Research Evaluation:** Evaluation metrics,
          comparisons, statistical analysis, and research outputs.
        """
    )


# ============================================================
# MODULE LOADER
# ============================================================

def run_module(folder_name):
    """
    Load and run:
        <dashboard directory>/<folder_name>/main.py

    If the module defines main(), call it explicitly.
    Otherwise, its top-level code executes when imported.
    """

    module_dir = os.path.join(BASE_DIR, folder_name)
    module_path = os.path.join(module_dir, "main.py")

    st.subheader(folder_name)

    # Validate module directory.
    if not os.path.isdir(module_dir):
        st.error(f"Module folder not found: {module_dir}")
        st.markdown("Expected folder structure:")
        st.code(f"{folder_name}/main.py")
        return

    # Validate module entry point.
    if not os.path.isfile(module_path):
        st.error(f"Module file not found: {module_path}")
        st.markdown(
            "Create a file named `main.py` inside the module folder."
        )
        return

    # Use a unique name for each imported module.
    module_name = f"ao_laccp_{folder_name.lower()}"

    # Track whether this function adds a path to sys.path.
    added_path = module_dir not in sys.path

    try:
        # Allow the module to import its own sibling files.
        if added_path:
            sys.path.insert(0, module_dir)

        spec = importlib.util.spec_from_file_location(
            module_name,
            module_path,
        )

        if spec is None or spec.loader is None:
            st.error(
                f"Python could not create a loader for {module_path}"
            )
            return

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module

        with st.spinner(f"Loading {folder_name}..."):
            spec.loader.exec_module(module)

        # Modules using an explicit main() entry point need it called.
        module_main = getattr(module, "main", None)

        if callable(module_main):
            module_main()

    except Exception as exc:
        st.error(f"Could not run module: {folder_name}")
        st.exception(exc)

    finally:
        # Remove only the path this function added.
        if added_path and module_dir in sys.path:
            sys.path.remove(module_dir)


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

st.sidebar.title("AO-LACCP Navigation")
st.sidebar.caption("Doctoral Research Demonstration")

# Create the radio widget using the initialized state.
selected_module = st.sidebar.radio(
    "Select a module",
    options=selection_options,
    key="module_choice",
)

st.sidebar.divider()
st.sidebar.caption("Module controls")

# The callback changes state before Streamlit reruns the app.
# Do not assign to module_choice inside an ordinary button block.
st.sidebar.button(
    "Return to Home",
    use_container_width=True,
    on_click=return_to_home,
)

st.sidebar.caption(
    "If a module does not open, check the folder structure "
    "and the error message shown on the main page."
)

# ============================================================
# MAIN CONTENT
# ============================================================

if selected_module == "Home":
    show_title_page()
else:
    folder_name = MODULES[selected_module]
    run_module(folder_name)
