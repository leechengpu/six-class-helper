-- 小校一表通 SQLite schema
-- 對應 Phase 1 文件第 3 節

CREATE TABLE IF NOT EXISTS school_meta (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    field_name TEXT UNIQUE NOT NULL,
    field_value TEXT,
    category TEXT,
    last_updated DATE DEFAULT (date('now')),
    source TEXT
);

CREATE TABLE IF NOT EXISTS students_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    academic_year INTEGER NOT NULL,
    grade INTEGER NOT NULL,
    class_code TEXT NOT NULL,
    total INTEGER DEFAULT 0,
    male INTEGER DEFAULT 0,
    female INTEGER DEFAULT 0,
    indigenous INTEGER DEFAULT 0,
    special_ed INTEGER DEFAULT 0,
    new_immigrant INTEGER DEFAULT 0,
    low_income INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(academic_year, grade, class_code)
);

CREATE TABLE IF NOT EXISTS staff (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    role TEXT,
    cert TEXT,
    subject TEXT,
    hours_per_week INTEGER,
    has_admin INTEGER DEFAULT 0,
    admin_role TEXT,
    hire_date DATE
);

CREATE TABLE IF NOT EXISTS filing_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    system_name TEXT NOT NULL,
    form_name TEXT NOT NULL,
    filed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    filed_by TEXT,
    fields_json TEXT,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_filing_system ON filing_history(system_name);
CREATE INDEX IF NOT EXISTS idx_filing_form ON filing_history(form_name);
CREATE INDEX IF NOT EXISTS idx_students_year ON students_stats(academic_year);

-- 使用事件記錄表（餵 📈 使用統計 tab）
CREATE TABLE IF NOT EXISTS usage_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    module TEXT NOT NULL,         -- procurement / official_doc / meeting
    event_type TEXT NOT NULL,     -- query / generate / summarize
    api_mode TEXT,                -- live / demo
    minutes_saved INTEGER         -- 估每次省時（分鐘）
);

CREATE INDEX IF NOT EXISTS idx_events_at ON usage_events(event_at);
CREATE INDEX IF NOT EXISTS idx_events_module ON usage_events(module);
