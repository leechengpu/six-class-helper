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

    manual_ask = st.button("🔍 諮詢採購法顧問", type="primary", key="proc_btn")

    # 顯示答案:1-click 示範 or 手動詢問,任一觸發即顯示
    auto_case = st.session_state.pop("proc_auto_show", None)
    if auto_case or manual_ask:
        if manual_ask and not q.strip():
            st.warning("請先輸入問題或點選上方 1-click 示範")
        else:
            with st.spinner("查詢中..."):
                if API_MODE == "live" and manual_ask:
                    ctx = f"本校 context:{school_name} / 校長 {principal}"
                    ans = call_claude(load_prompt("procurement_qa.md"), q, ctx)
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
                else:
                    demo = load_demo("meeting_demo.md")
                    if "**預期輸出**" in demo:
                        part = demo.split("**預期輸出**:")[1]
                    else:
                        part = demo
                    st.markdown(part)
                    st.info("💡 Demo 模式顯示預錄摘要。設定 `ANTHROPIC_API_KEY` 後可分析任何逐字稿。")


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
