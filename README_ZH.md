# jsonseek

[![PyPI version](https://badge.fury.io/py/jsonseek.svg)](https://badge.fury.io/py/jsonseek)
[![Downloads](https://static.pepy.tech/badge/jsonseek)](https://pepy.tech/project/jsonseek)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

**JSON/JSONL 解析工具包，专为 LLM 设计。**

> 当 LLM 触碰 JSON，应该先 `shape`，再 `query`，绝不要 `cat` 整个文件。
> 当人触碰 JSON，规则也一样——只是把 context window 换成键盘而已。

---

## 🤖 给 LLM Coding Agent 的 Skills

> **直接告诉 agent "用 jsonseek" 即可。** Skills 文档就摆在下面，按需查阅。

| Skills | 链接 | 适用 |
|---|---|---|
| **SKILL.md** | 👉 [在 GitHub 上查看](https://github.com/lo2589/JSONSEEK/blob/main/skills/jsonseek/SKILL.md) | Agent 启动加载：触发场景、核心命令速查、**写操作三铁律**、Windows API 兜底 |
| **commands.md** | 👉 [在 GitHub 上查看](https://github.com/lo2589/JSONSEEK/blob/main/skills/jsonseek/references/commands.md) | 按需查阅：每个命令的 flag / 示例 / 输出格式 |
| **path-syntax.md** | 👉 [在 GitHub 上查看](https://github.com/lo2589/JSONSEEK/blob/main/skills/jsonseek/references/path-syntax.md) | 按需查阅：路径语法全集（点号 / 方括号 / 混合 / 数组 / 转义） |

**接入 agent**（Claude Code / Cursor / Codex 等）：

```bash
git clone https://github.com/lo2589/JSONSEEK.git
ln -s ../jsonseek/skills/jsonseek/SKILL.md ~/.claude/skills/jsonseek.md
# 或 ~/.cursor/skills/  ~/.codex/skills/
```

---

## 📦 安装

```bash
pip install jsonseek
```

需要 Python 3.8+。**零依赖、零配置**，装完即用。

```bash
$ jsonseek --version
jsonseek <current_version>
```

完整英文文档：[README.md](README.md)

---

## 🔗 链接

| 资源 | 链接 |
|---|---|
| **PyPI** | https://pypi.org/project/jsonseek/ |
| **GitHub** | https://github.com/lo2589/JSONSEEK |
| **Issue** | https://github.com/lo2589/JSONSEEK/issues |

---

## 完整命令参考

14 个命令，每个都跑 `jsonseek <command> --help` 能看最全 flag。

**7 个只读命令**：`shape` / `fields` / `ls` / `get` / `query` / `extract` / `concat`
**7 个写命令**：`set` / `add` / `del` / `append` / `extend` / `cutline` / `replaceline`

**通用 flag**：

```
--kind {json,jsonl}        强制文件类型
--output {pretty,json}     pretty 默认，json 给 agent 用
--encoding ENCODING        强制编码（gbk / utf-8 等）
--backup                   写之前生成 .bak
--dry-run                  预览，不真写
--context N                JSONL 上下文行数（默认 2）
```

**每个命令独有 flag**：

| 命令 | 独有 flag |
|---|---|
| `shape` | `--max-depth` `--array-mode {sample,full}` `--sample-size` |
| `fields` | `--top` |
| `query` | `--case-sensitive` `--exact` `--match-mode {key,value,both}` `--max-results` `--record-id-field` `--preview-field` |
| `extract` | `--include-missing` |
| `concat` | `-o, --output-file` `--no-sort` |
| `set` / `add` | `--create-missing` `--from-file` |
| `del` | `-y, --yes` |
| `append` / `extend` | `--from-file` |
| `cutline` | `--save-temp` |
| `replaceline` | `--from-file` |

**退出码**：

| 码 | 含义 |
|---|---|
| 0 | 成功 |
| 1 | 通用错误（路径错、文件不存在等） |
| 2 | 参数错 |
