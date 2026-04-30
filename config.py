"""
集中設定：模型、token 上限等。可被環境變數覆寫。

範例：
    CLAUDE_MODEL=claude-opus-4-7 streamlit run app.py
    MAX_TOKENS=4096 streamlit run app.py
"""
import os

CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-5")
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "2048"))
