# tushare-fetcher

`tushare-fetcher` 是一个用于生成、冒烟测试和固化 Tushare 数据获取脚本的 Codex Skill。

它会根据用户的 Tushare 积分、接口文档 JSON、目标接口参数和限频规则，生成将数据保存为 Parquet 的 Python 脚本。

## 主要能力

- 读取 `tushare_interfaces_ai_optimized.json` 中的接口信息。
- 根据用户积分判断接口门槛和限频风险。
- 在用户未提供积分时，主动要求先配置积分。
- 生成独立的 Tushare 获取脚本。
- 冒烟测试脚本是否能真实获取数据并写出 Parquet。
- 冒烟测试通过后，将脚本固化到 skill 并更新接口 JSON。
- 默认输出格式固定为 Parquet。

## 目录结构

```text
tushare-fetcher/
├── SKILL.md
├── README.md
├── agents/
│   └── openai.yaml
├── references/
│   └── tushare_interfaces_ai_optimized.json
└── scripts/
    ├── configure_points.py
    ├── generate_fetch_script.py
    ├── smoke_test_fetch_script.py
    ├── solidify_fetch_script.py
    ├── tushare_runtime.py
    └── solidified/
```

## 使用前配置积分

每个 Tushare 用户的积分不同。第一次使用时，如果用户没有在请求中说明积分，智能体应先查询本地配置：

```bash
python3 "$SKILL_DIR/scripts/configure_points.py" --show
```

如果返回 `missing`，需要询问用户当前 Tushare 积分，然后保存：

```bash
python3 "$SKILL_DIR/scripts/configure_points.py" --points 10000
```

配置默认保存在用户本地配置目录：

```text
~/.config/tushare-fetcher/config.json
```

也可以通过环境变量或参数指定配置路径：

```bash
export TUSHARE_FETCHER_CONFIG=/path/to/config.json
python3 "$SKILL_DIR/scripts/configure_points.py" --points 10000
```

## 生成数据获取脚本

示例：生成 `stock_basic` 获取脚本。

```bash
python3 "$SKILL_DIR/scripts/generate_fetch_script.py" \
  --api stock_basic \
  --output-script ./stock_basic_fetch.py
```

如果没有显式传入 `--points`，脚本会自动读取本地积分配置。也可以直接传入并保存：

```bash
python3 "$SKILL_DIR/scripts/generate_fetch_script.py" \
  --api stock_basic \
  --points 10000 \
  --save-points \
  --output-script ./stock_basic_fetch.py
```

常用参数：

```text
--api API
--points N
--save-points
--user-config PATH
--interfaces-json PATH
--output-script PATH
--strategy single_call|date_loop|code_loop|date_range|param_grid|user_params
--default-output-dir PATH
--skeleton-only
--confirm-entitlement
```

## 冒烟测试

生成脚本后，先做小范围真实调用：

```bash
python3 "$SKILL_DIR/scripts/smoke_test_fetch_script.py" \
  --script ./stock_basic_fetch.py \
  --api stock_basic \
  --result-json ./stock_basic_smoke.json
```

如果需要读取项目 `config.py` 中的 `TUSHARE_TOKEN`，必须显式传入：

```bash
python3 "$SKILL_DIR/scripts/smoke_test_fetch_script.py" \
  --script ./stock_basic_fetch.py \
  --api stock_basic \
  --allow-config-token \
  --result-json ./stock_basic_smoke.json
```

默认 token 来源是环境变量 `TUSHARE_TOKEN`。

## 固化脚本

只有冒烟测试通过后才可以固化：

```bash
python3 "$SKILL_DIR/scripts/solidify_fetch_script.py" \
  --api stock_basic \
  --script ./stock_basic_fetch.py \
  --smoke-result ./stock_basic_smoke.json \
  --target skill
```

固化后会：

- 复制脚本到 `scripts/solidified/`。
- 在接口 JSON 中写入 `solidified_script` 元数据。
- 记录脚本 hash、接口 JSON hash、冒烟命令、输出格式和限频策略。

## 输出规则

生成的数据获取脚本固定保存 Parquet。

默认输出目录：

```text
./data/tushare/{api}
```

运行脚本时可以覆盖：

```bash
python3 ./stock_basic_fetch.py --output-dir /path/to/output
```

## 安全规则

- 不要假设用户积分，必须来自当前请求或本地配置。
- 积分不等于真实权限；实际可用性仍以 Tushare 账号权限和 API 返回为准。
- 不要把 token 写入日志、metadata、JSON 或 README。
- 默认不读取项目 `config.py`，除非用户明确允许 `--allow-config-token`。
- skill 内路径应相对 skill 根目录解析，避免写死个人机器路径。

## 验证

```bash
python3 -m py_compile "$SKILL_DIR"/scripts/*.py
python3 "$SKILL_CREATOR_DIR/scripts/quick_validate.py" "$SKILL_DIR"
python3 "$SKILL_DIR/scripts/generate_fetch_script.py" --help
```

