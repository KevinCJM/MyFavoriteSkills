# 动效与状态反馈

只读当前问题相关条目；分类不是推荐排名。★ 为最初指定的来源。
以下为目录快照，使用时核实具体版本、API 与许可；历史核验范围见 [维护记录](source-maintenance.md)。

## transitions — transitions.dev ★

- 入口：[演示](https://transitions.dev/)、[官方 Skill 与说明](https://transitions.dev/skill.html)。
- 用途/栈：弹窗、展开、状态切换、数字与按钮反馈；CSS 为主，具体 recipe 可能有框架版本。
- 参考方式：视觉、交互模式、单个 recipe 代码候选；与项目动效尺度及 reduced-motion 行为协调。
- 读取：操作所选演示，读取实际提供的 recipe；官方 Skill 已安装时可用，不作为前置依赖。
- 许可/范围：官方区分免费与 Pro；免费可取不等于可把全部 snippets 再分发为组件包，采用前查具体条款。

## beui — beUI ★

- 入口：[官网](https://beui.dev/)、[Agent Guide](https://beui.dev/docs/ai-agents.md)。
- 用途/栈：弹窗、dock、命令面板、状态反馈；React/Next.js、Motion、Tailwind，匹配项目版本。
- 参考方式：视觉、代码候选、registry 安装候选。
- 读取：[llms.txt](https://beui.dev/llms.txt)、[registry 索引](https://beui.dev/r)、[AI 工具说明](https://beui.dev/docs/ai-agents)。官方 MCP 按宿主可用配置选用，不要求安装。
- 许可/范围：官网标明 MIT，另有 Pro；所选代码与素材仍按实际层级核实。

## motion-primitives — Motion Primitives

- 入口：[官网](https://motion-primitives.com/)、[项目仓库](https://github.com/ibelick/motion-primitives)。
- 用途/栈：组件状态变化与交互动效；框架及动画依赖按具体源码核实。
- 参考方式：交互模式、代码候选；与现有动效体系协调。
- 读取：官网不可读时看仓库 README、示例及源码，视觉效果仍需实际观察。
- 许可/范围：仓库元数据为 MIT；复制前读取固定版本 LICENSE 和附属依赖。

## emil-animations — Emil Kowalski / Animations on the Web

- 入口：[review-animations](https://github.com/emilkowalski/skills/blob/main/skills/review-animations/SKILL.md)、[animations.dev](https://animations.dev/)。
- 用途/栈：判断动效的目的、使用频率、连续输入时的打断与衔接、触发位置、减少动态效果及指针场景；原则不绑定框架，具体实现按当前项目确认。
- 参考方式：动效决策与审视依据，补充 recipe 和组件来源；不默认安装或调用原 Skill。
- 读取：只查当前交互相关的公开说明，必要时沿原文链接查详细依据。不把专项审核的角色、固定输出、时长或 easing 偏好转成本 Skill 的全局硬规则。
- 许可/范围：公开可读不等于不限条件再分发；复制内容前查具体许可，课程访问权限另核实。调研不要求购买课程、登录或改变现有动画运行时。
