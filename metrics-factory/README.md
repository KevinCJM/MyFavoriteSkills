# MetricsFactory Skill

用于让 Codex/智能体可移植地调用本地 MetricsFactory 金融指标计算工具。

这个 skill 负责：

- 检查 MetricsFactory 运行环境；
- 在项目局部创建 Python venv；
- 导出当前仓库支持的指标目录；
- 生成 dry-run 执行计划；
- 执行区间指标和滚动指标计算；
- 输出可审计的 `run_manifest.json`。

## 目录结构

```text
metrics-factory/
├── SKILL.md
├── agents/openai.yaml
├── references/
│   ├── environment.md
│   ├── job-schema.md
│   └── metric-catalog.md
└── scripts/
    ├── check_runtime.py
    ├── export_metric_catalog.py
    ├── run_metrics_job.py
    ├── runtime_support.py
    └── setup_runtime.py
```

## 安装

把整个 `metrics-factory` 目录复制到 Codex skills 目录，例如：

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R metrics-factory "${CODEX_HOME:-$HOME/.codex}/skills/metrics-factory"
```

也可以放在项目内：

```text
MetricsFactory/skills/metrics-factory
```

## 前提

你需要有一个 MetricsFactory 源码目录。该目录至少包含：

```text
metrics_factory.py
metrics_cal_config.py
period_metrics_cal.py
rolling_metrics_cal.py
```

下文用：

- `<skill-dir>` 表示本 skill 目录；
- `<project-root>` 表示 MetricsFactory 源码目录；
- `<python>` 表示通过环境检查的 Python。

## 检查环境

先运行：

```bash
python <skill-dir>/scripts/check_runtime.py --project-root <project-root>
```

成功时返回 JSON，其中 `can_run` 为 `true`。

如果缺少依赖或 native wheel 架构不匹配，创建项目局部环境：

```bash
python <skill-dir>/scripts/setup_runtime.py --project-root <project-root>
```

默认会创建：

```text
<project-root>/.metricsfactory-venv
```

不会安装到系统 Python 或全局 user site-packages。

## 导出指标目录

```bash
python <skill-dir>/scripts/export_metric_catalog.py --project-root <project-root> --format markdown
python <skill-dir>/scripts/export_metric_catalog.py --project-root <project-root> --format json
```

`references/metric-catalog.md` 是快照。对目标机器或目标仓库做最终判断前，应重新运行导出脚本。

## 运行指标任务

先准备 `job.json`。schema 见：

```text
references/job-schema.md
```

先 dry-run：

```bash
<python> <skill-dir>/scripts/run_metrics_job.py --project-root <project-root> --request job.json --dry-run
```

确认 `can_execute=true` 后执行：

```bash
<python> <skill-dir>/scripts/run_metrics_job.py --project-root <project-root> --request job.json --execute
```

执行成功后，输出目录会包含 parquet 文件和：

```text
run_manifest.json
```

## 输入数据要求

所有输入是宽表 `pandas.DataFrame`：

- index 为升序日期；
- columns 为产品代码；
- values 为数值；
- 所有输入表必须有完全一致的 index、columns 和顺序。

区间指标需要：

```text
log_return
close_price
high_price
low_price
volume
```

滚动指标需要：

```text
open_price
close_price
high_price
low_price
volume
```

## 数据口径建议

强烈建议使用复权净值或复权价格：

- `close_price` 使用复权净值/复权收盘价；
- `log_return` 从同一条复权 close 序列生成；
- open/high/low/close 保持同一复权口径；
- 不混用未复权价格、单位净值和累计净值。

无真实成交量的产品，不应解释 `Vol*`、`OBV`、`PVT`、`VR` 等量价指标。

## 重要风险

- 滚动指标存在已知 open/close 参数顺序风险。默认会阻断 rolling 执行。
- 只有用户明确接受风险时，才使用：

```bash
--allow-rolling-open-close-risk
```

- `price_basis=unknown` 默认阻断。只有用户明确接受未知价格口径风险时，才使用：

```bash
--allow-unknown-basis
```

## 验证

分享或修改后建议运行：

```bash
python ${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py <skill-dir>
python -m py_compile <skill-dir>/scripts/*.py
python <skill-dir>/scripts/check_runtime.py --project-root <project-root>
python <skill-dir>/scripts/export_metric_catalog.py --project-root <project-root> --format json
```

## 不要打包

分享 skill 时不要包含：

- `__pycache__`
- `.venv`
- `.metricsfactory-venv`
- 临时输出目录
- 私有 pip 源 token 或代理配置
