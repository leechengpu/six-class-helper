"""應用程式日誌：API 呼叫的成功/失敗 + 計時。

設計取捨：
- 用 stdlib logging（不引 structlog）
- 寫到 stderr（Streamlit 把 stderr 流到 Streamlit Cloud Logs）
- 命名空間 `xiaoxiao.*`，不 propagate 到 root（避免污染 Streamlit 自己的 log）
- 級別可用 LOG_LEVEL env var 覆寫（預設 INFO）

使用：
    from logger import get_logger
    log = get_logger("claude")
    log.info("call_claude OK in %.2fs", elapsed)
"""
import logging
import os
import sys

_LOGGER = logging.getLogger("xiaoxiao")

if not _LOGGER.handlers:  # 模組重 import 時 idempotent（Streamlit 會重跑）
    _LOGGER.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())
    _h = logging.StreamHandler(sys.stderr)
    _h.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    ))
    _LOGGER.addHandler(_h)
    _LOGGER.propagate = False


def get_logger(child: str = "") -> logging.Logger:
    """取得命名子 logger（例：get_logger("claude") → xiaoxiao.claude）。"""
    if child:
        return _LOGGER.getChild(child)
    return _LOGGER
