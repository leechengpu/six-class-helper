# 小校一表通 · 總務小幫手

> **你的學校資料只填一次,所有公文表單自動產出。**

六班國小行政減負系統——採購法顧問 × 公文草稿 × 會議記錄,三模組共用一份本校資料 context。

> 📍 **定位**：本 app 是更大「**行政減負系統**」（vault `08_校務減負系統`）的子系統，是其中 **S03 採購 + S02 公文 + M07 會議記錄** 的單窗口 web 實作。完整系統地圖見 [SUBSYSTEM_MAP.md](SUBSYSTEM_MAP.md)。

## 背景

- 專案發起:2026-04-15
- 作者:李政蒲(東華科教所博士生,114 學年度候用校長)
- 用途:
  1. 校長遴選簡報武器
  2. 上任後(2026-08)的實際試辦原型
  3. 博論研究場域素材

## 快速開始(本機)

```bash
./init.sh                              # 一次性建環境(含 venv + DB)
source .venv/bin/activate
streamlit run app.py                   # 開啟 http://localhost:8501
```

沒設 `ANTHROPIC_API_KEY` 會自動走 Demo 模式(預錄範例),設了才會接真實 Claude API。

## 部署到 Streamlit Community Cloud

1. **Fork / Clone** 此 repo 到自己的 GitHub 帳號
2. 到 <https://share.streamlit.io> → `New app` → 選此 repo、branch `main`、`app.py`
3. 在 `Advanced settings → Secrets` 填入:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```
4. 按 `Deploy`,約 1–2 分鐘完成

雲端啟動時會自動從 `schemas/create_tables.sql` + `tests/demo_data.sql` 建 SQLite DB,不用手動 init。

**注意**:Community Cloud 每次重啟會清掉檔案系統,所以資料庫是**示範用**的,不要拿來存長期資料。

## 專案結構

```
xiaoxiao-yibiaotong/
├── README.md
├── app.py                  # Streamlit UI（page config + CSS + 7 個 tab）
├── config.py               # 模型/token 設定（env 可覆寫）
├── validators.py           # 使用者輸入驗證（長度/空值/role 偽造）
├── db.py                   # SQLite 開檔 + 自建 schema
├── prompts.py              # Prompt + demo 檔案載入
├── claude_client.py        # Anthropic API 呼叫 + 例外處理
├── agents.py               # Claude Agent SDK 進階模式
├── events.py               # 使用事件記錄（餵 📈 使用統計 tab）
├── logger.py               # 結構化日誌（stderr → Streamlit Cloud Logs）
├── init.sh                 # 本機一次性環境建置
├── requirements.txt
├── requirements-test.txt
├── runtime.txt             # Streamlit Cloud 的 Python 版本
├── pytest.ini
├── .streamlit/
│   ├── config.toml         # 主題 / 設定
│   └── secrets.toml.example # Cloud Secrets 範例（真實 secrets 別 commit）
├── .gitignore
├── schemas/
│   └── create_tables.sql   # DB schema（school_meta / usage_events 等）
├── prompts/                # AI system prompts(採購/公文/會議)
├── tests/
│   ├── demo_data.sql       # Demo 種子資料(虛構花蓮示範國小)
│   ├── demo_cases/         # 三模組的 demo 回答範例
│   └── unit/               # pytest unit tests（42 tests）
├── pages/                  # Streamlit 多頁面(預留)
└── data/                   # SQLite DB 放這裡(gitignore)
```

## 功能模組

- **A. 採購法顧問**:彙編採購法條、風險警示、簽呈檢查（進階模式 RAG 真查彙編 35 版 684 頁）
- **B. 公文草稿**:三段式格式自動產出,15 分鐘變 30 秒
- **C. 會議記錄**:逐字稿 → 摘要 + 決議 + 待辦（進階模式可寫入 macOS 行事曆）
- **D. 本校資料**:一次填寫,三模組自動帶入
- **E. 使用統計**:累計次數 + 估省時 KPI（給合作夥伴看的展示重點）

## 給合作夥伴 / For Collaborators

> 想複製給另一所學校用？或想加入開發？這段給你看。

### 部署一所新學校（~10 分鐘）

1. **Fork** [此 repo](https://github.com/leechengpu/six-class-helper) 到你的 GitHub
2. **改學校資料** [tests/demo_data.sql](tests/demo_data.sql)：把 `school_name` / `principal_name` / `address` / `phone` / `class_count` / `teacher_count` / `total_students` 換成你校的
3. (Optional) **改 prompt 語氣** [prompts/*.md](prompts/) — 想要更正式 / 更白話 / 加你校特定條例都從這裡改
4. (Optional) **改主題色** [app.py](app.py) 開頭的 `PRIMARY` / `ACCENT` / `SUCCESS` 等 hex 變數
5. `git push` 到你的 fork
6. <https://share.streamlit.io> → `New app` → 選你的 fork、`main`、`app.py`
7. `Advanced settings → Secrets`：貼 [.streamlit/secrets.toml.example](.streamlit/secrets.toml.example) 內容、填入真實 `ANTHROPIC_API_KEY`
8. `Deploy` → 1-2 分鐘上線

### 一所學校能客製的點

| 客製檔案 | 改什麼 | 影響 |
|---------|--------|------|
| `tests/demo_data.sql` | 學校 metadata（14 欄） | 自動帶入所有 prompt context |
| `prompts/official_doc.md` | 公文語氣 / 格式偏好 | B 模組生成風格 |
| `prompts/procurement_qa.md` | 採購法回答深度 / 風險警示口吻 | A 模組回答風格 |
| `prompts/meeting_summary.md` | 會議摘要結構 | C 模組摘要格式 |
| `schemas/create_tables.sql` | 加你校自己要追的資料表 | 擴充模組用 |
| `config.py` 或 env vars | 模型升級（換 Opus / Haiku）、token 上限 | 全 app 通用 |
| `.streamlit/config.toml` | Streamlit 主題 / server 設定 | 全 app 通用 |

### 技術棧

- Python 3.11 + Streamlit 1.40+
- SQLite（內建，不需外部 DB）
- Anthropic Claude API（必填，沒設會跑 demo 模式預錄）
- Claude Agent SDK + macOS Calendar / 採購法 RAG（選用，本機限定）

### 想找合作的點

**業務夥伴**：
- school onboarding 自動化（目前要手改 SQL → 能否做 web 表單導入）
- 多校共用部署（目前一校一 Cloud app → 能否一個 instance 服務多校）
- 校長社群推廣 / 跨縣市試辦

**技術夥伴**：
- Whisper 語音轉逐字稿（C 模組 step 1 預留）
- mlx-whisper(Mac) ↔ faster-whisper(Win) 跨平台支援
- 跟 [校事文書 CLI skill](https://github.com/leechengpu) 整合進 web

**資料夥伴**：
- 採購法彙編每年改版同步（目前是 35 版）
- 縣府 dataset 整合（學生轉學 / 教師調動 / 經費核撥）
- 全縣指標 dashboard（聚合 N 校 events）

聯繫請開 issue 或直接 PR。

## 授權

個人專案,未公開授權。合作意願請開 issue 聯繫。
