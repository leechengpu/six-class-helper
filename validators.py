"""
使用者輸入驗證：在送進 Claude API 前過濾。

只防三件事：
  1. 空字串 / 全空白 → 無意義 API 呼叫
  2. 過長 → token cost 失控
  3. 偽造對話 role prefix（Human:/Assistant:/System:）→ 干擾 system prompt

不擋一般敏感詞。Claude 對 prompt injection 有相當韌性，
擋詞會誤殺正常用法（例如「請忽略上一個建議」）。
"""
import re

DEFAULT_MAX_CHARS = 20000   # 約 10-15k tokens；長逐字稿夠用
SHORT_MAX_CHARS = 200       # 事由/受文者這類短欄位
MEDIUM_MAX_CHARS = 4000     # 問題、關鍵事實這類中等欄位

_ROLE_PREFIX_RE = re.compile(
    r'^[ \t]*(Human|Assistant|System)\s*:\s*',
    re.IGNORECASE | re.MULTILINE,
)


class InputValidationError(ValueError):
    """使用者輸入未通過驗證。"""


def validate_user_input(
    text: str,
    field_name: str = "輸入",
    max_chars: int = DEFAULT_MAX_CHARS,
) -> str:
    """驗證並清理使用者輸入；不通過則丟 InputValidationError。

    回傳值是已清理（去除 role prefix + strip）的字串，可直接用於 API 呼叫。
    """
    if text is None:
        raise InputValidationError(f"{field_name}不能為空")

    cleaned = _ROLE_PREFIX_RE.sub('', text).strip()

    if not cleaned:
        raise InputValidationError(f"{field_name}不能為空")

    if len(cleaned) > max_chars:
        raise InputValidationError(
            f"{field_name}過長（{len(cleaned):,} 字 / 上限 {max_chars:,} 字），請精簡後再送出"
        )

    return cleaned
