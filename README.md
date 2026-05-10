# jsonseek

> **给开发者和 coding agent 的 JSON/JSONL 导航与局部操作工具。**
>
> 核心目的：减少 LLM 全量读取大 JSON 的 token 浪费。先 `shape`/`fields`/`query` 定位，再 `get`/`set`/`add`/`del`/`append` 局部操作。
>
> 支持 JSON + JSONL 的结构理解、字段简表、局部查询和局部修改。

---

## JSON 为什么值得专门做一个工具

JSON 是现代数据交换的事实标准。从机器学习实验记录、API 接口配置、应用日志流，到微服务注册表和爬虫数据存储，JSON/JSONL 无处不在：

- **ML 实验追踪**：训练参数、指标曲线、模型配置全存在 JSON 里，一个实验目录轻松堆出几十 MB
- **API/微服务配置**：服务发现、路由规则、环境变量往往以 JSON 配置形式管理
- **日志与事件流**：结构化日志（JSONL）比纯文本更易查询，但文件体积增长极快
- **数据交换**：前后端通信、服务间 RPC、爬虫落地，JSON 是最常见的数据格式

问题是：**JSON 文件越大，LLM 和开发者处理它的成本越高**。全量 `cat` 一个 10MB 的 JSON 进上下文，相当于烧掉几百万 token；即使人类开发者，在几千行嵌套结构里找某个字段也是折磨。

**jsonseek 就是来解决这个问题的**——用局部操作替代全量读取，用结构化查询替代肉眼翻找。对于需要频繁处理 JSON/JSONL 的 coding agent 和开发者来说，这是一个值得一看的工具。

---

## 为什么用 jsonseek（面向 Coding Agent）

当你面对一个 10MB 的 JSON 文件时，全量 `cat` 进上下文是灾难性的 token 浪费。jsonseek 让你：

1. **先理解结构** — `shape` 看骨架，`fields` 看字段清单，不用读内容
2. **再定位目标** — `query` 搜索关键词，`ls` 看某层的子节点，`get` 取具体值
3. **最后局部修改** — `set`/`add`/`del`/`append` 只改需要改的地方

### Token 节省估算

| 文件大小 | 操作 | 全量读取 | jsonseek 输出 | 节省 |
|---|---|---|---|---|
| 100KB 配置 JSON | `shape` | ~25K tokens | ~100 tokens | **99%+** |
| 100KB 配置 JSON | `fields` | ~25K tokens | ~300 tokens | **98%+** |
| 100KB 配置 JSON | `get` 单值 | ~25K tokens | ~10 tokens | **99%+** |
| 100KB 配置 JSON | `query` 命中几处 | ~25K tokens | ~100 tokens | **99%+** |
| 10MB 日志 JSONL | `shape` 采样 | ~2.5M tokens | ~200 tokens | **99.9%+** |
| 10MB 日志 JSONL | `query` 命中几十条 | ~2.5M tokens | ~1K tokens | **99.9%+** |

> 粗略估算：1 token ≈ 4 字节英文文本。实际比例因内容和 tokenizer 差异会有浮动，但数量级不变——**越大文件的节省越夸张**。

**典型 agent 工作流：**

```bash
# Step 1: 理解结构（零内容读取，纯元数据）
jsonseek shape config.json          # 看到有几层、数组多大
jsonseek fields config.json         # 看到所有字段名和类型

# Step 2: 定位目标（只读命中部分）
jsonseek query config.json api_key  # 找到 api_key 在哪
jsonseek get config.json services[0].endpoint

# Step 3: 局部修改（只写目标路径）
jsonseek set config.json services[0].endpoint "https://new.api.com"
jsonseek del config.json services[0].deprecated_field
```

---

## 安装

```bash
pip install -e .
jsonseek --version    # jsonseek 0.1.0
```

要求 Python >= 3.8。跨平台支持 Windows / macOS / Linux。

---

## 命令速查（Agent 模式）

### 只读命令（安全，不会改文件）

| 命令 | 用途 | Agent 场景 |
|---|---|---|
| `shape FILE` | 显示 JSON 骨架树 | 第一次看到未知 JSON，快速理解结构 |
| `fields FILE [KEYWORD]` | 列出所有字段及类型 | 找字段名、看类型分布、过滤关键字 |
| `ls FILE [PATH]` | 列出某路径下的子节点 | 像 `ls` 目录一样浏览 JSON |
| `get FILE PATH` | 获取某个路径的值 | 精确读取单个值，避免全量加载 |
| `query FILE TERM` | 搜索 key 或 value | 找某个配置项在哪 |

### 写命令（会修改文件，建议加 `--backup`）

| 命令 | 用途 | Agent 场景 |
|---|---|---|
| `set FILE PATH VALUE` | 设置值 | 修改配置项、更新 URL、改数值 |
| `add FILE PATH VALUE` | 给对象加新键 | 新增配置字段 |
| `del FILE PATH` | 删除键或数组元素 | 清理废弃字段 |
| `append FILE PATH VALUE` | 往数组追加（JSON） | 往列表加新项 |
| `append FILE VALUE` | 追加记录（JSONL） | 往 JSONL 末尾加记录 |

### 全局选项

- `--output json` — 机器输出（给下游工具/LLM 解析）
- `--backup` — 修改前创建 `.bak`
- `--kind {json,jsonl}` — 强制指定文件类型

### Windows PowerShell 引号陷阱

PowerShell 会吃掉 JSON 字符串里的双引号，导致 `append` 或 `set` 的 JSON 值退化为裸字符串：

```powershell
# 错误：会变成字符串 "{id:4,name:eve}"
jsonseek append data.json items '{"id":4,"name":"eve"}'

# 正确：用 Python 中转生成 JSON
python -c "import json; print(json.dumps({'id':4,'name':'eve'}))" | Set-Content v.txt -NoNewline
$v = Get-Content v.txt
jsonseek append data.json items $v
```

在 macOS/Linux bash 或 Windows CMD 中没有这个问题。

---

## 路径语法

```bash
# 点号分隔
jsonseek get data.json meta.settings.timeout

# 方括号键名（支持字符串键）
jsonseek get data.json meta[settings][timeout]
jsonseek get data.json users[0][name]

# 数组索引
jsonseek get data.json items[0][1]

# JSONL 记录选择器
jsonseek get data.jsonl '[0].name'
jsonseek get data.jsonl 'records[12].payload.diff'
jsonseek set data.jsonl '[0].age' 30
```

规则：
- `[数字]` → 数组索引（`[0]`, `[12]`）
- `[字符串]` → 对象键名（`[name]`, `[key-1]`）
- 连续方括号直接连用：`a[b][c]`

---

## JSON vs JSONL 差异速查

| | JSON | JSONL |
|---|---|---|
| 读取 | 一次性加载到内存 | 流式逐行扫描 |
| `shape` | 完整树 | 采样前 N 条 |
| `fields` | 统计 count（出现次数） | 统计 coverage（记录覆盖率） |
| `get`/`ls` | `path` 直接解析 | 路径必须以 `[N].` 或 `records[N].` 开头 |
| `set`/`add`/`del` | 直接 patch 内存树 | 整文件 rewrite（原子替换） |
| `append` | 往数组内追加 | 根级追加一条记录 |

---

## Agent 实战示例

### 场景 1：探索未知配置 JSON

```bash
jsonseek shape config.json
# (root)
#   services
#     services[*]  (object) [5]
#       services[*].name
#       services[*].endpoint
#       services[*].timeout
#   database
#     database.host
#     database.port

jsonseek fields config.json
# services  types=array  paths=1
# name      types=string paths=5
# endpoint  types=string paths=5
# timeout   types=integer paths=5
# database  types=object paths=1
# host      types=string paths=1
# port      types=integer paths=1

jsonseek query config.json production
# services[2].name  [value] 'production'

jsonseek get config.json services[2].endpoint
# https://prod.api.example.com
```

### 场景 2：批量修改 JSONL

```bash
jsonseek shape logs.jsonl
# (root)
#   timestamp  (string)
#   level      (string)
#   message    (string)

jsonseek query logs.jsonl ERROR --max-results 5
# message  [value] 'connection failed' record=12 line=15

# 把第 12 条记录的 level 改成 warning
jsonseek set logs.jsonl '[12].level' "warning"

# 删除第 100 条记录
jsonseek del logs.jsonl '[100]'

# 追加新记录
jsonseek append logs.jsonl '{"timestamp":"2024-01-01","level":"info","message":"started"}'
```

### 场景 3：精确局部修改（避免全量读取）

```bash
# 不要这样：cat 10MB.json | 塞给 LLM 分析
# 要这样：
jsonseek get large.json data[0].metrics.cpu_usage
# 42.5

jsonseek set large.json data[0].metrics.cpu_usage 45.0
```

---

## 项目结构

```
src/jsonseek/
  cli.py            # CLI 入口
  types.py          # 核心数据类型
  errors.py         # 异常
  detect.py         # 文件类型识别
  formatters.py     # 输出格式化（pretty/json）
  path_parser.py    # 路径解析（支持 . / [] 混用）
  value_utils.py    # 类型推断与输入强制转换
  io/               # 文件 I/O（json, jsonl, rewrite）
  walkers/          # 树遍历（shape, fields, query）
  patch/            # Patch 操作（locator, object/array ops）
  commands/         # 命令处理器
tests/              # 单元测试（53 个用例）
```

---

## Roadmap

- [x] JSON 读写与 patch
- [x] JSONL 流式扫描与 rewrite
- [x] `--output json` 机器输出
- [x] Windows / macOS / Linux 跨平台支持
- [ ] `--dry-run` 预览修改
- [ ] Claude Code / Cursor / OpenAI-compatible coding workflows 插件化接入

---

## License

MIT
