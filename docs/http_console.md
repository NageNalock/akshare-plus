# AKShare 内置 Web 控制台与 MCP 服务

## 背景分析

当前仓库的核心是 `akshare/__init__.py` 这一层统一导出入口，它把上千个财经数据函数从不同子模块汇总成 `import akshare as ak` 的使用方式。

这个结构有两个很明显的特点：

1. 功能面非常广，接口数量已经超过 1000 个，不适合逐个手写 HTTP 路由和前端表单。
2. 仓库内已经有完整的文档分组，主要位于 `docs/data/**/*.md`，里面包含了函数名、目标地址、参数说明和输出字段。

因此，新增 Web 服务最合适的做法不是“为每个函数定制页面”，而是：

1. 自动扫描 `akshare/__init__.py` 暴露出来的函数；
2. 自动读取 `docs/data` 下的说明文档；
3. 根据函数签名动态生成参数表单；
4. 按返回值类型自动渲染结果。

## 新增内容

新增包：

1. `akshare_web`
2. `akshare_mcp`

主要组成如下：

1. `akshare_web/docs_parser.py`
   解析 `docs/data/**/*.md`，提取接口描述、输入参数、输出字段和文档来源。
2. `akshare_web/introspection.py`
   解析 `akshare/__init__.py` 的导出面，并在运行时动态加载可调用函数。
3. `akshare_web/serialization.py`
   将 DataFrame、Series、列表、字典和标量统一转换为前端可展示的 JSON 结构。
4. `akshare_web/app.py`
   提供 FastAPI 宿主，统一承载 React 前端、HTTP API 和挂载式 MCP 端点。
5. `akshare_web/frontend/*`
   React + Vite 前端工程，负责现代化交互界面。
6. `akshare_mcp/server.py`
   基于官方 MCP Python SDK 动态注册 AKShare 工具与资源。

## Web API 设计

### `GET /api/health`

返回服务健康状态、接口总数、分类数和文档条目数。

### `GET /api/functions`

返回所有可浏览函数的摘要信息，支持前端本地搜索和分类筛选。

### `GET /api/functions/{name}`

返回某个函数的详细元数据，包括：

1. 模块路径
2. 函数签名
3. 参数定义
4. 文档说明
5. 输出字段

### `POST /api/functions/{name}/execute`

执行指定函数，并返回结构化结果预览。

## MCP 设计

内置 MCP 服务提供两层能力：

1. 辅助工具
   例如 `akshare_search_functions`、`akshare_get_function`、`akshare_execute`。
2. 动态工具
   按 `akshare/__init__.py` 的公开导出面，自动把每个接口注册为同名 MCP Tool。

这样做的好处是：

1. LLM 可以先搜索可用函数，再读取函数元数据；
2. 也可以直接调用具体函数，如 `stock_zh_a_hist`、`bond_info_cm`；
3. 返回值会统一转成结构化预览，避免把超大 DataFrame 全量塞给客户端。

请求示例：

```json
{
  "preview_rows": 100,
  "parameters": {
    "symbol": "000001",
    "period": "daily",
    "start_date": "20240101",
    "end_date": "20240201",
    "adjust": ""
  }
}
```

## MCP 接入方式

本项目支持 3 种 MCP 接入方式：

1. 挂载在 Web 服务中的 HTTP MCP
2. 独立启动的 Streamable HTTP MCP
3. 独立启动的 stdio MCP

### 方式一：使用 Web 服务自带的 MCP 端点

启动 Web 服务：

```bash
./.venv/bin/akshare-web --host 127.0.0.1 --port 8000
```

启动后：

1. Dashboard 地址：`http://127.0.0.1:8000`
2. MCP 地址：`http://127.0.0.1:8000/mcp/`

这种方式最适合本地统一部署，一个进程同时提供：

1. React Dashboard
2. HTTP API
3. MCP Server

命令行方式接入支持 MCP 的客户端：

```bash
claude mcp add --transport http akshare http://127.0.0.1:8000/mcp/
```

### 方式二：单独启动 Streamable HTTP MCP

如果你不需要 Dashboard 和 HTTP API，只想单独暴露 MCP：

```bash
./.venv/bin/akshare-mcp --transport streamable-http --host 127.0.0.1 --port 8001
```

此时 MCP 地址为：

```text
http://127.0.0.1:8001/mcp
```

命令行方式接入：

```bash
claude mcp add --transport http akshare http://127.0.0.1:8001/mcp
```

### 方式三：单独启动 stdio MCP

如果你的 MCP 客户端更适合直接拉起本地进程，可以使用 stdio：

```bash
./.venv/bin/akshare-mcp --transport stdio
```

这种方式没有 HTTP 地址，而是由 MCP 客户端直接启动命令行进程。

一个典型的 stdio 配置可以抽象成：

1. command: `./.venv/bin/akshare-mcp`
2. args: `["--transport", "stdio"]`
3. cwd: 仓库根目录

### 应该选哪一种

优先推荐顺序：

1. 如果你已经要使用 Dashboard，直接使用 Web 服务自带的 `http://127.0.0.1:8000/mcp/`
2. 如果你只需要网络方式暴露 MCP，使用独立的 Streamable HTTP MCP
3. 如果客户端偏向本地进程拉起模式，使用 stdio

### MCP 中可用的工具

接入成功后，客户端可以使用两类能力：

1. 辅助工具
   `akshare_health`、`akshare_search_functions`、`akshare_get_function`、`akshare_execute`
2. 动态工具
   所有公开导出的 AKShare 函数都会按原函数名注册为 MCP Tool

例如：

1. `stock_zh_a_hist`
2. `bond_info_cm`
3. `spot_price_qh`

### 返回结果特点

为了避免 MCP 客户端一次性接收超大表格，所有工具返回的都是结构化预览结果：

1. DataFrame / Series 会返回预览行
2. 列表和字典会返回 JSON 结构
3. 所有动态工具都支持 `preview_rows` 参数控制结果规模

例如调用某个动态工具时，可以附带：

```json
{
  "symbol": "000001",
  "period": "daily",
  "start_date": "20240101",
  "end_date": "20240201",
  "adjust": "",
  "preview_rows": 50
}
```

## 一键部署

```bash
./scripts/deploy_web_console.sh
```

默认会完成以下步骤：

1. 创建 `.venv`
2. 安装 Python 依赖
3. 安装前端依赖
4. 构建 React 前端
5. 启动 Web Console

如果只想部署不启动：

```bash
SKIP_START=1 ./scripts/deploy_web_console.sh
```

## 启动方式

先安装项目、Web 和 MCP 依赖：

```bash
pip install -e ".[web,mcp]"
```

然后启动服务：

```bash
akshare-web --host 127.0.0.1 --port 8000
```

或：

```bash
python -m akshare_web.main --host 127.0.0.1 --port 8000
```

启动后访问：

```text
http://127.0.0.1:8000
```

同一个服务还会暴露 MCP 端点：

```text
http://127.0.0.1:8000/mcp/
```

也可以单独启动 MCP：

```bash
akshare-mcp --transport stdio
```

或：

```bash
akshare-mcp --transport streamable-http --host 127.0.0.1 --port 8001
```

## 当前实现边界

1. React 前端会自动覆盖 `akshare` 的公开导出函数，但不会展示私有内部辅助函数。
2. 复杂参数默认按 JSON 文本输入。
3. DataFrame 和 Series 默认返回预览行数，而不是一次性把全部结果塞进浏览器。
4. MCP 中的每个动态工具都会额外提供 `preview_rows` 参数，用于控制返回规模。
5. 实际执行依赖 AKShare 运行环境，如果本地缺少依赖，健康检查会给出明确错误提示。
