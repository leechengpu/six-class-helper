"""events.py 單元測試。"""
import sqlite3

import pytest

from events import (
    MINUTES_SAVED,
    get_daily_counts,
    get_event_counts,
    get_total_minutes_saved,
    log_event,
)


@pytest.fixture
def fake_conn(tmp_path, monkeypatch):
    """建一個有 usage_events 表的 SQLite 連線，並 patch get_conn 回傳它。"""
    db = tmp_path / "test.db"
    conn = sqlite3.connect(str(db), check_same_thread=False)
    conn.executescript("""
        CREATE TABLE usage_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            module TEXT NOT NULL,
            event_type TEXT NOT NULL,
            api_mode TEXT,
            minutes_saved INTEGER
        );
    """)
    conn.commit()

    monkeypatch.setattr("events.get_conn", lambda: conn)
    yield conn
    conn.close()


class TestLogEvent:
    def test_writes_event_with_correct_minutes(self, fake_conn):
        log_event("procurement", "query", "live")

        row = fake_conn.execute(
            "SELECT module, event_type, api_mode, minutes_saved FROM usage_events"
        ).fetchone()
        assert row == ("procurement", "query", "live", 30)

    def test_unknown_module_logs_zero_minutes(self, fake_conn):
        log_event("unknown_module", "test", "demo")

        row = fake_conn.execute(
            "SELECT minutes_saved FROM usage_events"
        ).fetchone()
        assert row[0] == 0

    def test_db_error_does_not_propagate(self, monkeypatch):
        """log_event 失敗只能記日誌，不該打斷 user flow。"""
        def broken_conn():
            raise sqlite3.Error("db unavailable")

        monkeypatch.setattr("events.get_conn", broken_conn)
        # 不該丟例外
        log_event("procurement", "query", "demo")


class TestGetEventCounts:
    def test_counts_per_module(self, fake_conn):
        log_event("procurement", "query", "live")
        log_event("procurement", "query", "demo")
        log_event("official_doc", "generate", "live")

        counts = get_event_counts()
        assert counts == {"procurement": 2, "official_doc": 1}

    def test_empty_returns_empty_dict(self, fake_conn):
        assert get_event_counts() == {}


class TestTotalMinutesSaved:
    def test_sum_across_modules(self, fake_conn):
        log_event("procurement", "query", "live")    # +30
        log_event("official_doc", "generate", "live") # +15
        log_event("meeting", "summarize", "live")     # +25

        assert get_total_minutes_saved() == 70

    def test_empty_returns_zero(self, fake_conn):
        assert get_total_minutes_saved() == 0


class TestDailyCounts:
    def test_pads_missing_days_with_zero(self, fake_conn):
        log_event("procurement", "query", "live")  # 今天

        df = get_daily_counts(days=7)
        assert len(df) == 7
        assert df["次數"].sum() >= 1
        # 7 天裡至少 6 天是 0
        assert (df["次數"] == 0).sum() >= 6

    def test_columns(self, fake_conn):
        df = get_daily_counts(days=7)
        assert list(df.columns) == ["日期", "次數"]


class TestMinutesSavedConfig:
    def test_all_modules_have_estimates(self):
        assert "procurement" in MINUTES_SAVED
        assert "official_doc" in MINUTES_SAVED
        assert "meeting" in MINUTES_SAVED
        assert all(v > 0 for v in MINUTES_SAVED.values())
