![Story Prose Writer](assets/prose-writer-hero.png)

# Story Prose Writer · 小说正文写作

[简体中文](README.md) | **English**

An agent skill for writing natural, well-paced fiction prose from existing worldbuilding, outlines, and author intent—covering word-budget planning, voice calibration, chapter drafting, revision, continuity auditing, and book-ready DOCX compilation. Current version: **v1.1.0**.

By default, the skill writes in **Simplified Chinese (`简体中文`)**, tuned for native Chinese narrative flow and visual breathing room. You can explicitly request **English**, **Traditional Chinese**, or any other language at any point—the skill switches its prose craft rules, dialogue conventions, linter mode, and book typography to match your chosen language natively.

## Key Capabilities

- **Outline Submersion & Veteran POV**: Dissolves structural outline beats (`Goal / Choice / Cost`) beneath tangible everyday actions and subtext-rich dialogue instead of marching through mechanical plot checklists. Characters native to the world treat its rules as mundane reality—showing friction and anomalies rather than lecturing the reader with exposition.
- **Natural Cadence Without Over-Correction**: Pairs anti-cliché discipline with sensory rationing and free indirect discourse—avoiding both generic LLM summaries and hyper-staged micro-gestures on every line of dialogue.
- **Voice Tuning Fork Against Drift**: Combines an 8-style preset matrix with web-verified custom style deconstruction, embedding a **150–250 word approved prose sample + signature raw character lines** directly inside `00_文风与声口卡.md` so Chapter 30 still sounds like Chapter 1.
- **Visual Breathing & Page Aesthetics**: Alternates full narrative blocks, crisp 1–2 line beats, bare rapid-fire dialogue runs (without repetitive speech tags), and clean scene breaks to eliminate monotonous "walls of gray blocks" and inline scare-quote clutter.
- **Scoped Context & Continuity Guard**: Loads only active character states, relevant foreshadowing threads, and triggered world rules per chapter; strictly separates author truth from POV knowledge and syncs handoff ledgers from verified chapter events.
- **Book & Screen DOCX Export**: Compiles single chapters or full manuscripts into either a **print-style `book` edition** (serif typography, first-line indent, centered `* * *` scene breaks) or a **clean `screen` edition** (unindented spaced paragraphs), while blocking accidental internal ID leaks.

## Companion Workflow

Use this skill standalone with your own notes, or pair it with its two companion skills for an end-to-end studio pipeline:

1. [Story World Architect](https://github.com/LilHaopeng/story-world-architect): Builds causally grounded worlds, social ecosystems, and hands off canon rules plus everyday vernacular textures.
2. [Story Outline Architect](https://github.com/LilHaopeng/story-outline-architect): Designs Story DNA, multi-track arcs, sequences, and concrete chapter outlines.
3. **Story Prose Writer**: Turns canon and chapter outlines into natural, resonant chapters with cross-chapter continuity.

## Installation

1. **Via `skill-installer` (Codex, etc.)**
   ```text
   $skill-installer Install skills/story-prose-writer from https://github.com/LilHaopeng/story-prose-writer
   ```
2. **Manual Local Installation (Antigravity / Claude Code / Codex / Cursor)**
   Clone this repository and copy `skills/story-prose-writer/` into your client's skills directory:
   - **Antigravity**: `~/.gemini/config/skills/story-prose-writer`
   - **Claude Code**: `~/.claude/skills/story-prose-writer`
   - **Codex**: `~/.codex/skills/story-prose-writer` or `~/.agents/skills/story-prose-writer`
   - **Cursor**: `~/.cursor/skills/story-prose-writer`

Core scripts (`init_prose_project.py`, `estimate_word_count.py`, `lint_prose.py`) use only the Python 3.10+ standard library. To export `.docx` manuscripts with `build_prose_docx.py`, install `python -m pip install -r requirements.txt`.

## Quick Start

**Writing in English (explicitly selected)**:

```text
$story-prose-writer
Write Chapter 2 in English (~3,200 words) from our Chapter 1 handoff and Chapter 2 outline.
Keep the close-third noir voice, submerge the negotiation stakes beneath the harbour inspection scene, and vary paragraph pacing for clean page rhythm.
```

**Default Simplified Chinese**:

```text
$story-prose-writer
请根据现有世界观、第一章交接卡和第二章细纲续写第二章，单章约 3500 字，保持市井冷硬文风与页面呼吸感。
```

## Helper Scripts

| Script | Purpose |
|---|---|
| `init_prose_project.py` | Non-destructively scaffolds `正文/`, `追踪/`, `交付/`, voice card (with tuning-fork slot), and chapter handoff templates (`--lang`, `--dry-run`). |
| `estimate_word_count.py` | Inventories existing chapter outlines and reports compact / standard / rich budget ranges alongside custom chapter targets. |
| `lint_prose.py` | Bilingual (`--lang auto\|zh\|en`) contextual craft & page-rhythm linter: separates dialogue from narration, flags LLM rhetorical clichés, uniform paragraph walls, local monotonous sentence runs, lexical echoes, pronoun/adverb density, and scare-quote clutter. |
| `build_prose_docx.py` | Compiles single or multiple chapter Markdown files into `book` or `screen` `.docx` editions (`--page-size a4\|b5\|a5`, `--lang auto\|zh\|en`) while guarding against workbench ID leaks. |

Example commands:

```bash
python skills/story-prose-writer/scripts/init_prose_project.py --root <project-root> --title "Night Harbour" --lang English
python skills/story-prose-writer/scripts/estimate_word_count.py --root <project-root> --total-chapters 24 --target-words 3200
python skills/story-prose-writer/scripts/lint_prose.py --file <chapter.md> --lang en --target-words 3200
python skills/story-prose-writer/scripts/build_prose_docx.py --chapters-dir <project-root>/正文 --out <project-root>/交付/Night_Harbour.docx --title "Night Harbour" --preset book --lang en
```

Run unit tests:

```bash
python -B -m unittest discover -s tests -v
```

## Reference Guides

- [Artifact Contract & Handoffs](skills/story-prose-writer/references/artifact-contract.md)
- [Word-Count Estimation & Scaling](skills/story-prose-writer/references/word-count-and-scaling.md)
- [Style Matrix, Native Craft & Page Aesthetics](skills/story-prose-writer/references/style-and-anti-ai.md)
- [Long-Form Execution & Outline Submersion](skills/story-prose-writer/references/long-form-execution.md)
- [Canon Audit & Dual-Preset DOCX Delivery](skills/story-prose-writer/references/audit-and-continuity.md)

## Privacy & License

All helper scripts read and write local files strictly within your workspace and never upload manuscripts. Released under the [MIT License](LICENSE) (Copyright © 2026 LilHaopeng).
