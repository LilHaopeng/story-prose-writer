#!/usr/bin/env python3
"""Report potentially noteworthy prose patterns for contextual review, without rewriting."""

from __future__ import annotations

import argparse
import json
import re
import statistics
from dataclasses import asdict, dataclass
from pathlib import Path


CJK_RE = re.compile(r"[\u4e00-\u9fff]")
BULLET_LINE_RE = re.compile(r"^\s*(?:[-*•]|\d+\.)\s+.+$")
SUBHEADING_RE = re.compile(r"^\s*#{2,6}\s+.+$")
SENTENCE_SPLIT_RE = re.compile(r"[。！？!?…]+")

# Heuristic patterns: occurrences are review candidates, not proven problems.
FORBIDDEN_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    (
        "ai_contrast_not_but",
        re.compile(r"不是[^，。！？；\n]{1,30}[，,]?\s*而是"),
        "检测到「不是……而是……」AI二元解释句式，建议直接写具体动作或事物本身，删去否定对比。",
    ),
    (
        "ai_contrast_rather_than",
        re.compile(r"与其说[^，。！？；\n]{1,30}[，,]?\s*不如说"),
        "检测到「与其说……不如说……」AI思辨腔，建议改为人物直观感受或动作细节。",
    ),
    (
        "ai_not_only_but_also",
        re.compile(r"这?不仅仅[是是一场次][^，。！？；\n]{1,30}[，,]?\s*更[是是一场次]"),
        "检测到「这不仅仅是……更是……」拔高汇报腔，建议删除旁白拔高，用事件后果体现分量。",
    ),
    (
        "ai_era_opening",
        re.compile(r"在(?:这个|那片|这座)[^，。！？\n]{2,20}的(?:时代|世界|大陆|社会|年代)里"),
        "检测到「在这个……的时代/世界里」纪录片解说腔，建议直接从眼前器物、天气或人物动作切入。",
    ),
    (
        "ai_named_metaphor",
        re.compile(r"名为[「“\"']?[^」”\"'，。！？\n]{1,8}[」”\"']?的(?:种子|火焰|毒蛇|情绪|野心|恐惧|嫉妒|枷锁|深渊)"),
        "检测到「名为XX的种子/火焰/情绪」翻译腔隐喻，建议改为具体生理反应或动作。",
    ),
    (
        "ai_pie_chart_expression",
        re.compile(r"三分[^，。！？\n]{1,8}[，、\s]*三分[^，。！？\n]{1,8}[，、\s]*(?:四分|还有)"),
        "检测到「三分……三分……四分……」扇形统计图式神态套话，建议只保留一个最核心的动作细节。",
    ),
    (
        "ai_wheel_of_fate",
        re.compile(r"命运的齿轮(?:开始|悄然|在这一刻)?转动"),
        "检测到「命运的齿轮开始转动」陈腐总结套话，建议删除，让章末停在具体悬念或动作上。",
    ),
]

# High-frequency AI physical/emotional clichés (warn on any occurrence)
CLICHE_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    (
        "cliche_smirk_arc",
        re.compile(r"嘴角(?:勾起|扬起|扯出)(?:一抹|一丝)?[^，。！？\n]{0,8}弧度"),
        "高频AI套话「嘴角勾起一抹弧度」，建议换为具体动作（如：嗤了一声、把茶盏推开、没接话）。",
    ),
    (
        "cliche_eye_flash",
        re.compile(r"眼(?:底|中|眸中|里)(?:闪过|掠过|划过)(?:一丝|一抹)(?:不易察觉的)?"),
        "高频AI套话「眼底闪过一丝（不易察觉的）……」，限知视角下建议改为可观察的肢体停顿或视线落点。",
    ),
    (
        "cliche_knuckles_white",
        re.compile(r"(?:骨节|指节)(?:捏得|攥得|有些)?发白|指甲(?:深深)?(?:嵌进|掐进|刺入)(?:掌心|肉里)"),
        "高频AI生理套话「骨节发白/指甲嵌进肉里」，建议改为贴合角色身份的手部物件交互。",
    ),
    (
        "cliche_air_froze",
        re.compile(r"空气(?:仿佛|似乎)?(?:在这一刻)?(?:凝固|冻结)了"),
        "高频AI氛围套话「空气仿佛凝固了」，建议改写为具体的环境声响中断或旁人动作定格。",
    ),
    (
        "cliche_pupil_earthquake",
        re.compile(r"瞳孔(?:猛地|骤然|剧烈)?(?:一缩|地震|收缩)"),
        "高频AI套话「瞳孔猛地一缩/地震」，建议改为具体的身体后撤、失手或呼吸停滞。",
    ),
    (
        "cliche_in_some_sense",
        re.compile(r"某种意义上(?:来说|而言)?|从某种程度上"),
        "检测到「某种意义上/某种程度上」论文解释词，小说叙事中建议直接删去。",
    ),
]


@dataclass
class LintIssue:
    level: str  # "error" or "warning"
    code: str
    line: int
    excerpt: str
    suggestion: str


def analyze_file(
    path: Path, target_words: int | None = None, tolerance: float = 0.15
) -> tuple[list[LintIssue], dict[str, int | float]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    issues: list[LintIssue] = []

    body_lines: list[tuple[int, str]] = []
    for idx, raw_line in enumerate(lines, start=1):
        stripped = raw_line.strip()
        if not stripped:
            continue
        if not body_lines and stripped.startswith("# "):
            continue
        if SUBHEADING_RE.match(raw_line):
            issues.append(
                LintIssue(
                    "warning",
                    "subheading_in_prose",
                    idx,
                    stripped[:50],
                    "检测到 Markdown 小标题；核对是否为有意采用的章节结构。",
                )
            )
            continue
        if BULLET_LINE_RE.match(raw_line):
            issues.append(
                LintIssue(
                    "warning",
                    "bullet_point_in_prose",
                    idx,
                    stripped[:50],
                    "检测到疑似列表；核对是否为人物文书、创作格式或其他有意表达。",
                )
            )
        body_lines.append((idx, stripped))

    body_text = "\n".join(line for _, line in body_lines)
    cjk_count = len(CJK_RE.findall(body_text))
    non_ws_count = len(re.sub(r"\s+", "", body_text))

    sentence_lengths: list[int] = []
    long_paragraphs = 0

    for line_no, para in body_lines:
        para_cjk = len(CJK_RE.findall(para))
        if para_cjk > 180:
            long_paragraphs += 1
            issues.append(
                LintIssue(
                    "warning",
                    "paragraph_too_long",
                    line_no,
                    para[:45] + "...",
                    f"单段约 {para_cjk} 个基本汉字；请按叙事和阅读需要判断是否拆段。",
                )
            )

        for seg in SENTENCE_SPLIT_RE.split(para):
            seg_cjk = len(CJK_RE.findall(seg))
            if seg_cjk > 0:
                sentence_lengths.append(seg_cjk)

        for code, pattern, msg in FORBIDDEN_PATTERNS:
            for m in pattern.finditer(para):
                issues.append(
                    LintIssue("warning", code, line_no, para[:100], "疑似匹配「" + m.group(0) + "」；结合对白、叙事语境及人物声口人工判断，不必机械删改。")
                )

        for code, pattern, msg in CLICHE_PATTERNS:
            for m in pattern.finditer(para):
                issues.append(
                    LintIssue("warning", code, line_no, para[:100], "疑似匹配「" + m.group(0) + "」；结合上下文及使用频率人工判断。")
                )

    avg_sent = round(statistics.mean(sentence_lengths), 1) if sentence_lengths else 0.0
    stdev_sent = (
        round(statistics.stdev(sentence_lengths), 1)
        if len(sentence_lengths) >= 2
        else 0.0
    )

    if len(sentence_lengths) >= 10 and stdev_sent < 5.5:
        issues.append(
            LintIssue(
                "warning",
                "low_sentence_burstiness",
                1,
                f"句长标准差仅 {stdev_sent}（均长 {avg_sent} 字）",
                "这只是句长统计，不能证明 AI 写作或文学质量；请按场景节奏判断。",
            )
        )

    if target_words and target_words > 0:
        min_w = int(target_words * (1.0 - tolerance))
        max_w = int(target_words * (1.0 + tolerance))
        if cjk_count < min_w:
            issues.append(
                LintIssue(
                    "warning",
                    "word_count_under_target",
                    1,
                    f"当前汉字数 {cjk_count} < 目标下限 {min_w}（目标 {target_words}）",
                    "按当前汉字统计口径低于目标；结合章节目标人工判断，不应机械填充。",
                )
            )
        elif cjk_count > max_w:
            issues.append(
                LintIssue(
                    "warning",
                    "word_count_over_target",
                    1,
                    f"当前汉字数 {cjk_count} > 目标上限 {max_w}（目标 {target_words}）",
                    "按当前汉字统计口径高于目标；结合内容、节奏和目标人工判断。",
                )
            )

    metrics: dict[str, int | float] = {
        "cjk_chars": cjk_count,
        "non_whitespace_chars": non_ws_count,
        "paragraphs": len(body_lines),
        "long_paragraphs": long_paragraphs,
        "sentences": len(sentence_lengths),
        "avg_sentence_cjk": avg_sent,
        "sentence_burstiness_stdev": stdev_sent,
        "errors": sum(1 for i in issues if i.level == "error"),
        "warnings": sum(1 for i in issues if i.level == "warning"),
    }
    return issues, metrics


def main() -> int:
    parser = argparse.ArgumentParser(
        description="扫描候选文风和格式提醒；匹配并不证明有问题，不会自动修改正文。"
    )
    parser.add_argument("--file", required=True, help="Path to chapter markdown file")
    parser.add_argument(
        "--target-words", type=int, default=0, help="Optional target CJK word count"
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=0.15,
        help="Allowed word count deviation ratio (default 0.15)",
    )
    parser.add_argument("--ignore", action="append", default=[], metavar="CODE", help="忽略指定规则，可重复或使用逗号分隔")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    if args.target_words < 0:
        parser.error("--target-words 不能为负数。")
    if not 0 <= args.tolerance <= 1:
        parser.error("--tolerance 必须在 0 到 1 之间。")
    path = Path(args.file).expanduser().resolve()
    if not path.is_file():
        parser.error(f"File not found: {path}")

    issues, metrics = analyze_file(
        path, target_words=args.target_words or None, tolerance=args.tolerance
    )

    ignored = {code.strip() for group in args.ignore for code in group.split(",") if code.strip()}
    issues = [issue for issue in issues if issue.code not in ignored]
    metrics["errors"] = sum(issue.level == "error" for issue in issues)
    metrics["warnings"] = sum(issue.level == "warning" for issue in issues)

    if args.json:
        print(
            json.dumps(
                {
                    "file": str(path),
                    "notice": "匹配仅供复核；字数按正文 U+4E00–U+9FFF 基本汉字统计，排除标题，可能与平台统计不同。",
                    "ignored_codes": sorted(ignored),
                    "metrics": metrics,
                    "issues": [asdict(i) for i in issues],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(f"file={path}")
        print("匹配仅供复核；字数按正文 U+4E00–U+9FFF 基本汉字统计，排除标题，可能与平台统计不同。")
        print(
            "metrics "
            + " ".join(f"{k}={v}" for k, v in metrics.items())
        )
        for issue in issues:
            print(
                f"[{issue.level.upper()}] line {issue.line} ({issue.code}): "
                f"「{issue.excerpt}」 -> {issue.suggestion}"
            )
    return 1 if metrics["errors"] > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
