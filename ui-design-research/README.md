# UI Design Research

让前端 AI 在设计与编码前，查找真实的组件、页面和交互参考，并把参考转成适合当前项目的实现建议。

A lightweight skill for researching real UI components, layouts, and interactions, then adapting the findings to the project's existing stack and design system.

版本：`1.0.0`。运行入口是 [SKILL.md](SKILL.md)；本 README 面向安装和使用者。

## 适合做什么

- 为新页面、视觉改版或组件选型寻找具体参考。
- 比较布局、信息密度、字体层级、留白、状态反馈和动效。
- 在现有技术栈内选择“改造已有组件”“改编兼容源码”或“借鉴模式后重新实现”。

普通尺寸调整、纯逻辑修复和已有完整设计稿的直接还原，通常无需启用外部调研。

## 工作方式

1. 先读取项目规则、框架、现有组件与主题，明确页面用途和用户要求。
2. 按具体问题选择来源，通常查看 2–3 个；用户指定的来源优先。
3. 查官方文档与源码，实际观察渲染效果，按需操作演示。
4. 给出具体参考链接、采用理由、适配方式和已核实的证据。
5. 用户要求只调研时交付建议；用户已要求实现时，继续编码与相关验证。

文字抓取、截图、操作演示、读取源码和本地验证分别说明。看过原站演示，不等于组件已经在你的项目里通过验证。

## 参考来源

当前目录收录 20 个来源，包括最初指定的 [shadcn/ui](https://ui.shadcn.com/)、[transitions.dev](https://transitions.dev/)、[Rare UI](https://www.rareui.com/)、[beUI](https://beui.dev/) 和 [Beautiful UI](https://www.beautifului.dev/)。

| 参考方向 | 目录中的部分来源 |
| --- | --- |
| 基础组件与业务控件 | shadcn/ui、Base UI、COSS UI、Kibo UI、Mantine、Ant Design |
| 数据分析与仪表盘 | Tremor |
| AI 助手与任务状态 | Beautiful UI、AI Elements |
| 动效与交互细节 | transitions.dev、beUI、Motion Primitives |
| 营销区块与视觉效果 | Rare UI、Tailark、Magic UI、React Bits、Aceternity UI |
| 页面与交互灵感 | Design Spells、Landingfolio、Awwwards |

完整入口、适用技术栈、读取方式和核验范围见 [来源目录](references/sources.md)。目录不是组件源码合集，也不限制使用目录外的官方来源；API、依赖、价格和许可在实际采用时重新核实。

## 安装

下载或克隆 [MyFavoriteSkills](https://github.com/KevinCJM/MyFavoriteSkills) 后，在仓库根目录执行以下首次安装命令，将完整文件夹放入共享目录：

```bash
mkdir -p "$HOME/.agents/skills"
ui_skill_target="$HOME/.agents/skills/ui-design-research"
if [ -e "$ui_skill_target" ] || [ -L "$ui_skill_target" ]; then
  echo "目标已存在，请先检查或备份旧版本。"
else
  cp -R ./ui-design-research "$ui_skill_target"
fi
```

支持 `~/.agents/skills/` 的智能体可从这里加载。其他客户端可把完整文件夹放入其支持的 Skills 目录；自动发现和调用语法以客户端为准。

如果你的 Codex 配置使用 `~/.codex/skills/`，可保留共享目录作为唯一安装文件源，再建立软链接：

```bash
ui_skill_source="$HOME/.agents/skills/ui-design-research"
ui_codex_skills="${CODEX_HOME:-$HOME/.codex}/skills"
mkdir -p "$ui_codex_skills"
if [ ! -f "$ui_skill_source/SKILL.md" ]; then
  echo "请先完成共享目录安装。"
elif [ -e "$ui_codex_skills/ui-design-research" ] || [ -L "$ui_codex_skills/ui-design-research" ]; then
  echo "Codex 入口已存在，请检查它是否指向共享目录。"
else
  ln -s "$ui_skill_source" "$ui_codex_skills/ui-design-research"
fi
```

更新时比较并备份自己的修改，再替换完整 Skill；已有软链接无需重复创建。加载未刷新时，按客户端方式重新加载 Skills 或开启新会话。

## 使用示例

在支持 `$skill-name` 的客户端中可以显式调用；其他客户端可要求 AI 读取本目录的 `SKILL.md` 并按其工作。

只调研并给方案：

```text
使用 $ui-design-research，为当前仪表盘调研布局、筛选区和表格密度。
保留项目已有组件库，给出具体参考链接与采用理由，先不改代码。
```

调研并实现：

```text
使用 $ui-design-research，先检查项目技术栈，再为这个页面寻找合适的 UI 参考。
按已有样式规范完成实现，并验证相关尺寸、状态和操作。
```

指定来源与范围：

```text
使用 $ui-design-research，参考 Beautiful UI 的任务状态展示和 transitions.dev 的切换反馈。
为现有 Vue 页面提出兼容实现，优先免费内容，接入真实业务状态。
```

常规输出包含具体参考、采用理由、实现建议及实际验证情况；需要详细比较或交接时才使用 [输出规范](references/research-output.md)，不强制生成额外设计文件。

## 工具与费用

Skill 本身是 Markdown 指令与来源目录，无需安装 Node.js、Python 或三个上游 Skill。实际调研使用智能体已有的联网、浏览器和文件读取工具；缺少视觉或交互能力时，会说明尚未验证的部分。

MCP 是可选读取通道，本包不附带 MCP 服务，也不会自动安装工具、组件或修改全局配置。Skill 以 MIT 许可免费提供；模型、第三方服务和付费组件的费用由对应提供方决定。默认优先免费内容，已有付费授权时按授权范围使用。

## 文件与维护

| 文件 | 用途 |
| --- | --- |
| [SKILL.md](SKILL.md) | 触发范围、调研流程与实现边界 |
| [references/sources.md](references/sources.md) | 20 个来源的选源索引与核验说明 |
| [references/research-output.md](references/research-output.md) | 简短输出和按需详细交接格式 |
| [agents/openai.yaml](agents/openai.yaml) | Codex 显示信息和默认调用提示 |
| [NOTICE.md](NOTICE.md) | 三个上游项目的固定提交、归属和许可证 |
| [LICENSE](LICENSE) | 本 Skill 的 MIT 许可证 |

维护时只更新实际检查过的来源字段和日期，保留上游归属。普通 UI 任务不会自动改写全局 Skill；目录也不会自动抓取网站或下载整个组件库。

本 Skill 选择性改编自 `ByeongminLee/nextjs-claude-code`、`Xiaoyang-Hu-96/design-resource-library` 和 `JasonColapietro/suede-creator-skills`，独立维护。具体来源与完整许可记录见 [NOTICE.md](NOTICE.md)。Skill 的 MIT 许可不替代所引用组件、图片、图标、字体或第三方服务的许可。
