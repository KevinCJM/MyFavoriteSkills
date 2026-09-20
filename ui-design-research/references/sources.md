# UI 参考来源

维护版本：2026-09-20。日期只覆盖注明的资料，不代表全部组件、视觉、依赖和许可已验证。
先看索引，再按来源 ID 读取条目。首页用于发现；输出优先链接实际采用的组件或示例。
“代码候选”表示可以继续检查源码与许可，不自动授予复制权限。未标明的价格、许可细节、MCP 或 registry 为未核实。

## 选源索引

| 需求 | 来源 ID | 提示 |
| --- | --- | --- |
| 已有组件库 | 优先该库，如 ant-design、mantine、shadcn | 保留当前基础、版本与主题 |
| 自定义基础行为 | base-ui、shadcn、coss-ui | 匹配现有 primitives 和样式体系 |
| 业务控件、复杂组合 | kibo-ui、coss-ui、ant-design、mantine | 按具体能力和框架筛选 |
| 数据分析与仪表盘 | tremor、现有表格/图表库 | 优先数据可读性和操作效率 |
| AI 助手、任务状态 | beautiful-ui、ai-elements | 映射产品真实状态 |
| 细节动效 | transitions、motion-primitives、beui | 解决具体反馈或状态变化 |
| 营销区块与视觉效果 | tailark、magic-ui、aceternity、react-bits、rare-ui | 区分必要交互与装饰成本 |
| 布局、审美与交互灵感 | design-spells、landingfolio、awwwards | 回到原始作品观察，资产许可另查 |
| Vue、Svelte 等其他栈 | 项目当前生态的官方来源 | React 来源可研究模式，不假设代码兼容 |

前五项 ★ 为用户指定的入口，保留在目录中；按任务选择，不强制全部采用。

## shadcn — shadcn/ui ★

- 入口：[官网](https://ui.shadcn.com/)、[组件](https://ui.shadcn.com/docs/components)、[区块](https://ui.shadcn.com/blocks)。
- 用途/栈：基础组件、表单、表格、应用外壳；React、Tailwind，具体 primitives 和版本看项目配置。
- 参考方式：视觉、代码候选、registry 安装候选。
- 读取：[文档索引](https://ui.shadcn.com/llms.txt)、[registry 说明](https://ui.shadcn.com/docs/registry)、[MCP 说明](https://ui.shadcn.com/docs/mcp)。已配置的 MCP 可检索，否则直接读文档。
- 许可/范围：从官方组件页指向的源码仓库查所选文件许可；第三方 registry 不自动继承主库许可。
- 核验：2026-09-20 已读官网、官方 MCP 文档；索引入口由官方文档列出，使用时读取内容。

## transitions — transitions.dev ★

- 入口：[演示](https://transitions.dev/)、[官方 Skill 与说明](https://transitions.dev/skill.html)。
- 用途/栈：弹窗、展开、状态切换、数字与按钮反馈；CSS 为主，具体 recipe 可能有框架版本。
- 参考方式：视觉、交互模式、单个 recipe 代码候选；与项目动效尺度及 reduced-motion 行为协调。
- 读取：操作所选演示，读取实际提供的 recipe；官方 Skill 已安装时可用，不作为前置依赖。
- 许可/范围：官方区分免费与 Pro；免费可取不等于可把全部 snippets 再分发为组件包，采用前查具体条款。
- 核验：2026-09-20 已读官方 Skill 页面及免费/Pro 路径；具体 recipe 许可与交互需逐项核实。

## rare-ui — Rare UI ★

- 入口：[官网](https://www.rareui.com/)、[组件目录](https://www.rareui.com/components)。
- 用途/栈：特色输入、选择器、文字和视觉交互；React，按组件检查动画依赖。
- 参考方式：视觉、代码候选；从具体组件页获取当前安装方式。
- 读取：演示、代码和 shadcn CLI；首页标识 `swamimalode07/rare-ui`，勿与其他同名 RareUI 项目混淆。
- 许可/范围：官网声明免费开源；复制时核实目标仓库及文件的许可证。
- 核验：2026-09-20 已读官网、组件入口与 CLI 示例，不代表每个演示都已操作。

## beui — beUI ★

- 入口：[官网](https://beui.dev/)、[Agent Guide](https://beui.dev/docs/ai-agents.md)。
- 用途/栈：弹窗、dock、命令面板、状态反馈；React/Next.js、Motion、Tailwind，匹配项目版本。
- 参考方式：视觉、代码候选、registry 安装候选。
- 读取：[llms.txt](https://beui.dev/llms.txt)、[registry 索引](https://beui.dev/r)、[AI 工具说明](https://beui.dev/docs/ai-agents)。说明页列有官方 MCP `https://mcp.beui.dev/mcp`，不代表宿主已连接。
- 许可/范围：官网标明 MIT，另有 Pro；所选代码与素材仍按实际层级核实。
- 核验：2026-09-20 已读官网，直接获取 llms.txt 和 AI 工具说明成功；搜索读取器读不到该说明时可使用直接读取或官方 Markdown 入口。

## beautiful-ui — Beautiful UI ★

- 入口：[组件演示](https://www.beautifului.dev/)、[MIT 许可](https://www.beautifului.dev/license)。
- 用途/栈：Chat、Prompt Bar、Thinking、Streaming Text、Tool Chips、Task Rows、Approval Card；具体技术依赖看所选源码。
- 参考方式：视觉、任务状态表达、代码候选；展示数据应来自产品实际允许呈现的状态。
- 读取：[官方 registry](https://www.beautifului.dev/r/registry.json)；使用真实条目及依赖，不从界面标题猜 slug。官网代码弹窗链接到 [slev12397/beautiful-ui 的基础样式](https://github.com/slev12397/beautiful-ui/blob/main/app/globals.css)。
- 许可/范围：官网代码为 MIT；附带图标、字体等另查。本目录不把第三方镜像指定为官方仓库。
- 核验：2026-09-20 已读官网/许可/registry，并观察 [Thinking](https://www.beautifului.dev/#thinking-state) 的折叠、展开与代码弹窗；代码采用定时器演示进度并要求 foundation 样式，业务实现需接入真实状态。未继承旧上游的第三方仓库归属或历史域名判断。

## coss-ui — COSS UI

- 入口：[官网及组件列表](https://coss.com/ui)。
- 用途/栈：应用控件与组合模式；基于 Base UI，检查 React、Tailwind 及 primitives 版本。
- 参考方式：视觉、代码候选；避免在同一页面交替引入不同库的同类基础控件。
- 读取：从首页对应组件进入官方文档、源码及当前安装说明。
- 许可/范围：采用时读取官网指向的仓库 LICENSE 和所选条目许可。
- 核验：2026-09-20 已读官网定位及组件目录；具体源码和许可未完整复核。

## kibo-ui — Kibo UI

- 入口：[官网](https://www.kibo-ui.com/)。
- 用途/栈：复杂业务组件与组合区块；面向 shadcn 的自定义 registry，React 生态。
- 参考方式：视觉、代码候选；检查额外依赖与本地 shadcn 变体。
- 读取：从 Browse components 进入具体文档，再取代码和 registry 信息。
- 许可/范围：官网声明免费开源；所选组件与依赖按其许可证核实。
- 核验：2026-09-20 已读官网 registry 定位及组件/区块入口；MCP 可用性未在此条确认。

## tremor — Tremor

- 入口：[官网](https://www.tremor.so/)、[安装与组件导航](https://www.tremor.so/docs/getting-started/installation)。
- 用途/栈：图表、指标与仪表盘；当前 Tremor Raw 文档要求 React 18.2+、Tailwind 4+，使用时复核。
- 参考方式：视觉、代码候选；保留现有数据定义、格式和图表逻辑。
- 读取：具体组件文档及 [Blocks](https://blocks.tremor.so/)；区分 Raw/复制源码与旧包版本。
- 许可/范围：所选组件、Blocks 与依赖分别核实，不默认全部素材同一许可。
- 核验：2026-09-20 已读官网、安装文档中的版本要求及 Blocks 入口。

## tailark — Tailark

- 入口：[官网](https://tailark.com/)、[registry 与安装说明](https://tailark.com/docs)。
- 用途/栈：营销页、定价、功能、页脚区块；shadcn 生态，注意 Base UI 与 Radix 版本。
- 参考方式：布局、视觉、区块代码候选。
- 读取：免费 `@tailark-oss` 使用 oss.tailark.com；Pro `@tailark` 使用 tailark.com；从具体预览页取当前命令。
- 许可/范围：官方把免费 OSS kits 与付费 Quartz 分开，资产许可按条目确认。
- 核验：2026-09-20 已读官方 docs 的 namespace、免费/Pro 和 UI base 路径；不能沿用旧的免费 `@tailark` 假设。

## magic-ui — Magic UI

- 入口：[官网](https://magicui.design/)。
- 用途/栈：展示组件、文字与视觉动效；React、TypeScript、Tailwind、Motion。
- 参考方式：视觉、代码候选；评估是否服务内容及移动端体验。
- 读取：Browse Components 中的具体文档和演示；按需要查看当前工具接入说明。
- 许可/范围：官网将免费开源组件与 Pro 模板分开；所选代码和素材分别核实。
- 核验：2026-09-20 已读官网技术栈和免费/Pro 定位；未统一验证具体依赖。

## react-bits — React Bits

- 入口：[官网](https://reactbits.dev/)、[项目仓库](https://github.com/DavidHDev/react-bits)。
- 用途/栈：背景、文字与特色效果；React，部分组件可能涉及 WebGL 或额外动画依赖。
- 参考方式：视觉、代码候选；确认 JavaScript/TypeScript 与 CSS/Tailwind 变体。
- 读取：官网文字提取为空时用浏览器或仓库文档，从具体条目查源码和依赖。
- 许可/范围：[LICENSE.md](https://github.com/DavidHDev/react-bits/blob/main/LICENSE.md) 为 MIT + Commons Clause，含对组件本身销售、再授权和再分发的限制；采用前按当前文件核实，不能标为无限制 MIT。
- 核验：2026-09-20 已通过 GitHub API 读取 LICENSE.md 全文；官网提取无正文、llms.txt 读取失败，视觉效果和具体源码需由浏览器或仓库继续核实。

## motion-primitives — Motion Primitives

- 入口：[官网](https://motion-primitives.com/)、[项目仓库](https://github.com/ibelick/motion-primitives)。
- 用途/栈：组件状态变化与交互动效；框架及动画依赖按具体源码核实。
- 参考方式：交互模式、代码候选；与现有动效体系协调。
- 读取：官网不可读时看仓库 README、示例及源码，视觉效果仍需实际观察。
- 许可/范围：仓库元数据为 MIT；复制前读取固定版本 LICENSE 和附属依赖。
- 核验：2026-09-20 官网 docs 在读取器中返回 403；GitHub API 已核实仓库 homepage 与官网一致及许可元数据，403 不等于项目失效。

## aceternity — Aceternity UI

- 入口：[官网](https://ui.aceternity.com/)。
- 用途/栈：营销区块与视觉交互；React、Tailwind、Motion。
- 参考方式：视觉、代码候选；区分单组件、完整区块和模板。
- 读取：Browse Components 中的具体演示、依赖与源码。
- 许可/范围：官网有 All-Access 付费入口，能看到演示不等于可以免费复制代码。
- 核验：2026-09-20 已读官网定位与技术栈；具体内容层级和许可按条目核实。

## ai-elements — AI Elements

- 入口：[官方文档](https://elements.ai-sdk.dev/docs)。
- 用途/栈：对话、消息与 AI 产品组件；基于 shadcn，当前文档针对 React 19、Tailwind 4，示例涉及 Next.js/AI SDK。
- 参考方式：视觉、代码候选；逐组件确认 SDK 耦合，不为展示 UI 自动迁移整个应用。
- 读取：具体组件文档与源码；CLI 可能初始化 shadcn 或引入依赖，执行前检查影响。
- 许可/范围：代码许可与模型/网关服务费用分别确认；调研不要求购买服务或提供 API key。
- 核验：2026-09-20 已读官方介绍、目标 React/Tailwind 版本及安装影响。

## base-ui — Base UI

- 入口：[官网及说明](https://base-ui.com/)。
- 用途/栈：自定义设计系统的无样式交互组件；React，支持多种样式方案。
- 参考方式：行为、结构、代码候选；该库不提供统一成品视觉风格。
- 读取：所选组件的官方 API 与示例，保留焦点管理、键盘和可访问性行为。
- 许可/范围：官网 FAQ 明确 MIT；依赖与附加资产仍单独处理。
- 核验：2026-09-20 已读官网 React-only、无样式与 MIT 说明。

## mantine — Mantine

- 入口：[官网](https://mantine.dev/)、[llms.txt](https://mantine.dev/llms.txt)。
- 用途/栈：表单、输入、日期与组合控件；React，项目版本优先。
- 参考方式：视觉、代码候选；现有 Mantine 项目优先在本体系内组合。
- 读取：具体组件文档；官网列有 LLM 文档、Skills 和 MCP，实际调用以宿主可用工具为准。
- 许可/范围：采用时查看仓库、具体包和依赖的 LICENSE，外部工具费用另核实。
- 核验：2026-09-20 已读官网 React、原生 CSS 和 AI 工具入口，索引内容按任务读取。

## ant-design — Ant Design

- 入口：[官网](https://ant.design/)。
- 用途/栈：企业应用、表格、筛选和表单；此条指 React Ant Design，其他框架实现需单独查。
- 参考方式：布局、交互模式、代码候选；已有项目优先沿用当前版本与主题。
- 读取：Components 中所选组件的 API、演示和源码，注意主版本差异。
- 许可/范围：核实官方仓库与依赖的 LICENSE，不混入独立模板产品的许可假设。
- 核验：2026-09-20 已读官网入口与 React 定位；API 需按项目版本核实。

## design-spells — Design Spells

- 入口：[灵感目录](https://designspells.com/)。
- 用途/栈：交互细节与反馈设计；视觉灵感，不绑定实现框架。
- 参考方式：模式借鉴，不默认提供或授权复制源码。
- 读取：具体作品及原站，观察行为后记录真正借鉴的细节。
- 许可/范围：作品、视频和素材归各自权利方；原站资源单独判断。
- 核验：2026-09-20 已读官网定位并确认 www 重定向，不代表逐个作品已查看。

## landingfolio — Landingfolio

- 入口：[灵感目录](https://www.landingfolio.com/)。
- 用途/栈：落地页结构、首屏、定价和区块顺序；灵感不限制栈，代码产品另看技术要求。
- 参考方式：布局/视觉学习；复制源码需要另行核实具体授权。
- 读取：具体案例及原始作品；浏览器看实际布局，目录截图只证明可见状态。
- 许可/范围：官网另有组件库、模板和会员，灵感可浏览不代表付费代码可复制。
- 核验：2026-09-20 已读灵感与组件/会员分类；只观察到 MCP 入口，未验证连接或权限。

## awwwards — Awwwards

- 入口：[作品目录](https://www.awwwards.com/)。
- 用途/栈：整体构图、品牌表达与展示方法；不限制技术栈。
- 参考方式：视觉/交互模式，不作为组件源码或开放许可目录。
- 读取：选择与产品相关的作品后观察原站，不只看评分或缩略图。
- 许可/范围：作品及素材各自授权；展示网站的高成本效果不默认适合业务后台。
- 核验：2026-09-20 已读作品分类与展示入口，具体作品需在任务中访问。

## 更新约定

保留稳定 ID、明确用途和证据链接，只更新实际核实的字段及日期。
确认官网与仓库关联后才指定源码归属，目录外的官方来源同样可用。
安装命令从采用时的具体组件页获取，不维护整库命令快照。
上游改编和固定提交见 [NOTICE](../NOTICE.md)，第三方页面不因列入目录而适用本 Skill 的 MIT 许可。
