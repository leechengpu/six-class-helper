"""Anthropic API 呼叫:金鑰解析 + 同步 messages.create 包裝。"""
import os

import streamlit as st

from config import CLAUDE_MODEL, MAX_TOKENS


def get_api_mode():
    """回傳 'live' 或 'demo'。優先讀環境變數，再讀 st.secrets。"""
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if key:
        return "live"
    try:
        key = st.secrets.get("ANTHROPIC_API_KEY", "")
        if key:
            os.environ["ANTHROPIC_API_KEY"] = key
            return "live"
    except Exception:
        pass
    return "demo"


def call_claude(system_prompt: str, user_prompt: str, context: str = "") -> str:
    try:
        import anthropic
    except ImportError:
        return "⚠️ 未安裝 anthropic SDK,請執行 `pip install anthropic`"

    full_user = f"{context}\n\n---\n\n{user_prompt}" if context else user_prompt
    try:
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            messages=[{"role": "user", "content": full_user}],
        )
        return msg.content[0].text
    except anthropic.AuthenticationError:
        return "⚠️ API 金鑰無效，請檢查 `ANTHROPIC_API_KEY` 環境變數或 `st.secrets`"
    except anthropic.RateLimitError:
        return "⚠️ API 用量已達上限，請稍後再試"
    except anthropic.APIConnectionError as e:
        return f"⚠️ 無法連線到 Anthropic:{e}"
    except anthropic.APIError as e:
        return f"⚠️ AI 回應失敗:{e}"
