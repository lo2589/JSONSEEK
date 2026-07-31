# jsonseek

[![PyPI version](https://badge.fury.io/py/jsonseek.svg)](https://badge.fury.io/py/jsonseek)
[![Downloads](https://static.pepy.tech/badge/jsonseek)](https://pepy.tech/project/jsonseek)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

**JSON/JSONL 解析工具包，专为 LLM 设计。**

> When LLMs touch JSON, they should `shape` first, `query` second, never `cat` the whole file.
> When a human touches JSON, the same rules apply — just with a keyboard instead of a context window.

`jsonseek` 是一个针对 **大 JSON / JSONL** 文件做的 **LLM-friendly 解析与局部修改工具**。核心目标：**不要让 LLM `cat` 整个 JSON 进上下文**。先 `shape` 看骨架，再 `query` / `get` 精准定位，最后 `set` / `add` / `del` / `append` 做最小化修改。

支持 **结构理解、字段简表、局部查询、局部修改、Bug 定位与修复** —— JSON 和 JSONL 同一套命令。

---

## 🤖 给 LLM Coding Agent 的 Skills（Claude / Kimi / Cursor / Codex 等）

> **直接告诉 agent "用 jsonseek" 即可。** Skills 文档就摆在下面，按需查阅。

| Skills | 链接 | 适用 |
|---|---|---|
| **SKILL.md** | 👉 [在 GitHub 上查看](https://github.com/lo2589/JSONSEEK/blob/main/skills/jsonseek/SKILL.md) | Agent 启动加载：触发场景、核心命令速查、**写操作三铁律**、Windows API 兜底 |
| **commands.md** | 👉 [在 GitHub 上查看](https://github.com/lo2589/JSONSEEK/blob/main/skills/jsonseek/references/commands.md) | 按需查阅：每个命令的 flag / 示例 / 输出格式 |
| **path-syntax.md** | 👉 [在 GitHub 上查看](https://github.com/lo2589/JSONSEEK/blob/main/skills/jsonseek/references/path-syntax.md) | 按需查阅：路径语法全集（点号 / 方括号 / 混合 / 数组 / 转义） |

**Skills 在 GitHub 上的位置**：[`lo2589/jsonseek/skills/jsonseek/`](https://github.com/lo2589/JSONSEEK/tree/main/skills/jsonseek)

**接入 agent**（Claude Code / Cursor / Codex 等）：

```bash
git clone https://github.com/lo2589/JSONSEEK.git
ln -s ../jsonseek/skills/jsonseek/SKILL.md ~/.claude/skills/jsonseek.md
# 或 ~/.cursor/skills/  ~/.codex/skills/
```

或 pip 安装后从 site-packages 里：

```
<site-packages>/jsonseek-<current_version>.data/data/skills/jsonseek/
├── SKILL.md
└── references/
    ├── commands.md
    └── path-syntax.md
```

---

## 为什么 JSON 值得专门做一个工具

JSON 是现代数据交换的事实标准。从机器学习实验记录、API 接口配置、应用日志流，到微服务注册表和爬虫数据存储，JSON/JSONL 无处不在：

- **ML 实验追踪**：训练参数、指标曲线、模型配置全存在 JSON 里，一个实验目录轻松堆出几十 MB
- **API / 微服务配置**：服务发现、路由规则、环境变量往往以 JSON 配置形式管理
- **日志与事件流**：结构化日志（JSONL）比纯文本更易查询，但文件体积增长极快
- **数据交换**：前后端通信、服务间 RPC、爬虫落地，JSON 是最常见的数据格式

**问题是：JSON 越大，处理它的成本越高**。全量 `cat` 一个 10MB JSON 进 LLM 上下文，等于烧掉几百万 token；人类开发者面对几千行嵌套结构手翻也是折磨。

`jsonseek` 就是来解决这个问题的——**用局部操作替代全量读取，用结构化查询替代肉眼翻找**。对于需要频繁处理 JSON / JSONL 的 **LLM coding agent 和开发者**，这是一个必备工具。

---

## 为什么 LLM 应该用 jsonseek

当你（或你正在运行的 Claude / Kimi / Cursor / Codex 等 agent）面对一个 10MB 的 JSON 时，全量 `cat` 进上下文是 **灾难性的 token 浪费**。`jsonseek` 让 agent 可以：

1. **先理解结构** —— `shape` 看骨架、`fields` 看字段表，**不读内容**
2. **再定位目标** —— `query` 搜关键词、`ls` 看某层子节点、`get` 取指定值
3. **最后局部修改** —— `set` / `add` / `del` / `append` 只动需要动的地方

### Token 节省估算

| 文件大小 | 操作 | 全量读取 | jsonseek 输出 | 节省 |
|---|---|---|---|---|
| 100KB config JSON | `shape` | ~25K tokens | ~100 tokens | **99%+** |
| 100KB config JSON | `fields` | ~25K tokens | ~300 tokens | **98%+** |
| 100KB config JSON | `get` 单值 | ~25K tokens | ~10 tokens | **99%+** |
| 100KB config JSON | `query` 命中几条 | ~25K tokens | ~100 tokens | **99%+** |
| 10MB log JSONL | `shape` 采样 | ~2.5M tokens | ~200 tokens | **99.9%+** |
| 10MB log JSONL | `query` 命中几十 | ~2.5M tokens | ~1K tokens | **99.9%+** |

> 粗估：1 token ≈ 4 bytes 英文文本。实际比例取决于内容和 tokenizer，但量级是稳定的——**文件越大，省得越多**。

### 给 LLM 的典型工作流

```bash
# 1. 看骨架 — 不用读内容
jsonseek shape data.jsonl

# 2. 看有哪些字段
jsonseek fields data.jsonl --top

# 3. 搜关键字段
jsonseek query data.jsonl password --record-id-field id --max-results 5

# 4. 读具体值
jsonseek get data.jsonl '[3].password'

# 5. 修改（**永远先 --dry-run**）
jsonseek set data.jsonl '[3].password' 'newpass' --dry-run
jsonseek set data.jsonl '[3].password' 'newpass' --backup
```

---

## 安装

```bash
pip install jsonseek
```

需要 Python 3.8+。**零依赖、零配置**，装完即用。

```bash
$ jsonseek --version
jsonseek <current_version>
```

---

## 命令一览

### 读 / 检视（只读，安全）

| 命令 | 用途 |
|---|---|
| `shape FILE` | 显示文件结构（树形） |
| `fields FILE [keyword]` | 列出所有字段及类型 |
| `ls FILE [path]` | 列出某层子节点 |
| `get FILE path` | 取某个路径的值 |
| `query FILE keyword` | 搜索 key / value |
| `extract PATTERN path` | 批量从多个文件取同一个路径 |
| `concat PATTERN` | 合并多个 JSON 文件为 JSONL |

### 改 / 局部操作（写入）

| 命令 | 用途 |
|---|---|
| `set FILE path value` | 修改字段 |
| `add FILE path value` | 添加新字段 |
| `del FILE path` | 删除字段 / 数组项 |
| `append FILE path value` | 向数组追加一项 |
| `extend FILE path json_array` | 用一个 JSON 数组扩展目标数组 |
| `cutline FILE N` | 提取 JSONL 第 N 行到临时文件 |
| `replaceline FILE N` | 替换 JSONL 第 N 行 |

### 通用选项

| 选项 | 用途 |
|---|---|
| `--output json` | 输出机器可读 JSON（管道 / agent 调用必加） |
| `--backup` | 写操作前生成 `.bak` 备份 |
| `--dry-run` | **写操作前永远先加这个预览** |
| `--kind {json,jsonl}` | 强制文件类型（自动检测失败时） |
| `--encoding ENCODING` | 强制编码（自动检测失败时，例如 gbk） |
| `--context N` | JSONL 预览行数（默认 2） |

### 路径语法

| 写法 | 例子 | 含义 |
|---|---|---|
| 点号 | `a.b.c` | `a -> b -> c` |
| 方括号 | `a[key1][key2]` | `a -> key1 -> key2` |
| 混合 | `a[key1].b[0]` | `a -> key1 -> b -> 0` |
| 数组下标 | `items[0][1]` | `items -> 0 -> 1` |

---

## 三条铁律（给 LLM 也给人类）

1. **改之前，永远先 `--dry-run`**：
   ```bash
   jsonseek set file.json path value --dry-run
   # [DRY-RUN] Before: path = old
   # [DRY-RUN] After:  path = new
   ```
2. **写之前，永远加 `--backup`**：
   ```bash
   jsonseek set file.json path value --backup
   # → 生成 file.json.bak
   ```
3. **管道到另一个工具，永远加 `--output json`**：
   ```bash
   jsonseek query file.json keyword --output json | jq '.hits[0]'
   ```

---

## 为 AI / Coding Agent 设计

`jsonseek` 的设计哲学是 **LLM 的 token 预算**：

- **输出尽可能短**：默认输出筛过的关键信息，不打印无用结构
- **输出格式稳定**：所有命令都支持 `--output json`，agent 能直接解析
- **写操作可预览**：所有 `set` / `add` / `del` 都有 `--dry-run`，agent 在工具调用前能先看 diff
- **干运行**：`jsonseek shape` 在 10MB JSONL 上**只读前 100 行**就停（`--sample-size` 可调），token 用量恒定

典型 agent 工作流：

```text
读取 → shape / fields / ls / query / get
       ↓ （了解结构）
定位 → query / get
       ↓ （找到目标）
修改 → set / add / del / append   （先 --dry-run 预览 → 再加 --backup 真改）
       ↓ （验证）
读取 → query / get
```

---

## 跨平台

- **macOS / Linux**：原生命令行工作
- **Windows PowerShell**：**读命令**（`shape` / `fields` / `get` / `query` / `ls` / `extract` / `concat`）走 CLI 完全可用
- **Windows 写命令**：因为 PowerShell 会剥离双引号，复杂值会失败——**用 Python API 代替**

Windows 写操作的 Python API：

```python
import sys
sys.path.insert(0, '.')

from jsonseek.commands.set_cmd import set_value
from jsonseek.commands.add_cmd import add_value
from jsonseek.commands.append_cmd import append_value
from jsonseek.commands.extend_cmd import extend_value
from jsonseek.commands.del_cmd import del_value
from jsonseek.commands.replaceline_cmd import replace_line

# Set/Add/Append/Extend 复杂值 — 不受 shell quoting 影响
set_value('file.json', 'path', {"key": "value"})
add_value('file.json', 'path', ["item1", "item2"])
append_value('file.json', 'items', {"id": 1})
extend_value('file.json', 'items', [{"id": 2}, {"id": 3}])

# Delete
del_value('file.json', 'path')

# JSONL 替换整行
replace_line('file.jsonl', 5, '{"id": 5, "name": "fixed"}')
```

CLI 写命令成功时打印 patch 预览，失败时打印 `Error: ...`。Python API 写助手成功时静默，失败时抛异常。

---

## 命令参考

完整文档见：

| 文档 | 内容 |
|---|---|
| [commands.md](https://github.com/lo2589/JSONSEEK/blob/main/skills/jsonseek/references/commands.md) | 每个命令的详细选项、参数、示例 |
| [path-syntax.md](https://github.com/lo2589/JSONSEEK/blob/main/skills/jsonseek/references/path-syntax.md) | 路径语法的所有写法（点号、方括号、混合、数组下标、转义、负数下标等） |

> Skills 链接见 **前面**的 "🤖 给 LLM Coding Agent 的 Skills" 段。

---

## Links

| 资源 | 链接 |
|---|---|
| **PyPI** | https://pypi.org/project/jsonseek/ |
| **GitHub** | https://github.com/lo2589/JSONSEEK |
| **Issue 追踪** | https://github.com/lo2589/JSONSEEK/issues |
