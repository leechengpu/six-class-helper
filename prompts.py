"""Prompt 與 demo 案例檔案載入。"""
from pathlib import Path

BASE = Path(__file__).parent
PROMPTS = BASE / "prompts"
DEMOS = BASE / "tests" / "demo_cases"


def load_prompt(name: str) -> str:
    p = PROMPTS / name
    return p.read_text(encoding="utf-8") if p.exists() else ""


def load_demo(name: str) -> str:
    p = DEMOS / name
    return p.read_text(encoding="utf-8") if p.exists() else "(demo 檔案不存在)"
