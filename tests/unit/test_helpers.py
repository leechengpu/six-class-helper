"""db.py + prompts.py 單元測試。

涵蓋不依賴 Streamlit 執行期的純函數。
@st.cache_data 包住的 load_meta / get_conn 需要 Streamlit runtime，這裡略過。
"""
import sqlite3

import pandas as pd
import pytest

from db import ensure_db, meta_value
from prompts import load_demo, load_prompt


class TestMetaValue:
    @pytest.fixture
    def df(self):
        return pd.DataFrame({
            "field_name": ["school_name", "principal_name", "phone"],
            "field_value": ["示範國小", "李校長", "03-8xxxxxx"],
        })

    def test_returns_value_when_field_exists(self, df):
        assert meta_value(df, "school_name") == "示範國小"
        assert meta_value(df, "principal_name") == "李校長"

    def test_returns_default_when_field_missing(self, df):
        assert meta_value(df, "nonexistent") == "—"

    def test_custom_default(self, df):
        assert meta_value(df, "nonexistent", default="N/A") == "N/A"

    def test_empty_dataframe(self):
        empty = pd.DataFrame({"field_name": [], "field_value": []})
        assert meta_value(empty, "any") == "—"


class TestEnsureDb:
    def test_creates_db_when_missing(self, tmp_path, monkeypatch):
        db_path = tmp_path / "school.db"
        schema = tmp_path / "schema.sql"
        schema.write_text(
            "CREATE TABLE school_meta (id INTEGER, field_name TEXT, field_value TEXT);",
            encoding="utf-8",
        )

        monkeypatch.setattr("db.DB_PATH", db_path)
        monkeypatch.setattr("db.SCHEMA_SQL", schema)
        monkeypatch.setattr("db.SEED_SQL", tmp_path / "noseed.sql")  # 不存在

        assert not db_path.exists()
        ensure_db()
        assert db_path.exists()

        # 驗證 schema 跑了
        conn = sqlite3.connect(str(db_path))
        try:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            assert ("school_meta",) in tables
        finally:
            conn.close()

    def test_idempotent_when_db_exists(self, tmp_path, monkeypatch):
        db_path = tmp_path / "school.db"
        db_path.touch()
        original_mtime = db_path.stat().st_mtime

        monkeypatch.setattr("db.DB_PATH", db_path)
        ensure_db()  # 不該動已存在的檔

        assert db_path.stat().st_mtime == original_mtime

    def test_runs_seed_sql_if_present(self, tmp_path, monkeypatch):
        db_path = tmp_path / "school.db"
        schema = tmp_path / "schema.sql"
        seed = tmp_path / "seed.sql"

        schema.write_text(
            "CREATE TABLE school_meta (id INTEGER PRIMARY KEY, field_name TEXT, field_value TEXT);",
            encoding="utf-8",
        )
        seed.write_text(
            "INSERT INTO school_meta (field_name, field_value) VALUES ('school_name', '測試國小');",
            encoding="utf-8",
        )

        monkeypatch.setattr("db.DB_PATH", db_path)
        monkeypatch.setattr("db.SCHEMA_SQL", schema)
        monkeypatch.setattr("db.SEED_SQL", seed)

        ensure_db()

        conn = sqlite3.connect(str(db_path))
        try:
            row = conn.execute(
                "SELECT field_value FROM school_meta WHERE field_name=?",
                ("school_name",),
            ).fetchone()
            assert row[0] == "測試國小"
        finally:
            conn.close()


class TestLoadPrompt:
    def test_returns_content_when_exists(self, tmp_path, monkeypatch):
        f = tmp_path / "test.md"
        f.write_text("prompt 內容", encoding="utf-8")
        monkeypatch.setattr("prompts.PROMPTS", tmp_path)

        assert load_prompt("test.md") == "prompt 內容"

    def test_returns_empty_when_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr("prompts.PROMPTS", tmp_path)
        assert load_prompt("nope.md") == ""


class TestLoadDemo:
    def test_returns_content_when_exists(self, tmp_path, monkeypatch):
        f = tmp_path / "demo.md"
        f.write_text("demo 內容", encoding="utf-8")
        monkeypatch.setattr("prompts.DEMOS", tmp_path)

        assert load_demo("demo.md") == "demo 內容"

    def test_returns_placeholder_when_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr("prompts.DEMOS", tmp_path)
        assert load_demo("nope.md") == "(demo 檔案不存在)"
