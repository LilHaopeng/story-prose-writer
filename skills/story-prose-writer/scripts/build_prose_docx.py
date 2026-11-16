#!/usr/bin/env python3
"""Compile clean novel chapter Markdown files into a book- or screen-styled DOCX."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

CJK_RE = re.compile(r"[\u4e00-\u9fff]")
EN_WORD_RE = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
SCENE_BREAK_RE = re.compile(r"^\s*(?:\*\s*\*\s*\*|-{3,}|⸻|✦\s*✦\s*✦)\s*$")
WORKBENCH_TOKEN_RE = re.compile(
    r"\b(?:RULE|INST|FAC|CON|SEED|WS|WCR|ARC|SEQ|EVT|CH|LOOP|WLOOP|CR)-\d{3}\b"
    r"|\[(?:待确认|待补充)\]|\{\{[^{}\n]+\}\}"
)
EXCLUDED_STEMS = {"写作状态", "00_文风与声口卡", "readme", "license"}

PAGE_SIZES_MM: dict[str, tuple[float, float, tuple[float, float, float, float]]] = {
    # (width_mm, height_mm, (top_mm, bottom_mm, left_mm, right_mm))
    "a4": (210.0, 297.0, (25.0, 23.0, 28.0, 28.0)),
    "b5": (176.0, 250.0, (22.0, 20.0, 23.0, 23.0)),
    "a5": (148.0, 210.0, (18.0, 17.0, 19.0, 19.0)),
}


def detect_lang(text: str, requested: str = "auto") -> str:
    if requested in ("zh", "en"):
        return requested
    cjk = len(CJK_RE.findall(text))
    en = len(EN_WORD_RE.findall(text))
    if cjk == 0 and en > 0:
        return "en"
    if en > cjk * 2 and en >= 30:
        return "en"
    return "zh"


def discover_chapters(chapters_dir: Path) -> list[Path]:
    if not chapters_dir.is_dir():
        raise ValueError(f"Chapters directory does not exist: {chapters_dir}")
    candidates: list[Path] = []
    for path in sorted(chapters_dir.glob("*.md")):
        stem_lower = path.stem.lower()
        if stem_lower in EXCLUDED_STEMS or stem_lower.startswith("00_"):
            continue
        candidates.append(path)
    if not candidates:
        raise ValueError(f"No chapter Markdown files found in: {chapters_dir}")
    return candidates


def parse_chapter(path: Path, default_index: int) -> tuple[str, list[tuple[str, str]]]:
    raw = path.read_text(encoding="utf-8-sig")
    lines = raw.splitlines()
    chapter_title = ""
    blocks: list[tuple[str, str]] = []
    para_buf: list[str] = []

    def flush_para() -> None:
        if para_buf:
            blocks.append(("paragraph", " ".join(para_buf)))
            para_buf.clear()

    for line in lines:
        s = line.strip()
        if not s:
            flush_para()
            continue
        if not chapter_title and not blocks and not para_buf and s.startswith("# "):
            chapter_title = re.sub(r"\s+#+\s*$", "", s[2:]).strip()
            continue
        if SCENE_BREAK_RE.match(s):
            flush_para()
            blocks.append(("scene_break", "* * *"))
            continue
        if re.match(r"^#{2,6}\s+", s):
            flush_para()
            sub = re.sub(r"^#{2,6}\s+|\s+#+\s*$", "", s).strip()
            blocks.append(("subheading", sub))
            continue
        para_buf.append(s)
    flush_para()

    if not chapter_title:
        chapter_title = path.stem.replace("_", " ") or f"Chapter {default_index}"
    return chapter_title, blocks


def set_style_fonts(style: Any, ascii_font: str, east_asia_font: str, qn: Any) -> None:
    style.font.name = ascii_font
    rfonts = style._element.get_or_add_rPr().get_or_add_rFonts()
    for slot in ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme", "csTheme"):
        rfonts.attrib.pop(qn("w:" + slot), None)
    rfonts.set(qn("w:ascii"), ascii_font)
    rfonts.set(qn("w:hAnsi"), ascii_font)
    rfonts.set(qn("w:cs"), ascii_font)
    rfonts.set(qn("w:eastAsia"), east_asia_font)


def add_inline_runs(paragraph: Any, text: str) -> None:
    pattern = re.compile(r"(\*\*[^*]+\*\*|\*[^*]+\*)")
    pos = 0
    for m in pattern.finditer(text):
        if m.start() > pos:
            paragraph.add_run(text[pos : m.start()])
        token = m.group(0)
        if token.startswith("**"):
            run = paragraph.add_run(token[2:-2])
            run.bold = True
        else:
            run = paragraph.add_run(token[1:-1])
            run.italic = True
        pos = m.end()
    if pos < len(text):
        paragraph.add_run(text[pos:])


def add_page_number_field(paragraph: Any, OxmlElement: Any, qn: Any) -> None:
    run = paragraph.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_end)


def build_prose_docx(
    chapter_paths: list[Path],
    out: Path,
    title: str,
    subtitle: str = "",
    author: str = "",
    preset: str = "book",
    page_size: str = "a4",
    lang: str = "auto",
    allow_workbench_tokens: bool = False,
) -> dict[str, Any]:
    try:
        from docx import Document
        from docx.enum.style import WD_STYLE_TYPE
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn
        from docx.shared import Inches, Mm, Pt, RGBColor
    except ImportError as exc:
        raise RuntimeError(
            "Building DOCX requires 'python-docx'. Install it via: python -m pip install python-docx"
        ) from exc

    resolved_sources = [p.resolve() for p in chapter_paths]
    if out.resolve() in resolved_sources:
        raise ValueError("Output path must not overwrite any source chapter file.")

    parsed_chapters: list[tuple[Path, str, list[tuple[str, str]]]] = []
    combined_sample: list[str] = []
    leaks: list[str] = []

    for idx, ch_path in enumerate(chapter_paths, start=1):
        ch_title, blocks = parse_chapter(ch_path, idx)
        parsed_chapters.append((ch_path, ch_title, blocks))
        for _, b_text in blocks:
            combined_sample.append(b_text)
            if not allow_workbench_tokens:
                for match in WORKBENCH_TOKEN_RE.finditer(b_text):
                    leaks.append(f"{ch_path.name}: {match.group(0)}")

    if leaks:
        preview = ", ".join(leaks[:5])
        raise ValueError(
            f"Detected internal workbench tokens in prose ({preview}). "
            "Clean chapter text before exporting or pass --allow-workbench-tokens."
        )

    full_body = "\n".join(combined_sample)
    resolved_lang = detect_lang(full_body, lang)
    cjk_total = len(CJK_RE.findall(full_body))
    en_total = len(EN_WORD_RE.findall(full_body))

    doc = Document()
    section = doc.sections[0]
    w_mm, h_mm, (top_mm, bot_mm, left_mm, right_mm) = PAGE_SIZES_MM[page_size]
    section.page_width = Mm(w_mm)
    section.page_height = Mm(h_mm)
    section.top_margin = Mm(top_mm)
    section.bottom_margin = Mm(bot_mm)
    section.left_margin = Mm(left_mm)
    section.right_margin = Mm(right_mm)
    section.different_first_page_header_footer = True

    if resolved_lang == "zh":
        body_ascii, body_ea = ("Georgia", "宋体") if preset == "book" else ("Segoe UI", "微软雅黑")
        head_ascii, head_ea = ("Georgia", "微软雅黑")
        body_pt = 11.5 if preset == "book" else 11.0
    else:
        body_ascii, body_ea = ("Georgia", "宋体") if preset == "book" else ("Segoe UI", "微软雅黑")
        head_ascii, head_ea = ("Georgia", "微软雅黑") if preset == "book" else ("Segoe UI", "微软雅黑")
        body_pt = 11.0

    ink_color = RGBColor(0x22, 0x22, 0x22)
    title_color = RGBColor(0x1B, 0x26, 0x3B)
    muted_color = RGBColor(0x5C, 0x67, 0x7D)

    normal = doc.styles["Normal"]
    set_style_fonts(normal, body_ascii, body_ea, qn)
    normal.font.size = Pt(body_pt)
    normal.font.color.rgb = ink_color

    novel_body = doc.styles.add_style("Novel Body", WD_STYLE_TYPE.PARAGRAPH)
    novel_body.base_style = normal
    set_style_fonts(novel_body, body_ascii, body_ea, qn)
    novel_body.font.size = Pt(body_pt)
    novel_body.font.color.rgb = ink_color
    pf = novel_body.paragraph_format
    pf.space_before = Pt(0)
    if preset == "book":
        pf.line_spacing = 1.48 if resolved_lang == "zh" else 1.38
        pf.space_after = Pt(1.5)
        pf.first_line_indent = Pt(body_pt * 2) if resolved_lang == "zh" else Inches(0.28)
    else:
        pf.line_spacing = 1.52 if resolved_lang == "zh" else 1.42
        pf.space_after = Pt(7.0)
        pf.first_line_indent = Pt(0)

    h1 = doc.styles["Heading 1"]
    set_style_fonts(h1, head_ascii, head_ea, qn)
    h1.font.size = Pt(16.5)
    h1.font.bold = True
    h1.font.color.rgb = title_color
    h1.paragraph_format.space_before = Pt(18)
    h1.paragraph_format.space_after = Pt(16)
    h1.paragraph_format.first_line_indent = Pt(0)
    h1.paragraph_format.keep_with_next = True
    h1.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER if preset == "book" else WD_ALIGN_PARAGRAPH.LEFT

    # Header & Footer
    hdr_p = section.header.paragraphs[0]
    hdr_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    hdr_run = hdr_p.add_run(title)
    hdr_run.font.size = Pt(9)
    hdr_run.font.color.rgb = muted_color

    ftr_p = section.footer.paragraphs[0]
    ftr_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_page_number_field(ftr_p, OxmlElement, qn)
    for r in ftr_p.runs:
        r.font.size = Pt(9)
        r.font.color.rgb = muted_color

    # Cover Page
    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_before = Pt(96)
    cover_title = doc.add_paragraph()
    cover_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cover_title.paragraph_format.first_line_indent = Pt(0)
    cover_title.paragraph_format.space_after = Pt(12)
    ct_run = cover_title.add_run(title)
    ct_run.bold = True
    ct_run.font.size = Pt(26)
    ct_run.font.color.rgb = title_color
    set_style_fonts(cover_title.style, head_ascii, head_ea, qn)

    if not subtitle:
        if len(parsed_chapters) == 1:
            subtitle = parsed_chapters[0][1]
        else:
            subtitle = (
                f"共 {len(parsed_chapters)} 章 · 约 {cjk_total:,} 字"
                if resolved_lang == "zh"
                else f"{len(parsed_chapters)} Chapters · {en_total:,} words"
            )
    cover_sub = doc.add_paragraph()
    cover_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cover_sub.paragraph_format.first_line_indent = Pt(0)
    cover_sub.paragraph_format.space_after = Pt(8)
    cs_run = cover_sub.add_run(subtitle)
    cs_run.font.size = Pt(12.5)
    cs_run.font.color.rgb = muted_color

    meta_parts = [p for p in (author.strip(), date.today().isoformat()) if p]
    cover_meta = doc.add_paragraph()
    cover_meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cover_meta.paragraph_format.first_line_indent = Pt(0)
    cover_meta.paragraph_format.space_before = Pt(36)
    cm_run = cover_meta.add_run(" · ".join(meta_parts))
    cm_run.font.size = Pt(10)
    cm_run.font.color.rgb = muted_color

    # Chapters
    total_paragraphs = 0
    for ch_idx, (_, ch_title, blocks) in enumerate(parsed_chapters):
        hp = doc.add_paragraph(style="Heading 1")
        hp.paragraph_format.page_break_before = True
        hp.add_run(ch_title)
        prev_was_break = True
        for kind, b_text in blocks:
            if kind == "scene_break":
                sp = doc.add_paragraph(style="Novel Body")
                sp.alignment = WD_ALIGN_PARAGRAPH.CENTER
                sp.paragraph_format.first_line_indent = Pt(0)
                sp.paragraph_format.space_before = Pt(8)
                sp.paragraph_format.space_after = Pt(8)
                sr = sp.add_run("* * *")
                sr.font.color.rgb = muted_color
                prev_was_break = True
            elif kind == "subheading":
                sub_p = doc.add_paragraph(style="Novel Body")
                sub_p.paragraph_format.first_line_indent = Pt(0)
                sub_p.paragraph_format.space_before = Pt(10)
                sub_p.paragraph_format.space_after = Pt(4)
                sub_p.paragraph_format.keep_with_next = True
                sr = sub_p.add_run(b_text)
                sr.bold = True
                prev_was_break = True
            else:
                bp = doc.add_paragraph(style="Novel Body")
                if preset == "book" and resolved_lang == "en" and prev_was_break:
                    # Standard English book typography omits indent on first para after heading/break
                    bp.paragraph_format.first_line_indent = Pt(0)
                add_inline_runs(bp, b_text)
                total_paragraphs += 1
                prev_was_break = False

    out.parent.mkdir(parents=True, exist_ok=True)
    doc.core_properties.title = title
    doc.core_properties.author = author
    doc.core_properties.subject = subtitle
    doc.save(out)

    return {
        "output": str(out.resolve()),
        "title": title,
        "language": resolved_lang,
        "preset": preset,
        "page_size": page_size,
        "chapters": len(parsed_chapters),
        "paragraphs": total_paragraphs,
        "cjk_chars": cjk_total,
        "en_words": en_total,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="将单章或多章小说正文 Markdown 编译为书籍沉浸版（book）或屏幕轻读版（screen）DOCX。"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--source", type=Path, help="Single chapter Markdown file")
    group.add_argument("--chapters-dir", type=Path, help="Directory of chapter Markdown files")
    parser.add_argument("--out", required=True, type=Path, help="Output .docx path")
    parser.add_argument("--title", default="", help="Book title (defaults to first chapter or folder name)")
    parser.add_argument("--subtitle", default="", help="Optional cover subtitle")
    parser.add_argument("--author", default="", help="Optional author name on cover")
    parser.add_argument(
        "--preset",
        choices=("book", "screen"),
        default="book",
        help="Typography preset: book (serif + indent) or screen (clean spacing, no indent)",
    )
    parser.add_argument(
        "--page-size",
        choices=("a4", "b5", "a5"),
        default="a4",
        help="Page geometry (default: a4)",
    )
    parser.add_argument(
        "--lang",
        choices=("auto", "zh", "en"),
        default="auto",
        help="Typography language mode (default: auto)",
    )
    parser.add_argument(
        "--allow-workbench-tokens",
        action="store_true",
        help="Allow internal IDs like RULE-001 or [待确认] in output without failing",
    )
    args = parser.parse_args()

    try:
        if args.source:
            if not args.source.is_file():
                parser.error(f"Source file not found: {args.source}")
            chapters = [args.source]
            inferred_title = args.title.strip() or args.source.stem.replace("_", " ")
        else:
            chapters = discover_chapters(args.chapters_dir)
            inferred_title = args.title.strip() or args.chapters_dir.parent.name or "小说正文"

        result = build_prose_docx(
            chapter_paths=chapters,
            out=args.out,
            title=inferred_title,
            subtitle=args.subtitle,
            author=args.author,
            preset=args.preset,
            page_size=args.page_size,
            lang=args.lang,
            allow_workbench_tokens=args.allow_workbench_tokens,
        )
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
