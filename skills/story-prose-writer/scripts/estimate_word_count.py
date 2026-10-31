#!/usr/bin/env python3
"""Conservative word-budget inventory for structured chapter outlines.

Figures are planning ranges, not a measurement of narrative complexity. A book
projection requires an explicitly supplied total chapter count.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

TIERS = {
    "compact": {"label": "精简档", "range": (2000, 2500)},
    "standard": {"label": "标准档", "range": (3000, 4000)},
    "rich": {"label": "丰满档", "range": (4500, 6000)},
}
FIELD_RE = re.compile(r"^\s*[-*]\s+(?:\*\*)?([^：:]+?)(?:\*\*)?\s*[：:]\s*(.*?)\s*$")
WORLD_ID_RE = re.compile(r"\b(?:RULE|INST|FAC|CON|SEED|WS|REG|CHAR|WLOOP)-\d{3}\b", re.I)


def safe_root(raw: str) -> Path:
    root = Path(raw).expanduser().resolve()
    if root.parent == root:
        raise ValueError("拒绝扫描文件系统根目录。")
    if not root.is_dir():
        raise ValueError(f"项目目录不存在或不是目录: {root}")
    return root


def parse_explicit_word_target(raw: str) -> list[int] | None:
    """Read a simple target, retaining a supplied range instead of averaging it."""
    nums = [int(n.replace(",", "")) for n in re.findall(r"\d+(?:,\d{3})*", raw)]
    nums = [n for n in nums if 300 <= n <= 50000]
    if not nums:
        return None
    return [min(nums), max(nums)]


def inspect_chapter(path: Path, root: Path) -> dict:
    text = path.read_text(encoding="utf-8-sig")
    fields = {}
    for line in text.splitlines():
        match = FIELD_RE.match(line)
        if match:
            fields[re.sub(r"[\s*`_]+", "", match.group(1)).lower()] = match.group(2).strip()
    target = parse_explicit_word_target(fields.get("字数目标", ""))
    return {
        "chapter_id": fields.get("id", path.stem),
        "path": path.relative_to(root).as_posix(),
        "explicit_target_range": target,
        "numbered_lines": len(re.findall(r"^\s*\d+[.、]\s*.+$", text, re.M)),
        "world_refs": len(set(m.group(0).upper() for m in WORLD_ID_RE.finditer(text))),
        "note": "编号行及设定引用仅作盘点，不代表情节点数量、冲突密度或文学复杂度。",
    }


def scale(n: int, pair: tuple[int, int]) -> list[int]:
    return [n * pair[0], n * pair[1]]


def main() -> int:
    p = argparse.ArgumentParser(description="盘点已找到的细纲，按档位粗估；全书章数须明确提供。")
    p.add_argument("--root", required=True, help="小说项目根目录")
    p.add_argument("--total-chapters", type=int, help="已知并确认的全书计划章数；不自动猜测")
    p.add_argument("--target-words", type=int, help="用户指定的每章目标汉字数，另列预算并逐章比较")
    p.add_argument("--json", action="store_true", help="JSON 输出")
    args = p.parse_args()
    try:
        root = safe_root(args.root)
    except ValueError as exc:
        p.error(str(exc))
    if args.total_chapters is not None and args.total_chapters < 1:
        p.error("--total-chapters 必须为正整数。")
    if args.target_words is not None and args.target_words < 1:
        p.error("--target-words 必须为正整数。")
    outline = root / "大纲"
    if not outline.is_dir():
        p.error(f"未找到标准大纲目录: {outline}；请先识别项目材料或指定正确根目录。")
    arcs = sorted((outline / "故事弧").glob("ARC-*.md"))
    seqs = sorted((outline / "剧情段").glob("SEQ-*.md"))
    paths = sorted(outline.glob("细纲_第*.md"))
    scenes = sorted((outline / "场景").glob("CH-*.md"))
    if args.total_chapters is not None and args.total_chapters < len(paths):
        p.error("--total-chapters 小于找到的细纲文件数；请先检查重复细纲或总章数。")
    chapters = [inspect_chapter(path, root) for path in paths]
    covered = len(chapters)
    remaining = args.total_chapters - covered if args.total_chapters is not None else None
    tiers = {}
    for key, tier in TIERS.items():
        pair = tier["range"]
        tiers[key] = {
            "label": tier["label"], "per_chapter_words": list(pair),
            "detailed_chapters_range": scale(covered, pair),
            "remaining_planned_chapters_range": scale(remaining, pair) if remaining is not None else None,
            "total_planned_range": scale(args.total_chapters, pair) if args.total_chapters is not None else None,
        }
    budget = None
    if args.target_words is not None:
        budget = {
            "source": "--target-words", "per_chapter": args.target_words,
            "detailed_chapters": covered * args.target_words,
            "remaining_planned_chapters": remaining * args.target_words if remaining is not None else None,
            "total_planned": args.total_chapters * args.target_words if args.total_chapters is not None else None,
            "note": "这是指定目标的预算，不是对大纲能否承载该字数的判断；请逐章人工审阅。",
        }
    summary = {
        "root": str(root),
        "counts": {"arcs": len(arcs), "sequences": len(seqs), "chapter_outline_files": covered,
                   "scene_files": len(scenes), "total_planned_chapters": args.total_chapters,
                   "total_chapters_source": "--total-chapters" if args.total_chapters is not None else None,
                   "remaining_planned_chapters": remaining},
        "coverage_note": "只识别标准文件名；文件数不一定等于实际章节数，请核对重复、遗漏和非标准文件。未明确提供总章数时，不推断全书总数。",
        "estimation_note": "各档均为章数乘固定区间的预算，并非冲突密度测量；请审阅每章承载力。章节自带目标另列，未自动覆盖档位。",
        "tiers": tiers, "user_target_budget": budget, "chapters": chapters,
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"项目: {root}")
        print(f"已找到 {covered} 个细纲文件、{len(arcs)} 个故事弧、{len(seqs)} 个剧情段、{len(scenes)} 个场景文件。")
        print(f"计划总章数: {args.total_chapters if args.total_chapters is not None else '未知（未提供）'}；未细化章节: {remaining if remaining is not None else '未知'}。")
        print(summary["coverage_note"])
        print(summary["estimation_note"])
        for tier in tiers.values():
            a, b = tier["detailed_chapters_range"]
            print(f"{tier['label']}：已找到细纲 {a:,}–{b:,} 字", end="")
            if tier["remaining_planned_chapters_range"] is not None:
                c, d = tier["remaining_planned_chapters_range"]
                e, f = tier["total_planned_range"]
                print(f"；其余计划章节 {c:,}–{d:,} 字；合计 {e:,}–{f:,} 字")
            else:
                print("；全书范围未知")
        if budget:
            print(f"用户目标：{args.target_words:,} 字/章；已找到细纲预算 {budget['detailed_chapters']:,} 字；全书预算 " + (f"{budget['total_planned']:,} 字" if budget['total_planned'] is not None else "未知"))
            print(budget["note"])
        for chapter in chapters:
            print(f"  {chapter['chapter_id']} | {chapter['path']} | 细纲字数目标={chapter['explicit_target_range'] or '未标明'} | 编号行={chapter['numbered_lines']} | 设定引用={chapter['world_refs']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
