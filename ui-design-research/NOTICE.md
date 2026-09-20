# 来源与许可记录

版本：1.2.0；制作及更新日期：2026-09-20。

v1.1 将来源拆分为按需读取的分类，补充设计取舍、状态与数据检查、评测用例，以及 APG、Carbon、React Aria 的官方资料入口。以下上游固定提交和归属保持不变；新增资料作为参考链接，不附带第三方组件源码。

v1.2 按第二轮审核补强触发边界、本地设计依据、设计主线、渲染与文案检查及评测方法，新增 Emil 的动效资料入口。核对的概念参考包括 [Anthropic frontend-design](https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md)、[PaulRBerg frontend-design](https://github.com/PaulRBerg/agent-skills/blob/main/skills/frontend-design/SKILL.md)、[nolly design-md](https://github.com/nolly-studio/agent-skills/blob/main/skills/design-md/SKILL.md) 和 mblode 的 [ui-verification](https://github.com/mblode/agent-skills/blob/main/skills/ui-verification/SKILL.md)、[评测方法](https://github.com/mblode/agent-skills/blob/main/skills/agent-skills-creator/references/evaluation-and-iteration.md)。本次仅独立表述通用方法与添加链接，不收录这些项目的正文、脚本或审美规则集；链接内容遵循各自许可，不因被引用而适用本包 MIT。

本 Skill 独立维护。以下文件仅作为经过检查的改编资料，不在运行时加载，也未运行上游安装器或脚本。
所有重写和目录选择均服务于 ui-design-research；不代表上游作者背书。

## ByeongminLee/nextjs-claude-code

固定提交：`330a71e3d12264515ce3477e446d29fd34a88a9d`。

采用按需求分类、先读项目组件体系再查官方资料的结构；删除 NCC/spec 目录和指定工具依赖。

- [template/.claude/skills/ui-reference/SKILL.md](https://github.com/ByeongminLee/nextjs-claude-code/blob/330a71e3d12264515ce3477e446d29fd34a88a9d/template/.claude/skills/ui-reference/SKILL.md)
  SHA-256：`be3b411422fd5f7907b7319d8384040f3fa0848328a431f3d6ea365676ef8dbf`。
- [LICENSE](https://github.com/ByeongminLee/nextjs-claude-code/blob/330a71e3d12264515ce3477e446d29fd34a88a9d/LICENSE)
  SHA-256：`55807ab72ff4c04c2c9103e63151921895ba5c6f0054b7c438c9b46a50cb95f1`。

保留的上游许可证全文：

```text
MIT License

Copyright (c) 2026 Byeongmin Lee

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Xiaoyang-Hu-96/design-resource-library

固定提交：`bbd6b7b6aa2afc47b33406b7f5313cfde9de33ad`。

选择性改编组件与设计灵感目录；删除社交账号、作者个性化信息、固定推荐数量和强制追问。

- [skills/design-resource-library/SKILL.md](https://github.com/Xiaoyang-Hu-96/design-resource-library/blob/bbd6b7b6aa2afc47b33406b7f5313cfde9de33ad/skills/design-resource-library/SKILL.md)
  SHA-256：`f6559002d8871e6249a33361abd884ba7f15662427d6884f329b65a3a7b2d73a`。
- [skills/design-resource-library/reference.md](https://github.com/Xiaoyang-Hu-96/design-resource-library/blob/bbd6b7b6aa2afc47b33406b7f5313cfde9de33ad/skills/design-resource-library/reference.md)
  SHA-256：`132cf567f53d59691d71ac39083806e2f343b1e69c622cbcf74dc1c510b1dcef`。
- [LICENSE](https://github.com/Xiaoyang-Hu-96/design-resource-library/blob/bbd6b7b6aa2afc47b33406b7f5313cfde9de33ad/LICENSE)
  SHA-256：`ac99da8e9b6e8ebd9d592f3f0a450c7d9b5ebc4c22fbbc148e844fb6d521351c`。

保留的上游许可证全文：

```text
MIT License

Copyright (c) 2026 Xiaoyang Hu (Elena)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## JasonColapietro/suede-creator-skills

固定提交：`05d69df3c3b6a51d497ba14b0be90cc8932216a7`。

改编组件选源、映射本地样式和渲染验证方法；删除品牌规则、配套技能包依赖、历史域名判断和过时来源归属。

- [skills/suede-design/SKILL.md](https://github.com/JasonColapietro/suede-creator-skills/blob/05d69df3c3b6a51d497ba14b0be90cc8932216a7/skills/suede-design/SKILL.md)
  SHA-256：`e4d5ba4d76a5566fbc93550373ac69a56004086e98d23ea33aaedf00272be599`。
- [skills/suede-design/references/ui-component-sources.md](https://github.com/JasonColapietro/suede-creator-skills/blob/05d69df3c3b6a51d497ba14b0be90cc8932216a7/skills/suede-design/references/ui-component-sources.md)
  SHA-256：`b5e89b92c008d3372aab82a116842b9a8ede895884b52fca5f98c2c99e1b4f51`。
- [LICENSE](https://github.com/JasonColapietro/suede-creator-skills/blob/05d69df3c3b6a51d497ba14b0be90cc8932216a7/LICENSE)
  SHA-256：`14fd9c2c7341f4baa182dbd75393a29c1a91a032452e974a15f086e6a1369d4d`。

保留的上游许可证全文：

```text
MIT License

Copyright (c) 2026 Suede Labs AI

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 本地维护与第三方内容

入口指令和输出规范已重写为中文；目录条目通过官方资料重新核实并记录核验范围。
更新时比较上游固定版本，选择性吸收并保留本文件及所需许可证。
目录中的第三方组件、字体、图标、图片和服务不因被引用而获得本 Skill 的许可。
