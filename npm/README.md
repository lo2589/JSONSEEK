# jsonseek-dsh — DeepSeek Harness plugin for jsonseek

**目的**：让 `jsonseek` 的 14 个子命令作为 DeepSeek Harness 的模型可调用工具出现在 dsh 的 **Plugin list** 里。

**特点**：

- **零侵入 JSONSEEK 源码** —— npm 包完全独立，不修改 `src/jsonseek/` 任何文件
- npm 包是数据 + apply(ctx) 壳，运行时调本地 `jsonseek` CLI
- 用户装一行命令搞定

---

## 三种消费方式

| 你是什么身份 | 看哪节 |
|---|---|
| **dsh 用户**（只想用） | [§1](#1-dsh-用户) |
| **JSONSEEK 维护者**（要发布 npm 包） | [§2](#2-jsonseek-维护者要发布) |
| **JSONSEEK 维护者**（要发布 pip 包） | [§3](#3-jsonseek-维护者要发布-pip) |

---

## 1. dsh 用户

### 1.1 装（必须装 Python 和 npm 两份）

```bash
# 装 Python CLI 工具本体（dsh 调它）
pip install jsonseek

# 装 dsh 插件
dsh plugin --profile web add jsonseek-dsh
```

`dsh plugin add` 自动会：
1. 把 `jsonseek-dsh` 加进 profile 的 `package.json` 的 `dependencies`
2. 加进 `dsh.profile.bundles` 列表
3. 重启 dsh，插件列表里就出现 `jsonseek-dsh`

### 1.2 验证

```bash
# 启动 dsh
dsh web

# 命令行看 plugin list
dsh --profile web --dump-config | grep jsonseek

# 应该看到:
# # == jsonseek-dsh
# - id: jsonseek-tools
#   name: jsonseek-dsh

# Web UI 看
# 打开 http://127.0.0.1:3080
# Settings → Plugin list → 找 "jsonseek-dsh"
```

### 1.3 在 agent 里用

启动 Web UI 后，dsh agent 现在多了 14 个工具：

| 工具 | 干啥 | 例子 |
|---|---|---|
| `jsonseek_shape` | 看结构 | `{"file": "data.json"}` |
| `jsonseek_fields` | 列字段 | `{"file": "data.json"}` |
| `jsonseek_query` | 搜关键字 | `{"file": "data.json", "keyword": "Alice"}` |
| `jsonseek_get` | 取一个值 | `{"file": "data.json", "path": "users[0].name"}` |
| `jsonseek_ls` | 列子节点 | `{"file": "data.json", "path": "users"}` |
| `jsonseek_set` | 改值 | `{"file": "data.json", "path": "meta.count", "value": 99}` |
| `jsonseek_add` | 加字段 | `{"file": "data.json", "path": "meta.owner", "value": "team"}` |
| `jsonseek_del` | 删字段 | `{"file": "data.json", "path": "meta.owner"}` |
| `jsonseek_append` | 追加 | `{"file": "data.json", "path": "tags", "value": "new"}` |
| `jsonseek_extract` | 批量取 | `{"pattern": "*.json", "path": "id"}` |
| `jsonseek_extend` | 数组合并 | `{"file": "data.json", "path": "tags", "value": "[\"a\",\"b\"]"}` |
| `jsonseek_concat` | 多文件合并 | `{"pattern": "data/*.json"}` |
| `jsonseek_cutline` | 取一行 | `{"file": "data.jsonl", "line": 42}` |
| `jsonseek_replaceline` | 改一行 | `{"file": "data.jsonl", "line": 42, "content": "..."}` |

你不用记这些，agent 会自己挑。

### 1.4 卸载

```bash
dsh plugin --profile web remove jsonseek-dsh
```

### 1.5 故障排查

| 现象 | 原因 | 修法 |
|---|---|---|
| Plugin list 没显示 | `dsh plugin add` 没成功 | 看 profile/package.json 是否有 `jsonseek-dsh` 在 `dsh.profile.bundles` |
| 工具调用报 "jsonseek: command not found" | Python 包没装 | `pip install jsonseek` |
| Web UI 启动失败 | npm 包和 dsh 版本不兼容 | `dsh plugin update jsonseek-dsh` |

---

## 2. JSONSEEK 维护者（要发布）

**目标**：让 npm 包发到 https://www.npmjs.com/package/jsonseek-dsh，用户能 `dsh plugin add jsonseek-dsh` 装上。

### 2.1 一次性操作

```bash
# 注册 npm 账号（一次性）
npm adduser

# 发布 npm 包
cd JSONSEEK/npm
npm publish --access public
```

### 2.2 发布后用户能干啥

```bash
dsh plugin --profile web add jsonseek-dsh
```

### 2.3 升级流程

改 `JSONSEEK/npm/` 下三个文件后：

```bash
# 1. 改 package.json 的 version (语义化版本)
vim npm/package.json  # 0.1.6 → 0.1.7

# 2. 改 index.js / cordis.patch.yml / README.md
# ...

# 3. 测试本地装
cd /tmp && pnpm add /path/to/JSONSEEK/npm/

# 4. 发布
cd JSONSEEK/npm
npm publish
```

用户升级：
```bash
dsh plugin --profile web update jsonseek-dsh
```

---

## 3. JSONSEEK 维护者（要发布 pip）

### 3.1 pip 包完全独立

`JSONSEEK/src/jsonseek_dsh/`（Python 包装层）只影响 `jsonseek-dsh` 这个 pip CLI，**不影响 npm 包和 dsh 集成**。

如果你不想维护 Python 包装层：
- **删** `src/jsonseek_dsh/` 整个目录
- **删** `pyproject.toml` 里的 `jsonseek-dsh` console script
- **删** `setup.py` 里的 `cordis.plugins` entry point
- pip 包发布时就不带 Python 包装层

### 3.2 npm 包不需要任何 Python 代码

`JSONSEEK/npm/index.js` 用 Node.js 调用 `jsonseek` CLI，**完全不依赖 Python**。所以：

- 不需要装 `jsonseek_dsh` Python 包
- 不需要 Python 包装层存在
- 用户只需要 `pip install jsonseek`（上游 jsonseek CLI）+ npm `jsonseek-dsh`

### 3.3 想让两者都发布

| 发布 | 内容 | 文件 |
|---|---|---|
| **PyPI** | `jsonseek` (CLI) + `jsonseek_dsh` (Python 包装层) | `pyproject.toml`, `setup.py` |
| **npm** | `jsonseek-dsh` (dsh 插件) | `npm/package.json`, `npm/index.js`, `npm/cordis.patch.yml` |

互不干扰，可以独立发版。

---

## 4. 文件结构

```
JSONSEEK/
├── src/jsonseek/              # ⛔ 不动 - jsonseek CLI 源码
├── src/jsonseek_dsh/          # 🟡 可选 - Python 包装层（与 dsh 无关）
├── pyproject.toml             # 🟡 可选 - Python 打包（含 jsonseek_dsh）
├── setup.py                   # 🟡 可选 - Python 打包（含 jsonseek_dsh）
├── npm/                       # ✅ 必须 - dsh 集成 npm 包
│   ├── package.json           #    npm manifest + dsh.bundle 声明
│   ├── cordis.patch.yml       #    dsh 插件行
│   ├── index.js               #    apply(ctx) + 14 个工具
│   └── README.md              #    本文件
└── ...
```

---

## 5. 关键事实

1. **JSONSEEK CLI 没改一行** —— npm 包独立维护
2. **dsh plugin list 加载机制**：从 npm `package.json` 读 `dsh.bundle.patch`，加载 `cordis.patch.yml` 里的 row，row 调 `apply(ctx)`
3. **用户视角**：`pip install jsonseek && dsh plugin add jsonseek-dsh` 两步搞定
4. **不需要 JSONSEEK 改任何代码**
5. **Python 包装层（`jsonseek_dsh/`）是可选的** —— 给 `python -m jsonseek_dsh` CLI 用，跟 dsh 集成**完全无关**
