#!/usr/bin/env python3
"""Initialize prose writing directories and tracking files non-destructively."""

from __future__ import annotations

import argparse
from pathlib import Path


def safe_root(raw: str) -> Path:
    root = Path(raw).expanduser().resolve()
    if root.parent == root:
        raise ValueError("Refusing to initialize a filesystem root.")
    return root


def templates(title: str, lang: str = "简体中文") -> dict[str, str]:
    return {
        "正文/写作状态.md": f"""# 正文写作状态

- 项目名：{title}
- 写作语言：{lang}
- 当前工作模式：estimate
- 绑定的大纲版本：[待确认]
- 绑定的世界观版本：[待确认]
- 字数配置档位：[待确认；可自定义]
- 单章目标规模：[待确认]
- 全书预估总规模：[待确认]
- 当前已锁定文风：见 `正文/00_文风与声口卡.md`（状态：draft）
- 已完成章节：无
- 当前累计净规模：0
- 下一待写章节：CH-001
- 待确认事项：字数档位与开篇试写文风确认
""",
        "正文/00_文风与声口卡.md": f"""# 文风与声口卡

- 项目名：{title}
- 状态：draft
- 写作语言：{lang}
- 模式来源：预设方向 / 自定义风格 / 用户提供样本 [待确认]
- 基底与调整方向：[待试写确认]
- 文风资料及依据：
  - 研究状态：[待确认：已联网核实 / 用户提供 / 暂拟未核实]
  - 参考资料和链接：[待填写；未知时不编造来源]
  - 核心叙事技法提炼：[待填写]
- 叙事视角与信息边界：[依用户、世界观与大纲确认]
- 叙述距离：[待试写确认]
- 句法与页面呼吸节奏：[长短段错落、裸对白留白、避免连续等高豆腐块段落]
- 感官锚点与世界日常词表：[每场精选 1–2 处核心感官；记录本作常用称谓、器物与行话]
- 本书修辞禁区：[禁止照搬技能示例动作；严控碎引号、代词堆叠与句尾解释尾巴]

## 定调原声切片（Voice Tuning Fork · 每次动笔必读）

> 试写确认后，在此粘贴 150–250 字经认可的本书标杆正文切片，锁死语调、句长弹性与留白手感：
>
> [待试写确认后填入]

## 核心角色声口表（Voice Matrix）

| 角色名 | 身份与性格底色 | 句式与用词特征 | 潜台词与防御习惯 | 代表性原声台词（1–2 句样本） | 绝对不会说的话 |
|---|---|---|---|---|---|
""",
        "追踪/章节交接.md": """# 章节交接台账

> 每完成一章正文后追加交接卡，记录章末时间、地点、人物状态、伤势道具、本章起收镜头方式、信息边界及章末 1–3 句原文；未知内容标记为未知。
""",
        "追踪/角色状态.md": """# 角色状态台账

| 角色名 | 当前位置 | 身份/阵营 | 身体与伤病状态 | 核心持有物/资源 | 当前已知关键秘密 | 对主角/核心冲突态度 | 最近更新章节 |
|---|---|---|---|---|---|---|---|
""",
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Initialize prose directories and tracking files for story-prose-writer."
    )
    parser.add_argument("--root", required=True, help="Fiction project root")
    parser.add_argument("--title", default="未命名小说", help="Project title")
    parser.add_argument(
        "--lang",
        default="简体中文",
        help="Default writing language recorded in project templates (default: 简体中文)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show actions without writing"
    )
    args = parser.parse_args()

    try:
        root = safe_root(args.root)
    except ValueError as exc:
        parser.error(str(exc))

    dirs = [
        root / "正文",
        root / "正文" / "试写",
        root / "正文" / "版本",
        root / "追踪",
        root / "交付",
    ]
    for d in dirs:
        if not args.dry_run:
            d.mkdir(parents=True, exist_ok=True)

    created: list[Path] = []
    skipped: list[Path] = []
    title = args.title.strip() or "未命名小说"
    lang = args.lang.strip() or "简体中文"
    for rel, content in templates(title, lang).items():
        dest = root / Path(rel)
        if dest.exists():
            skipped.append(dest)
            continue
        created.append(dest)
        if not args.dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content.rstrip() + "\n", encoding="utf-8")

    print(f"root={root}")
    print(f"lang={lang}")
    print(f"created={len(created)}")
    for p in created:
        print(f"  + {p.relative_to(root)}")
    print(f"skipped={len(skipped)}")
    for p in skipped:
        print(f"  = {p.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
