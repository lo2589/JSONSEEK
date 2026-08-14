# jsonseek

[![PyPI version](https://badge.fury.io/py/jsonseek.svg)](https://badge.fury.io/py/jsonseek)
[![Downloads](https://static.pepy.tech/badge/jsonseek)](https://pepy.tech/project/jsonseek)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/) [![npm jsonseek-dsh](https://img.shields.io/npm/v/jsonseek-dsh)](https://www.npmjs.com/package/jsonseek-dsh)

[English](./README.md) | [中文](./README_ZH.md)

**JSON/JSONL 解析工具包，专为 LLM 设计。**

---

## 🤖 DeepSeek Harness 插件支持

`jsonseek` 自带 [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness)（dsh）原生 bundle。装好之后，每个 `jsonseek <子命令>` 都会成为 dsh agent 里一个模型可调用的工具 —— 同时 `jsonseek` 会和 dsh 内置插件一起出现在 **Settings → Plugin list**。

```bash
# 1. 装 Python CLI（dsh 插件会调用它）
pip install jsonseek

# 2. 装 dsh bundle 到你平时 `dsh web` 启动的 profile
dsh plugin --profile web add jsonseek-dsh

# 3. 重启 dsh —— jsonseek-dsh 出现在 Plugin list，
#    agent 多了 14 个 jsonseek_* 工具可用。
dsh restart
```

三步搞定。**不需要改 JSONSEEK 一行代码、不需要 fork** —— npm bundle 是一个独立的数据型包，把每次 `jsonseek_<cmd>({...})` 调用翻译成对应的 `jsonseek` CLI 调用。

装好之后 dsh agent 就能做这种事：

> "用 jsonseek_shape 看下 `data.json` 的结构，再用 jsonseek_query 找所有提到 'password' 的记录。"

模型自己选工具，你的 CLI 负责读文件。

**详细文档：**

- [`npm/QUICKSTART.md`](./npm/QUICKSTART.md) — 30 秒装上 + 验证
- [`npm/README.md`](./npm/README.md) — 完整用法、发布、故障排查

---

## 💸 别再为你不读的 token 买单

把整个 JSON 文件喂进 LLM 上下文窗口是很贵的。一个 10 MB 的 JSON 约等于 **250 万 token** —— 用 Claude Opus 跑一个任务就要 **~$15**。

`jsonseek` 给你的是手术刀级别的命令，让你只为真正需要的数据付钱：

```bash
jsonseek shape file.json       # 看骨架，约 50 tokens
jsonseek fields file.json      # 字段+类型，约 200 tokens
jsonseek query file.json 'X'   # 搜索内容，约 100 tokens
jsonseek get file.json path    # 取一个值，约 50 tokens
```

**10 MB → 5 KB。** 同等答案，**便宜 1000 倍**。

> 当 LLM 触碰 JSON，应该先 `shape`，再 `query`，绝不要 `cat` 整个文件。
> 当人触碰 JSON，规则也一样——只是把 context window 换成键盘而已。

![jsonseek 在 50,000 行的 JSONL 里定位三处损坏，只修其中一条](demo/demo.gif)

> 三条记录被咬坏。`shape` 一次全部找出来，`replaceline` 只改第 18372 行，其余
> 49,997 行逐字未变。上面的输出是真跑出来的，不是排版出来的。


---

## 🐛 精确告诉你哪一行坏了

文件出问题的时候，`jsonseek` 会报告**具体行号 + 解析器的报错原文**——LLM（或你）一眼就能修：

```
$ jsonseek shape broken.jsonl
Error: Found 2 invalid lines in broken.jsonl:
  Line 2: {"id": 2, "name": "unterminated
    Error: Unterminated string starting at
  Line 4: {"id": 4,,}
    Error: Expecting property name enclosed in double quotes
```

```
$ jsonseek shape broken.json
Error: Invalid JSON at line 4 in broken.json
  Line 4:   "c": 3
  Expecting ',' delimiter
```

**JSONL 报告每一行错误；JSON 只报第一个错。** JSONL 每行独立，能逐行查；JSON 是单一文档，一旦坏了只能报第一个错误。

然后原位修复：

```bash
jsonseek replaceline broken.jsonl 2 '{"id": 2, "name": "fixed"}'
jsonseek replaceline broken.jsonl 4 '{"id": 4, "name": "fixed"}'
```

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
