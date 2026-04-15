# 小校一表通(Xiaoxiao Yi-Biao-Tong)

> **你的學校資料只填一次,所有公文表單自動產出。**

六班國小行政減負系統——跨系統填報整合、AI 自然語言問答、歷史填報查詢。

## 背景

- 專案發起:2026-04-15
- 作者:李政蒲(東華科教所博士生,114 學年度候用校長)
- 用途:
  1. 校長遴選簡報武器
  2. 上任後(2026-08)的實際試辦原型
  3. 博論研究場域素材
- 對應企劃文件:`~/leeaoomacsecondbrain/00_工作流程系統/校長遴選_行政減負系統/`

## 快速開始

```bash
# 1. 建環境(只需跑一次)
./init.sh

# 2. 啟動 Streamlit
source .venv/bin/activate
streamlit run app.py
```

開啟後會看到 http://localhost:8501

## 專案結構

```
xiaoxiao-yibiaotong/
├── README.md
├── init.sh              # 一次性環境建置
├── requirements.txt
├── app.py               # Streamlit 主檔
├── .gitignore
├── schemas/
│   └── create_tables.sql
├── pages/               # Streamlit 多頁面
├── prompts/             # AI system prompts
├── data/
│   ├── school.db        # SQLite 主資料庫(.gitignore)
│   └── imports/         # CSV 匯入暫存
└── tests/
    └── demo_data.sql    # Demo 種子資料
```

## MVP 功能(Phase 1 W1-W5)

- [ ] F1 本校資料主檔瀏覽與編輯
- [ ] F2 自然語言問答(Claude API)
- [ ] F3 填報資料包產出
- [ ] F4 歷史填報查詢

## 授權

個人專案,未公開授權。
