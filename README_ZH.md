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
