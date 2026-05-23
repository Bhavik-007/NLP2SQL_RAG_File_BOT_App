import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st

from app.core.config import config
from app.core.logging_config import write_audit_event
from app.services.bot_service import SQLBotService
from app.services.rag_service import RAGService


st.set_page_config(
    page_title="Enterprise SQL Assistant",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_enterprise_styles() -> None:
    st.markdown(
        """
        <style>
            :root {
                --app-bg: #f5f7fb;
                --panel-bg: #ffffff;
                --ink: #172033;
                --muted: #637083;
                --line: #d9e0ea;
                --accent: #1f5eff;
            }

            .stApp {
                background: var(--app-bg);
                color: var(--ink);
            }

            .block-container {
                padding-top: 1.35rem;
                padding-bottom: 5.5rem;
                max-width: 1180px;
            }

            [data-testid="stSidebar"] {
                background: #101827;
                border-right: 1px solid #1f2b3d;
            }

            [data-testid="stSidebar"] * {
                color: #eef4ff;
            }

            [data-testid="stSidebar"] .stSelectbox label,
            [data-testid="stSidebar"] .stCaptionContainer {
                color: #b8c4d6;
            }

            [data-testid="stSidebar"] div[data-baseweb="select"] > div {
                background: #172236;
                border-color: #334155;
                border-radius: 8px;
            }

            [data-testid="stSidebar"] [data-testid="stFileUploader"] section {
                background: #ffffff;
                border: 1px solid #d9e0ea;
                border-radius: 8px;
            }

            [data-testid="stSidebar"] [data-testid="stFileUploader"] section * {
                color: #172033;
            }

            .document-list {
                background: #172236;
                border: 1px solid #2a3850;
                border-radius: 8px;
                padding: 10px 12px;
                margin: 10px 0 12px;
            }

            .document-list-title {
                color: #93a4bb;
                font-size: 0.73rem;
                font-weight: 700;
                text-transform: uppercase;
                margin-bottom: 6px;
            }

            .document-item {
                color: #ffffff;
                font-size: 0.82rem;
                padding: 4px 0;
                border-top: 1px solid #25344b;
                overflow-wrap: anywhere;
            }

            .document-item:first-of-type {
                border-top: 0;
            }

            .app-header {
                background: var(--panel-bg);
                border: 1px solid var(--line);
                border-radius: 8px;
                padding: 22px 24px;
                box-shadow: 0 10px 28px rgba(23, 32, 51, 0.06);
                margin-bottom: 18px;
            }

            .eyebrow {
                color: var(--accent);
                font-size: 0.78rem;
                font-weight: 700;
                letter-spacing: 0;
                text-transform: uppercase;
                margin-bottom: 6px;
            }

            .app-title {
                color: var(--ink);
                font-size: 2rem;
                line-height: 1.15;
                font-weight: 760;
                margin: 0;
            }

            .app-subtitle {
                color: var(--muted);
                font-size: 0.98rem;
                line-height: 1.55;
                margin-top: 8px;
                max-width: 760px;
            }

            .status-grid {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 12px;
                margin: 8px 0 18px;
            }

            .status-card {
                background: var(--panel-bg);
                border: 1px solid var(--line);
                border-radius: 8px;
                padding: 14px 16px;
                min-height: 86px;
            }

            .status-label {
                color: var(--muted);
                font-size: 0.78rem;
                font-weight: 650;
                margin-bottom: 6px;
            }

            .status-value {
                color: var(--ink);
                font-size: 0.98rem;
                font-weight: 720;
                overflow-wrap: anywhere;
            }

            .status-note {
                color: var(--muted);
                font-size: 0.75rem;
                margin-top: 5px;
            }

            .chat-shell {
                padding: 4px 0 0;
            }

            .section-title {
                color: var(--ink);
                font-size: 0.95rem;
                font-weight: 740;
                margin-bottom: 3px;
            }

            .section-caption {
                color: var(--muted);
                font-size: 0.82rem;
                margin-bottom: 10px;
            }

            .empty-state {
                border-left: 3px solid var(--line);
                padding: 8px 0 8px 12px;
                margin: 8px 0 10px;
                color: var(--muted);
                font-size: 0.86rem;
            }

            .sidebar-brand {
                font-size: 1.08rem;
                font-weight: 760;
                color: #ffffff;
                margin-bottom: 2px;
            }

            .sidebar-copy {
                font-size: 0.82rem;
                line-height: 1.45;
                color: #b8c4d6;
                margin-bottom: 18px;
            }

            .sidebar-panel {
                background: #172236;
                border: 1px solid #2a3850;
                border-radius: 8px;
                padding: 12px;
                margin: 12px 0;
            }

            .sidebar-panel-label {
                color: #93a4bb;
                font-size: 0.73rem;
                font-weight: 700;
                text-transform: uppercase;
                margin-bottom: 4px;
            }

            .sidebar-panel-value {
                color: #ffffff;
                font-size: 0.86rem;
                overflow-wrap: anywhere;
            }

            .stButton > button,
            .stDownloadButton > button {
                border-radius: 8px;
                border: 1px solid #2a3850;
                background: #172236;
                color: #eef4ff;
                font-weight: 650;
            }

            .stButton > button:hover,
            .stDownloadButton > button:hover {
                border-color: #6b8cff;
                color: #ffffff;
            }

            section.main .stButton > button {
                background: #ffffff;
                color: #243047;
                border: 1px solid var(--line);
                font-weight: 600;
                min-height: 2.35rem;
            }

            section.main .stButton > button:hover {
                color: var(--accent);
                border-color: #b9c8ff;
                background: #fbfcff;
            }

            div[data-testid="stChatInput"] {
                border-top: 1px solid var(--line);
                background: rgba(245, 247, 251, 0.95);
            }

            @media (max-width: 780px) {
                .status-grid {
                    grid-template-columns: 1fr;
                }

                .app-title {
                    font-size: 1.55rem;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource(show_spinner=False)
def get_bot(model_name: str) -> SQLBotService:
    return SQLBotService(model_name=model_name)


@st.cache_resource(show_spinner=False)
def get_rag_bot(model_name: str) -> RAGService:
    return RAGService(model_name=model_name)


def set_pending_prompt(text: str) -> None:
    st.session_state.pending_prompt = text


def uploaded_file_signature(uploaded_file) -> str:
    return f"{uploaded_file.name}:{len(uploaded_file.getvalue())}"


def render_uploaded_documents(uploaded_files) -> None:
    if not uploaded_files:
        return

    items = []
    for uploaded_file in uploaded_files:
        size_kb = len(uploaded_file.getvalue()) / 1024
        items.append(
            f'<div class="document-item">{uploaded_file.name} - {size_kb:.1f} KB</div>'
        )

    st.markdown(
        f"""
        <div class="document-list">
            <div class="document-list-title">Selected Documents</div>
            {''.join(items)}
        </div>
        """,
        unsafe_allow_html=True,
    )


def create_document_index(model: str, uploaded_files) -> None:
    if not uploaded_files:
        st.warning("Please upload at least one document before creating the index.")
        return

    rag_bot = get_rag_bot(model_name=model)
    with st.spinner("Creating document index..."):
        chunk_count, errors, indexed_files = rag_bot.ingest_files(uploaded_files)

    indexed_signatures = st.session_state.indexed_document_signatures
    for uploaded_file in uploaded_files:
        if uploaded_file.name in indexed_files:
            indexed_signatures.add(uploaded_file_signature(uploaded_file))

    if chunk_count:
        st.session_state.document_index_ready = True
        st.success(f"Indexed {chunk_count} document chunks.")
    elif not errors:
        st.session_state.document_index_ready = False
        st.warning("No text chunks were indexed from the uploaded documents.")
    for error in errors:
        st.session_state.document_index_ready = False
        st.error(error)


def render_sidebar(model: str, mode: str) -> None:
    db_info = config.effective_database_settings
    rag_settings = config.rag_settings.get("rag", {})

    st.markdown(
        f"""
        <div class="sidebar-panel">
            <div class="sidebar-panel-label">Database</div>
            <div class="sidebar-panel-value">{db_info['server']} / {db_info['database']}</div>
        </div>
        <div class="sidebar-panel">
            <div class="sidebar-panel-label">Driver</div>
            <div class="sidebar-panel-value">{db_info['driver']}</div>
        </div>
        <div class="sidebar-panel">
            <div class="sidebar-panel-label">Qdrant Endpoint</div>
            <div class="sidebar-panel-value">{config.qdrant_url}</div>
        </div>
        <div class="sidebar-panel">
            <div class="sidebar-panel-label">Active Model</div>
            <div class="sidebar-panel-value">{model}</div>
        </div>
        <div class="sidebar-panel">
            <div class="sidebar-panel-label">Assistant Mode</div>
            <div class="sidebar-panel-value">{mode}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if mode == "Document Assistant":
        uploaded_files = st.file_uploader(
            "Upload Documents",
            type=rag_settings.get("supported_file_types", ["txt", "md", "csv", "pdf", "docx"]),
            accept_multiple_files=True,
            key="document_uploads",
        )
        render_uploaded_documents(uploaded_files)
        if uploaded_files:
            current_signatures = {uploaded_file_signature(item) for item in uploaded_files}
            if not current_signatures.issubset(st.session_state.indexed_document_signatures):
                st.session_state.document_index_ready = False

            if st.button("Create Document Index", use_container_width=True):
                create_document_index(model, uploaded_files)

            if st.session_state.document_index_ready:
                st.success("Document index is ready.")
            else:
                st.caption("Click Create Document Index before asking document questions.")

    if st.button("Clear Chat", use_container_width=True):
        st.session_state[active_messages_key(mode)] = []

    audit_path = config.root_dir / "logs" / "app.csv"
    if audit_path.exists():
        with open(audit_path, "rb") as file:
            st.download_button(
                "Download Audit Logs",
                file,
                "app.csv",
                "text/csv",
                use_container_width=True,
            )
    else:
        st.caption("No audit log has been created yet.")


def render_header(model: str, mode: str) -> None:
    db_info = config.effective_database_settings
    title = (
        "Ask business questions. Get database-backed answers."
        if mode == "SQL Assistant"
        else "Ask document questions. Get grounded answers with sources."
    )
    subtitle = (
        "Query SQL Server through a controlled assistant that retrieves approved schema context, "
        "validates generated SQL, executes read-only queries, and returns business-ready summaries."
        if mode == "SQL Assistant"
        else "Upload business documents, index them into a vector store, and ask questions answered only from retrieved document context."
    )
    st.markdown(
        f"""
        <div class="app-header">
            <div class="eyebrow">Governed analytics bot</div>
            <h1 class="app-title">{title}</h1>
            <div class="app-subtitle">
                {subtitle}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="status-grid">
            <div class="status-card">
                <div class="status-label">Assistant Mode</div>
                <div class="status-value">{mode}</div>
                <div class="status-note">SQL and document RAG are separated</div>
            </div>
            <div class="status-card">
                <div class="status-label">{'Database' if mode == 'SQL Assistant' else 'Vector Store'}</div>
                <div class="status-value">{db_info['database'] if mode == 'SQL Assistant' else config.qdrant_url}</div>
                <div class="status-note">{'Read-only query execution' if mode == 'SQL Assistant' else 'Qdrant with memory fallback'}</div>
            </div>
            <div class="status-card">
                <div class="status-label">LLM Runtime</div>
                <div class="status-value">{model}</div>
                <div class="status-note">Ollama local model</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state(mode: str) -> None:
    message = (
        "Start with a focused business question. The assistant keeps generated SQL internal and returns the result as a business answer."
        if mode == "SQL Assistant"
        else "Upload a document from the sidebar. Once indexed, ask a question about the document content."
    )
    st.markdown(
        f"""
        <div class="empty-state">
            {message}
        </div>
        """,
        unsafe_allow_html=True,
    )


def active_messages_key(mode: str) -> str:
    return "sql_messages" if mode == "SQL Assistant" else "rag_messages"


def handle_prompt(prompt: str, model: str, mode: str) -> None:
    messages_key = active_messages_key(mode)
    st.session_state[messages_key].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        spinner_text = (
            "Querying database and preparing the answer..."
            if mode == "SQL Assistant"
            else "Retrieving document context and preparing the answer..."
        )
        with st.spinner(spinner_text):
            if mode == "SQL Assistant":
                bot = get_bot(model_name=model)
                answer, generated_sql = bot.ask(prompt)
                status = (
                    "success"
                    if generated_sql
                    and not answer.startswith(
                        ("Execution Error", "Security Violation", "I could not generate")
                    )
                    else "failed"
                )
                write_audit_event(prompt, generated_sql, answer, status)
            else:
                rag_bot = get_rag_bot(model_name=model)
                answer, _ = rag_bot.ask(prompt)
                write_audit_event(prompt, "", answer, "document_rag")
            st.markdown(answer)

    st.session_state[messages_key].append({"role": "assistant", "content": answer})


inject_enterprise_styles()

if "sql_messages" not in st.session_state:
    st.session_state.sql_messages = []

if "rag_messages" not in st.session_state:
    st.session_state.rag_messages = []

if "indexed_document_signatures" not in st.session_state:
    st.session_state.indexed_document_signatures = set()

if "document_index_ready" not in st.session_state:
    st.session_state.document_index_ready = False

configured_model = config.settings.get("ollama", {}).get("model", "llama3")
available_models = list(dict.fromkeys([configured_model, "llama3", "mistral"]))

with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">Enterprise SQL Assistant</div>
        <div class="sidebar-copy">Natural language access to governed SQL Server insights.</div>
        """,
        unsafe_allow_html=True,
    )
    selected_model = st.selectbox("Ollama Model", available_models)
    selected_mode = st.radio(
        "Assistant Mode",
        ["SQL Assistant", "Document Assistant"],
        horizontal=False,
    )
    render_sidebar(selected_model, selected_mode)

render_header(selected_model, selected_mode)

st.markdown('<div class="chat-shell">', unsafe_allow_html=True)
st.markdown('<div class="section-title">Ask a Question</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-caption">Type a business question for SQL mode or a document question for Document Assistant mode.</div>',
    unsafe_allow_html=True,
)

messages_key = active_messages_key(selected_mode)
messages = st.session_state[messages_key]

if not messages:
    render_empty_state(selected_mode)

for message in messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

typed_prompt = st.chat_input(
    "Ask a business question..." if selected_mode == "SQL Assistant" else "Ask a question about uploaded documents..."
)
active_prompt = typed_prompt or st.session_state.pop("pending_prompt", None)

if active_prompt:
    handle_prompt(active_prompt, selected_model, selected_mode)

st.markdown("</div>", unsafe_allow_html=True)
