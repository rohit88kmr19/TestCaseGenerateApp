import csv
import html
import inspect
import io
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import load_prompt
from langchain_openrouter import ChatOpenRouter

# ----------------------------------------------------------------------
# Setup
# ----------------------------------------------------------------------
load_dotenv()  # Keeps local .env support; Streamlit Secrets take precedence below.

# Read credentials from Streamlit Secrets first, with environment-variable
# fallback for local development. Never put real credentials in source code.
def get_setting(secret_name: str, env_name: str | None = None, default: str = "") -> str:
    """Read a setting from Streamlit Secrets, then from the environment."""
    value = ""
    try:
        value = st.secrets.get(secret_name, "")
    except Exception:
        # Streamlit Secrets may not be configured in local development.
        pass

    if not value and env_name:
        value = os.getenv(env_name, "")

    if not value:
        value = default

    return str(value).strip()


OPENROUTER_API_KEY = get_setting("OPENROUTER_API_KEY", "OPENROUTER_API_KEY")
MODEL_NAME = get_setting("MODEL_NAME", "Model", "openai/gpt-4o-mini")

# ChatOpenRouter reads OPENROUTER_API_KEY from the process environment.
# Set it before the model/chain is initialized.
if OPENROUTER_API_KEY:
    os.environ["OPENROUTER_API_KEY"] = OPENROUTER_API_KEY

st.set_page_config(
    page_title="AI Test Case Generator",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Newer Streamlit versions use width="stretch"; older ones use use_container_width.
STRETCH = (
    {"width": "stretch"}
    if "width" in inspect.signature(st.button).parameters
    else {"use_container_width": True}
)

PROMPT_PATH = Path("test_case_template.json")

APPLICATION_TYPES = [
    "Web Application",
    "Mobile Application",
    "API",
    "POS / Retail Application",
    "Desktop Application",
]
TESTING_TYPES = [
    "All Types",
    "Functional Testing",
    "Positive Testing",
    "Negative Testing",
    "Boundary Value Testing",
    "Regression Testing",
    "API Testing",
    "Accessibility Testing",
]
PRIORITIES = ["All Priorities", "High", "Medium", "Low"]
DETAIL_LEVELS = ["Standard", "Detailed"]

SAMPLE_REQUIREMENTS = {
    "🔐 Login": (
        "As a registered user, I want to log in using my email and "
        "password so that I can access my account. After 5 failed "
        "attempts the account is locked for 15 minutes."
    ),
    "🛒 Checkout": (
        "As a shopper, I want to apply a discount code at checkout so "
        "that the order total is reduced. Each code can be used once "
        "per customer and expired codes must be rejected."
    ),
    "💳 POS Payment": (
        "As a cashier, I want to accept card and cash payments at the "
        "POS so that I can complete a sale and print a receipt. Split "
        "payments across multiple tenders must be supported."
    ),
    "🔌 Create User API": (
        "As an API consumer, I want to create a user through "
        "POST /users with name, email and role so that the user can be "
        "managed in the system. Duplicate emails must be rejected."
    ),
}

PRIORITY_META = {
    "High": ("#dc2626", "🔴"),
    "Medium": ("#d97706", "🟠"),
    "Low": ("#16a34a", "🟢"),
}

# ----------------------------------------------------------------------
# Styling
# ----------------------------------------------------------------------
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding-top: 2rem; padding-bottom: 3rem;}

    .hero {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 55%, #0891b2 100%);
        padding: 2.1rem 2.3rem;
        border-radius: 18px;
        margin-bottom: 1.4rem;
        box-shadow: 0 10px 30px rgba(79, 70, 229, 0.25);
    }
    .hero h1 {color: #ffffff; margin: 0 0 0.4rem 0; padding: 0; font-size: 2.1rem;}
    .hero p {color: rgba(255, 255, 255, 0.92); margin: 0; font-size: 1.05rem;}
    .hero .pill {
        display: inline-block; margin: 0.9rem 0.45rem 0 0;
        padding: 0.2rem 0.75rem; border-radius: 999px;
        background: rgba(255, 255, 255, 0.18); color: #fff;
        font-size: 0.78rem; font-weight: 600;
    }

    .card {
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 14px; padding: 1.15rem 1.3rem; height: 100%;
        background: rgba(128, 128, 128, 0.06);
    }
    .card .icon {font-size: 1.6rem;}
    .card h4 {margin: 0.35rem 0 0.35rem 0;}
    .card p {margin: 0; opacity: 0.8; font-size: 0.92rem; line-height: 1.5;}

    div[data-testid="stMetric"] {
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 12px; padding: 0.8rem 1rem;
        background: rgba(128, 128, 128, 0.06);
    }

    .badge {
        display: inline-block; padding: 0.18rem 0.65rem; margin: 0 0.4rem 0.4rem 0;
        border-radius: 999px; font-size: 0.74rem; font-weight: 600; color: #fff;
    }
    .badge-type {background: #4f46e5;}
    .meta-label {
        font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.06em;
        opacity: 0.6; margin: 0.5rem 0 0.15rem 0; font-weight: 600;
    }
    .app-footer {text-align: center; opacity: 0.55; font-size: 0.8rem; margin-top: 2.5rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


@st.cache_resource(show_spinner=False)
def get_chain(model_name: str, prompt_mtime: float):
    """Build the chain once; rebuild if the model or prompt file changes."""
    prompt = load_prompt(str(PROMPT_PATH))
    model = ChatOpenRouter(model=model_name)
    return prompt | model | StrOutputParser()


def parse_json_response(text: str) -> dict:
    """Parse the model output as JSON, tolerating accidental code fences."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return json.loads(cleaned)


def normalize_priority(value) -> str:
    return str(value or "").strip().title()


def as_list(value) -> list:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return value
    return [value]


def esc(value) -> str:
    return html.escape(str(value if value is not None else ""))


def build_csv(test_cases: list) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "Test Case ID", "Scenario", "Test Type", "Priority",
            "Preconditions", "Test Data", "Steps", "Expected Result",
            "Requirement Coverage",
        ]
    )
    for tc in test_cases:
        steps = "\n".join(
            f"{i}. {s}" for i, s in enumerate(as_list(tc.get("steps")), 1)
        )
        writer.writerow(
            [
                tc.get("test_case_id", ""), tc.get("scenario", ""),
                tc.get("test_type", ""), tc.get("priority", ""),
                tc.get("preconditions", ""), tc.get("test_data", ""),
                steps, tc.get("expected_result", ""),
                tc.get("requirement_coverage", ""),
            ]
        )
    return buffer.getvalue().encode("utf-8-sig")


def build_markdown(entry: dict) -> str:
    data, meta = entry["data"], entry["meta"]
    lines = [
        "# Test Case Document",
        "",
        f"- **Generated:** {meta['timestamp']}",
        f"- **Application Type:** {meta['application_type']}",
        f"- **Testing Type:** {meta['testing_type']}",
        f"- **Priority Focus:** {meta['priority']}",
        f"- **Detail Level:** {meta['detail_level']}",
        "",
        "## Requirement",
        "",
        meta["requirement"],
        "",
    ]
    assumptions = as_list(data.get("assumptions"))
    if assumptions:
        lines += ["## Assumptions", ""] + [f"- {a}" for a in assumptions] + [""]
    questions = as_list(data.get("open_questions"))
    if questions:
        lines += ["## Open Questions", ""] + [f"- {q}" for q in questions] + [""]
    lines += ["## Test Cases", ""]
    for tc in data.get("test_cases", []):
        lines += [
            f"### {tc.get('test_case_id', '')} - {tc.get('scenario', '')}",
            "",
            f"- **Type:** {tc.get('test_type', 'N/A')}",
            f"- **Priority:** {tc.get('priority', 'N/A')}",
            f"- **Requirement Coverage:** {tc.get('requirement_coverage', 'N/A')}",
            f"- **Preconditions:** {tc.get('preconditions', 'N/A')}",
            f"- **Test Data:** {tc.get('test_data', 'N/A')}",
            "",
            "**Steps**",
            "",
        ]
        lines += [
            f"{i}. {s}" for i, s in enumerate(as_list(tc.get("steps")), 1)
        ]
        lines += ["", f"**Expected Result:** {tc.get('expected_result', 'N/A')}", ""]
    return "\n".join(lines)


def set_sample(text: str):
    st.session_state["requirement"] = text


def load_history(index: int):
    st.session_state["result"] = st.session_state["history"][index]


def clear_results():
    st.session_state["result"] = None


# ----------------------------------------------------------------------
# Session state
# ----------------------------------------------------------------------
st.session_state.setdefault("requirement", "")
st.session_state.setdefault("result", None)
st.session_state.setdefault("history", [])

# ----------------------------------------------------------------------
# Hero
# ----------------------------------------------------------------------
st.markdown(
    """
    <div class="hero">
        <h1>🧪 AI Test Case Generator</h1>
        <p>Turn requirements and user stories into structured, traceable
        test cases in seconds.</p>
        <span class="pill">Functional</span>
        <span class="pill">Negative</span>
        <span class="pill">Boundary</span>
        <span class="pill">Regression</span>
        <span class="pill">API</span>
        <span class="pill">Accessibility</span>
    </div>
    """,
    unsafe_allow_html=True,
)

if not OPENROUTER_API_KEY:
    st.error(
        "OpenRouter API key is missing. Add OPENROUTER_API_KEY to "
        "Streamlit Secrets or your local .env file."
    )
    st.stop()

if not MODEL_NAME:
    st.error("The MODEL_NAME setting is missing. Add it to Streamlit Secrets or .env.")
    st.stop()

if not PROMPT_PATH.exists():
    st.error(
        f"`{PROMPT_PATH}` was not found. Run `python test_case_template.py` "
        "to generate it."
    )
    st.stop()

# ----------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Test Configuration")
    application_type = st.selectbox("Application Type", APPLICATION_TYPES)
    testing_type = st.selectbox("Testing Type", TESTING_TYPES)
    priority = st.selectbox("Priority Focus", PRIORITIES)
    detail_level = st.selectbox(
        "Test Case Detail Level",
        DETAIL_LEVELS,
        help="Detailed adds explicit preconditions, exact test data and "
        "finer-grained steps.",
    )

    st.divider()
    history = st.session_state["history"]
    if history:
        st.subheader("🕘 Recent Generations")
        for idx in range(len(history) - 1, -1, -1):
            item = history[idx]
            st.button(
                item["label"],
                key=f"history_{idx}",
                on_click=load_history,
                args=(idx,),
                **STRETCH,
            )
        st.divider()

    with st.expander("💡 Tips for better results"):
        st.markdown(
            "- Include **acceptance criteria** and business rules.\n"
            "- State **limits** (min/max length, counts, time windows) "
            "for boundary tests.\n"
            "- Mention **roles** and **permissions** when they matter.\n"
            "- Keep one feature per request for focused coverage.\n"
            "- Review the **Assumptions** and **Open Questions** tabs."
        )
    st.caption(f"Model: `{MODEL_NAME}`")

# ----------------------------------------------------------------------
# Requirement input
# ----------------------------------------------------------------------
st.subheader("📝 Requirement")

sample_cols = st.columns(len(SAMPLE_REQUIREMENTS) + 1)
sample_cols[0].markdown("**Try an example:**")
for col, (name, text) in zip(sample_cols[1:], SAMPLE_REQUIREMENTS.items()):
    col.button(
        name,
        key=f"sample_{name}",
        on_click=set_sample,
        args=(text,),
        **STRETCH,
    )

requirement = st.text_area(
    "Requirement / User Story",
    key="requirement",
    placeholder=(
        "Example: As a user, I want to log in using my email "
        "and password so that I can access my account."
    ),
    height=170,
    label_visibility="collapsed",
)

action_cols = st.columns([1, 4])
generate = action_cols[0].button(
    "🚀 Generate Test Cases", type="primary", **STRETCH
)
action_cols[1].caption(
    f"{len(requirement.strip())} characters · {application_type} · "
    f"{testing_type} · {priority} · {detail_level}"
)

# ----------------------------------------------------------------------
# Generation
# ----------------------------------------------------------------------
if generate:
    if not requirement.strip():
        st.warning("Please enter a requirement or user story.")
    else:
        inputs = {
            "requirement": requirement,
            "application_type": application_type,
            "testing_type": testing_type,
            "priority": priority,
            "detail_level": detail_level,
        }
        response = ""
        started = time.time()
        with st.spinner("Analyzing the requirement and generating test cases..."):
            try:
                chain = get_chain(MODEL_NAME, PROMPT_PATH.stat().st_mtime)
                response = chain.invoke(inputs)
                data = parse_json_response(response)

                if not isinstance(data, dict):
                    raise ValueError("Unexpected response structure.")

                entry = {
                    "data": data,
                    "label": (
                        f"{datetime.now():%H:%M} · "
                        f"{requirement.strip()[:28]}..."
                    ),
                    "meta": {
                        "timestamp": f"{datetime.now():%Y-%m-%d %H:%M}",
                        "requirement": requirement.strip(),
                        "application_type": application_type,
                        "testing_type": testing_type,
                        "priority": priority,
                        "detail_level": detail_level,
                        "duration": time.time() - started,
                    },
                }
                st.session_state["result"] = entry
                st.session_state["history"] = (
                    st.session_state["history"] + [entry]
                )[-5:]

            except json.JSONDecodeError:
                st.error(
                    "The AI response was not valid JSON. "
                    "Please try again or check your prompt template."
                )
                with st.expander("View raw response"):
                    st.code(response or "(empty response)")

            except Exception as e:
                st.error(f"Unable to generate test cases: {e}")

# ----------------------------------------------------------------------
# Results
# ----------------------------------------------------------------------


def render_test_case(tc: dict, expanded: bool):
    prio = normalize_priority(tc.get("priority"))
    color, icon = PRIORITY_META.get(prio, ("#6b7280", "⚪"))
    title = f"{icon} {tc.get('test_case_id', '')} — {tc.get('scenario', 'Test Case')}"

    with st.expander(title, expanded=expanded):
        st.markdown(
            f'<span class="badge badge-type">{esc(tc.get("test_type", "N/A"))}</span>'
            f'<span class="badge" style="background:{color}">'
            f'{esc(prio or "N/A")} priority</span>',
            unsafe_allow_html=True,
        )

        left, right = st.columns(2)
        with left:
            st.markdown('<div class="meta-label">Preconditions</div>', unsafe_allow_html=True)
            st.write(tc.get("preconditions") or "N/A")
        with right:
            st.markdown('<div class="meta-label">Test Data</div>', unsafe_allow_html=True)
            st.write(tc.get("test_data") or "N/A")

        st.markdown('<div class="meta-label">Requirement Coverage</div>', unsafe_allow_html=True)
        st.write(tc.get("requirement_coverage") or "N/A")

        st.markdown('<div class="meta-label">Test Steps</div>', unsafe_allow_html=True)
        for i, step in enumerate(as_list(tc.get("steps")), start=1):
            st.markdown(f"{i}. {step}")

        st.success(f"**Expected Result:** {tc.get('expected_result') or 'N/A'}")


def render_results(entry: dict):
    data, meta = entry["data"], entry["meta"]
    test_cases = [tc for tc in as_list(data.get("test_cases")) if isinstance(tc, dict)]

    st.divider()
    head_l, head_r = st.columns([4, 1])
    head_l.subheader("✅ Generated Test Cases")
    head_r.button("Clear results", on_click=clear_results, **STRETCH)
    st.caption(
        f"Generated {meta['timestamp']} in {meta['duration']:.1f}s · "
        f"{meta['application_type']} · {meta['testing_type']} · "
        f"{meta['priority']} · {meta['detail_level']}"
    )

    if not test_cases:
        st.warning("The AI response did not contain any test cases.")
        return

    prio_counts = pd.Series(
        [normalize_priority(tc.get("priority")) or "Unspecified" for tc in test_cases]
    ).value_counts()
    type_counts = pd.Series(
        [str(tc.get("test_type") or "Unspecified") for tc in test_cases]
    ).value_counts()

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Test Cases", len(test_cases))
    m2.metric("🔴 High", int(prio_counts.get("High", 0)))
    m3.metric("🟠 Medium", int(prio_counts.get("Medium", 0)))
    m4.metric("🟢 Low", int(prio_counts.get("Low", 0)))
    m5.metric("Test Types", len(type_counts))

    with st.expander("📈 Coverage overview"):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**By priority**")
            st.bar_chart(prio_counts)
        with c2:
            st.markdown("**By test type**")
            st.bar_chart(type_counts)

    with st.expander("📄 Requirement used"):
        st.write(meta["requirement"])

    tab_cases, tab_table, tab_notes, tab_export = st.tabs(
        [
            "🧪 Test Cases",
            "📋 Summary Table",
            "📝 Assumptions & Questions",
            "📤 Export",
        ]
    )

    with tab_cases:
        f1, f2, f3, f4 = st.columns([2, 2, 2, 1])
        search = f1.text_input("Search", placeholder="Search scenarios, steps...")
        prio_filter = f2.multiselect(
            "Priority", ["High", "Medium", "Low"], placeholder="All priorities"
        )
        type_filter = f3.multiselect(
            "Test type", sorted(type_counts.index), placeholder="All types"
        )
        expand_all = f4.checkbox("Expand all")

        def matches(tc: dict) -> bool:
            if prio_filter and normalize_priority(tc.get("priority")) not in prio_filter:
                return False
            if type_filter and str(tc.get("test_type") or "Unspecified") not in type_filter:
                return False
            if search and search.lower() not in json.dumps(tc).lower():
                return False
            return True

        filtered = [tc for tc in test_cases if matches(tc)]
        st.caption(f"Showing {len(filtered)} of {len(test_cases)} test cases")
        if not filtered:
            st.info("No test cases match the current filters.")
        for tc in filtered:
            render_test_case(tc, expand_all)

    with tab_table:
        st.dataframe(
            [
                {
                    "Test Case ID": tc.get("test_case_id", ""),
                    "Scenario": tc.get("scenario", ""),
                    "Test Type": tc.get("test_type", ""),
                    "Priority": tc.get("priority", ""),
                    "Steps": len(as_list(tc.get("steps"))),
                    "Requirement Coverage": tc.get("requirement_coverage", ""),
                    "Expected Result": tc.get("expected_result", ""),
                }
                for tc in test_cases
            ],
            **STRETCH,
            hide_index=True,
        )

    with tab_notes:
        assumptions = as_list(data.get("assumptions"))
        questions = as_list(data.get("open_questions"))
        n1, n2 = st.columns(2)
        with n1:
            st.markdown("#### Assumptions")
            if assumptions:
                for item in assumptions:
                    st.info(str(item))
            else:
                st.caption("No assumptions were recorded.")
        with n2:
            st.markdown("#### Open Questions")
            if questions:
                for item in questions:
                    st.warning(str(item))
            else:
                st.caption("No open questions. The requirement was clear enough.")

    with tab_export:
        st.markdown("Download the generated test cases in your preferred format.")
        stamp = datetime.now().strftime("%Y%m%d_%H%M")
        e1, e2, e3 = st.columns(3)
        e1.download_button(
            "⬇️ JSON",
            data=json.dumps(data, indent=2),
            file_name=f"test_cases_{stamp}.json",
            mime="application/json",
            **STRETCH,
        )
        e2.download_button(
            "⬇️ CSV (Excel)",
            data=build_csv(test_cases),
            file_name=f"test_cases_{stamp}.csv",
            mime="text/csv",
            **STRETCH,
        )
        e3.download_button(
            "⬇️ Markdown",
            data=build_markdown(entry),
            file_name=f"test_cases_{stamp}.md",
            mime="text/markdown",
            **STRETCH,
        )
        st.caption(
            "JSON suits automation and tooling, CSV opens in Excel or can be "
            "imported into test management tools, and Markdown works well for "
            "documentation and reviews."
        )


def render_welcome():
    st.divider()
    st.subheader("How it works")
    c1, c2, c3 = st.columns(3)
    cards = [
        ("1️⃣", "Describe the requirement",
         "Paste a user story, acceptance criteria or feature description. "
         "More detail means better coverage."),
        ("2️⃣", "Configure the test scope",
         "Choose the application type, testing type, priority focus and "
         "detail level from the sidebar."),
        ("3️⃣", "Review and export",
         "Filter and review the generated cases, then export them as "
         "JSON, CSV or Markdown."),
    ]
    for col, (icon, title, body) in zip((c1, c2, c3), cards):
        col.markdown(
            f'<div class="card"><div class="icon">{icon}</div>'
            f"<h4>{title}</h4><p>{body}</p></div>",
            unsafe_allow_html=True,
        )

    st.write("")
    st.subheader("What you get")
    f1, f2, f3, f4 = st.columns(4)
    features = [
        ("🎯", "Full scenario coverage",
         "Positive, negative, boundary and validation scenarios."),
        ("🔗", "Requirement traceability",
         "Every case links back to the rule or criterion it covers."),
        ("🧭", "Assumptions surfaced",
         "Gaps and open questions are listed instead of guessed."),
        ("📦", "Export ready",
         "Download as JSON, CSV or Markdown for your tools."),
    ]
    for col, (icon, title, body) in zip((f1, f2, f3, f4), features):
        col.markdown(
            f'<div class="card"><div class="icon">{icon}</div>'
            f"<h4>{title}</h4><p>{body}</p></div>",
            unsafe_allow_html=True,
        )


if st.session_state["result"]:
    render_results(st.session_state["result"])
else:
    render_welcome()

st.markdown(
    '<div class="app-footer">AI-generated test cases should be reviewed '
    "by a QA engineer before execution.</div>",
    unsafe_allow_html=True,
)