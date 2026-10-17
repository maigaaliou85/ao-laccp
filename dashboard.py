
from pathlib import Path
import importlib.util
import re
import sys

import streamlit as st
from PIL import Image


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

st.set_page_config(
    page_title="AO-LACCP Dashboard",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# TITLE PAGE AND LOGO
# ============================================================

def show_logo():
    logo_path = BASE_DIR / "marymount_logo.png"

    if not logo_path.is_file():
        st.warning(f"Marymount logo not found: {logo_path.name}")
        return

    try:
        with Image.open(logo_path) as image:
            logo = image.copy()

        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            st.image(logo, width=440)

    except Exception as exc:
        st.warning(f"Unable to display the Marymount logo: {exc}")


def show_title_page():
    show_logo()

    st.markdown(
        """
        <div style="
            text-align:center;
            padding:12px;
            background-color:#f5f5f5;
            border-radius:8px;
        ">
            <h1 style="color:#10069F;">AO-LACCP Dashboard</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style="text-align:center; padding:18px 8px;">

            <h3 style="color:#2c3e50;">
                AI-Orchestrated Latency-Aware Cryptographic Control Plane
            </h3>

            <p style="
                font-family:Arial;
                font-size:15px;
                color:#8B0000;
            ">
                <strong>
                    TOPIC: AI-Orchestrated Cyber Resilience: An Adaptive
                    Framework for Cyber Risk Management in Banking and
                    FinTech Ecosystems
                </strong>
            </p>

            <p style="
                font-family:Arial;
                font-size:18px;
                color:#8B0000;
            ">
                <strong>
                    AO-LACCP Artifact Simulation – Doctoral Research Demo
                </strong>
            </p>

            <p style="
                font-family:Arial;
                font-size:14px;
                color:#2c3e50;
                line-height:1.8;
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
                of the Requirements for the Degree of Doctor of Science
                <br><br>

                Marymount University<br>
                May 2027
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# MODULE CONFIGURATION
# ============================================================

MODULES = {
    "Full Code 1: AO-LACCP Full Framework": "FullCode1",
    "Full Code 2: AO-LACCP Multi-Agent": "FullCode2",
    "Case Study Scenario: Threat Scenarios": "CaseStudyScenario",
}

NONE_OPTION = "None"

if "module_choice" not in st.session_state:
    st.session_state.module_choice = NONE_OPTION


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("AO-LACCP Navigation")
st.sidebar.header("Select Module to Run")

# Process the close button BEFORE rendering the radio widget.
# This avoids modifying a widget's state after it has been created.
if st.session_state.module_choice != NONE_OPTION:
    if st.sidebar.button("Close Module", use_container_width=True):
        st.session_state.module_choice = NONE_OPTION

        # The next run returns to the title page.
        st.rerun()

module_options = [NONE_OPTION] + list(MODULES.keys())

current_choice = st.session_state.module_choice

if current_choice not in module_options:
    current_choice = NONE_OPTION

selected_choice = st.sidebar.radio(
    "Choose Module",
    options=module_options,
    index=module_options.index(current_choice),
)

st.session_state.module_choice = selected_choice

st.sidebar.divider()
st.sidebar.caption("AO-LACCP | Doctoral Research Prototype")


# ============================================================
# MODULE LOADER
# ============================================================

def resolve_module_path(folder_name):
    """
    Support either of these repository layouts:

        FullCode1/main.py
        FullCode2/main.py
        CaseStudyScenario/main.py

    Or standalone files:

        FullCode1.py
        FullCode2.py
        CaseStudyScenario.py
    """

    folder_path = BASE_DIR / folder_name

    candidates = [
        folder_path / "main.py",
        BASE_DIR / f"{folder_name}.py",
    ]

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    expected = "\n".join(str(path) for path in candidates)

    raise FileNotFoundError(
        f"Could not locate module '{folder_name}'. "
        f"Expected one of these files:\n{expected}"
    )


def run_module(folder_name):
    """Load a module and report syntax errors with their source location."""

    try:
        module_path = resolve_module_path(folder_name)

        # Read and compile the source first so syntax errors can be
        # displayed with the exact filename and line number.
        source = module_path.read_text(encoding="utf-8")

        code = compile(
            source,
            str(module_path),
            "exec",
        )

        module_id = re.sub(
            r"\W+",
            "_",
            f"_ao_laccp_{folder_name}",
        )

        spec = importlib.util.spec_from_file_location(
            module_id,
            module_path,
        )

        if spec is None:
            raise ImportError(
                f"Unable to create a module specification for "
                f"{module_path.name}"
            )

        module = importlib.util.module_from_spec(spec)

        # Make sibling Python files importable when a module is
        # located in its own subdirectory.
        module_directory = str(module_path.parent)

        if module_directory not in sys.path:
            sys.path.insert(0, module_directory)

        sys.modules[module_id] = module

        # Execute the already-compiled code.
        exec(code, module.__dict__)

    except SyntaxError as exc:
        st.error("Python syntax error in the selected module.")

        st.write(f"**Module:** `{folder_name}`")
        st.write(f"**File:** `{exc.filename or 'Unknown file'}`")
        st.write(f"**Line:** `{exc.lineno or 'Unknown line'}`")
        st.write(f"**Column:** `{exc.offset or 'Unknown column'}`")
        st.write(f"**Error:** {exc.msg}")

        if exc.text:
            st.code(
                exc.text.rstrip("\n"),
                language="python",
            )

        st.info(
            "Correct the indicated line in the module's source file, "
            "commit the change, and allow Streamlit Cloud to redeploy."
        )

    except FileNotFoundError as exc:
        st.error("The selected module could not be found.")
        st.code(str(exc))

    except Exception as exc:
        st.error(
            f"An error occurred while running the "
            f"{folder_name} module."
        )
        st.exception(exc)


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

if selected_choice == NONE_OPTION:
    show_title_page()

else:
    folder_name = MODULES[selected_choice]
    run_module(folder_name)
