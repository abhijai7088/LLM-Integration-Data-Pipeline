"""
Streamlit dashboard for the LLM Integration & Data Pipeline.
Run with:  streamlit run streamlit_app.py
"""
from __future__ import annotations

import io
import json
import logging
import os
import tempfile
from collections import Counter
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── page config (MUST be first Streamlit call) ──────────────────────────────
st.set_page_config(
    page_title="LLM Data Pipeline",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Dark background */
.stApp { background: #0d0d14; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #13131f 0%, #0d0d14 100%);
    border-right: 1px solid #1e1e2e;
}

/* Metric cards */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border: 1px solid #2a2a4a;
    border-radius: 12px;
    padding: 16px;
}

/* Glass card helper */
.glass-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 20px 24px;
    margin-bottom: 16px;
    backdrop-filter: blur(10px);
}

/* Sentiment badge */
.badge-positive { background:#14532d; color:#86efac; border-radius:6px; padding:2px 10px; font-size:0.78rem; font-weight:600; }
.badge-neutral  { background:#1e3a5f; color:#93c5fd; border-radius:6px; padding:2px 10px; font-size:0.78rem; font-weight:600; }
.badge-negative { background:#4c0519; color:#fca5a5; border-radius:6px; padding:2px 10px; font-size:0.78rem; font-weight:600; }

/* Entity chips */
.entity-chip {
    display:inline-block;
    background:rgba(99,102,241,0.18);
    color:#a5b4fc;
    border:1px solid rgba(99,102,241,0.35);
    border-radius:20px;
    padding:2px 10px;
    font-size:0.75rem;
    margin:2px 3px 2px 0;
}

/* Header gradient text */
.gradient-title {
    background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.4rem;
    font-weight: 700;
    line-height: 1.2;
}

/* Run button */
div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #6366f1, #a855f7);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 10px 32px;
    font-weight: 600;
    font-size: 1rem;
    width: 100%;
    transition: opacity 0.2s;
}
div[data-testid="stButton"] > button:hover { opacity: 0.88; }

/* Expander */
details { border: 1px solid #1e1e2e !important; border-radius: 10px !important; }

/* Dataframe */
[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }

/* Log area */
.log-box {
    background:#0a0a12;
    border:1px solid #1e1e2e;
    border-radius:10px;
    padding:12px 16px;
    font-family:monospace;
    font-size:0.78rem;
    color:#94a3b8;
    max-height:220px;
    overflow-y:auto;
    white-space:pre-wrap;
}
</style>
""", unsafe_allow_html=True)


# ── helpers ──────────────────────────────────────────────────────────────────

SENTIMENT_COLORS = {
    "positive": "#22c55e",
    "neutral":  "#60a5fa",
    "negative": "#f87171",
}


def badge(sentiment: str) -> str:
    css = f"badge-{sentiment}"
    return f'<span class="{css}">{sentiment.upper()}</span>'


def entity_chips(entities: list[str]) -> str:
    return "".join(f'<span class="entity-chip">{e}</span>' for e in entities)


def _make_log_handler() -> tuple[logging.Handler, io.StringIO]:
    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    return handler, buf


def run_pipeline(
    files: list[str],
    urls: list[str],
    provider: str,
    model: str,
    api_key: str,
    max_chars: int,
    timeout: int,
    output_dir: Path,
):
    """Run the pipeline inside the Streamlit process."""
    # Inject env vars so Settings picks them up
    os.environ["LLM_PROVIDER"]             = provider
    os.environ["LLM_MODEL"]                = model
    os.environ[f"{provider.upper()}_API_KEY"] = api_key
    os.environ["MAX_CHARS_PER_CHUNK"]      = str(max_chars)
    os.environ["REQUEST_TIMEOUT_SECONDS"]  = str(timeout)
    os.environ["OUTPUT_DIR"]               = str(output_dir)
    os.environ["LOG_LEVEL"]                = "INFO"

    # Re-import so Settings re-reads env vars
    import importlib
    import app.config as cfg_mod
    importlib.reload(cfg_mod)
    settings = cfg_mod.Settings()

    from app.logger import setup_logger
    from app.pipeline.runner import PipelineRunner
    from app.pipeline.reporter import ReportBuilder
    from app.output.writer import ResultWriter

    log_handler, log_buf = _make_log_handler()
    logger = setup_logger("INFO")
    logger.handlers.clear()
    logger.addHandler(log_handler)

    runner = PipelineRunner(settings, logger)
    documents = runner.load_inputs(files, urls)
    chunks    = runner.build_chunks(documents)
    results   = runner.run(chunks)

    writer  = ResultWriter(output_dir)
    builder = ReportBuilder()

    json_path   = writer.write_json(results)
    csv_path    = writer.write_csv(results)
    excel_path  = writer.write_excel(results)
    report_path = writer.write_report(builder.build(results, runner.skipped_items))

    log_text = log_buf.getvalue()
    return results, runner.skipped_items, json_path, csv_path, excel_path, report_path, log_text


# ── sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ⚡ Pipeline Config")
    st.markdown("---")

    provider = st.selectbox("LLM Provider", ["groq", "openai"], index=0)

    default_model = "llama-3.1-8b-instant" if provider == "groq" else "gpt-4o-mini"
    model = st.text_input("Model", value=default_model)

    env_key_name = "GROQ_API_KEY" if provider == "groq" else "OPENAI_API_KEY"
    _env_key     = os.getenv(env_key_name, "")

    # Show status — never expose the actual key value in the UI
    if _env_key:
        st.markdown(
            "<small style='color:#86efac'>🔒 API key loaded from <code>.env</code></small>",
            unsafe_allow_html=True,
        )

    api_key_override = st.text_input(
        f"{provider.upper()} API Key",
        value="",           # always blank — key is never pre-filled
        type="password",
        placeholder="Paste key here to override .env…" if _env_key else "Required — paste your key here",
        help="Leave blank to use the key from your .env file. Type here only to override it.",
    )
    # Resolve: typed override takes priority; fall back to .env value
    api_key = api_key_override.strip() or _env_key

    st.markdown("---")
    st.markdown("**Advanced**")
    max_chars = st.slider("Max chars per chunk", 1000, 12000, 6000, 500)
    timeout   = st.slider("Request timeout (s)",  10,    120,    45,   5)

    output_dir = Path(st.text_input("Output directory", "sample_outputs"))

    st.markdown("---")
    st.markdown(
        "<small style='color:#475569'>No LangChain · Direct httpx calls · "
        "Tenacity retry · Structured JSON</small>",
        unsafe_allow_html=True,
    )


# ── header ───────────────────────────────────────────────────────────────────

st.markdown('<p class="gradient-title">⚡ LLM Data Pipeline</p>', unsafe_allow_html=True)
st.markdown(
    "<p style='color:#64748b;margin-top:-8px;'>Ingest files & URLs · Extract entities, "
    "sentiment & summaries · Export JSON / CSV / Excel</p>",
    unsafe_allow_html=True,
)
st.markdown("---")


# ── input section ─────────────────────────────────────────────────────────────

col_file, col_url = st.columns(2, gap="large")

with col_file:
    st.markdown("### 📄 File Inputs")
    uploaded = st.file_uploader(
        "Drag & drop `.txt` or `.pdf` files",
        type=["txt", "pdf"],
        accept_multiple_files=True,
    )

with col_url:
    st.markdown("### 🌐 URL Inputs")
    url_text = st.text_area(
        "One URL per line",
        placeholder="https://example.com\nhttps://www.ietf.org/about/",
        height=160,
    )

st.markdown("")
run_clicked = st.button("🚀  Run Pipeline", use_container_width=True)


# ── run pipeline ─────────────────────────────────────────────────────────────

if run_clicked:
    urls = [u.strip() for u in url_text.splitlines() if u.strip()]

    if not uploaded and not urls:
        st.error("⚠️  Please upload at least one file or enter at least one URL.")
        st.stop()

    if not api_key:
        st.error(f"⚠️  Please enter your {provider.upper()} API key in the sidebar.")
        st.stop()

    # Save uploaded files to a temp directory
    tmp_dir   = Path(tempfile.mkdtemp())
    tmp_paths: list[str] = []
    for uf in (uploaded or []):
        dest = tmp_dir / uf.name
        dest.write_bytes(uf.read())
        tmp_paths.append(str(dest))

    progress = st.progress(0, text="⚙️  Starting pipeline…")

    try:
        progress.progress(15, text="📥  Loading inputs…")
        (
            results, skipped,
            json_path, csv_path, excel_path, report_path,
            log_text,
        ) = run_pipeline(
            files=tmp_paths,
            urls=urls,
            provider=provider,
            model=model,
            api_key=api_key,
            max_chars=max_chars,
            timeout=timeout,
            output_dir=output_dir,
        )
        progress.progress(100, text="✅  Done!")

        st.session_state["results"]     = results
        st.session_state["skipped"]     = skipped
        st.session_state["json_path"]   = json_path
        st.session_state["csv_path"]    = csv_path
        st.session_state["excel_path"]  = excel_path
        st.session_state["report_path"] = report_path
        st.session_state["log_text"]    = log_text

    except Exception as exc:
        progress.empty()
        st.error(f"❌  Pipeline failed: {exc}")
        st.stop()


# ── results dashboard ─────────────────────────────────────────────────────────

if "results" not in st.session_state:
    st.stop()

results     = st.session_state["results"]
skipped     = st.session_state["skipped"]
json_path   = st.session_state["json_path"]
csv_path    = st.session_state["csv_path"]
excel_path  = st.session_state["excel_path"]
report_path = st.session_state["report_path"]
log_text    = st.session_state["log_text"]

if not results:
    st.warning("Pipeline ran but produced no results. Check the log below.")
else:
    st.markdown("---")
    st.markdown("## 📊 Results")

    # ── KPI metrics ──────────────────────────────────────────────────────────
    sentiments   = Counter(r.sentiment for r in results)
    all_entities = [e for r in results for e in r.entities]
    sources      = len({r.source_id for r in results})
    avg_conf     = sum(r.confidence_score for r in results) / len(results)

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("📦 Chunks", len(results))
    m2.metric("📂 Sources", sources)
    m3.metric("😊 Positive", sentiments.get("positive", 0))
    m4.metric("😐 Neutral",  sentiments.get("neutral",  0))
    m5.metric("😠 Negative", sentiments.get("negative", 0))

    st.markdown("")

    # ── charts ───────────────────────────────────────────────────────────────
    chart_col, entity_col = st.columns([1, 2], gap="large")

    with chart_col:
        st.markdown("#### Sentiment Distribution")
        labels = list(sentiments.keys())
        values = list(sentiments.values())
        colors = [SENTIMENT_COLORS.get(l, "#94a3b8") for l in labels]
        fig_pie = go.Figure(go.Pie(
            labels=labels, values=values,
            marker_colors=colors,
            hole=0.55,
            textinfo="label+percent",
            textfont_size=13,
        ))
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#cbd5e1",
            showlegend=False,
            margin=dict(t=10, b=10, l=10, r=10),
            height=240,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with entity_col:
        st.markdown("#### Top 10 Entities")
        top_entities = Counter(all_entities).most_common(10)
        if top_entities:
            ent_df = pd.DataFrame(top_entities, columns=["Entity", "Count"])
            fig_bar = px.bar(
                ent_df, x="Count", y="Entity",
                orientation="h",
                color="Count",
                color_continuous_scale=["#6366f1", "#a855f7", "#ec4899"],
            )
            fig_bar.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#cbd5e1",
                coloraxis_showscale=False,
                margin=dict(t=10, b=10, l=10, r=20),
                height=240,
                yaxis=dict(autorange="reversed"),
                xaxis=dict(gridcolor="#1e1e2e"),
            )
            fig_bar.update_traces(marker_line_width=0)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No entities extracted.")

    st.markdown("")

    # ── avg confidence gauge ─────────────────────────────────────────────────
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(avg_conf * 100, 1),
        title={"text": "Avg Confidence Score", "font": {"color": "#cbd5e1", "size": 14}},
        number={"suffix": "%", "font": {"color": "#a5b4fc", "size": 32}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#475569"},
            "bar":  {"color": "#6366f1"},
            "bgcolor": "#1a1a2e",
            "bordercolor": "#2a2a4a",
            "steps": [
                {"range": [0,  40], "color": "#4c0519"},
                {"range": [40, 70], "color": "#1e3a5f"},
                {"range": [70, 100],"color": "#14532d"},
            ],
        },
    ))
    fig_gauge.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#cbd5e1",
        height=200,
        margin=dict(t=30, b=10, l=40, r=40),
    )
    g1, g2, g3 = st.columns([1, 1, 1])
    with g2:
        st.plotly_chart(fig_gauge, use_container_width=True)

    st.markdown("---")

    # ── flat results table ────────────────────────────────────────────────────
    st.markdown("#### 📋 All Chunks")
    rows = []
    for r in results:
        rows.append({
            "Chunk ID":    r.chunk_id,
            "Source":      r.source_name,
            "Type":        r.source_type,
            "Chunk #":     r.chunk_index,
            "Sentiment":   r.sentiment,
            "Confidence":  f"{r.confidence_score:.0%}",
            "Summary":     r.summary[:120] + ("…" if len(r.summary) > 120 else ""),
            "Entities":    ", ".join(r.entities[:5]),
        })
    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
        height=min(60 + len(rows) * 38, 420),
    )

    st.markdown("")

    # ── per-chunk expanders ───────────────────────────────────────────────────
    st.markdown("#### 🔍 Detailed Results")
    for r in results:
        icon = {"positive": "🟢", "neutral": "🔵", "negative": "🔴"}.get(r.sentiment, "⚪")
        with st.expander(f"{icon}  {r.chunk_id}  ·  {r.source_name}  ·  chunk {r.chunk_index}"):
            dc1, dc2 = st.columns([3, 1])
            with dc1:
                st.markdown(f"**Summary**\n\n{r.summary}")
                st.markdown("**Questions raised**")
                for q in r.questions:
                    st.markdown(f"- {q}")
            with dc2:
                st.markdown("**Sentiment**")
                st.markdown(badge(r.sentiment), unsafe_allow_html=True)
                st.markdown(f"**Confidence**\n\n`{r.confidence_score:.0%}`")
                st.markdown("**Entities**")
                st.markdown(entity_chips(r.entities), unsafe_allow_html=True)

    st.markdown("---")

    # ── downloads ─────────────────────────────────────────────────────────────
    st.markdown("#### 💾 Download Outputs")
    dl1, dl2, dl3, dl4 = st.columns(4)

    with dl1:
        st.download_button(
            "⬇ JSON",
            data=json_path.read_text(encoding="utf-8"),
            file_name="extracted_results.json",
            mime="application/json",
            use_container_width=True,
        )
    with dl2:
        st.download_button(
            "⬇ CSV",
            data=csv_path.read_bytes(),
            file_name="extracted_results.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with dl3:
        if excel_path and excel_path.exists():
            st.download_button(
                "⬇ Excel",
                data=excel_path.read_bytes(),
                file_name="extracted_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
    with dl4:
        st.download_button(
            "⬇ Report",
            data=report_path.read_text(encoding="utf-8"),
            file_name="summary_report.txt",
            mime="text/plain",
            use_container_width=True,
        )

    # ── skipped items ─────────────────────────────────────────────────────────
    if skipped:
        st.markdown("")
        with st.expander(f"⚠️  {len(skipped)} skipped input(s)"):
            for s in skipped:
                st.markdown(f"- `{s}`")

# ── pipeline log ──────────────────────────────────────────────────────────────
if "log_text" in st.session_state and st.session_state["log_text"]:
    st.markdown("---")
    with st.expander("🪵  Pipeline Log"):
        st.markdown(
            f'<div class="log-box">{st.session_state["log_text"]}</div>',
            unsafe_allow_html=True,
        )
