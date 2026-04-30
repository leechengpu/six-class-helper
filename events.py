"""使用事件記錄與統計：餵 📈 使用統計 tab。

設計：
- 寫入 usage_events 表（schema 在 schemas/create_tables.sql）
- 寫入失敗不擋 user flow（就是統計，掛了也不該影響 demo）
- 查詢透過 pandas DataFrame，方便 Streamlit chart 直接用
"""
from __future__ import annotations

import sqlite3
from typing import Optional

import pandas as pd

from db import get_conn
from logger import get_logger

log = get_logger("events")

# 估每次模組省的時間（分鐘）— 給「估省時」KPI 用
MINUTES_SAVED = {
    "procurement": 30,    # 查條文 + 寫風險警示，本來要翻彙編
    "official_doc": 15,   # 三段式公文，本來要查格式 + 草稿
    "meeting": 25,        # 逐字稿 → 摘要 + 決議 + 待辦
}

MODULE_LABELS = {
    "procurement": "採購法諮詢",
    "official_doc": "公文草稿",
    "meeting": "會議摘要",
}


def log_event(module: str, event_type: str, api_mode: str = "demo") -> None:
    """寫入一筆使用事件。失敗只記錄不丟例外（demo 重於統計）。"""
    minutes = MINUTES_SAVED.get(module, 0)
    try:
        conn = get_conn()
        conn.execute(
            "INSERT INTO usage_events (module, event_type, api_mode, minutes_saved) "
            "VALUES (?, ?, ?, ?)",
            (module, event_type, api_mode, minutes),
        )
        conn.commit()
    except sqlite3.Error as e:
        log.warning("log_event failed: %s", e)


def get_event_counts() -> dict[str, int]:
    """各模組累計次數。回傳 dict[module_key, count]。"""
    try:
        conn = get_conn()
        rows = conn.execute(
            "SELECT module, COUNT(*) FROM usage_events GROUP BY module"
        ).fetchall()
        return {m: c for m, c in rows}
    except sqlite3.Error as e:
        log.warning("get_event_counts failed: %s", e)
        return {}


def get_total_minutes_saved() -> int:
    """累計估省時（分鐘）。"""
    try:
        conn = get_conn()
        result = conn.execute(
            "SELECT COALESCE(SUM(minutes_saved), 0) FROM usage_events"
        ).fetchone()
        return int(result[0]) if result else 0
    except sqlite3.Error as e:
        log.warning("get_total_minutes_saved failed: %s", e)
        return 0


def get_daily_counts(days: int = 7) -> pd.DataFrame:
    """近 N 天的每日使用次數，給 st.bar_chart 用。

    回傳的 DataFrame 已補齊缺日（沒事件的日期 count=0），
    avoid Streamlit chart 出現空缺。
    """
    try:
        conn = get_conn()
        df = pd.read_sql_query(
            f"""SELECT date(event_at) AS 日期, COUNT(*) AS 次數
                FROM usage_events
                WHERE event_at >= date('now', '-{days} days')
                GROUP BY date(event_at)
                ORDER BY 日期""",
            conn,
        )
    except sqlite3.Error as e:
        log.warning("get_daily_counts failed: %s", e)
        return pd.DataFrame({"日期": [], "次數": []})

    # 補齊缺日
    full_range = pd.date_range(end=pd.Timestamp.today(), periods=days).strftime("%Y-%m-%d")
    full_df = pd.DataFrame({"日期": full_range})
    full_df = full_df.merge(df, on="日期", how="left").fillna({"次數": 0})
    full_df["次數"] = full_df["次數"].astype(int)
    return full_df
