
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

# Absolute path to the directory containing this dashboard file.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LOGO_PATH = os.path.join(BASE_DIR, "marymount_logo.png")

# Map sidebar labels to actual module folders.
MODULES = {
    "Full Code 1: AO-LACCP Full Framework": "FullCode1",
    "Full Code 2: AO-LACCP Multi-Agent": "FullCode2",
    "Case Study Scenario: Threat Scenarios": "CaseStudyScenario",
    "Full Code 3: AO-LACCP Scientific Research Evaluation": "FullCode3",
}

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
        "Select a module from the sidebar, then click "
        "**Run Selected Module**."
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
    Load and run a module from:
        <dashboard directory>/<folder_name>/main.py

    Modules with a main() function are called explicitly.
    Modules without a main() function execute their top-level
    code when imported.
    """

    module_dir = os.path.join(BASE_DIR, folder_name)
    module_path = os.path.join(module_dir, "main.py")

    st.subheader(folder_name)

    if not os.path.isdir(module_dir):
        st.error(f"Module folder not found: {module_dir}")
        st.markdown("Check that your repository has this folder:")
        st.code(f"{folder_name}/main.py")
        return

    if not os.path.isfile(module_path):
        st.error(f"Module file not found: {module_path}")
        st.markdown(
            "Create a file named `main.py` inside the module folder."
        )
        return

    # Use a unique module name to avoid collisions.
    module_name = f"ao_laccp_{folder_name.lower()}"

    try:
        # Ensure the module can import sibling files from its folder.
        if module_dir not in sys.path:
            sys.path.insert(0, module_dir)

        spec = importlib.util.spec_from_file_location(
            module_name,
            module_path,
        )

        if spec is None or spec.loader is None:
            st.error("Python could not create a loader for this module.")
            return

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module

        with st.spinner(f"Loading {folder_name}..."):
            spec.loader.exec_module(module)

        # Support modules written with:
        # def main():
        #     ...
        #
        # if __name__ == "__main__":
        #     main()
        #
        # Importing a module does not satisfy that __main__ condition,
        # so call main() here when it exists.
        module_main = getattr(module, "main", None)

        if callable(module_main):
            module_main()

    except Exception as exc:
        st.error(f"Could not run module: {folder_name}")
        st.exception(exc)

    finally:
        # Remove the inserted path without removing it if it was
        # already present before this function ran.
        if (
            module_dir in sys.path
            and sys.path.index(module_dir) == 0
        ):
            sys.path.remove(module_dir)


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

st.sidebar.title("AO-LACCP Navigation")
st.sidebar.caption("Doctoral Research Demonstration")

selection_options = ["Home"] + list(MODULES.keys())

if "module_choice" not in st.session_state:
    st.session_state["module_choice"] = "Home"

# Recover safely if the stored choice no longer exists.
if st.session_state["module_choice"] not in selection_options:
    st.session_state["module_choice"] = "Home"

selected_module = st.sidebar.radio(
    "Select a module",
    options=selection_options,
    key="module_choice",
)

st.sidebar.divider()

st.sidebar.caption("Module controls")

if st.sidebar.button(
    "Return to Home",
    use_container_width=True,
):
    st.session_state["module_choice"] = "Home"
    st.rerun()

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
