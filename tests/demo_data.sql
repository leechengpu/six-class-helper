-- Demo 種子資料:花蓮縣某虛構六班國小
-- 格式真實,個資虛構

INSERT OR REPLACE INTO school_meta (field_name, field_value, category) VALUES
('school_name', '花蓮縣示範國民小學', '基本'),
('school_code', '154601', '基本'),
('phone', '03-8xxxxxx', '基本'),
('address', '花蓮縣示範鄉示範村 1 號', '基本'),
('zip_code', '970', '基本'),
('principal_name', '李校長', '人事'),
('principal_term_start', '2026-08-01', '人事'),
('class_count', '6', '基本'),
('teacher_count', '11', '基本'),
('total_students', '78', '基本'),
('district', '示範、xx、yy 三村', '基本'),
('library_books', '4200', '設備'),
('computer_count', '15', '設備'),
('tablet_count', '30', '設備');

INSERT OR REPLACE INTO students_stats (academic_year, grade, class_code, total, male, female, indigenous, special_ed, new_immigrant, low_income) VALUES
(114, 1, '甲', 13, 7, 6, 2, 1, 1, 2),
(114, 2, '甲', 12, 6, 6, 3, 0, 1, 1),
(114, 3, '甲', 14, 8, 6, 2, 1, 2, 2),
(114, 4, '甲', 13, 6, 7, 2, 0, 1, 1),
(114, 5, '甲', 14, 7, 7, 2, 1, 1, 2),
(114, 6, '甲', 12, 6, 6, 1, 1, 0, 1),
(113, 1, '甲', 12, 6, 6, 2, 1, 1, 2),
(113, 2, '甲', 14, 7, 7, 3, 0, 2, 2),
(113, 3, '甲', 13, 6, 7, 2, 1, 1, 1),
(113, 4, '甲', 14, 8, 6, 2, 1, 1, 2),
(113, 5, '甲', 12, 6, 6, 1, 1, 0, 1),
(113, 6, '甲', 13, 7, 6, 2, 1, 1, 2);

INSERT OR REPLACE INTO staff (name, role, subject, hours_per_week, has_admin, admin_role) VALUES
('李校長', '校長', '綜合活動', 4, 0, NULL),
('王主任', '教務主任', '國語', 16, 1, '教務主任'),
('陳主任', '學務主任', '數學', 16, 1, '學務主任'),
('林主任', '總務主任', '自然', 16, 1, '總務主任'),
('張老師', '教師', '英語', 22, 1, '資訊組長'),
('黃老師', '教師', '國語', 22, 0, NULL),
('吳老師', '教師', '數學', 22, 0, NULL),
('劉老師', '教師', '社會', 22, 1, '體育組長'),
('蔡老師', '教師', '藝術', 20, 0, NULL),
('楊老師', '教師', '健體', 20, 0, NULL),
('鄭老師', '教師', '本土語', 20, 0, NULL);

INSERT INTO filing_history (system_name, form_name, filed_by, fields_json, notes) VALUES
('教育部統計處', '學校基本統計 114 學年度', '李校長', '{"total_students":78,"class_count":6,"teacher_count":11}', '114-09-15 填報'),
('花蓮縣政府 eschool', '原住民學生數調查', '王主任', '{"indigenous_total":12}', '114-09-20'),
('教育部統計處', '特教學生數調查', '陳主任', '{"special_ed_total":4}', '114-09-22'),
('花蓮縣政府', '新住民子女調查', '王主任', '{"new_immigrant_total":6}', '114-10-05');

-- 使用事件 seed（過去 14 天分布，給 📈 使用統計 tab 一開就有數字）
-- 採購法 18 次、公文 12 次、會議 8 次 → 共 38 次 ≈ 14 小時估省時
INSERT INTO usage_events (event_at, module, event_type, api_mode, minutes_saved) VALUES
(datetime('now', '-13 days', '+09 hours'), 'procurement', 'query', 'live', 30),
(datetime('now', '-13 days', '+11 hours'), 'official_doc', 'generate', 'live', 15),
(datetime('now', '-12 days', '+10 hours'), 'procurement', 'query', 'live', 30),
(datetime('now', '-12 days', '+14 hours'), 'meeting', 'summarize', 'live', 25),
(datetime('now', '-11 days', '+09 hours'), 'procurement', 'query', 'demo', 30),
(datetime('now', '-11 days', '+15 hours'), 'official_doc', 'generate', 'live', 15),
(datetime('now', '-10 days', '+10 hours'), 'procurement', 'query', 'live', 30),
(datetime('now', '-10 days', '+11 hours'), 'procurement', 'query', 'live', 30),
(datetime('now', '-10 days', '+16 hours'), 'official_doc', 'generate', 'demo', 15),
(datetime('now', '-09 days', '+09 hours'), 'meeting', 'summarize', 'live', 25),
(datetime('now', '-09 days', '+13 hours'), 'procurement', 'query', 'live', 30),
(datetime('now', '-08 days', '+10 hours'), 'official_doc', 'generate', 'live', 15),
(datetime('now', '-08 days', '+14 hours'), 'procurement', 'query', 'demo', 30),
(datetime('now', '-07 days', '+09 hours'), 'procurement', 'query', 'live', 30),
(datetime('now', '-07 days', '+15 hours'), 'meeting', 'summarize', 'demo', 25),
(datetime('now', '-06 days', '+10 hours'), 'official_doc', 'generate', 'live', 15),
(datetime('now', '-06 days', '+11 hours'), 'procurement', 'query', 'live', 30),
(datetime('now', '-06 days', '+16 hours'), 'meeting', 'summarize', 'live', 25),
(datetime('now', '-05 days', '+09 hours'), 'procurement', 'query', 'live', 30),
(datetime('now', '-05 days', '+13 hours'), 'official_doc', 'generate', 'live', 15),
(datetime('now', '-05 days', '+15 hours'), 'procurement', 'query', 'demo', 30),
(datetime('now', '-04 days', '+10 hours'), 'meeting', 'summarize', 'live', 25),
(datetime('now', '-04 days', '+14 hours'), 'official_doc', 'generate', 'demo', 15),
(datetime('now', '-03 days', '+09 hours'), 'procurement', 'query', 'live', 30),
(datetime('now', '-03 days', '+11 hours'), 'procurement', 'query', 'live', 30),
(datetime('now', '-03 days', '+16 hours'), 'official_doc', 'generate', 'live', 15),
(datetime('now', '-02 days', '+10 hours'), 'meeting', 'summarize', 'live', 25),
(datetime('now', '-02 days', '+13 hours'), 'procurement', 'query', 'live', 30),
(datetime('now', '-02 days', '+15 hours'), 'official_doc', 'generate', 'live', 15),
(datetime('now', '-01 days', '+09 hours'), 'procurement', 'query', 'live', 30),
(datetime('now', '-01 days', '+11 hours'), 'meeting', 'summarize', 'live', 25),
(datetime('now', '-01 days', '+14 hours'), 'official_doc', 'generate', 'live', 15),
(datetime('now', '-01 days', '+16 hours'), 'procurement', 'query', 'demo', 30),
(datetime('now', '+0 hours'), 'procurement', 'query', 'live', 30),
(datetime('now', '-1 hours'), 'official_doc', 'generate', 'live', 15),
(datetime('now', '-3 hours'), 'meeting', 'summarize', 'live', 25),
(datetime('now', '-5 hours'), 'procurement', 'query', 'live', 30),
(datetime('now', '-7 hours'), 'procurement', 'query', 'live', 30);
