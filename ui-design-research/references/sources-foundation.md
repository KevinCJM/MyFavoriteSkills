# 基础组件与交互行为

只读当前问题相关条目；分类不是推荐排名。★ 为最初指定的来源。
以下为目录快照，使用时核实具体版本、API 与许可；历史核验范围见 [维护记录](source-maintenance.md)。

## w3c-apg — W3C ARIA APG

- 入口：[模式目录](https://www.w3.org/WAI/ARIA/apg/patterns/)、[使用前说明](https://www.w3.org/WAI/ARIA/apg/practices/read-me-first/)。
- 用途/栈：Dialog、Combobox、Tabs、Menu、Tree、Grid 等的语义、焦点和键盘约定；不绑定框架。
- 参考方式：行为指导与示例，不是视觉主题库或项目可访问性认证。
- 读取：只读对应模式与必要实践；优先合适的原生 HTML，ARIA role 本身不实现键盘行为。示例仍需目标浏览器与辅助技术验证。
- 许可/范围：指南与示例按页面、仓库的实际条款核实，不套用本 Skill 的 MIT 许可。

## shadcn — shadcn/ui ★

- 入口：[官网](https://ui.shadcn.com/)、[组件](https://ui.shadcn.com/docs/components)、[区块](https://ui.shadcn.com/blocks)。
- 用途/栈：基础组件、表单、表格、应用外壳；React、Tailwind，具体 primitives 和版本看项目配置。
- 参考方式：视觉、代码候选、registry 安装候选。
- 读取：[文档索引](https://ui.shadcn.com/llms.txt)、[registry 说明](https://ui.shadcn.com/docs/registry)、[MCP 说明](https://ui.shadcn.com/docs/mcp)。已配置的 MCP 可检索，否则直接读文档。
- 许可/范围：从官方组件页指向的源码仓库查所选文件许可；第三方 registry 不自动继承主库许可。

## base-ui — Base UI

- 入口：[官网及说明](https://base-ui.com/)。
- 用途/栈：自定义设计系统的无样式交互组件；React，支持多种样式方案。
- 参考方式：行为、结构、代码候选；该库不提供统一成品视觉风格。
- 读取：所选组件的官方 API 与示例，保留焦点管理、键盘和可访问性行为。
- 许可/范围：官网 FAQ 明确 MIT；依赖与附加资产仍单独处理。

## react-aria — React Aria

- 入口：[官方站点](https://react-aria.adobe.com/)。
- 用途/栈：React 中需要自定义视觉的组件行为、交互状态和国际化；官方提供无预设样式的组件。
- 参考方式：行为与实现候选；不将其默认演示样式当作产品必须采用的主题。
- 读取：从官网进入目标组件文档，核实项目版本、样式与安装影响；已有基础库能满足时不重复引入，非 React 项目不直接复制 React 代码。
- 许可/范围：采用源码或包前核实对应仓库、版本和依赖许可；不因官网强调可访问性就宣称本项目已经通过验证。

## coss-ui — COSS UI

- 入口：[官网及组件列表](https://coss.com/ui)。
- 用途/栈：应用控件与组合模式；基于 Base UI，检查 React、Tailwind 及 primitives 版本。
- 参考方式：视觉、代码候选；避免在同一页面交替引入不同库的同类基础控件。
- 读取：从首页对应组件进入官方文档、源码及当前安装说明。
- 许可/范围：采用时读取官网指向的仓库 LICENSE 和所选条目许可。
