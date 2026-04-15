#!/bin/bash
# 小校一表通 · 環境建置腳本
# 執行方式:./init.sh
# 一次性,跑完就能 streamlit run app.py

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "========================================"
echo "📋 小校一表通 · 環境建置"
echo "========================================"
echo "專案路徑:$PROJECT_DIR"
echo ""

# 1. 檢查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 找不到 python3,請先安裝 Python 3.10 以上"
    exit 1
fi

PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✅ Python 版本:$PY_VERSION"

# 2. 建立 venv
if [ ! -d ".venv" ]; then
    echo ""
    echo "🔧 建立虛擬環境(.venv)..."
    python3 -m venv .venv
    echo "✅ 虛擬環境建立完成"
else
    echo "ℹ️  虛擬環境已存在,略過建立"
fi

# 3. 啟動 venv 並安裝套件
echo ""
echo "📦 安裝套件..."
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo "✅ 套件安裝完成"

# 4. 建立 SQLite 資料庫 + schema
DB_PATH="data/school.db"
if [ ! -f "$DB_PATH" ]; then
    echo ""
    echo "💾 建立 SQLite 資料庫..."
    sqlite3 "$DB_PATH" < schemas/create_tables.sql
    echo "✅ 資料庫建立完成:$DB_PATH"

    # 載入 demo 種子資料
    echo ""
    echo "🌱 載入 demo 種子資料(虛構花蓮示範國小)..."
    sqlite3 "$DB_PATH" < tests/demo_data.sql
    echo "✅ 種子資料載入完成"
else
    echo "ℹ️  資料庫已存在:$DB_PATH(略過建立)"
fi

# 5. 初始化 git
if [ ! -d ".git" ]; then
    echo ""
    echo "🔖 初始化 git repo..."
    git init -q
    git add .
    git commit -q -m "初始化小校一表通專案 · Phase 2 W1"
    echo "✅ git repo 建立完成"
else
    echo "ℹ️  git repo 已存在,略過初始化"
fi

# 6. 建立 touch file 給空資料夾
touch data/imports/.gitkeep pages/.gitkeep prompts/.gitkeep 2>/dev/null || true

echo ""
echo "========================================"
echo "🎉 建置完成!"
echo "========================================"
echo ""
echo "接下來:"
echo "  1. 啟動虛擬環境: source .venv/bin/activate"
echo "  2. 啟動 Streamlit: streamlit run app.py"
echo "  3. 瀏覽器自動開啟 http://localhost:8501"
echo ""
echo "專案文件:~/leeaoomacsecondbrain/00_工作流程系統/校長遴選_行政減負系統/"
echo ""
