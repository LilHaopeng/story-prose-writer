![小说正文写作 · Story Prose Writer](assets/prose-writer-hero.png)

# 小说正文写作 · Story Prose Writer

**简体中文** | [English](README_EN.md)

面向长中短篇小说的正文创作 Agent Skill：基于已有的世界观、故事大纲与创作意图，完成篇幅盘点、声口校准、逐章写作、润色修订、连续性审校与排版导出。当前版本 **v1.1.0**。

默认采用**简体中文**起笔，贴合现代汉语的零形回指、意合推进与留白节奏；同时也支持按你的指令切换为**英文（English）**、**繁体中文**或其他语言创作，自动匹配对应语种的叙事习惯、质检规则与成书排版。

## 核心特性

- **大纲消融与老手视角**：将细纲中的目标、冲突与代价自然藏入人物手头的日常事务与错位对白，消除分段打卡的“大纲腔”；土著视角对世界常态熟视无睹，只在遇到摩擦与反常时显影设定，拒绝借角色内心给读者写制度说明书。
- **母语松弛感与防反向紧绷**：遵循承前省主语、半句留白、去英文量词翻译腔等母语准则；引入感官配额与自由间接引语，避免把去 AI 味写成“句句端茶盏、摸刀柄”的僵硬舞台调度。
- **原声调音叉防漂移**：支持八大预设文风组合及自定义流派检索解构，在 `00_文风与声口卡.md` 中直接固化 150–250 字经认可的标杆正文切片与角色原声台词，连载数十章依然保持开书声口。
- **页面呼吸感与视觉律动**：主动错落饱满叙述段、短促动作段、无旁白裸对白连击与单句气口，打破满屏等高的“豆腐块”段落；清理滥用强调引号（“引号麻子脸”），并在章节交接时错开相邻章节的起收镜头。
- **按需上下文与正典守恒**：每章仅装配出场角色状态、相关伏笔与触发规则，严守视角信息边界以防提前漏底；定稿后依据正文实际发生的事实回写交接卡与追踪台账。
- **双端 DOCX 排版导出**：内置小说排版构建器，一键生成**实体书沉浸版（`book`，宋体/Georgia 衬线 + 首行缩进 + 居中星号转场）**或**屏幕轻读版（`screen`，舒展段距 + 无缩进清爽版面）**，自动拦截内部工程编号外泄。

## 配套创作工作流

三个同系列技能既可独立服务现有文稿，也可串联成从设定、架构到成书的完整管线：

1. [小说世界观架构师 · Story World Architect](https://github.com/LilHaopeng/story-world-architect)：构建自洽运转的世界规则、社会生态，并向下游交接设定契约与日常语言肌理。
2. [小说大纲架构师 · Story Outline Architect](https://github.com/LilHaopeng/story-outline-architect)：从创作初衷推演故事弧、剧情段与具象章纲。
3. **小说正文写作 · Story Prose Writer**：承接上游设定与章纲（或你自己的大纲笔记），完成文风定调、章节撰写、语感打磨与成稿交付。

## 安装方式

1. **通过 `skill-installer` 安装（Codex 等）**
   ```text
   $skill-installer 请从 https://github.com/LilHaopeng/story-prose-writer 安装 skills/story-prose-writer
   ```
2. **手动复制到本地技能目录（Antigravity / Claude Code / Codex / Cursor）**
   克隆本仓库，将 `skills/story-prose-writer/` 目录完整复制到对应客户端的技能目录：
   - **Antigravity**：`~/.gemini/config/skills/story-prose-writer`
   - **Claude Code**：`~/.claude/skills/story-prose-writer`
   - **Codex**：`~/.codex/skills/story-prose-writer` 或 `~/.agents/skills/story-prose-writer`
   - **Cursor**：`~/.cursor/skills/story-prose-writer`

核心辅助脚本仅使用 Python 3.10+ 标准库；如需使用 `build_prose_docx.py` 导出 Word 文档，可执行 `python -m pip install -r requirements.txt` 安装 `python-docx`。

## 快速上手

**默认简体中文续写**：

```text
$story-prose-writer
请根据当前项目的世界观、第一章正文和第二章细纲续写第二章。
保持现有冷硬市井文风，单章约 3500 字，注意把博弈藏进日常动作里，控制页面段落呼吸感。
```

**指定英文或其他语言起笔**：

```text
$story-prose-writer
Write Chapter 1 in English (~3,000 words) based on our outline and world notes, using a crisp close-third-person noir voice with natural dialogue pacing.
```

你也可以单独调用其中任意一环：盘点字数预算、做 A/B 文风试写、润色旧稿去 AI 味、核对跨章吃书问题，或将完结章节打包为 `.docx`。

## 配套辅助脚本

| 脚本 | 功能说明 |
|---|---|
| `init_prose_project.py` | 非破坏性初始化 `正文/`、`追踪/`、`交付/` 目录及写作状态、文风声口卡、章节交接模板（支持 `--lang` 与 `--dry-run`）。 |
| `estimate_word_count.py` | 盘点已有细纲覆盖情况，输出精简/标准/丰满三档篇幅区间与单章目标对照。 |
| `lint_prose.py` | 旁白与对白分流质检（支持 `--lang auto\|zh\|en`）：检测套话模板、连续等高“豆腐块”段落、局部匀速句窗、高频词复读、代词过密与碎引号噪点。 |
| `build_prose_docx.py` | 将单章或整本章节 Markdown 编译为 `book`（纸书衬线缩进）或 `screen`（屏幕轻读）排版的 `.docx`，自动拦截工作台编号泄露。 |

常用命令示例：

```bash
python skills/story-prose-writer/scripts/init_prose_project.py --root <项目根> --title "旧港夜航"
python skills/story-prose-writer/scripts/estimate_word_count.py --root <项目根> --total-chapters 24 --target-words 3500
python skills/story-prose-writer/scripts/lint_prose.py --file <章节.md> --target-words 3500
python skills/story-prose-writer/scripts/build_prose_docx.py --chapters-dir <项目根>/正文 --out <项目根>/交付/旧港夜航_正文.docx --title "旧港夜航" --preset book
```

运行回归测试：

```bash
python -B -m unittest discover -s tests -v
```

## 参考文档

- [产物契约与上下游接口](skills/story-prose-writer/references/artifact-contract.md)：目录约定、所有权边界、原声调音叉与交接卡模板。
- [字数预估与双向缩放](skills/story-prose-writer/references/word-count-and-scaling.md)：篇幅档位及压缩、扩充手法。
- [文风、母语语感与页面观感](skills/story-prose-writer/references/style-and-anti-ai.md)：八大文风矩阵、自定义流派解构、汉语语感四律、页面呼吸感与多语种适配。
- [长篇连载执行与大纲消融](skills/story-prose-writer/references/long-form-execution.md)：按需上下文装配、大纲消融律、老手视角与连章起收错峰。
- [正典审校与 DOCX 交付](skills/story-prose-writer/references/audit-and-continuity.md)：六维审校表、状态回写与双端排版规范。

## 隐私与许可证

所有本地脚本仅在当前工作目录内读写文件，不会上传任何原稿。本仓库采用 [MIT License](LICENSE) 开源（Copyright © 2026 LilHaopeng）。
