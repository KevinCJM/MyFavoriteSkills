# AI 界面与任务状态

只读当前问题相关条目；分类不是推荐排名。★ 为最初指定的来源。
以下为目录快照，使用时核实具体版本、API 与许可；历史核验范围见 [维护记录](source-maintenance.md)。

## beautiful-ui — Beautiful UI ★

- 入口：[组件演示](https://www.beautifului.dev/)、[MIT 许可](https://www.beautifului.dev/license)。
- 用途/栈：Chat、Prompt Bar、Thinking、Streaming Text、Tool Chips、Task Rows、Approval Card；具体技术依赖看所选源码。
- 参考方式：视觉、任务状态表达、代码候选；展示数据应来自产品实际允许呈现的状态。
- 读取：[官方 registry](https://www.beautifului.dev/r/registry.json)；使用真实条目及依赖，不从界面标题猜 slug。官网代码弹窗链接到 [slev12397/beautiful-ui 的基础样式](https://github.com/slev12397/beautiful-ui/blob/main/app/globals.css)。
- 许可/范围：官网代码为 MIT；附带图标、字体等另查。本目录不把第三方镜像指定为官方仓库。

## ai-elements — AI Elements

- 入口：[官方文档](https://elements.ai-sdk.dev/docs)。
- 用途/栈：对话、消息与 AI 产品组件；基于 shadcn，当前文档针对 React 19、Tailwind 4，示例涉及 Next.js/AI SDK。
- 参考方式：视觉、代码候选；逐组件确认 SDK 耦合，不为展示 UI 自动迁移整个应用。
- 读取：具体组件文档与源码；CLI 可能初始化 shadcn 或引入依赖，执行前检查影响。
- 许可/范围：代码许可与模型/网关服务费用分别确认；调研不要求购买服务或提供 API key。
