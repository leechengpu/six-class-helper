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
├── app.py                  # Streamlit 主檔(含 DB 自建邏輯)
├── init.sh                 # 本機一次性環境建置
├── requirements.txt
├── runtime.txt             # Streamlit Cloud 的 Python 版本
├── .streamlit/
│   └── config.toml         # 主題 / 設定
├── .gitignore
├── schemas/
│   └── create_tables.sql   # DB schema
├── prompts/                # AI system prompts(採購/公文/會議)
├── tests/
│   ├── demo_data.sql       # Demo 種子資料(虛構花蓮示範國小)
│   └── demo_cases/         # 三模組的 demo 回答範例
├── pages/                  # Streamlit 多頁面(預留)
└── data/                   # SQLite DB 放這裡(gitignore)
```

## 功能模組

- **A. 採購法顧問**:彙編採購法條、風險警示、簽呈檢查
- **B. 公文草稿**:三段式格式自動產出,15 分鐘變 30 秒
- **C. 會議記錄**:逐字稿 → 摘要 + 決議 + 待辦
- **D. 本校資料**:一次填寫,三模組自動帶入

## 授權

個人專案,未公開授權。
