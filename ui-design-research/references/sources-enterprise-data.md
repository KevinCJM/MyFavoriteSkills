# 企业业务与数据界面

只读当前问题相关条目；分类不是推荐排名。★ 为最初指定的来源。
以下为目录快照，使用时核实具体版本、API 与许可；历史核验范围见 [维护记录](source-maintenance.md)。

## ant-design — Ant Design

- 入口：[官网](https://ant.design/)。
- 用途/栈：企业应用、表格、筛选和表单；此条指 React Ant Design，其他框架实现需单独查。
- 参考方式：布局、交互模式、代码候选；已有项目优先沿用当前版本与主题。
- 读取：Components 中所选组件的 API、演示和源码，注意主版本差异。
- 许可/范围：核实官方仓库与依赖的 LICENSE，不混入独立模板产品的许可假设。

## mantine — Mantine

- 入口：[官网](https://mantine.dev/)、[llms.txt](https://mantine.dev/llms.txt)。
- 用途/栈：表单、输入、日期与组合控件；React，项目版本优先。
- 参考方式：视觉、代码候选；现有 Mantine 项目优先在本体系内组合。
- 读取：具体组件文档；官网列有 LLM 文档、Skills 和 MCP，实际调用以宿主可用工具为准。
- 许可/范围：采用时查看仓库、具体包和依赖的 LICENSE，外部工具费用另核实。

## carbon — Carbon Design System

- 入口：[Data table 用法](https://carbondesignsystem.com/components/data-table/usage/)、[可访问性](https://carbondesignsystem.com/components/data-table/accessibility/)、[React 实现](https://carbondesignsystem.com/developing/frameworks/react/)。
- 用途/栈：企业表格、工具栏、筛选、选择、展开与批量操作；设计模式可跨框架借鉴，代码按所选实现与版本确认。
- 参考方式：业务模式、密度与行为；已有 Ant Design 等体系时优先迁移模式，不默认新增 Carbon 或替换主题。
- 读取：按具体问题查看用法、Accessibility 与 Code；Carbon 的组件测试结论不自动适用于修改后的项目。
- 许可/范围：具体包、示例和品牌资产分别核实；页面中的 IBM 内部扩展不视为公共可用代码。

## kibo-ui — Kibo UI

- 入口：[官网](https://www.kibo-ui.com/)。
- 用途/栈：复杂业务组件与组合区块；面向 shadcn 的自定义 registry，React 生态。
- 参考方式：视觉、代码候选；检查额外依赖与本地 shadcn 变体。
- 读取：从 Browse components 进入具体文档，再取代码和 registry 信息。
- 许可/范围：官网声明免费开源；所选组件与依赖按其许可证核实。

## tremor — Tremor

- 入口：[官网](https://www.tremor.so/)、[安装与组件导航](https://www.tremor.so/docs/getting-started/installation)。
- 用途/栈：图表、指标与仪表盘；当前 Tremor Raw 文档要求 React 18.2+、Tailwind 4+，使用时复核。
- 参考方式：视觉、代码候选；保留现有数据定义、格式和图表逻辑。
- 读取：具体组件文档及 [Blocks](https://blocks.tremor.so/)；区分 Raw/复制源码与旧包版本。
- 许可/范围：所选组件、Blocks 与依赖分别核实，不默认全部素材同一许可。
