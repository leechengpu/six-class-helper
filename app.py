import streamlit as st

from agents import (
    _agent_sdk_available,
    call_claude_agentic_meeting_to_calendar,
    call_claude_agentic_procurement,
)
from claude_client import call_claude, get_api_mode
from db import ensure_db, load_meta, meta_value
from events import (
    MODULE_LABELS,
    get_daily_counts,
    get_event_counts,
    get_total_minutes_saved,
    log_event,
)
from prompts import load_demo, load_prompt
from validators import (
    InputValidationError,
    MEDIUM_MAX_CHARS,
    SHORT_MAX_CHARS,
    validate_user_input,
)

PRIMARY = "#1B4F72"
ACCENT = "#E86C00"
SUCCESS = "#27AE60"
WARN = "#C0392B"
BG_SOFT = "#F4F6F8"

st.set_page_config(
    page_title="校長 AI 副手系統 · 行政減負平台",
    page_icon="🎩",
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
    <div class="brand">校長 AI 副手系統 · 行政減負平台</div>
    <h1>校長不孤單。13 條管考線，13 個 AI 副手分擔。</h1>
    <p>從教師到校長,AI 陪我走每一步 — {school_name} {principal}</p>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="pain-box">
    <div class="quote">📌 校長一人面對 13 條管考線（採購、公文、校事、輔導、特教、課程、研習、校外、防災、經費、人事、計畫、媒體）— 每條都要 sign-off,但每條都不可能精通。</div>
    <div class="sub">AI 副手分擔每條線,校長只看「<b>需要我裁示的</b>」+「<b>有風險的</b>」+「<b>跨處室卡住的</b>」。把人留給有溫度的事。</div>
</div>
""",
    unsafe_allow_html=True,
)

tab_home, tab_arch, tab_a, tab_b, tab_c, tab_d, tab_stats = st.tabs(
    ["📊 校長儀表板", "🏛️ 系統架構", "📋 採購法顧問", "📝 公文草稿", "🎙️ 會議記錄", "🏫 本校資料", "📈 使用統計"]
)

# ===== 校長儀表板（首頁）=====
with tab_home:
    st.subheader(f"🎩 校長視角 · {school_name}")
    st.caption("只看：需要我裁示的 + 有風險的 + 跨處室卡住的")

    # 4 metric cards (mock 數據,demo 用)
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("📍 今日待我核決", "5 件", "↑ 比昨日 +2")
    with m2:
        st.metric("🚨 高風險案件", "2 件", "S03-001 / S01-003")
    with m3:
        st.metric("✅ 主任已處理", "18 件", "↑ 比上週 +6")
    with m4:
        st.metric("📅 本週新進案件", "23 件", "S02 公文 14 / S03 採購 5 / 其他 4")

    st.markdown("---")

    # 13 子系統 traffic light (校長一目掌全校)
    st.markdown("### 🚦 13 子系統 · 全校溫度計")
    st.caption("綠 = 正常 / 黃 = 接近時效 / 紅 = 需校長介入")

    sub_l, sub_m, sub_r = st.columns(3)
    with sub_l:
        st.markdown("**📘 教導處**")
        st.markdown(
            """
- 🟢 S01 校事會議 *(2 結案中)*
- 🟡 S02 公文管考 *(3 件 ≤ 2 日到期)*
- 🟢 S04 學生輔導 *(平穩)*
- 🟢 S05 特教 IEP *(下次會議 5/15)*
- 🟢 S06 課程計畫 *(送審中)*
- 🟡 S07 研習時數 *(2 位老師時數不足)*
- 🟢 S08 校外教學 *(下月安排中)*
- 🟢 S11 人事派發 *(待派 3 件)*
            """
        )
    with sub_m:
        st.markdown("**🧰 總務處**")
        st.markdown(
            """
- 🔴 S03 政府採購 *(45 萬平板簽呈待我核)*
- 🟢 S09 防災演練 *(下次 5/12)*
- 🟡 S10 經費控管 *(主計駁回 1 件待補件)*
            """
        )
    with sub_r:
        st.markdown("**🌐 跨處室**")
        st.markdown(
            """
- 🟢 S12 計畫案件庫 *(8 案執行中)*
- 🟢 S13 媒體發佈 *(本週 2 則)*
            """
        )

    st.markdown("---")

    # 7 層視角覆蓋率
    st.markdown("### 🧠 7 層視角覆蓋率（系統可看見的待辦數）")
    coverage = [
        ("🎩 校長", 5, 5),
        ("💰 主計", 1, 5),
        ("🧰 總務主任", 8, 12),
        ("🏫 教導主任", 7, 10),
        ("📘 教務組長", 4, 6),
        ("🎌 訓導組長", 3, 5),
        ("👤 承辦人", 23, 30),
    ]
    for role, current, total in coverage:
        col_role, col_bar, col_num = st.columns([2, 5, 1])
        with col_role:
            st.markdown(f"**{role}**")
        with col_bar:
            st.progress(current / total if total else 0)
        with col_num:
            st.caption(f"{current} / {total}")

    st.markdown("---")

    # 三個 AI 副手（從校長視角看）
    st.markdown("### 🤖 我已派出 3 個 AI 副手（其餘 10 條線規劃中）")
    st.caption("校長不直接用這些工具 — 是『派給承辦人/總務/組長使用』的 AI 副手。校長只看結果。")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            """
<div class="module-card a">
<div class="module-title">📋 A. 採購法 AI 副手</div>
<div class="module-desc">服務「總務主任」<br>彙編 35 版 684 頁法條 RAG 查詢、風險警示、簽呈檢查<br>→ 對應 <b>S03 採購</b></div>
</div>
""",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """
<div class="module-card b">
<div class="module-title">📝 B. 公文 AI 副手</div>
<div class="module-desc">服務「組長與承辦人」<br>三段式公文 30 秒草稿,15 分鐘 → 30 秒<br>→ 對應 <b>S02 公文管考</b></div>
</div>
""",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            """
<div class="module-card c">
<div class="module-title">🎙️ C. 會議 AI 副手</div>
<div class="module-desc">服務「會議記錄者」<br>逐字稿 → 摘要+決議+待辦,並自動寫入行事曆<br>→ 對應 <b>M07 共用模組</b></div>
</div>
""",
            unsafe_allow_html=True,
        )

    st.markdown("")
    st.info(
        "💡 **校長角色**：派工 + 把關。不事必躬親，不接管承辦人工作。"
        "把校長從「翻簽辦清單追進度」解放，從「決策」回歸「願景」。"
        "點上方 tab「🏛️ 系統架構」看完整 13 子系統規劃。"
    )

# ===== 系統架構：母系統願景 =====
with tab_arch:
    st.subheader("行政減負系統 · 全貌")
    st.caption("本 app（小校一表通）是「**行政減負系統**」的子系統 — 是其中 S03 + S02 + M07 三個項目的 web 實作。")

    st.markdown("### 🎯 設計哲學")
    st.markdown(
        """
- **行政減負，不是稽核** — 看板用「需要支援」不用「逾期」，語彙刻意溫和
- **填一次不再填第二次** — S12 計畫案件庫是入口，其他子系統自動回寫
- **承辦人省力 > 主任可視 > 校長聚合** — 順序不可顛倒
        """
    )

    with st.expander("🧠 七層視角", expanded=False):
        st.markdown(
            """
| 視角 | 看什麼 |
|------|--------|
| 🎩 校長 | 待核決 / 跨處室協調 / 高風險 |
| 💰 主計（=人事幹事兼任） | S10 經費控管核章彙整 |
| 🧰 總務主任 | S03 採購 / S09 防災 / S10 經費 |
| 🏫 教導主任 | S01 校事 / S11 人事派發（親辦）+ 兩組長上報案 |
| 📘 教務組長 | S06 課程 / S07 研習 / S02（教務類公文） |
| 🎌 訓導組長 | S04 輔導 / S08 校外教學 / S02（訓育類公文） |
| 👤 承辦人 | 自己手上的案件（S05 特教承辦人直達主任） |
            """
        )

    st.markdown("### 📐 整體架構（13 子系統 + 3 共用模組）")
    st.code(
        """
                              🏛️ 行政減負系統
                         (vault: 08_校務減負系統)
                        ▶ 哲學：行政減負，不是稽核 ◀
                                       │
       ┌───────────────────────────────┼───────────────────────────────┐
       ▼                               ▼                               ▼
  🧠 七層視角                    📦 13 子系統                    🔧 3 共用模組

  🎩 校長        ┌────────────┬────────────┬────────────┐
  💰 主計        │ 📘 教導處  │ 🧰 總務處  │ 🌐 跨處室  │      M07 會議記錄
  🧰 總務主任    │            │            │            │       (錄音→結構化)
  🏫 教導主任    │ S01 校事 ✅│ S03 採購 ✅│ S12 計畫案 │
  📘 教務組長    │ S02 公文🚧 │ S09 防災🚧 │  件庫 🚧P1 │      S12 計畫案件庫
  🎌 訓導組長    │ S04 輔導🚧 │ S10 經費🚧 │ S13 媒體   │       (一份 md 從
  👤 承辦人      │ S05 特教🚧 │            │  發佈 🚧   │        立案到結案)
                 │ S06 課程🚧 │            │            │
                 │ S07 研習🚧 │            │            │      S13 媒體發佈
                 │ S08 校外🚧 │            │            │       (活動→新聞稿)
                 │ S11 人事🚧 │            │            │
                 └────────────┴────────────┴────────────┘
                                       │
                                       ▼
                              💻 前端實作
       ┌───────────────────────────────┼───────────────────────────────┐
       ▼                               ▼                               ▼
   小校一表通 (本 app)            CLI Skill                     UI 原型
   (Streamlit web)              (Claude Code)                 (6 HTML)

   模組 A → S03 採購 ✅          /校事文書 → S01 ✅           總入口 Portal
   模組 B → S02 公文 🚧          /採購法 → S03/06 ✅           校長儀表板
   模組 C → M07 會議 🚧          /關懷 → S12/S13 🚧            其他 4 個
        """,
        language="text",
    )

    with st.expander("🔄 連動主流程（S12 為減負入口）", expanded=False):
        st.code(
            """
              👤 承辦人在 S12 立案（一份 md）
                              │
              ┌───────────────┼───────────────┬────────────────┐
              ▼               ▼               ▼                ▼
        📨 S02 公文      💰 S10 經費     🎙️ M07 會議      👥 S11 派發
        自動關聯案號     自動回寫執行率   錄音→結構化       子任務給教師
              │               │               │                │
              └───────────────┴───────┬───────┴────────────────┘
                                      ▼
                          📡 通知整合層
                       Email / 行事曆 / LINE
            """,
            language="text",
        )

    st.markdown("### 📚 學術 USP（雙軌文獻交叉驗證 30 篇 SSCI/arXiv）")
    st.success(
        "「**小校 × 總務 × 中文法規 × Tool use 寫入行事曆**」四維齊全的整合系統，"
        "在 SSCI 文獻為**真空地帶**。"
    )
    st.markdown("**3 篇必引文獻**（5/11 校長遴選簡報用）：")
    st.markdown(
        """
| # | 文獻 | Cites | 用途 |
|---|------|-------|------|
| 1 | **Magesh, Surani & Ho 2025**（Stanford JELS）| 42 | 商用 RAG 法律工具仍有 17-33% 錯誤率 → 模組 A 設計差異化 |
| 2 | **Berkovich 2025**（Frontiers in Education）| new | 校長 GenAI 採用 early majority → xiaoxiao 整體 why |
| 3 | **Chen et al. 2025**（Adv Eng Inform）| 17 | Meet2Mitigate 框架 → 模組 C 升級藍本 |
        """
    )

    with st.expander("🎯 投稿期刊路線圖（學術延伸）", expanded=False):
        st.markdown(
            """
- 🥇 **Educational Management Administration & Leadership (EMAL)** — Q1 SSCI、近 2 年已收 5+ 篇 generative AI × school leadership
- 🥈 **Education and Information Technologies** — Q1 SSCI、UTAUT 框架友善
- 🥉 **Frontiers in Education** — Q2 SSCI、OA 較快、台灣 case study 友善
- ⚠️ **避雷 Computers & Education**：主題偏教與學非行政
            """
        )

    st.divider()
    st.caption("📂 詳細資料：vault `~/leeaoomacsecondbrain/08_校務減負系統/` (行政減負系統知識庫)")


# ===== 模組 A:採購法顧問 =====
with tab_a:
    st.subheader("採購法顧問")
    st.caption("問情境、查條文、檢查簽呈、風險警示 — 資深總務主任 + 採購法專業人員")

    st.markdown("**⚡ 1-click 示範**（點下去直接看 AI 分析）")
    ex_col1, ex_col2 = st.columns(2)
    with ex_col1:
        if st.button("⚡ 45 萬平板採購簽呈審查", width="stretch", key="proc_demo_1"):
            st.session_state["proc_q"] = "總務主任想採購 30 台平板給五六年級,總金額 45 萬,請問要走什麼程序?有什麼要注意?"
            st.session_state["proc_auto_show"] = "tablet"
    with ex_col2:
        if st.button("⚡ 邀 3 家只回 1 家能議價嗎", width="stretch", key="proc_demo_2"):
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
                    try:
                        q_clean = validate_user_input(q, "問題", MEDIUM_MAX_CHARS)
                    except InputValidationError as e:
                        st.error(str(e))
                        st.stop()
                    ctx = f"本校 context:{school_name} / 校長 {principal}"
                    ans = ""
                    if proc_agent_mode:
                        try:
                            ans = call_claude_agentic_procurement(load_prompt("procurement_qa.md"), q_clean, ctx)
                            st.success("🔬 RAG 模式：已查詢採購法彙編（35 版 684 頁）")
                        except RuntimeError as e:
                            st.error(f"❌ 進階模式失敗：{e}")
                    else:
                        ans = call_claude(load_prompt("procurement_qa.md"), q_clean, ctx)
                    if ans:
                        st.markdown(ans)
                        log_event("procurement", "query", "live")
                else:
                    demo = load_demo("procurement_demo.md")
                    log_event("procurement", "query", "demo")
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
        if st.button("⚡ 申請操場跑道整修補助", width="stretch", key="doc_demo_1"):
            st.session_state["demo_show"] = "track"
            st.session_state["doc_auto_show"] = True
    with ex2:
        if st.button("⚡ 邀廠商到校進行設備簡報", width="stretch", key="doc_demo_2"):
            st.session_state["demo_show"] = "vendor"
            st.session_state["doc_auto_show"] = True

    manual_gen = st.button("✍️ 生成公文草稿", type="primary", key="doc_btn")

    auto_trigger = st.session_state.pop("doc_auto_show", False)
    if (manual_gen or auto_trigger):
        if API_MODE == "live" and manual_gen and not auto_trigger:
            try:
                doc_subject_v = validate_user_input(doc_subject, "事由", SHORT_MAX_CHARS)
                doc_target_v = validate_user_input(doc_target, "受文者", SHORT_MAX_CHARS)
                doc_facts_v = validate_user_input(doc_facts, "關鍵事實", MEDIUM_MAX_CHARS)
            except InputValidationError as e:
                st.error(str(e))
                st.stop()
            with st.spinner("撰寫中..."):
                user_prompt = f"""事由:{doc_subject_v}
受文者:{doc_target_v}
類型:{doc_type}
對象層級:{doc_tone}
關鍵事實:
{doc_facts_v}

請依三段式產出公文草稿。"""
                ctx = f"本校 context:學校名稱 {school_name}、地址 {school_addr}、電話 {school_phone}、校長 {principal}"
                ans = call_claude(load_prompt("official_doc.md"), user_prompt, ctx)
                st.markdown(ans)
                log_event("official_doc", "generate", "live")
        else:
            demo = load_demo("official_doc_demo.md")
            log_event("official_doc", "generate", "demo")
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
                    try:
                        transcript_v = validate_user_input(transcript, "逐字稿")
                    except InputValidationError as e:
                        st.error(str(e))
                        st.stop()
                    user_prompt = f"會議類型:{meet_type}\n\n逐字稿:\n{transcript_v}"
                    ans = call_claude(load_prompt("meeting_summary.md"), user_prompt)
                    st.markdown(ans)
                    # 記住逐字稿讓「寫入行事曆」按鈕可用
                    st.session_state["meet_last_transcript"] = transcript_v
                    log_event("meeting", "summarize", "live")
                else:
                    demo = load_demo("meeting_demo.md")
                    log_event("meeting", "summarize", "demo")
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
                st.dataframe(sub, width="stretch", hide_index=True)


# ===== 模組 E:使用統計 =====
with tab_stats:
    st.subheader("📈 使用統計")
    st.caption("AI 副手分擔的工作量 — 累計次數 × 估省時")

    counts = get_event_counts()
    total_minutes = get_total_minutes_saved()
    proc_n = counts.get("procurement", 0)
    doc_n = counts.get("official_doc", 0)
    meet_n = counts.get("meeting", 0)
    total_n = proc_n + doc_n + meet_n

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.metric("⚖️ 採購法諮詢", f"{proc_n} 次", help="估每次省 30 分鐘")
    with s2:
        st.metric("📝 公文草稿", f"{doc_n} 次", help="估每次省 15 分鐘")
    with s3:
        st.metric("🎙️ 會議摘要", f"{meet_n} 次", help="估每次省 25 分鐘")
    with s4:
        hours = total_minutes // 60
        mins = total_minutes % 60
        st.metric(
            "⏱️ 累計估省時",
            f"{hours} 小時 {mins} 分" if hours else f"{total_minutes} 分鐘",
            help=f"基於累計 {total_n} 次使用 × 各模組估值",
        )

    st.markdown("**📅 近 7 天使用趨勢**")
    daily = get_daily_counts(days=7)
    if daily["次數"].sum() > 0:
        st.bar_chart(daily.set_index("日期"), height=200)
    else:
        st.info("近 7 天還沒事件 — 去其他 tab 點幾次 1-click 示範就會出現")

    st.divider()
    st.markdown("**💡 給合作夥伴的展示重點**")
    # 換算每年估省時：14 天累計 × 365/14 × 50 校
    annual_per_school = (total_minutes / 60) * (365 / 14)  # 一校一年
    annual_50_schools = int(annual_per_school * 50)
    st.markdown(
        f"""
- 一個 6 班 78 名學生的小校，校長一人面對 **13 條管考線**，本系統覆蓋其中 **3 條**
  （採購、公文、會議）= 23% 覆蓋率
- 近 14 天累計 {total_n} 次使用 ≈ **{total_minutes // 60} 小時**人工時間，相當於 {total_minutes // (60 * 8)} 個工作天
- 線性外推：一校一年估省 **{int(annual_per_school)} 小時**；
  全縣若有 50 所小校採用 → 估省 **{annual_50_schools:,} 小時/年**
"""
    )


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
