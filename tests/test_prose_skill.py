"""Regression tests for story-prose-writer scripts, bilingual linting, and DOCX export."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "story-prose-writer"
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_prose_docx import build_prose_docx
from lint_prose import analyze_file


class ProseSkillTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="story-prose-test-")
        self.folder = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_markdown_links_resolve(self) -> None:
        md_files = [ROOT / "README.md", ROOT / "README_EN.md", SKILL / "SKILL.md", *SKILL.glob("references/*.md")]
        link_re = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
        for md in md_files:
            self.assertTrue(md.is_file(), f"Missing {md}")
            text = md.read_text(encoding="utf-8")
            for target in link_re.findall(text):
                if target.startswith(("http://", "https://", "#")):
                    continue
                clean = target.split("#", 1)[0]
                resolved = (md.parent / clean).resolve()
                self.assertTrue(resolved.exists(), f"Broken link in {md}: {target} -> {resolved}")

    def test_initializer_preserves_existing_and_records_language(self) -> None:
        project = self.folder / "proj"
        cmd = [
            sys.executable, "-B", str(SCRIPTS / "init_prose_project.py"),
            "--root", str(project), "--title", "夜航船", "--lang", "English",
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True, encoding="utf-8")
        voice = (project / "正文" / "00_文风与声口卡.md").read_text(encoding="utf-8")
        self.assertIn("写作语言：English", voice)
        self.assertIn("定调原声切片", voice)
        custom = "# 自定义状态\n"
        (project / "正文" / "写作状态.md").write_text(custom, encoding="utf-8")
        subprocess.run(cmd, check=True, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual((project / "正文" / "写作状态.md").read_text(encoding="utf-8"), custom)

    def test_chinese_linter_surfaces_specific_craft_suggestions_and_spares_dialogue(self) -> None:
        chapter = self.folder / "ch1.md"
        chapter.write_text(
            "# 第001章 栈桥\n\n"
            "“我不是怕死，而是不想白白送命！”陈三把烟锅往鞋底一磕。\n\n"
            "这不是一场普通的查账，而是一次生死试探。他嘴角勾起一抹冰冷的弧度，仿佛在证明自己的镇定。\n",
            encoding="utf-8",
        )
        issues, metrics = analyze_file(chapter)
        self.assertEqual(metrics["language"], "zh")
        codes = [i.code for i in issues]
        # Spoken dialogue contrast should NOT trigger ai_contrast_not_but on line 3
        contrast_lines = [i.line for i in issues if i.code == "ai_contrast_not_but"]
        self.assertEqual(contrast_lines, [5])
        self.assertIn("cliche_smirk_arc", codes)
        self.assertIn("ai_explanatory_tail", codes)
        # Specific craft advice `msg` must be included rather than discarded
        smirk_issue = next(i for i in issues if i.code == "cliche_smirk_arc")
        self.assertIn("高频神态套话", smirk_issue.suggestion)

    def test_uniform_blocks_echo_and_scare_quotes_detected(self) -> None:
        para = (
            "推开栈桥边的旧木门，潮湿的海风裹着咸腥味扑面而来，微微晃动的马灯把桌上的账册照得发黄，"
            "众人站在屋檐底下看着雨丝落下，谁也没有先开口说话，只是微微皱眉盯着那本厚厚的旧账册。"
        )
        blocks = "\n\n".join([para] * 6)
        scare = (
            "他维持着表面的“体面”，遵循着所谓的“规矩”，接受了这种“默契”，"
            "守住了最后的“底线”，保住了手里的“筹码”，也看透了对方的“诚意”。"
        )
        chapter = self.folder / "ch2.md"
        chapter.write_text(f"# 第002章 旧账\n\n{blocks}\n\n{scare}\n", encoding="utf-8")
        issues, metrics = analyze_file(chapter)
        codes = {i.code for i in issues}
        self.assertIn("uniform_paragraph_blocks", codes)
        self.assertIn("lexical_echo", codes)
        self.assertIn("scare_quote_clutter", codes)
        self.assertGreaterEqual(int(metrics["uniform_block_streaks"]), 1)

    def test_english_prose_mode_and_cliches(self) -> None:
        chapter = self.folder / "ch_en.md"
        chapter.write_text(
            "# Chapter 1: The Pier\n\n"
            "It was not a simple inspection, it was a trap. A shiver ran down his spine as he stepped onto the dock, "
            "a testament to the palpable tension between the two crews.\n\n"
            '"Get the lantern," Mara said.\n\n'
            '"Already lit."\n',
            encoding="utf-8",
        )
        issues, metrics = analyze_file(chapter, target_words=45, tolerance=0.5, lang="auto")
        self.assertEqual(metrics["language"], "en")
        self.assertEqual(metrics["bare_dialogue_paragraphs"], 1)
        codes = {i.code for i in issues}
        self.assertIn("en_ai_not_but", codes)
        self.assertIn("en_ai_testament", codes)
        self.assertIn("en_cliche_breath_held", codes)

    def test_build_prose_docx_book_screen_and_leak_guard(self) -> None:
        chapters_dir = self.folder / "正文"
        chapters_dir.mkdir()
        (chapters_dir / "写作状态.md").write_text("# 状态\n", encoding="utf-8")
        (chapters_dir / "00_文风与声口卡.md").write_text("# 声口\n", encoding="utf-8")
        ch1 = chapters_dir / "第001章_夜雨.md"
        ch1.write_text(
            "# 第001章 夜雨\n\n"
            "栈桥上的风停了。老周把灯笼挂上铁钩，转身进了货仓。\n\n"
            "* * *\n\n"
            "“账对上了？”\n\n"
            "“差三页。”\n",
            encoding="utf-8",
        )
        out_book = self.folder / "交付" / "book.docx"
        res = build_prose_docx([ch1], out_book, title="旧港夜航", preset="book", page_size="b5")
        self.assertTrue(out_book.is_file())
        self.assertEqual(res["chapters"], 1)
        self.assertEqual(res["preset"], "book")

        # Workbench leak must fail cleanly unless explicitly allowed
        leaked = chapters_dir / "第002章_漏底.md"
        leaked.write_text("# 第002章\n\n这里不小心留下了 RULE-001 标记。\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            build_prose_docx([ch1, leaked], self.folder / "交付" / "bad.docx", title="旧港夜航")


if __name__ == "__main__":
    unittest.main()
