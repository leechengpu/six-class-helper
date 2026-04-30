"""進階模式：Claude Agent SDK + Tool Use。

本機限定（需安裝 Claude Code CLI: `npm i -g @anthropic-ai/claude-code`）。
Streamlit Cloud 沒有 claude CLI，UI 端會自動隱藏切換鈕。

提供：
  - _agent_sdk_available(): 檢查 SDK + CLI 是否可用
  - call_claude_agentic_procurement(): 採購法 RAG agent
  - call_claude_agentic_meeting_to_calendar(): 會議決議寫入 macOS 行事曆
"""
import time
from datetime import datetime
from pathlib import Path

from config import CLAUDE_MODEL
from logger import get_logger

log = get_logger("agent")
BASE = Path(__file__).parent


def _agent_sdk_available() -> bool:
    """檢查 Agent SDK + claude CLI 都可用。"""
    import shutil
    if not shutil.which("claude"):
        return False
    try:
        import claude_agent_sdk  # noqa: F401
        return True
    except ImportError:
        return False


def _extract_assistant_text(msg) -> str:
    """從 Agent SDK 串流訊息抽出最終 assistant 文字（跳過 tool use blocks）。"""
    if type(msg).__name__ != "AssistantMessage":
        return ""
    parts = []
    for block in getattr(msg, "content", []):
        if type(block).__name__ == "TextBlock":
            parts.append(getattr(block, "text", ""))
    return "\n".join(parts)


async def _agentic_procurement_query(system_prompt: str, user_prompt: str, context: str) -> str:
    """模組 A 進階：採購法 RAG agent。"""
    from claude_agent_sdk import (
        query,
        tool,
        create_sdk_mcp_server,
        ClaudeAgentOptions,
        HookMatcher,
    )

    @tool(
        "search_procurement_law",
        "從政府採購法彙編（35 版 684 頁，含本文/施行細則/子法/GPA/相關法令）查詢條文。"
        "傳入關鍵字（條號如「第 22 條」、術語如「公告金額」「綁標」「最有利標」），"
        "回傳前 8 筆命中的上下文（含檔名、行號、前後 2 行）。",
        {"keyword": str},
    )
    async def search_law(args):
        keyword = args["keyword"]
        law_dir = BASE / "data" / "procurement_law"
        if not law_dir.exists():
            return {"content": [{"type": "text", "text": "❌ 法規資料夾不存在"}]}
        hits = []
        for md_file in sorted(law_dir.glob("*.md")):
            try:
                text = md_file.read_text(encoding="utf-8")
            except Exception:
                continue
            lines = text.split("\n")
            for i, line in enumerate(lines):
                if keyword in line:
                    start = max(0, i - 2)
                    end = min(len(lines), i + 3)
                    ctx = "\n".join(lines[start:end])
                    hits.append(f"📄 {md_file.name}:{i+1}\n{ctx}")
                    if len(hits) >= 8:
                        break
            if len(hits) >= 8:
                break
        if not hits:
            return {"content": [{"type": "text", "text": f"未找到包含「{keyword}」的條文。"}]}
        return {"content": [{"type": "text", "text": "\n\n---\n\n".join(hits)}]}

    async def log_law_query(input_data, tool_use_id, context):
        keyword = input_data.get("tool_input", {}).get("keyword", "")
        log_path = BASE / "data" / "audit_law.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()}\t{keyword}\n")
        return {}

    server = create_sdk_mcp_server(name="procurement-law", version="1.0.0", tools=[search_law])
    full_user = f"{context}\n\n---\n\n{user_prompt}" if context else user_prompt
    augmented_sys = (
        system_prompt
        + "\n\n## 🚨 進階模式紀律\n"
        + "你**必須**先呼叫 search_procurement_law 工具查詢真實條文，再回答。"
        + "禁止僅憑記憶引用條號。每個引用條文都要附查詢來源（檔名）。"
    )
    options = ClaudeAgentOptions(
        system_prompt=augmented_sys,
        mcp_servers={"law": server},
        allowed_tools=["mcp__law__search_procurement_law"],
        disallowed_tools=[
            "Read", "Write", "Edit", "Bash",
            "Glob", "Grep", "WebSearch", "WebFetch",
        ],
        setting_sources=[],
        hooks={
            "PostToolUse": [
                HookMatcher(
                    matcher="mcp__law__search_procurement_law",
                    hooks=[log_law_query],
                ),
            ],
        },
        model=CLAUDE_MODEL,
        max_turns=8,
    )
    chunks = []
    async for msg in query(prompt=full_user, options=options):
        text = _extract_assistant_text(msg)
        if text:
            chunks.append(text)
    return "\n\n".join(chunks) if chunks else "（無回應）"


def call_claude_agentic_procurement(system_prompt: str, user_prompt: str, context: str = "") -> str:
    import anyio
    from claude_agent_sdk import (
        CLINotFoundError, CLIConnectionError, ProcessError, CLIJSONDecodeError,
    )
    start = time.monotonic()
    log.info("procurement agent start (q_len=%d)", len(user_prompt))
    try:
        result = anyio.run(_agentic_procurement_query, system_prompt, user_prompt, context)
        log.info("procurement agent OK %.2fs (out_len=%d)", time.monotonic() - start, len(result))
        return result
    except CLINotFoundError:
        log.error("procurement agent: claude CLI not found")
        raise RuntimeError("找不到 Claude Code CLI，請執行：npm i -g @anthropic-ai/claude-code")
    except ProcessError as e:
        log.error("procurement agent ProcessError exit=%s after %.2fs", e.exit_code, time.monotonic() - start)
        raise RuntimeError(f"Claude CLI 執行失敗（exit {e.exit_code}）")
    except CLIJSONDecodeError as e:
        log.error("procurement agent JSON decode error after %.2fs: %s", time.monotonic() - start, e)
        raise RuntimeError(f"Claude CLI 回應解析錯誤：{e}")
    except CLIConnectionError as e:
        log.error("procurement agent connection error after %.2fs: %s", time.monotonic() - start, e)
        raise RuntimeError(f"Claude CLI 連線錯誤：{e}")


async def _agentic_meeting_to_calendar(transcript: str) -> str:
    """模組 C 進階：把會議決議寫入 macOS 行事曆。"""
    import subprocess
    from claude_agent_sdk import (
        query,
        tool,
        create_sdk_mcp_server,
        ClaudeAgentOptions,
        HookMatcher,
    )

    @tool(
        "add_to_calendar",
        "把單一決議事項或待辦寫入 macOS 行事曆。datetime 格式必須為 YYYY-MM-DD HH:MM。",
        {"title": str, "datetime": str, "notes": str},
    )
    def _as_quote(s: str) -> str:
        # AppleScript 字串字面值轉義：壓平換行 → escape backslash → escape quote
        s = s.replace("\r", "").replace("\n", " ")
        s = s.replace("\\", "\\\\").replace('"', '\\"')
        return '"' + s + '"'

    async def add_to_calendar(args):
        try:
            dt = datetime.strptime(args["datetime"], "%Y-%m-%d %H:%M")
        except ValueError:
            return {"content": [{"type": "text", "text": f"❌ 日期格式錯誤：{args['datetime']}"}]}
        if dt < datetime.now():
            return {"content": [{"type": "text", "text": f"❌ 日期已過：{args['datetime']}（agent 應重新推算未來時間）"}]}
        script = f'''tell application "Calendar"
    set theDate to current date
    set year of theDate to {dt.year}
    set month of theDate to {dt.month}
    set day of theDate to {dt.day}
    set hours of theDate to {dt.hour}
    set minutes of theDate to {dt.minute}
    set seconds of theDate to 0
    set endDate to theDate + 60 * 60
    tell calendar 1
        make new event with properties {{summary:{_as_quote(args["title"])}, start date:theDate, end date:endDate, description:{_as_quote(args["notes"])}}}
    end tell
end tell'''
        try:
            subprocess.run(
                ["osascript", "-"],
                input=script,
                check=True, capture_output=True, timeout=15, text=True,
            )
            return {"content": [{"type": "text", "text": f"✅ 已加入：{args['title']} @ {args['datetime']}"}]}
        except subprocess.CalledProcessError as e:
            return {"content": [{"type": "text", "text": f"❌ 加入失敗：{e.stderr or str(e)}"}]}
        except subprocess.TimeoutExpired:
            return {"content": [{"type": "text", "text": "❌ Calendar 沒回應（可能權限未授予）"}]}

    async def log_calendar_event(input_data, tool_use_id, context):
        ti = input_data.get("tool_input", {})
        log_path = BASE / "data" / "audit_calendar.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(
                f"{datetime.now().isoformat()}\t"
                f"{ti.get('datetime','')}\t{ti.get('title','')}\n"
            )
        return {}

    server = create_sdk_mcp_server(name="cal", version="1.0.0", tools=[add_to_calendar])
    today = datetime.now().strftime("%Y-%m-%d")
    sys_prompt = f"""你是會議決議分派助理。從逐字稿萃取「決議事項」與「待辦」並逐一呼叫 add_to_calendar。

今天日期：{today}

規則：
- 有明確日期 → 用該日期
- 「下週 X」「月底」→ 合理推算
- 沒提時間 → 用相關日期 14:00
- 純粹「報告」「分享」「討論」沒有要做的事 → 不要加
- title 簡短（< 30 字），notes 寫負責人 + 完整脈絡

完成所有 add_to_calendar 呼叫後，總結：
- 共寫入 N 筆
- 條列每筆：標題 + 時間 + 負責人
- 列出「未寫入但值得追蹤」的事項（如果有）
"""
    options = ClaudeAgentOptions(
        system_prompt=sys_prompt,
        mcp_servers={"cal": server},
        allowed_tools=["mcp__cal__add_to_calendar"],
        disallowed_tools=[
            "Read", "Write", "Edit", "Bash",
            "Glob", "Grep", "WebSearch", "WebFetch",
        ],
        setting_sources=[],
        hooks={
            "PostToolUse": [
                HookMatcher(
                    matcher="mcp__cal__add_to_calendar",
                    hooks=[log_calendar_event],
                ),
            ],
        },
        model=CLAUDE_MODEL,
        max_turns=20,
    )
    chunks = []
    async for msg in query(prompt=f"逐字稿：\n\n{transcript}", options=options):
        text = _extract_assistant_text(msg)
        if text:
            chunks.append(text)
    return "\n\n".join(chunks) if chunks else "（無回應）"


def call_claude_agentic_meeting_to_calendar(transcript: str) -> str:
    import anyio
    from claude_agent_sdk import (
        CLINotFoundError, CLIConnectionError, ProcessError, CLIJSONDecodeError,
    )
    start = time.monotonic()
    log.info("calendar agent start (transcript_len=%d)", len(transcript))
    try:
        result = anyio.run(_agentic_meeting_to_calendar, transcript)
        log.info("calendar agent OK %.2fs (out_len=%d)", time.monotonic() - start, len(result))
        return result
    except CLINotFoundError:
        log.error("calendar agent: claude CLI not found")
        raise RuntimeError("找不到 Claude Code CLI，請執行：npm i -g @anthropic-ai/claude-code")
    except ProcessError as e:
        log.error("calendar agent ProcessError exit=%s after %.2fs", e.exit_code, time.monotonic() - start)
        raise RuntimeError(f"Claude CLI 執行失敗（exit {e.exit_code}）")
    except CLIJSONDecodeError as e:
        log.error("calendar agent JSON decode error after %.2fs: %s", time.monotonic() - start, e)
        raise RuntimeError(f"Claude CLI 回應解析錯誤：{e}")
    except CLIConnectionError as e:
        log.error("calendar agent connection error after %.2fs: %s", time.monotonic() - start, e)
        raise RuntimeError(f"Claude CLI 連線錯誤：{e}")
