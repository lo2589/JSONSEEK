# jsonseek-dsh QUICKSTART

## 30 秒装上

```bash
# 1. 装 jsonseek CLI（如果没装）
pip install jsonseek

# 2. 装 dsh 插件
dsh plugin --profile web add jsonseek-dsh

# 3. 重启 dsh（如果它在跑）
deepseek restart  # 或 pkill dsh 然后 dsh web
```

打开 http://127.0.0.1:3080 → **Settings → Plugin list** → 看到 `jsonseek-dsh`。

## 验证插件加载

```bash
dsh --profile web --dump-config 2>&1 | grep -A 2 jsonseek
```

应该看到：
```
# == jsonseek-dsh
- id: jsonseek-tools
  name: jsonseek-dsh
```

## 在 agent 里用

随便告诉 agent：

> "用 jsonseek_shape 看看 data.json 的结构"

agent 会自己调 `jsonseek_shape({"file": "data.json"})` 拿结果。

## 卸载

```bash
dsh plugin --profile web remove jsonseek-dsh
deepseek restart
```

## 故障

| 错 | 修 |
|---|---|
| Plugin list 没显示 | 看 `~/.dsh/profiles/web/package.json` 是否有 `jsonseek-dsh` 在 `dsh.profile.bundles` |
| 工具调用失败 | `which jsonseek` 看 CLI 装没装 |
| 启动报错 | `deepseek logs \| tail -30` 看错误 |

## JSONSEEK 维护者

发 npm 包（一次性）：
```bash
cd JSONSEEK/npm
npm publish --access public
```

升级：
```bash
# 改 JSONSEEK/npm/package.json 的 version
cd JSONSEEK/npm
npm publish
```