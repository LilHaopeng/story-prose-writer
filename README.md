![小说正文写作 · Story Prose Writer](assets/prose-writer-hero.png)

# 小说正文写作 · Story Prose Writer

面向中文小说的正文写作 Agent Skill：依据已有世界观、大纲与作者意图，完成试写、逐章写作、修订和连续性审校。当前版本 **v1.0.0**。

写作时保留世界规则和章节因果，也给不同题材、叙事视角与作者声口留下空间。它提供创作流程和辅助工具，不能保证模型永不出错，也不能代替作者对剧情、文字与人物的判断。

## 能做什么

- **识别现有项目**：查阅世界观、章节安排、已写正文和相关记录，支持本系列项目的约定，也接受用户提供的其他等价材料。可选台账缺失时，依据已有内容整理本章所需摘要；关键事实不明时标记未知。
- **遵循正典与大纲**：结合已确认规则、人物认知以及章节中的选择、代价和状态变化写作；发现实质冲突时说明依据与影响，提出修复选择。普通细节可在不违背设定的范围内创作。
- **估算篇幅**：按需盘点已发现的细纲，提供精简、标准、丰满三档预算。已知全书章数或自定单章目标时可另列预算；未提供总章数时不猜测全书字数。
- **设计文风与声口**：提供八种可组合的风格方向，从叙述距离、句法节奏、感官、词汇与对白等方面校准；必要时针对本书场景试写。用户已明确风格或要求直接写作时，无须重复确认。
- **自定义风格研究**：结合可用的联网工具和可核实来源提炼技法；无法联网时，依据用户材料，或明确说明尚未核实，再决定如何继续。
- **长篇写作与审校**：按需装配本章大纲、前章结尾和相关角色、线索、规则；按项目选择的叙事视角控制信息边界，并维护需要的交接和状态记录。
- **去 AI 味与节奏调整**：用语境判断套话、重复和空泛解释，保留自然对白。节拍、句长、场景数量与章末形式是可选方法，依故事和作者偏好调整。
- **按需汇编**：在宿主具备文档工具及相应依赖时，可制作 DOCX 并进行渲染核对；本仓库不包含专门的 DOCX 生成器。

## 与世界观、大纲项目配合

三者可以分别使用，也可以依次衔接：

1. [小说世界观架构师 · Story World Architect](https://github.com/LilHaopeng/story-world-architect)：构建设定、世界规则及其交接材料。
2. [小说大纲架构师 · Story Outline Architect](https://github.com/LilHaopeng/story-outline-architect)：组织故事弧、剧情段与章节安排，并引用适用的世界观。
3. **小说正文写作 · Story Prose Writer**：依据已有材料写作和修订章节，检查对应关系及跨章连续性。

世界观的正典与已锁定的大纲仍以项目和作者确认为准。需要调整重要设定或锁定大纲时，先指出影响并按用户授权处理；正文中实际发生的变化再依据证据回写相应记录。使用者不必为了适配本 skill 改造已有目录。

## 安装到 Codex

在支持 `skill-installer` 的 Codex 中发送：

```text
$skill-installer 请从 https://github.com/LilHaopeng/story-prose-writer 安装 skills/story-prose-writer
```

也可以克隆或下载本仓库，将 `skills/story-prose-writer/` **整个文件夹**复制到当前 Codex 支持的技能目录，保留 `SKILL.md`、`references/` 和 `scripts/`。本机使用的个人目录是 `%USERPROFILE%\.codex\skills\story-prose-writer`；如设置了 `CODEX_HOME`，则对应 `%CODEX_HOME%\skills\story-prose-writer`。不同宿主的目录、工具权限和发现机制可能不同，请以实际配置为准。已有同名 skill 时请先备份，避免覆盖自己的修改；如果安装后未显示，可重新打开 Codex。

辅助脚本使用 Python 标准库，建议 Python 3.10 或更高版本。仅阅读工作流程不要求执行脚本；未运行脚本时，不应将其检查描述为已通过。

## 开始使用

```text
$story-prose-writer
请根据这个项目现有世界观、第一章正文和第二章细纲，准备续写第二章。
先检查能确认的角色状态、信息边界和承接问题；不确定的内容标为未知。
我希望单章约 3500 字，保持已有文风。
```

也可以只要求估算、试写、修订、审校或导出，不必每次执行完整流程。涉及的材料应由用户提供或由用户授权读取；大纲与世界观不是本 skill 的必然固定目录。

## 三个辅助脚本

| 脚本 | 实际职责与边界 |
|---|---|
| `init_prose_project.py` | 创建缺失的正文目录、声口卡和部分交接台账；支持 `--dry-run`，跳过已有文件，不会自动从正文提取状态。 |
| `estimate_word_count.py` | 识别标准命名的细纲文件，按章节数乘以固定档位计算预算；可传入已知总章数或单章目标，分别展示已覆盖和其余部分。文件数不一定等于实际章数，不会语义理解冲突密度或判断故事能否承载指定篇幅。 |
| `lint_prose.py` | 以规则扫描部分格式、套话与句式，统计基本汉字、段落和句长，按需提示字数偏差。命中是待复核提醒，不证明有 AI 味；可按规则忽略，不自动修改正文，也不检验正典或文学质量。 |

在仓库根目录运行（把路径替换成自己的项目）：

```text
python skills/story-prose-writer/scripts/init_prose_project.py --root <项目根> --title <书名> --dry-run
python skills/story-prose-writer/scripts/estimate_word_count.py --root <项目根>
python skills/story-prose-writer/scripts/estimate_word_count.py --root <项目根> --total-chapters 30 --target-words 3500
python skills/story-prose-writer/scripts/lint_prose.py --file <章节文件> --target-words 3500
```

`--total-chapters` 只填写已知并确认的全书计划章数；不是必填项。初始化去掉 `--dry-run` 后才创建文件。带空格的路径请加引号；各脚本完整参数见 `--help`。

## 参考文档

- [产物契约与接口](skills/story-prose-writer/references/artifact-contract.md)：项目资料识别、权责及台账。
- [字数预估与缩放](skills/story-prose-writer/references/word-count-and-scaling.md)：篇幅覆盖、不确定性与大纲缩放。
- [文风与去 AI 味](skills/story-prose-writer/references/style-and-anti-ai.md)：文风参数、来源核实、试写和语言检查。
- [长篇执行](skills/story-prose-writer/references/long-form-execution.md)：上下文装配、视角、节奏和交接。
- [审校与连续性](skills/story-prose-writer/references/audit-and-continuity.md)：正典、人物、连续性核对及按需 DOCX 交付。

## 使用边界与数据

辅助脚本在当前环境中读取或写入用户指定的本地文件，不主动上传原稿。使用模型或联网服务时，数据处理遵循相应服务和用户设置。发布问题或寻求帮助时，请避免上传私人原稿、密钥或未获授权的第三方材料。

脚本与检查清单不能保证人物一致、剧情无漏洞或读者喜欢作品；正式交付前仍需结合原文、设定和项目目标审阅。DOCX 的生成、转换与视觉验收取决于实际可用工具、字体及环境，应分别确认。

## 许可证

本仓库使用 [MIT License](LICENSE)。本项目不是 OpenAI 官方产品；仓库许可不要求用户公开自己的小说或世界观。
