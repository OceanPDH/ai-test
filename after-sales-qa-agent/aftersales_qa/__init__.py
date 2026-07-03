"""after-sales-qa-agent — Temu 售后页面数据的接口/一致性校验层。

数据由浏览器抽取层 (extractor/extract.js) 在已登录会话里产出归一化 JSON，
本包只负责纯代码的确定性断言与报告，不触网、不烧 token。
"""

from .validators import Finding, run_all
from .report import render_report

__all__ = ["Finding", "run_all", "render_report"]
