#!/bin/bash
# 发布 jsonseek 到 PyPI
# 用法:
#   1. 在 https://pypi.org/account/login/ 申请 API token
#   2. 配置 ~/.pypirc (看下面)
#   3. ./publish.sh 0.1.7

set -e

VERSION="${1:?usage: $0 <version>}"

cd "$(dirname "$0")/.."

echo "=== 发布 jsonseek ${VERSION} 到 PyPI ==="
echo ""

# 1. 改 pyproject.toml 版本
echo "[1/5] 更新 pyproject.toml 版本号..."
sed -i '' "s/^version = \".*\"/version = \"${VERSION}\"/" pyproject.toml
grep "^version" pyproject.toml
echo ""

# 2. 清理旧 dist
echo "[2/5] 清理旧 dist..."
rm -rf dist/ build/ *.egg-info src/*.egg-info
echo "✓"
echo ""

# 3. 安装 build
echo "[3/5] 安装 build 工具..."
python3 -m pip install --quiet --user build twine 2>&1 | tail -3
echo "✓"
echo ""

# 4. 构建
echo "[4/5] 构建包..."
python3 -m build 2>&1 | tail -10
echo ""

# 5. 上传
echo "[5/5] 上传到 PyPI..."
echo "  - 用 ~/.pypirc 里 [pypi] 的 token"
echo "  - 或临时输入 username + password"
echo ""
python3 -m twine upload dist/*
echo ""
echo "✅ 完成"
echo ""
echo "检查: https://pypi.org/project/jsonseek/"
