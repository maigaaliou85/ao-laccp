
import streamlit as st
from PIL import Image
import os
import importlib.util
import sys
import uuid
import traceback

# ============================================================
# PAGE CONFIGURATION
# ============================================================
# This must be the first Streamlit command.
# Imported modules must not call st.set_page_config() again.
st.set_page_config(
    page_title="AO-LACCP Dashboard",
    page_icon="🔐",
    layout="wide"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ============================================================
# DASHBOARD HEADER: LOGO AND ORIGINAL HEADER DESIGN
# ============================================================
def show_dashboard_header():
    logo_path = os.path.join(BASE_DIR, "marymount_logo.png")

    # Display the Marymount logo centered.
    if os.path.isfile(logo_path):
        try:
            img = Image.open(logo_path)
            col1, col2, col3 = st.columns([1, 2, 1])

            with col2:
                st.image(img, width=440)

        except Exception as e:
            st.warning(f"Cannot open logo: {e}")
    else:
        st.warning(f"Logo not found: {logo_path}")

    # Original dashboard heading and subtitle.
    st.markdown(
        """
        <div style="
            text-align: center;
            padding: 10px;
            background-color: #f5f5f5;
        ">
            <h1 style="
                color: #10069F;
                margin-bottom: 8px;
            ">
                AO-LACCP Dashboard
            </h1>

            <h4 style="
                color: #2c3e50;
                margin-top: 0;
                margin-bottom: 8px;
            ">
                AI-Orchestrated Latency-Aware Cryptographic Control Plane
            </h4>
        </div>
        """,
        unsafe_allow_html=True
    )


# Display the common header on every dashboard view.
show_dashboard_header()


# ============================================================
# DOCTORAL RESEARCH TITLE PAGE
# ============================================================
def show_title_page():
    st.markdown(
        """
        <div style="
            text-align: center;
            padding: 15px 10px;
        ">

            <p style="
                font-family: Arial, sans-serif;
                font-size: 11pt;
                color: #8B0000;
                line-height: 1.5;
            ">
                <strong>
                    TOPIC: AI-Orchestrated Cyber Resilience:
                    An Adaptive Framework for Cyber Risk Management
                    in Banking and FinTech Ecosystems
                </strong>
            </p>

            <p style="
                font-family: Arial, sans-serif;
                font-size: 14pt;
                color: #8B0000;
            ">
                <strong>
                    AO-LACCP Artifact Simulation – Doctoral Research Demo
                </strong>
            </p>

            <p style="
                text-align: center;
                font-family: Arial, sans-serif;
                font-size: 14px;
                color: #2c3e50;
                line-height: 1.7;
            ">
                By<br>
                <strong>Aliou Maiga</strong><br><br>

                MICHELLE LIU, PhD, Committee Chair<br>
                NATHAN GREEN, PhD, Committee Member<br>
                SEYEDAMIN POURIYEH, PhD, External Reader<br>
                ANNE MAGRO, PhD, Dean<br><br>

                College of Business, Innovation, Leadership, and Technology
                <br><br>

                A Dissertation Proposal Presented in Partial Fulfillment
                of the Requirements for the Degree Doctor of Science
                <br><br>

                Marymount University<br>
                May 2027
            </p>

        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# SIDEBAR MODULE SELECTION
# ============================================================
MODULE_OPTIONS = [
    "None",
    "Full Code 1: AO-LACCP Full Framework",
    "Full Code 2: AO-LACCP Multi-Agent",
    "Case Study Scenario: Threat Scenarios",
    "Full Code 3: AO-LACCP Scientific Research Evaluation"
]

MODULE_FOLDERS = {
    "Full Code 1": "FullCode1",
    "Full Code 2": "FullCode2",
    "Case Study Scenario": "CaseStudyScenario",
    "Full Code 3": "FullCode3"
}

st.sidebar.header("Select Module to Run")

if "module_choice" not in st.session_state:
    st.session_state.module_choice = "None"

# Ensure the saved selection remains valid.
if st.session_state.module_choice not in MODULE_OPTIONS:
    st.session_state.module_choice = "None"

selected_choice = st.sidebar.radio(
    "Choose Module",
    MODULE_OPTIONS,
    index=MODULE_OPTIONS.index(st.session_state.module_choice),
    key="module_radio"
)

st.session_state.module_choice = selected_choice

# Close the selected module and return to the title page.
if selected_choice != "None":
    if st.sidebar.button("Close Module", key="close_module"):
        st.session_state.module_choice = "None"
        st.rerun()


# ============================================================
# IMPORT AND RUN A MODULE
# ============================================================
def run_module(folder_name):
    module_path = os.path.join(
        BASE_DIR,
        folder_name,
        "main.py"
    )

    # Check whether the module file exists.
    if not os.path.isfile(module_path):
        st.error(f"Module file not found: {module_path}")
        st.info(
            "Check your GitHub repository. The folder must contain "
            "a file named main.py, with matching capitalization."
        )
        return

    # Use a unique import name for each execution.
    module_name = (
        f"ao_laccp_{folder_name}_{uuid.uuid4().hex}"
    )

    try:
        spec = importlib.util.spec_from_file_location(
            module_name,
            module_path
        )

        if spec is None or spec.loader is None:
            st.error(
                f"Unable to create an import loader for: {module_path}"
            )
            return

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module

        # Load and execute the module's Python file.
        spec.loader.exec_module(module)

        # CRITICAL FIX:
        # Imported modules do not enter their
        # if __name__ == "__main__" block.
        # Call main() explicitly when it exists.
        main_function = getattr(module, "main", None)

        if callable(main_function):
            main_function()
        else:
            st.error(
                f"{folder_name}/main.py loaded, but no callable "
                "main() function was found."
            )

            st.warning(
                "If this file contains its Streamlit interface at "
                "the top level instead of inside main(), its code "
                "structure must be adjusted."
            )

    except Exception as e:
        st.error(
            f"An error occurred while loading {folder_name}: {e}"
        )

        with st.expander("View technical error details"):
            st.code(traceback.format_exc())

    finally:
        sys.modules.pop(module_name, None)


# ============================================================
# DISPLAY THE TITLE PAGE OR THE SELECTED MODULE
# ============================================================
if st.session_state.module_choice == "None":
    show_title_page()

else:
    selected_folder = None

    for module_label, folder_name in MODULE_FOLDERS.items():
        if st.session_state.module_choice.startswith(module_label):
            selected_folder = folder_name
            break

    if selected_folder is not None:
        run_module(selected_folder)
    else:
        st.error(
            "Unable to identify the selected module. "
            "Please choose a module again from the sidebar."
        )
