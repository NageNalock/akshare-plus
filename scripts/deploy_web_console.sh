#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
SKIP_START="${SKIP_START:-0}"

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "error: ${PYTHON_BIN} 不可用，请先安装 Python 3" >&2
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "error: npm 不可用，请先安装 Node.js 和 npm" >&2
  exit 1
fi

cd "${ROOT_DIR}"

if [ ! -d "${VENV_DIR}" ]; then
  echo "[1/5] 创建虚拟环境 ${VENV_DIR}"
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

echo "[2/5] 升级 pip"
"${VENV_DIR}/bin/python" -m pip install --upgrade pip

echo "[3/5] 安装 Python 依赖 (web + mcp)"
"${VENV_DIR}/bin/pip" install -e ".[web,mcp]"

echo "[4/5] 安装 React 前端依赖"
npm install --prefix "${ROOT_DIR}/akshare_web/frontend"

echo "[5/5] 构建 React 前端"
npm run build --prefix "${ROOT_DIR}/akshare_web/frontend"

echo
echo "部署完成"
echo "HTTP 控制台: http://${HOST}:${PORT}"
echo "MCP 端点:    http://${HOST}:${PORT}/mcp/"
echo

if [ "${SKIP_START}" = "1" ]; then
  echo "已按要求跳过启动阶段"
  exit 0
fi

echo "启动 AKShare Web Console ..."
exec "${VENV_DIR}/bin/akshare-web" --host "${HOST}" --port "${PORT}"
