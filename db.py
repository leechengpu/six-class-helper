"""SQLite 資料存取：開檔、自動建檔、學校 metadata 載入。"""
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

BASE = Path(__file__).parent
DB_PATH = BASE / "data" / "school.db"
SCHEMA_SQL = BASE / "schemas" / "create_tables.sql"
SEED_SQL = BASE / "tests" / "demo_data.sql"


def ensure_db():
    """啟動時建/補 DB schema。

    - schema 用 CREATE TABLE IF NOT EXISTS，每次啟動都跑（idempotent，
      可加新表不破壞既有資料；解決舊 DB 沒有新表的 migration 問題）
    - seed 只在第一次（DB 不存在）跑，避免重複塞 demo 資料
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    is_new = not DB_PATH.exists()
    conn = sqlite3.connect(str(DB_PATH))
    try:
        if SCHEMA_SQL.exists():
            conn.executescript(SCHEMA_SQL.read_text(encoding="utf-8"))
        if is_new and SEED_SQL.exists():
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
