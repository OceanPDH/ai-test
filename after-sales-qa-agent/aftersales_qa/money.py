"""金额解析：把 Temu 展示串（"$5.49" / "-$5.00" / "FREE"）转成整数分，避免浮点误差。"""

import re

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
