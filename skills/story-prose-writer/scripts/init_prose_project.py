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


def templates(title: str) -> dict[str, str]:
    return {
        "正文/写作状态.md": f"""# 正文写作状态

- 项目名：{title}
- 当前工作模式：estimate
- 绑定的大纲版本：[待确认]
- 绑定的世界观版本：[待确认]
- 字数配置档位：[待确认；可自定义]
- 单章目标字数区间：[待确认]
- 全书预估总字数：[待确认]
- 当前已锁定文风：见 `正文/00_文风与声口卡.md`（状态：draft）
- 已完成章节：无
- 当前累计净字数：0
- 下一待写章节：CH-001
- 待确认事项：字数档位与开篇试写文风确认
""",
        "正文/00_文风与声口卡.md": f"""# 文风与声口卡

- 项目名：{title}
- 状态：draft
- 模式来源：预设方向 / 自定义风格 / 用户提供样本 [待确认]
- 基底与调整方向：[待试写确认]
- 文风资料及依据：
  - 研究状态：[待确认：已联网核实 / 用户提供 / 未联网核实]
  - 参考资料和链接：[待填写；未知时不编造来源]
  - 来源支持的技法与个人归纳：[分别记录]
- 叙事视角与信息边界：[依用户、世界观与大纲确认，可为限知、多视角或其他形式]
- 叙述距离：[待试写确认]
- 句法与节奏：[待试写确认；随场景变化，不设统一句长或段落上限]
- 感官与意象：[待试写确认]
- 词汇肌理与修辞：[待试写确认]
- 对白与留白：[待试写确认；不设固定占比]
- 本书专属禁用或注意表达：[用户确认后填写；结合语境判断]

## 核心角色声口表（Voice Matrix）

| 角色名 | 身份与性格底色 | 句式与用词习惯 | 潜台词与情绪防御机制 | 标志性小动作（克制使用） | 绝对不会说的话 |
|---|---|---|---|---|---|
""",
        "追踪/章节交接.md": """# 章节交接台账

> 每完成一章正文后按已知内容追加交接卡，记录章末时间、地点、人物状态、伤势道具、信息边界及末尾原文；不确定的内容标记为未知。
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
    for rel, content in templates(args.title.strip() or "未命名小说").items():
        dest = root / Path(rel)
        if dest.exists():
            skipped.append(dest)
            continue
        created.append(dest)
        if not args.dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content.rstrip() + "\n", encoding="utf-8")

    print(f"root={root}")
    print(f"created={len(created)}")
    for p in created:
        print(f"  + {p.relative_to(root)}")
    print(f"skipped={len(skipped)}")
    for p in skipped:
        print(f"  = {p.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
