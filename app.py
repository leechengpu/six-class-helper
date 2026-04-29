import os
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

BASE = Path(__file__).parent
DB_PATH = BASE / "data" / "school.db"
PROMPTS = BASE / "prompts"
DEMOS = BASE / "tests" / "demo_cases"

PRIMARY = "#1B4F72"
ACCENT = "#E86C00"
SUCCESS = "#27AE60"
WARN = "#C0392B"
BG_SOFT = "#F4F6F8"

st.set_page_config(
    page_title="總務小幫手 · 六班小校 AI 助理套件",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    f"""
<style>
.block-container {{ padding-top: 2rem; padding-bottom: 3rem; max-width: 1200px; }}
[data-testid="stHeader"] {{ background: transparent; }}
h1, h2, h3 {{ color: {PRIMARY}; }}

.hero {{
    background: linear-gradient(135deg, {PRIMARY} 0%, #2874A6 100%);
    color: white;
    padding: 2.2rem 2rem;
    border-radius: 12px;
    margin-bottom: 1.2rem;
    box-shadow: 0 4px 14px rgba(27,79,114,0.2);
}}
.hero h1 {{ color: white; font-size: 2.2rem; margin: 0 0 0.4rem 0; font-weight: 800; }}
.hero p {{ color: #EAF2F8; margin: 0; font-size: 1.05rem; }}
.hero .brand {{
    display: inline-block;
    background: {ACCENT};
    color: white;
    padding: 0.2rem 0.8rem;
    border-radius: 999px;
    font-size: 0.8rem;
    margin-bottom: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.05em;
}}

.module-card {{
    background: white;
    border-left: 5px solid {PRIMARY};
    padding: 1rem 1.2rem;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    margin-bottom: 0.8rem;
}}
.module-card.a {{ border-left-color: {PRIMARY}; }}
.module-card.b {{ border-left-color: {ACCENT}; }}
.module-card.c {{ border-left-color: {SUCCESS}; }}
.module-title {{ font-weight: 800; font-size: 1.05rem; color: {PRIMARY}; margin-bottom: 0.2rem; }}
.module-desc {{ font-size: 0.85rem; color: #666; }}

.pain-box {{
    background: #FFF8E7;
    border-left: 5px solid {ACCENT};
    padding: 1.2rem 1.6rem;
    border-radius: 8px;
    margin: 1rem 0 1.5rem 0;
}}
.pain-box .quote {{ font-size: 1.15rem; color: #444; font-weight: 600; line-height: 1.6; }}
.pain-box .sub {{ font-size: 0.88rem; color: #888; margin-top: 0.3rem; }}

.mode-badge {{
    display: inline-block;
    padding: 0.15rem 0.6rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 700;
    margin-left: 0.5rem;
}}
.mode-live {{ background: {SUCCESS}; color: white; }}
.mode-demo {{ background: {WARN}; color: white; }}

section[data-testid="stSidebar"] {{ background: {BG_SOFT}; }}
.stTabs [data-baseweb="tab-list"] {{ gap: 4px; }}
.stTabs [data-baseweb="tab"] {{
    background: {BG_SOFT};
    padding: 0.6rem 1.4rem;
    border-radius: 8px 8px 0 0;
    font-weight: 600;
    font-size: 1rem;
}}
.stTabs [aria-selected="true"] {{
    background: {PRIMARY} !important;
    color: white !important;
}}
</style>
""",
    unsafe_allow_html=True,
)


SCHEMA_SQL = BASE / "schemas" / "create_tables.sql"
SEED_SQL = BASE / "tests" / "demo_data.sql"


def ensure_db():
    """首次啟動自建 DB（供 Streamlit Community Cloud 使用，雲端檔案系統是短暫的）。"""
    if DB_PATH.exists():
        return
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    try:
        if SCHEMA_SQL.exists():
            conn.executescript(SCHEMA_SQL.read_text(encoding="utf-8"))
        if SEED_SQL.exists():
            conn.executescript(SEED_SQL.read_text(encoding="utf-8"))
        conn.commit()
    finally:
        conn.close()


@st.cache_resource
def get_conn():
    ensure_db()
    return sqlite3.connect(str(DB_PATH), check_same_thread=False)


@st.cache_data
def load_meta():
    return pd.read_sql_query("SELECT * FROM school_meta", get_conn())


def meta_value(df, name, default="—"):
    row = df[df["field_name"] == name]
    return row["field_value"].iloc[0] if not row.empty else default


def load_prompt(name: str) -> str:
    p = PROMPTS / name
    return p.read_text(encoding="utf-8") if p.exists() else ""


def load_demo(name: str) -> str:
    p = DEMOS / name
    return p.read_text(encoding="utf-8") if p.exists() else "(demo 檔案不存在)"


def get_api_mode():
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if key:
        return "live"
    try:
        key = st.secrets.get("ANTHROPIC_API_KEY", "")
        if key:
            os.environ["ANTHROPIC_API_KEY"] = key
            return "live"
    except Exception:
        pass
    return "demo"


def call_claude(system_prompt: str, user_prompt: str, context: str = "") -> str:
    try:
        import anthropic
    except ImportError:
        return "⚠️ 未安裝 anthropic SDK,請執行 `pip install anthropic`"

    client = anthropic.Anthropic()
    full_user = f"{context}\n\n---\n\n{user_prompt}" if context else user_prompt
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2048,
        system=system_prompt,
        messages=[{"role": "user", "content": full_user}],
    )
    return msg.content[0].text


# ============================================================
# 🧪 進階模式：Claude Agent SDK + Tool Use
# - 本機限定（需安裝 Claude Code CLI: `npm i -g @anthropic-ai/claude-code`）
# - Streamlit Cloud 不支援，UI 端會自動隱藏切換鈕
# ============================================================

def _agent_sdk_available() -> bool:
    """檢查 Agent SDK + claude CLI 都可用。"""
    import shutil
    if not shutil.which("claude"):
        return False
    try:
        import claude_agent_sdk  # noqa: F401
        return True
    except ImportError:
        return False


def _extract_assistant_text(msg) -> str:
    """從 Agent SDK 串流訊息抽出最終 assistant 文字（跳過 tool use blocks）。"""
    if type(msg).__name__ != "AssistantMessage":
        return ""
    parts = []
    for block in getattr(msg, "content", []):
        if type(block).__name__ == "TextBlock":
            parts.append(getattr(block, "text", ""))
    return "\n".join(parts)


async def _agentic_procurement_query(system_prompt: str, user_prompt: str, context: str) -> str:
    """模組 A 進階：採購法 RAG agent。"""
    from claude_agent_sdk import (
        query,
        tool,
        create_sdk_mcp_server,
        ClaudeAgentOptions,
    )

    @tool(
        "search_procurement_law",
        "從政府採購法彙編（35 版 684 頁，含本文/施行細則/子法/GPA/相關法令）查詢條文。"
        "傳入關鍵字（條號如「第 22 條」、術語如「公告金額」「綁標」「最有利標」），"
        "回傳前 8 筆命中的上下文（含檔名、行號、前後 2 行）。",
        {"keyword": str},
    )
    async def search_law(args):
        keyword = args["keyword"]
        law_dir = BASE / "data" / "procurement_law"
        if not law_dir.exists():
            return {"content": [{"type": "text", "text": "❌ 法規資料夾不存在"}]}
        hits = []
        for md_file in sorted(law_dir.glob("*.md")):
            try:
                text = md_file.read_text(encoding="utf-8")
            except Exception:
                continue
            lines = text.split("\n")
            for i, line in enumerate(lines):
                if keyword in line:
                    start = max(0, i - 2)
                    end = min(len(lines), i + 3)
                    ctx = "\n".join(lines[start:end])
                    hits.append(f"📄 {md_file.name}:{i+1}\n{ctx}")
                    if len(hits) >= 8:
                        break
            if len(hits) >= 8:
                break
        if not hits:
            return {"content": [{"type": "text", "text": f"未找到包含「{keyword}」的條文。"}]}
        return {"content": [{"type": "text", "text": "\n\n---\n\n".join(hits)}]}

    server = create_sdk_mcp_server(name="procurement-law", version="1.0.0", tools=[search_law])
    full_user = f"{context}\n\n---\n\n{user_prompt}" if context else user_prompt
    augmented_sys = (
        system_prompt
        + "\n\n## 🚨 進階模式紀律\n"
        + "你**必須**先呼叫 search_procurement_law 工具查詢真實條文，再回答。"
        + "禁止僅憑記憶引用條號。每個引用條文都要附查詢來源（檔名）。"
    )
    options = ClaudeAgentOptions(
        system_prompt=augmented_sys,
        mcp_servers={"law": server},
        allowed_tools=["mcp__law__search_procurement_law"],
        disallowed_tools=[
            "Read", "Write", "Edit", "Bash",
            "Glob", "Grep", "WebSearch", "WebFetch",
        ],
        setting_sources=[],
        model="claude-sonnet-4-5",
        max_turns=8,
    )
    chunks = []
    async for msg in query(prompt=full_user, options=options):
        text = _extract_assistant_text(msg)
        if text:
            chunks.append(text)
    return "\n\n".join(chunks) if chunks else "（無回應）"


def call_claude_agentic_procurement(system_prompt: str, user_prompt: str, context: str = "") -> str:
    import anyio
    from claude_agent_sdk import (
        CLINotFoundError, CLIConnectionError, ProcessError, CLIJSONDecodeError,
    )
    try:
        return anyio.run(_agentic_procurement_query, system_prompt, user_prompt, context)
    except CLINotFoundError:
        raise RuntimeError("找不到 Claude Code CLI，請執行：npm i -g @anthropic-ai/claude-code")
    except ProcessError as e:
        raise RuntimeError(f"Claude CLI 執行失敗（exit {e.exit_code}）")
    except CLIJSONDecodeError as e:
        raise RuntimeError(f"Claude CLI 回應解析錯誤：{e}")
    except CLIConnectionError as e:
        raise RuntimeError(f"Claude CLI 連線錯誤：{e}")


async def _agentic_meeting_to_calendar(transcript: str) -> str:
    """模組 C 進階：把會議決議寫入 macOS 行事曆。"""
    import subprocess
    from datetime import datetime
    from claude_agent_sdk import (
        query,
        tool,
        create_sdk_mcp_server,
        ClaudeAgentOptions,
    )

    @tool(
        "add_to_calendar",
        "把單一決議事項或待辦寫入 macOS 行事曆。datetime 格式必須為 YYYY-MM-DD HH:MM。",
        {"title": str, "datetime": str, "notes": str},
    )
    async def add_to_calendar(args):
        try:
            dt = datetime.strptime(args["datetime"], "%Y-%m-%d %H:%M")
        except ValueError:
            return {"content": [{"type": "text", "text": f"❌ 日期格式錯誤：{args['datetime']}"}]}
        title = args["title"].replace('"', "'").replace("\\", "")
        notes = args["notes"].replace('"', "'").replace("\\", "")
        script = f'''tell application "Calendar"
    set theDate to current date
    set year of theDate to {dt.year}
    set month of theDate to {dt.month}
    set day of theDate to {dt.day}
    set hours of theDate to {dt.hour}
    set minutes of theDate to {dt.minute}
    set seconds of theDate to 0
    set endDate to theDate + 60 * 60
    tell calendar 1
        make new event with properties {{summary:"{title}", start date:theDate, end date:endDate, description:"{notes}"}}
    end tell
end tell'''
        try:
            subprocess.run(
                ["osascript", "-e", script],
                check=True, capture_output=True, timeout=15, text=True,
            )
            return {"content": [{"type": "text", "text": f"✅ 已加入：{title} @ {args['datetime']}"}]}
        except subprocess.CalledProcessError as e:
            return {"content": [{"type": "text", "text": f"❌ 加入失敗：{e.stderr or str(e)}"}]}
        except subprocess.TimeoutExpired:
            return {"content": [{"type": "text", "text": "❌ Calendar 沒回應（可能權限未授予）"}]}

    server = create_sdk_mcp_server(name="cal", version="1.0.0", tools=[add_to_calendar])
    today = datetime.now().strftime("%Y-%m-%d")
    sys_prompt = f"""你是會議決議分派助理。從逐字稿萃取「決議事項」與「待辦」並逐一呼叫 add_to_calendar。

今天日期：{today}

規則：
- 有明確日期 → 用該日期
- 「下週 X」「月底」→ 合理推算
- 沒提時間 → 用相關日期 14:00
- 純粹「報告」「分享」「討論」沒有要做的事 → 不要加
- title 簡短（< 30 字），notes 寫負責人 + 完整脈絡

完成所有 add_to_calendar 呼叫後，總結：
- 共寫入 N 筆
- 條列每筆：標題 + 時間 + 負責人
- 列出「未寫入但值得追蹤」的事項（如果有）
"""
    options = ClaudeAgentOptions(
        system_prompt=sys_prompt,
        mcp_servers={"cal": server},
        allowed_tools=["mcp__cal__add_to_calendar"],
        disallowed_tools=[
            "Read", "Write", "Edit", "Bash",
            "Glob", "Grep", "WebSearch", "WebFetch",
        ],
        setting_sources=[],
        model="claude-sonnet-4-5",
        max_turns=20,
    )
    chunks = []
    async for msg in query(prompt=f"逐字稿：\n\n{transcript}", options=options):
        text = _extract_assistant_text(msg)
        if text:
            chunks.append(text)
    return "\n\n".join(chunks) if chunks else "（無回應）"


def call_claude_agentic_meeting_to_calendar(transcript: str) -> str:
    import anyio
    from claude_agent_sdk import (
        CLINotFoundError, CLIConnectionError, ProcessError, CLIJSONDecodeError,
    )
    try:
        return anyio.run(_agentic_meeting_to_calendar, transcript)
    except CLINotFoundError:
        raise RuntimeError("找不到 Claude Code CLI，請執行：npm i -g @anthropic-ai/claude-code")
    except ProcessError as e:
        raise RuntimeError(f"Claude CLI 執行失敗（exit {e.exit_code}）")
    except CLIJSONDecodeError as e:
        raise RuntimeError(f"Claude CLI 回應解析錯誤：{e}")
    except CLIConnectionError as e:
        raise RuntimeError(f"Claude CLI 連線錯誤：{e}")


ensure_db()
meta_df = load_meta()
school_name = meta_value(meta_df, "school_name", "示範國小")
principal = meta_value(meta_df, "principal_name", "—")
school_addr = meta_value(meta_df, "address", "—")
school_phone = meta_value(meta_df, "phone", "—")

API_MODE = get_api_mode()

with st.sidebar:
    st.markdown(f"### 🏫 {school_name}")
    st.caption(f"校長:{principal}")
    st.caption(f"地址:{school_addr}")
    st.caption(f"電話:{school_phone}")
    st.divider()
    st.markdown("**系統狀態**")
    if API_MODE == "live":
        st.success("🟢 Live 模式(接 Claude API)")
    else:
        st.warning("🟡 Demo 模式(離線範例)")
        st.caption("設定 `ANTHROPIC_API_KEY` 環境變數以啟用真實 AI")
    if _agent_sdk_available():
        st.info("🔬 Agent SDK 已就緒\n（採購法 RAG / 行事曆寫入）")
    st.divider()
    st.markdown("**本校 context**")
    st.caption("所有模組會自動帶入上述基本資料作為 prompt context")

st.markdown(
    f"""
<div class="hero">
    <div class="brand">總務小幫手 · 六班小校 AI 助理套件</div>
    <h1>總務主任不再孤軍奮戰。</h1>
    <p>採購有顧問、公文有草稿、會議有記錄 — {school_name}</p>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="pain-box">
    <div class="quote">📌 六班小校,總務主任一人兼「<b>採購 + 公文 + 總務 + 財產 + 工程</b>」,每件事都是第一次做。</div>
    <div class="sub">AI 做雜事、人做有溫度的事 — 把重複的腦力勞動接走,讓總務主任有時間去議價、溝通、解決真正的問題。</div>
</div>
""",
    unsafe_allow_html=True,
)

tab_home, tab_a, tab_b, tab_c, tab_d = st.tabs(
    ["🏠 首頁", "📋 採購法顧問", "📝 公文草稿", "🎙️ 會議記錄", "🏫 本校資料"]
)

# ===== 首頁:三模組總覽 =====
with tab_home:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            """
<div class="module-card a">
<div class="module-title">📋 A. 採購法顧問</div>
<div class="module-desc">彙編 35 版 684 頁法條、風險警示、簽呈檢查</div>
</div>
""",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """
<div class="module-card b">
<div class="module-title">📝 B. 公文草稿</div>
<div class="module-desc">三段式格式自動產出,可匯 docx,15 分鐘變 30 秒</div>
</div>
""",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            """
<div class="module-card c">
<div class="module-title">🎙️ C. 會議記錄</div>
<div class="module-desc">逐字稿 30 秒 → 摘要 + 決議 + 待辦,每月省 3 小時、記錄者回歸討論</div>
</div>
""",
            unsafe_allow_html=True,
        )

    st.markdown("")
    st.info(
        "💡 **一表通精神**：本校資料只填一次（見「🏫 本校資料」tab），"
        "三模組會自動帶入為 prompt context。點擊上方任一模組 tab 開始使用。"
    )

# ===== 模組 A:採購法顧問 =====
with tab_a:
    st.subheader("採購法顧問")
    st.caption("問情境、查條文、檢查簽呈、風險警示 — 資深總務主任 + 採購法專業人員")

    st.markdown("**⚡ 1-click 示範**（點下去直接看 AI 分析）")
    ex_col1, ex_col2 = st.columns(2)
    with ex_col1:
        if st.button("⚡ 45 萬平板採購簽呈審查", use_container_width=True, key="proc_demo_1"):
            st.session_state["proc_q"] = "總務主任想採購 30 台平板給五六年級,總金額 45 萬,請問要走什麼程序?有什麼要注意?"
            st.session_state["proc_auto_show"] = "tablet"
    with ex_col2:
        if st.button("⚡ 邀 3 家只回 1 家能議價嗎", use_container_width=True, key="proc_demo_2"):
            st.session_state["proc_q"] = "公告金額以下採購,我邀請了 3 家廠商報價,結果只有 1 家回覆,可以直接跟他議價嗎?"
            st.session_state["proc_auto_show"] = "vendor"

    q = st.text_area(
        "或自行描述您的採購情境或問題",
        value=st.session_state.get("proc_q", ""),
        height=120,
        key="proc_input",
    )

    # 進階：RAG 模式 toggle（本機限定）
    proc_agent_mode = False
    if _agent_sdk_available():
        proc_agent_mode = st.checkbox(
            "🔬 RAG 模式：強制查詢真實採購法條文（避免幻覺，較慢）",
            value=False,
            key="proc_agent_mode",
            help="啟用 Claude Agent SDK + 採購法彙編 RAG。回答前必呼叫 search_procurement_law 工具。本機限定（需 claude CLI）。",
        )

    manual_ask = st.button("🔍 諮詢採購法顧問", type="primary", key="proc_btn")

    # 顯示答案:1-click 示範 or 手動詢問,任一觸發即顯示
    auto_case = st.session_state.pop("proc_auto_show", None)
    if auto_case or manual_ask:
        if manual_ask and not q.strip():
            st.warning("請先輸入問題或點選上方 1-click 示範")
        else:
            spinner_msg = "查詢真實條文中..." if proc_agent_mode else "查詢中..."
            with st.spinner(spinner_msg):
                if API_MODE == "live" and manual_ask:
                    ctx = f"本校 context:{school_name} / 校長 {principal}"
                    ans = ""
                    if proc_agent_mode:
                        try:
                            ans = call_claude_agentic_procurement(load_prompt("procurement_qa.md"), q, ctx)
                            st.success("🔬 RAG 模式：已查詢採購法彙編（35 版 684 頁）")
                        except RuntimeError as e:
                            st.error(f"❌ 進階模式失敗：{e}")
                    else:
                        ans = call_claude(load_prompt("procurement_qa.md"), q, ctx)
                    if ans:
                        st.markdown(ans)
                else:
                    demo = load_demo("procurement_demo.md")
                    # 判斷情境:auto_case 優先,否則從文字推
                    case = auto_case
                    if not case:
                        if "45 萬" in q or "平板" in q:
                            case = "tablet"
                        elif "3 家" in q or "議價" in q:
                            case = "vendor"
                    if case == "tablet":
                        part = demo.split("## 案例 2")[0].replace("## 案例 1:45 萬平板採購簽呈審查", "").strip()
                    elif case == "vendor":
                        part = demo.split("## 案例 2")[1] if "## 案例 2" in demo else demo
                    else:
                        part = demo
                    st.markdown(part)
                    st.info("💡 這是 demo 模式的預錄回答。設定 `ANTHROPIC_API_KEY` 後可問任何採購問題。")


# ===== 模組 B:公文草稿 =====
with tab_b:
    st.subheader("公文草稿生成")
    st.caption("輸入事由、對象、關鍵事實 → 30 秒生成三段式公文草稿")

    col_l, col_r = st.columns(2)
    with col_l:
        doc_subject = st.text_input("事由", key="doc_subject", placeholder="例:申請操場 PU 跑道整修補助")
        doc_target = st.text_input("受文者", key="doc_target", placeholder="例:花蓮縣政府教育處")
    with col_r:
        doc_type = st.selectbox("公文類型", ["申請/陳請", "邀請/函請", "通知/公告", "回覆"], key="doc_type")
        doc_tone = st.selectbox("對象層級", ["對上級(縣府/教育部)", "對平行(他校/廠商)", "對下級(家長/社區)"], key="doc_tone")

    doc_facts = st.text_area(
        "關鍵事實(3-5 點)",
        key="doc_facts",
        height=100,
        placeholder="例:\n- 現有跑道使用 15 年、多處破損\n- 影響學生運動安全\n- 估價 180 萬",
    )

    st.markdown("**⚡ 1-click 示範**（點下去直接看 30 秒生成的公文草稿）")
    ex1, ex2 = st.columns(2)
    with ex1:
        if st.button("⚡ 申請操場跑道整修補助", use_container_width=True, key="doc_demo_1"):
            st.session_state["demo_show"] = "track"
            st.session_state["doc_auto_show"] = True
    with ex2:
        if st.button("⚡ 邀廠商到校進行設備簡報", use_container_width=True, key="doc_demo_2"):
            st.session_state["demo_show"] = "vendor"
            st.session_state["doc_auto_show"] = True

    manual_gen = st.button("✍️ 生成公文草稿", type="primary", key="doc_btn")

    auto_trigger = st.session_state.pop("doc_auto_show", False)
    if (manual_gen or auto_trigger):
        if API_MODE == "live" and manual_gen and not auto_trigger:
            with st.spinner("撰寫中..."):
                user_prompt = f"""事由:{doc_subject}
受文者:{doc_target}
類型:{doc_type}
對象層級:{doc_tone}
關鍵事實:
{doc_facts}

請依三段式產出公文草稿。"""
                ctx = f"本校 context:學校名稱 {school_name}、地址 {school_addr}、電話 {school_phone}、校長 {principal}"
                ans = call_claude(load_prompt("official_doc.md"), user_prompt, ctx)
                st.markdown(ans)
        else:
            demo = load_demo("official_doc_demo.md")
            which = st.session_state.get("demo_show", "track")
            if which == "track":
                part = demo.split("## 案例 2")[0]
            else:
                part = "## 案例 2" + demo.split("## 案例 2")[1] if "## 案例 2" in demo else demo
            st.markdown(part)
            st.info("💡 Demo 模式顯示預錄範例。設定 `ANTHROPIC_API_KEY` 後可即時生成任何公文。")


# ===== 模組 C:會議記錄 =====
with tab_c:
    st.subheader("會議記錄自動化")
    st.caption("逐字稿貼上 → 重點摘要 + 決議事項 + 待辦清單")

    st.markdown("**Step 1:提供逐字稿**")
    meet_source = st.radio(
        "來源",
        ["直接貼逐字稿", "上傳錄音檔(未來功能)"],
        horizontal=True,
        key="meet_source",
    )

    transcript = ""
    if meet_source == "直接貼逐字稿":
        if st.button("⚡ 1-click 示範:行政會議逐字稿 → 結構化記錄", key="load_demo_meet"):
            demo = load_demo("meeting_demo.md")
            if "```" in demo:
                st.session_state["transcript"] = demo.split("```")[1].strip()
            st.session_state["meet_auto_show"] = True
        transcript = st.text_area(
            "逐字稿（或貼上你自己的）",
            value=st.session_state.get("transcript", ""),
            height=200,
            key="transcript_input",
        )
    else:
        st.info("🎤 錄音檔自動轉錄功能:Phase 0.5 W4 開發(mlx-whisper + Claude 摘要)")

    meet_type = st.selectbox(
        "會議類型",
        ["行政會議", "校務會議", "導師會議", "個案會議", "其他"],
        key="meet_type",
    )

    manual_gen_meet = st.button("📝 生成會議記錄", type="primary", key="meet_btn")
    auto_trigger_meet = st.session_state.pop("meet_auto_show", False)

    if manual_gen_meet or auto_trigger_meet:
        if manual_gen_meet and not transcript.strip() and not auto_trigger_meet and meet_source == "直接貼逐字稿":
            st.warning("請先貼上逐字稿或點選上方 1-click 示範")
        else:
            with st.spinner("分析中..."):
                if API_MODE == "live" and transcript.strip() and not auto_trigger_meet:
                    user_prompt = f"會議類型:{meet_type}\n\n逐字稿:\n{transcript}"
                    ans = call_claude(load_prompt("meeting_summary.md"), user_prompt)
                    st.markdown(ans)
                    # 記住逐字稿讓「寫入行事曆」按鈕可用
                    st.session_state["meet_last_transcript"] = transcript
                else:
                    demo = load_demo("meeting_demo.md")
                    if "**預期輸出**" in demo:
                        part = demo.split("**預期輸出**:")[1]
                    else:
                        part = demo
                    st.markdown(part)
                    st.info("💡 Demo 模式顯示預錄摘要。設定 `ANTHROPIC_API_KEY` 後可分析任何逐字稿。")

    # 進階：把決議寫進 macOS 行事曆（本機限定）
    last_t = st.session_state.get("meet_last_transcript", "")
    if _agent_sdk_available() and last_t and API_MODE == "live":
        st.divider()
        st.markdown("**🧪 進階：Agent 自動派工**")
        st.caption("讓 Claude Agent 從逐字稿萃取決議事項 → 逐筆呼叫 macOS 行事曆寫入（首次需授予權限）")
        if st.button("📅 把決議寫進 macOS 行事曆", key="meet_to_cal_btn"):
            with st.spinner("Agent 分析決議並寫入行事曆中..."):
                try:
                    result = call_claude_agentic_meeting_to_calendar(last_t)
                    st.success("完成")
                    st.markdown(result)
                except Exception as e:
                    st.error(f"Agent 執行失敗：{e}")


# ===== 模組 D:本校資料 =====
with tab_d:
    st.subheader("本校基本資料主檔")
    st.caption("所有模組會自動讀取本校資料作為 prompt context — 一次維護,處處套用")
    if meta_df.empty:
        st.info("尚無資料")
    else:
        for category in meta_df["category"].unique():
            with st.expander(f"📁 {category}", expanded=True):
                sub = meta_df[meta_df["category"] == category][
                    ["field_name", "field_value", "last_updated"]
                ].rename(columns={"field_name": "欄位", "field_value": "值", "last_updated": "更新日期"})
                st.dataframe(sub, use_container_width=True, hide_index=True)


st.divider()
st.markdown(
    f"""
<div style="text-align:center; color:#888; font-size:0.85rem; padding: 1rem 0;">
    總務小幫手 · 六班小校 AI 助理套件 · Phase 0.5<br>
    模組:採購法顧問 / 公文草稿 / 會議記錄 · AI 做雜事,人做有溫度的事
</div>
""",
    unsafe_allow_html=True,
)
