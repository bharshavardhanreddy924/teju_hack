import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
from google import genai
from google.genai import types
import plotly.graph_objects as go
import plotly.express as px
import json
import io

st.set_page_config(page_title="InsightForge AI", page_icon="⚡", layout="wide")

EMERALD = "#10b981"
EMERALD_LIGHT = "#34d399"
EMERALD_DIM = "rgba(16, 185, 129, 0.12)"
GOLD = "#f59e0b"
GOLD_LIGHT = "#fbbf24"
BG_DARK = "#0b0f19"
SURFACE = "#111827"
BORDER = "rgba(255,255,255,0.06)"
TEXT = "#f9fafb"
TEXT_DIM = "#9ca3af"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'DM Sans', sans-serif !important; }}
    .stApp {{ background: {BG_DARK}; }}

    h1 {{
        color: {EMERALD_LIGHT} !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em;
    }}
    h2, h3 {{ color: {TEXT} !important; font-weight: 600 !important; }}

    section[data-testid="stSidebar"] {{
        background: {SURFACE} !important;
        border-right: 1px solid {BORDER} !important;
    }}
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {{
        color: {TEXT} !important;
    }}

    .stChatMessage {{
        border-radius: 14px !important;
        padding: 1.15rem !important;
        margin-bottom: 0.75rem !important;
        border: 1px solid {BORDER} !important;
        background: {SURFACE} !important;
    }}

    [data-testid="stChatInput"] {{ background: transparent !important; }}
    [data-testid="stChatInput"] > div {{
        border: 1px solid rgba(16, 185, 129, 0.25) !important;
        border-radius: 14px !important;
        background: {SURFACE} !important;
        transition: all 0.2s ease;
    }}
    [data-testid="stChatInput"] > div:focus-within {{
        border-color: {EMERALD} !important;
        box-shadow: 0 0 0 3px {EMERALD_DIM} !important;
    }}
    [data-testid="stBottom"] {{
        background: {BG_DARK} !important;
        border-top: 1px solid {BORDER} !important;
        padding-top: 0.5rem !important;
    }}
    [data-testid="stBottom"] > div {{
        background: {BG_DARK} !important;
    }}

    .stButton>button {{
        background: {EMERALD} !important;
        color: white !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }}
    .stButton>button:hover {{
        background: {EMERALD_LIGHT} !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3) !important;
    }}

    .stDataFrame {{ border-radius: 10px !important; overflow: hidden !important; }}
    div[data-testid="stExpander"] {{
        border: 1px solid {BORDER} !important;
        border-radius: 10px !important;
        background: {SURFACE} !important;
    }}
    hr {{ border-color: {BORDER} !important; }}

    .kpi-row {{ display: flex; gap: 0.75rem; margin: 0.75rem 0 1.25rem 0; }}
    .kpi {{ flex:1; background:{SURFACE}; border:1px solid {BORDER}; border-radius:12px; padding:1rem; text-align:center; }}
    .kpi-num {{ font-size:1.5rem; font-weight:700; color:{EMERALD_LIGHT}; }}
    .kpi-lbl {{ font-size:0.7rem; color:{TEXT_DIM}; text-transform:uppercase; letter-spacing:0.06em; font-weight:600; margin-top:0.15rem; }}
    .q-bar {{ height:5px; border-radius:3px; background:rgba(255,255,255,0.08); overflow:hidden; margin-top:0.4rem; }}
    .q-fill {{ height:100%; border-radius:3px; }}

    .note-card {{
        background: rgba(16, 185, 129, 0.06);
        border: 1px solid rgba(16, 185, 129, 0.15);
        border-radius: 12px;
        padding: 1.25rem;
        margin: 0.75rem 0;
    }}
    .note-card h4 {{ margin:0 0 0.5rem 0; color:{EMERALD_LIGHT}; font-weight:600; font-size:0.95rem; }}
    .note-card p {{ color:{TEXT_DIM}; margin:0; line-height:1.6; font-size:0.9rem; }}

    .welcome-box {{
        text-align: center;
        padding: 3rem 2rem;
        border: 1px dashed rgba(16, 185, 129, 0.2);
        border-radius: 16px;
        margin: 2rem 0;
    }}
    .welcome-box h3 {{ color: {EMERALD_LIGHT} !important; margin-bottom: 0.5rem; }}
    .welcome-box p {{ color: {TEXT_DIM}; font-size: 0.95rem; }}

    @media print {{
        * {{ -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }}
        section[data-testid="stSidebar"], header[data-testid="stHeader"],
        .stButton, [data-testid="stChatInput"], [data-testid="stFileUploader"] {{ display: none !important; }}
        .stApp {{ width:100% !important; max-width:100% !important; margin:0 !important; padding:0 !important; }}
        .stPlotlyChart, .stDataFrame {{ page-break-inside: avoid; }}
    }}
</style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "db_connection" not in st.session_state:
    st.session_state.db_connection = sqlite3.connect(":memory:", check_same_thread=False)
if "schema_info" not in st.session_state:
    st.session_state.schema_info = ""
if "current_df" not in st.session_state:
    st.session_state.current_df = None
if "last_file_id" not in st.session_state:
    st.session_state.last_file_id = None
if "data_profile" not in st.session_state:
    st.session_state.data_profile = None
if "ai_summary" not in st.session_state:
    st.session_state.ai_summary = None
if "smart_questions" not in st.session_state:
    st.session_state.smart_questions = []
if "api_keys" not in st.session_state:
    st.session_state.api_keys = [""]

with st.sidebar:
    st.title("InsightForge")

    st.subheader("API Keys")
    for i in range(len(st.session_state.api_keys)):
        cols = st.columns([5, 1])
        st.session_state.api_keys[i] = cols[0].text_input(
            f"Key {i + 1}",
            value=st.session_state.api_keys[i],
            type="password",
            label_visibility="collapsed",
            key=f"apikey_input_{i}",
        )
        if cols[1].button("✕", key=f"rm_key_{i}", help="Remove") and len(st.session_state.api_keys) > 1:
            st.session_state.api_keys.pop(i)
            st.rerun()

    if st.button("＋ Add Key", use_container_width=True):
        st.session_state.api_keys.append("")
        st.rerun()

    model_choice = "gemini-2.5-flash"
    st.divider()

    st.subheader("Upload Data here")
    uploaded_file = st.file_uploader("CSV file", type=["csv"])

    if uploaded_file is not None:
        if st.session_state.last_file_id != getattr(uploaded_file, "file_id", uploaded_file.name):
            header_bytes = uploaded_file.read(10)
            uploaded_file.seek(0)
            if header_bytes.startswith(b"bplist00"):
                st.error("This appears to be a web archive, not a CSV.")
                st.stop()

            try:
                df = pd.read_csv(uploaded_file, encoding="utf-8", low_memory=False)
            except Exception:
                try:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding="cp1252", low_memory=False)
                except Exception as e2:
                    st.error(f"Could not read CSV. Error: {e2}")
                    st.stop()

            if df.empty or len(df.columns) == 0:
                st.error("The file has no readable data.")
                st.stop()

            df.columns = [str(c).strip().replace(' ', '_').replace('.', '').replace('-', '_') for c in df.columns]

            try:
                table_name = "user_data"
                df.to_sql(table_name, st.session_state.db_connection, if_exists="replace", index=False)
                st.session_state.current_df = df
                st.session_state.last_file_id = getattr(uploaded_file, "file_id", uploaded_file.name)

                schema_df = pd.read_sql_query(f"PRAGMA table_info({table_name});", st.session_state.db_connection)
                schema_str = f"Table name: '{table_name}'\nColumns:\n"
                for _, row in schema_df.iterrows():
                    col_name, col_type = row['name'], row['type']
                    sample_str = ""
                    if col_type == "TEXT" or df[col_name].dtype == "object":
                        try:
                            uv = df[col_name].dropna().unique()
                            if len(uv) <= 7:
                                sample_str = f" [Unique: {', '.join(map(str, uv))}]"
                            else:
                                sample_str = f" [Examples: {', '.join(map(str, uv[:5]))}, ...]"
                        except Exception:
                            pass
                    schema_str += f"  - {col_name} ({col_type}){sample_str}\n"
                st.session_state.schema_info = schema_str

                profile = {
                    "rows": len(df),
                    "cols": len(df.columns),
                    "numeric": len(df.select_dtypes(include=[np.number]).columns),
                    "categorical": len(df.select_dtypes(include=["object"]).columns),
                    "missing_pct": round((df.isnull().sum().sum() / (df.shape[0] * df.shape[1])) * 100, 1),
                }
                completeness = 100 - profile["missing_pct"]
                dup_pct = max(0, 100 - (df.duplicated().sum() / max(len(df), 1)) * 100)
                profile["quality"] = round(completeness * 0.6 + dup_pct * 0.4, 1)
                st.session_state.data_profile = profile

                st.session_state.ai_summary = None
                st.session_state.smart_questions = []
                st.session_state.messages = []
            except Exception as sql_err:
                st.error(f"Database error: {sql_err}")
                st.stop()

        st.success(f"{len(st.session_state.current_df):,} rows × {len(st.session_state.current_df.columns)} cols")
        with st.expander("Preview"):
            st.dataframe(st.session_state.current_df.head())
    else:
        st.session_state.schema_info = ""
        st.session_state.current_df = None
        st.session_state.last_file_id = None
        st.session_state.data_profile = None
        st.session_state.ai_summary = None
        st.session_state.smart_questions = []
        st.info("Upload a CSV to begin.")

    if st.session_state.messages:
        st.divider()
        if st.button("🗑 Clear Chat"):
            st.session_state.messages = []
            st.rerun()


def call_gemini(prompt_text: str) -> str:
    keys = [k.strip() for k in st.session_state.api_keys if k.strip()]
    if not keys:
        raise Exception("No API key configured. Add at least one Gemini API key in the sidebar.")
    last_err = None
    for key in keys:
        try:
            client = genai.Client(api_key=key)
            return client.models.generate_content(model=model_choice, contents=prompt_text).text.strip()
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                last_err = e
                continue
            raise e
    raise Exception(f"All API keys exhausted (rate limit). Wait ~60s and retry. Last error: {last_err}")


def clean_code_block(text: str, lang: str = "") -> str:
    import re
    text = text.strip()
    # Strip opening fence with ANY language tag (```sql, ```sqlite, ```python, etc.)
    text = re.sub(r'^```[a-zA-Z]*\n?', '', text)
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def get_sql_query(user_query, schema_info, history_context):
    prompt = f"""You are an expert SQL Data Analyst for a BI platform.

Database schema (SQLite):
{schema_info}

Recent conversation:
{history_context}

User question: "{user_query}"

Rules:
1. Return ONLY a bare SQLite SELECT query — no markdown, no explanations.
2. If greeting (hi/hello), return EXACTLY: CONVERSATION: Hello! How can I help you analyze your data today?
3. ONLY error if the metric is completely missing. Ignore brand/company context words.
4. Map synonyms smartly (e.g. "revenue" -> "Sales"). NEVER invent columns.
5. NEVER include _ID columns unless user explicitly asks for IDs. Use descriptive columns instead.
6. For funnel stages (Impressions, Clicks, Leads, Conversions) you may UNION ALL to unpivot.
7. Handle follow-up questions by refining the previous query.
8. For anomalies/outliers, compare values to averages or use statistical approaches.
9. For summaries, aggregate key metrics.
"""
    try:
        sql = call_gemini(prompt)
        sql = clean_code_block(sql, "sql")
        if "Campaign_ID" in sql:
            sql = sql.replace("Campaign_ID", "Campaign_Type")
        if "User_ID" in sql:
            sql = sql.replace("User_ID", "Customer_Segment")
        return sql
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
            raise Exception("Rate limit exceeded. Please wait ~60s and retry.")
        raise e


def sanitize_chart_code(code: str) -> str:
    import re
    gc_match = re.search(r"gridcolor\s*=\s*['\"]([^'\"]+)['\"]", code)
    if gc_match:
        gc_val = gc_match.group(1)
        code = re.sub(r",?\s*gridcolor\s*=\s*['\"][^'\"]+['\"]\s*,?", "", code)
        code += f'\nif fig is not None:\n    fig.update_xaxes(gridcolor="{gc_val}", zeroline=False)\n    fig.update_yaxes(gridcolor="{gc_val}", zeroline=False)\n'
    return code


def get_chart_code(user_query, sql_query, result_head, columns):
    prompt = f"""You are an expert Data Visualizer using Plotly.

User asked: "{user_query}"
SQL run: "{sql_query}"
DataFrame `df` columns: {columns}
Sample:
{result_head}

Write Python 3 Plotly code to visualize this dataframe.
RULES:
1. `df` is already defined. Do NOT redefine it.
2. Assign final figure to `fig`.
3. Use template='plotly_dark'. Colors: '#10b981', '#34d399', '#f59e0b', '#fbbf24', '#3b82f6', '#ef4444', '#ec4899'. Set plot_bgcolor='rgba(0,0,0,0)' and paper_bgcolor='rgba(0,0,0,0)'.
4. For axis styling, call fig.update_xaxes(gridcolor='rgba(255,255,255,0.06)', color='#9ca3af') and fig.update_yaxes(gridcolor='rgba(255,255,255,0.06)', color='#9ca3af') AFTER creating the figure. For global font, use fig.update_layout(font=dict(family='DM Sans', color='#9ca3af')). CRITICAL: NEVER pass gridcolor as a direct argument to update_layout() — it is not a valid layout property and will crash.
5. Single row + single column: set fig=None, text_response=summary string.
6. Single row + two numeric columns: melt for bar chart or fig=None with text_response.
7. Single-row categorical: bar chart, not line.
8. If unchartable: fig=None, text_response=summary.
9. Response must be 100% pure Python. No English outside comments/strings.
10. 4-space indentation.
"""
    try:
        code = call_gemini(prompt)
        code = clean_code_block(code, "python")
        return sanitize_chart_code(code)
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
            raise Exception("Rate limit exceeded. Please wait ~60s and retry.")
        raise e


def get_ai_insight(user_query, sql_query, result_df):
    prompt = f"""You are a senior data analyst. User asked: "{user_query}"
SQL: {sql_query}
Result (first rows):
{result_df.head(5).to_string()}

Write 2-3 concise sentences analyzing what this data reveals. Mention specific numbers. No markdown."""
    try:
        return call_gemini(prompt)
    except Exception:
        return None


def generate_smart_questions(schema_info):
    prompt = f"""Given this schema:
{schema_info}

Generate exactly 4 smart analytical questions specific to these columns. Return ONLY a JSON array of 4 strings."""
    try:
        raw = clean_code_block(call_gemini(prompt), "json")
        questions = json.loads(raw)
        if isinstance(questions, list) and len(questions) >= 4:
            return questions[:4]
    except Exception:
        pass
    return []


def generate_ai_summary(schema_info, df):
    num_stats = ""
    for col in df.select_dtypes(include=[np.number]).columns[:5]:
        num_stats += f"  {col}: min={df[col].min()}, max={df[col].max()}, mean={df[col].mean():.2f}\n"
    cat_stats = ""
    for col in df.select_dtypes(include=["object"]).columns[:3]:
        cat_stats += f"  {col}: {df[col].value_counts().head(3).to_dict()}\n"

    prompt = f"""You are a senior BI analyst. Dataset:
Schema: {schema_info}
{len(df)} rows, {len(df.columns)} columns
Numeric: {num_stats}
Categories: {cat_stats}

Write a concise 3-4 sentence executive summary. Be specific with numbers. No markdown."""
    try:
        return call_gemini(prompt)
    except Exception:
        return None


st.title("InsightForge AI")
st.caption("Ask questions in plain English — get instant charts, SQL, and AI-powered insights.")

if st.session_state.current_df is not None and st.session_state.data_profile:
    prof = st.session_state.data_profile
    qs = prof["quality"]
    qc = "#10b981" if qs >= 90 else ("#f59e0b" if qs >= 70 else "#ef4444")
    st.markdown(f"""<div class="kpi-row">
        <div class="kpi"><div class="kpi-num">{prof['rows']:,}</div><div class="kpi-lbl">Records</div></div>
        <div class="kpi"><div class="kpi-num">{prof['cols']}</div><div class="kpi-lbl">Columns</div></div>
        <div class="kpi"><div class="kpi-num">{prof['numeric']}</div><div class="kpi-lbl">Numeric</div></div>
        <div class="kpi"><div class="kpi-num">{prof['categorical']}</div><div class="kpi-lbl">Categorical</div></div>
        <div class="kpi"><div class="kpi-num">{qs}%</div><div class="kpi-lbl">Quality</div>
            <div class="q-bar"><div class="q-fill" style="width:{qs}%;background:{qc};"></div></div></div>
    </div>""", unsafe_allow_html=True)

    if any(k.strip() for k in st.session_state.api_keys):
        if st.session_state.ai_summary is None:
            with st.spinner("Generating summary..."):
                st.session_state.ai_summary = generate_ai_summary(st.session_state.schema_info, st.session_state.current_df)
        if st.session_state.ai_summary:
            st.markdown(f"""<div class="note-card"><h4> Executive Summary</h4><p>{st.session_state.ai_summary}</p></div>""", unsafe_allow_html=True)

        if not st.session_state.smart_questions:
            with st.spinner("Generating suggestions..."):
                st.session_state.smart_questions = generate_smart_questions(st.session_state.schema_info)

    st.divider()

if st.session_state.current_df is None:
    st.markdown(f"""<div class="welcome-box">
        <h3>Welcome</h3>
        <p>Upload a CSV in the sidebar to start. Ask anything in natural language<br/>and get instant charts and AI insights.</p>
    </div>""", unsafe_allow_html=True)

for msg in st.session_state.messages:
    avatar = "👤" if msg["role"] == "user" else "⚡"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        if "chart" in msg and msg["chart"]:
            st.plotly_chart(msg["chart"], use_container_width=True)
        if "dataframe" in msg and msg["dataframe"] is not None:
            st.dataframe(msg["dataframe"].head(10))

if st.session_state.current_df is not None and not st.session_state.messages:
    if st.session_state.smart_questions:
        sq1, sq2 = st.columns(2)
        for i, q in enumerate(st.session_state.smart_questions[:4]):
            with (sq1 if i % 2 == 0 else sq2):
                if st.button(q, key=f"sq_{i}", use_container_width=True):
                    st.session_state.demo_prompt = q
                    st.rerun()
    else:
        qc1, qc2, qc3 = st.columns(3)
        with qc1:
            if st.button("📈 Top Performers", use_container_width=True):
                st.session_state.demo_prompt = "Show me the top 5 performers by the most important metric"
        with qc2:
            if st.button("📊 Overview", use_container_width=True):
                st.session_state.demo_prompt = "Give me a complete overview with key aggregated metrics"
        with qc3:
            if st.button("🔍 Anomalies", use_container_width=True):
                st.session_state.demo_prompt = "Find anomalies and outliers in the data"

chat_prompt = st.chat_input(" Ask anything about your data...")

if "demo_prompt" in st.session_state and st.session_state.get("demo_prompt"):
    prompt = st.session_state.demo_prompt
    st.session_state.demo_prompt = None
else:
    prompt = chat_prompt

if prompt:
    if not any(k.strip() for k in st.session_state.api_keys):
        st.error("Add at least one Gemini API Key in the sidebar.")
        st.stop()
    if not st.session_state.schema_info:
        st.warning("Upload a CSV to begin.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="⚡"):
        with st.status("Analyzing...", expanded=True) as status:
            try:
                history_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-5:-1]])

                status.update(label="Generating SQL...", state="running")
                sql = get_sql_query(prompt, st.session_state.schema_info, history_text)

                if sql.startswith("ERROR:"):
                    status.update(label="Done", state="complete")
                    st.info(sql.replace("ERROR:", "").strip())
                    st.session_state.messages.append({"role": "assistant", "content": sql.replace("ERROR:", "").strip()})
                    st.stop()

                if sql.startswith("CONVERSATION:"):
                    msg_text = sql.replace("CONVERSATION:", "").replace("```", "").strip()
                    status.update(label="Done", state="complete")
                    st.markdown(msg_text)
                    st.session_state.messages.append({"role": "assistant", "content": msg_text})
                    st.stop()

                with st.expander("SQL Query"):
                    st.code(sql, language="sql")

                status.update(label="Querying...", state="running")
                result_df = pd.read_sql_query(sql, st.session_state.db_connection)

                if result_df.empty:
                    status.update(label="Done", state="complete")
                    st.info("No results found.")
                    st.session_state.messages.append({"role": "assistant", "content": "No results found."})
                    st.stop()

                status.update(label="Visualizing...", state="running")
                try:
                    chart_code = get_chart_code(prompt, sql, result_df.head(3).to_string(), list(result_df.columns))
                except Exception as chart_err:
                    st.warning(f"Chart skipped: {chart_err}")
                    st.dataframe(result_df.head(10))
                    st.session_state.messages.append({"role": "assistant", "content": "Here is the data:", "dataframe": result_df})
                    status.update(label="Done", state="complete")
                    st.stop()

                status.update(label="Rendering...", state="running")
                # Convert numpy scalar types → native Python so Plotly bar/scatter don't reject them
                chart_df = result_df.copy()
                for _col in chart_df.select_dtypes(include=[np.number]).columns:
                    chart_df[_col] = chart_df[_col].astype(float)
                local_vars = {"df": chart_df, "px": px, "go": go, "pd": pd, "np": np, "fig": None, "text_response": None}
                exec_globals = {"__builtins__": __builtins__, "px": px, "go": go, "pd": pd, "np": np, "df": chart_df}

                try:
                    exec(chart_code, exec_globals, local_vars)
                    fig = local_vars.get("fig")
                    text_res = local_vars.get("text_response")

                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    if text_res:
                        st.markdown(text_res)
                    if not fig and not text_res:
                        st.dataframe(result_df.head(10))

                    insight = get_ai_insight(prompt, sql, result_df)
                    if insight:
                        st.markdown(f'<div class="note-card"><h4>💡 Insight</h4><p>{insight}</p></div>', unsafe_allow_html=True)

                    with st.expander("Raw Data"):
                        st.dataframe(result_df)
                        csv_buf = io.StringIO()
                        result_df.to_csv(csv_buf, index=False)
                        st.download_button("📥 Download CSV", csv_buf.getvalue(), "result.csv", "text/csv")

                    content = text_res or insight or "Here is the result."
                    msg_data = {"role": "assistant", "content": content}
                    if fig:
                        msg_data["chart"] = fig
                    msg_data["dataframe"] = result_df
                    st.session_state.messages.append(msg_data)
                    status.update(label="Done", state="complete")

                except Exception as e:
                    st.error(f"Chart error: {e}")
                    with st.expander("Debug"):
                        st.code(chart_code)
                    st.dataframe(result_df.head(10))
                    st.session_state.messages.append({"role": "assistant", "content": "Chart failed. Showing raw data.", "dataframe": result_df})
                    status.update(label="Error", state="error")

            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    error_msg = "Rate limit exceeded. Wait ~60s and retry."
                status.update(label="Error", state="error")
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})