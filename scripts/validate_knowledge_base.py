#!/usr/bin/env python3
"""Audit repository Markdown links and core folder conventions; stdlib only."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
RE_LINK = re.compile(r'!?\[[^\]]*\]\(([^)]+)\)')
RE_IMAGE = re.compile(r'!\[[^\]]*\]\(')

def text_without_code(raw: str) -> str:
    result = []
    fenced = False
    for line in raw.splitlines():
        if line.strip().startswith(("```", "~~~")):
            fenced = not fenced
            continue
        if not fenced:
            result.append(re.sub(r'`[^`]*`', '', line))
    return "\n".join(result)

def main() -> int:
    errors = []
    checks = 0
    md_files = sorted(ROOT.rglob("*.md"))
    for file in md_files:
        content = text_without_code(file.read_text(encoding="utf-8"))
        if file.relative_to(ROOT).parts[0] == "01-信息图形数据逻辑" and RE_IMAGE.search(content):
            errors.append(f"{file.relative_to(ROOT)}: 01 禁止嵌入图片")
        for match in RE_LINK.finditer(content):
            dest = unquote(match.group(1).strip())
            if not dest or dest.startswith(("#", "http://", "https://", "mailto:", "data:")):
                continue
            relative = dest.split("#", 1)[0].split("?", 1)[0]
            if not relative:
                continue
            checks += 1
            resolved = (file.parent / relative).resolve()
            if not resolved.is_relative_to(ROOT.resolve()) or not resolved.is_file():
                errors.append(f"{file.relative_to(ROOT)}: 无效链接 → {dest}")
    logic = ROOT / "01-信息图形数据逻辑"
    types = ROOT / "02-信息图形类型案例"
    cases = types / "案例库"
    counts = {
        "01 数据逻辑": len(list(logic.glob("[0-9][0-9]-*.md"))),
        "02 表现类型": len([p for p in types.glob("[0-9][0-9]-*.md") if p.name != "00-案例索引.md"]),
        "02 案例": len(list(cases.glob("CASE-*.md"))),
        "04 基础数据/统计": len(list((ROOT / "04-数据类型与基础统计图表").glob("[0-9][0-9]-*.md"))),
    }
    for label,expected in (("01 数据逻辑",5),("02 表现类型",16),("02 案例",29),("04 基础数据/统计",13)):
        if counts[label] < expected:
            errors.append(f"{label}: 数量不足；预期至少 {expected}，实际 {counts[label]}")
    print(f"Markdown 文件：{len(md_files)}；内部链接检查：{checks}；分类数量：{counts}")
    for item in errors:
        print("ERROR:",item,file=sys.stderr)
    if errors:
        print(f"校验失败：{len(errors)} 处")
        return 1
    print("校验通过：内部路径及 01 图片禁用规则无错误")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
