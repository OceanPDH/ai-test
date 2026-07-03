"""金额解析：把 Temu 展示串（"$5.49" / "-$5.00" / "FREE"）转成整数分，避免浮点误差。

已知限制：假定美式数字格式（'.' 小数点、',' 千位分隔），面向 Temu 美区(region 211)。
欧式逗号小数（如 "0,49"）会被误解析为 0；接入非美区前需按 region 扩展本函数。
"""

import re

# 美式格式：整数部分可含千位逗号，小数部分用点。见上方"已知限制"。
_NUM = re.compile(r"(\d+(?:,\d{3})*(?:\.\d+)?)")


def parse_money(text):
    """返回整数分；无法解析返回 None。'FREE'/'' 视为 0/None。

    >>> parse_money("$5.49")
    549
    >>> parse_money("-$5.00")
    -500
    >>> parse_money("FREE")
    0
    """
    if text is None:
        return None
    t = str(text).strip()
    if t == "":
        return None
    if t.upper() == "FREE":
        return 0
    neg = t.lstrip().startswith("-") or "-$" in t or "−" in t
    m = _NUM.search(t)
    if not m:
        return None
    cents = round(float(m.group(1).replace(",", "")) * 100)
    return -cents if neg else cents


def fmt_cents(cents):
    if cents is None:
        return "n/a"
    return f"${cents / 100:.2f}"
