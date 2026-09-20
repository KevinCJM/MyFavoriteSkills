# 来源维护与核验记录

仅在维护目录、解释历史结论或排查来源变化时读取。下面的日期只覆盖注明字段，不证明全部组件、视觉、依赖或许可已验证。
来源 ID 与分类文件保持一致；前 20 项沿用 v1.0 的实际核验记录，新增三项单列当前核验范围。本次拆分未重新完整核验旧来源。

## 更新约定

- 普通任务从分类条目读官方入口和重要限制，不依赖旧快照执行安装。
- 更新实际检查过的字段与日期；确认官网和仓库关联后再指定源码归属。
- 许可限制、必要依赖提示和有效读取入口保留在分类中；历史异常与工具端点快照留在这里。
- 命令从采用时的组件页获取；不维护整库安装命令，不因未找到 MCP 就断言不存在。
- 上游固定提交与归属见 [NOTICE](../NOTICE.md)；页面和素材不因列入目录而采用本 Skill 的许可。

## shadcn — shadcn/ui ★

- 核验：2026-09-20 已读官网、官方 MCP 文档；索引入口由官方文档列出，使用时读取内容。

## transitions — transitions.dev ★

- 核验：2026-09-20 已读官方 Skill 页面及免费/Pro 路径；具体 recipe 许可与交互需逐项核实。

## rare-ui — Rare UI ★

- 核验：2026-09-20 已读官网、组件入口与 CLI 示例，不代表每个演示都已操作。

## beui — beUI ★

- 核验：2026-09-20 已读官网，直接获取 llms.txt 和 AI 工具说明成功；搜索读取器读不到该说明时可使用直接读取或官方 Markdown 入口。
- 工具快照：当日官方说明列出 `https://mcp.beui.dev/mcp`；未连接验证，不作为安装指令。

## beautiful-ui — Beautiful UI ★

- 核验：2026-09-20 已读官网/许可/registry，并观察 [Thinking](https://www.beautifului.dev/#thinking-state) 的折叠、展开与代码弹窗；代码采用定时器演示进度并要求 foundation 样式，业务实现需接入真实状态。未继承旧上游的第三方仓库归属或历史域名判断。

## coss-ui — COSS UI

- 核验：2026-09-20 已读官网定位及组件目录；具体源码和许可未完整复核。

## kibo-ui — Kibo UI

- 核验：2026-09-20 已读官网 registry 定位及组件/区块入口；MCP 可用性未在此条确认。

## tremor — Tremor

- 核验：2026-09-20 已读官网、安装文档中的版本要求及 Blocks 入口。

## tailark — Tailark

- 核验：2026-09-20 已读官方 docs 的 namespace、免费/Pro 和 UI base 路径；不能沿用旧的免费 `@tailark` 假设。

## magic-ui — Magic UI

- 核验：2026-09-20 已读官网技术栈和免费/Pro 定位；未统一验证具体依赖。

## react-bits — React Bits

- 核验：2026-09-20 已通过 GitHub API 读取 LICENSE.md 全文；官网提取无正文、llms.txt 读取失败，视觉效果和具体源码需由浏览器或仓库继续核实。

## motion-primitives — Motion Primitives

- 核验：2026-09-20 官网 docs 在读取器中返回 403；GitHub API 已核实仓库 homepage 与官网一致及许可元数据，403 不等于项目失效。

## aceternity — Aceternity UI

- 核验：2026-09-20 已读官网定位与技术栈；具体内容层级和许可按条目核实。

## ai-elements — AI Elements

- 核验：2026-09-20 已读官方介绍、目标 React/Tailwind 版本及安装影响。

## base-ui — Base UI

- 核验：2026-09-20 已读官网 React-only、无样式与 MIT 说明。

## mantine — Mantine

- 核验：2026-09-20 已读官网 React、原生 CSS 和 AI 工具入口，索引内容按任务读取。

## ant-design — Ant Design

- 核验：2026-09-20 已读官网入口与 React 定位；API 需按项目版本核实。

## design-spells — Design Spells

- 核验：2026-09-20 已读官网定位并确认 www 重定向，不代表逐个作品已查看。

## landingfolio — Landingfolio

- 核验：2026-09-20 已读灵感与组件/会员分类；只观察到 MCP 入口，未验证连接或权限。

## awwwards — Awwwards

- 核验：2026-09-20 已读作品分类与展示入口，具体作品需在任务中访问。

## w3c-apg — W3C ARIA APG

- 核验：2026-09-20 已读 APG Patterns、Read Me First；核实模式覆盖、ARIA 不自动提供键盘行为及示例需要浏览器/辅助技术验证。未操作所有示例，未做项目可访问性验收。

## react-aria — React Aria

- 核验：2026-09-20 已读官网关于行为、交互、可访问性、国际化及自定义样式的介绍；旧 Adobe 文档首页重定向到 react-aria.adobe.com。文档导航在读取器中一次失败，未核实具体组件 API、安装依赖或许可证全文，也未操作演示。

## carbon — Carbon Design System

- 核验：2026-09-20 已读 Data table Usage、Accessibility 与 React 入口；核实选择、展开、工具栏、批量操作与键盘说明。未操作 Storybook、未复制代码、未核实全部包许可。
