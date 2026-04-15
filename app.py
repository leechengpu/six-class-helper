import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

DB_PATH = Path(__file__).parent / "data" / "school.db"

st.set_page_config(
    page_title="小校一表通",
    page_icon="📋",
    layout="wide",
)

st.title("📋 小校一表通")
st.caption("你的學校資料只填一次,所有公文表單自動產出。")


@st.cache_resource
def get_conn():
    return sqlite3.connect(str(DB_PATH), check_same_thread=False)


def load_school_meta():
    conn = get_conn()
    return pd.read_sql_query(
        "SELECT category, field_name, field_value, last_updated FROM school_meta ORDER BY category, field_name",
        conn,
    )


def load_students_stats(year: int):
    conn = get_conn()
    return pd.read_sql_query(
        "SELECT grade, class_code, total, male, female, indigenous, special_ed, new_immigrant, low_income FROM students_stats WHERE academic_year = ? ORDER BY grade, class_code",
        conn,
        params=(year,),
    )


def load_staff():
    conn = get_conn()
    return pd.read_sql_query(
        "SELECT name, role, subject, hours_per_week, has_admin, admin_role FROM staff",
        conn,
    )


def load_filing_history():
    conn = get_conn()
    return pd.read_sql_query(
        "SELECT system_name, form_name, filed_at, filed_by, notes FROM filing_history ORDER BY filed_at DESC",
        conn,
    )


if not DB_PATH.exists():
    st.error(
        f"❌ 資料庫不存在:{DB_PATH}\n\n請先執行 `./init.sh` 建立環境與種子資料。"
    )
    st.stop()

tab1, tab2, tab3, tab4 = st.tabs(
    ["🏫 本校資料", "👥 學生統計", "👨‍🏫 教職員", "📜 填報歷史"]
)

with tab1:
    st.subheader("本校基本資料")
    meta_df = load_school_meta()
    if meta_df.empty:
        st.info("尚無資料,請先匯入或手動新增。")
    else:
        for category in meta_df["category"].unique():
            st.markdown(f"### {category}")
            sub = meta_df[meta_df["category"] == category][
                ["field_name", "field_value", "last_updated"]
            ]
            st.dataframe(sub, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("學生統計")
    year = st.selectbox("學年度", [114, 113], index=0)
    stats = load_students_stats(year)
    if stats.empty:
        st.info(f"{year} 學年度尚無資料。")
    else:
        st.dataframe(stats, use_container_width=True, hide_index=True)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("總學生數", int(stats["total"].sum()))
        col2.metric("原住民", int(stats["indigenous"].sum()))
        col3.metric("特教", int(stats["special_ed"].sum()))
        col4.metric("新住民", int(stats["new_immigrant"].sum()))

with tab3:
    st.subheader("教職員名單")
    staff_df = load_staff()
    if staff_df.empty:
        st.info("尚無資料。")
    else:
        st.dataframe(staff_df, use_container_width=True, hide_index=True)

with tab4:
    st.subheader("填報歷史紀錄")
    st.caption("每次填報都會記錄,方便下次回查「這題去年填什麼?」")
    history = load_filing_history()
    if history.empty:
        st.info("尚無填報紀錄。")
    else:
        st.dataframe(history, use_container_width=True, hide_index=True)

st.divider()
st.caption("Phase 2 W2-W5 即將加入:AI 自然語言問答、填報資料包產出")
