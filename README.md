# AKShare Plus

> AKShare Plus extends AKShare with a built-in React dashboard, HTTP API, and MCP server for local financial data exploration and automation.

AKShare Plus 是基于 [AKShare](https://github.com/akfamily/akshare) 的增强版发行项目：
保留原有 `import akshare as ak` 的财经数据接口能力，并新增可本地部署的
React Dashboard、HTTP API 与 MCP Server，方便在浏览器界面、脚本服务和支持 MCP 的 AI 客户端中直接调用全量 AKShare 能力。

**资源分享**：对于想了解更多财经数据与量化投研的小伙伴，推荐一个专注于财经数据和量化研究的知识社区。
该社区提供相关文档和视频学习资源，汇集了各类财经数据源和量化投研工具的使用经验。
有兴趣深入学习的朋友可点此[了解更多](https://t.zsxq.com/ZCxUG)，也推荐大家关注微信公众号【数据科学实战】。

**重磅推荐**：AKQuant 是一款专为 **量化投研 (Quantitative Research)** 打造的高性能量化回测框架。它以 Rust 铸造极速撮合内核，
以 Python 链接数据与 AI 生态，旨在为量化投资者提供可靠高效的量化投研解决方案。参见[AKQuant](https://github.com/akfamily/akquant)

**工具推荐**：期魔方是一款本地化期货量化分析工具，适合数据分析爱好者使用。无需复杂部署，支持数据分析和机器学习功能，研究功能免费开放。
如需了解更多信息可访问[期魔方](https://qmfquant.com)。

![AKShare Logo](assets/images/akshare_logo.jpg)

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![akshare-plus](https://img.shields.io/badge/Data%20Science-AKShare%20Plus-green)](https://github.com/NageNalock/akshare-plus)
[![Actions Status](https://github.com/NageNalock/akshare-plus/actions/workflows/release_and_deploy.yml/badge.svg)](https://github.com/NageNalock/akshare-plus/actions)
[![MIT Licence](https://img.shields.io/badge/license-MIT-blue)](https://github.com/NageNalock/akshare-plus/blob/main/LICENSE)
[![](https://img.shields.io/github/forks/NageNalock/akshare-plus)](https://github.com/NageNalock/akshare-plus)
[![](https://img.shields.io/github/stars/NageNalock/akshare-plus)](https://github.com/NageNalock/akshare-plus)
[![](https://img.shields.io/github/issues/NageNalock/akshare-plus)](https://github.com/NageNalock/akshare-plus)
[![code style: prettier](https://img.shields.io/badge/code_style-prettier-ff69b4.svg?style=flat-square)](https://github.com/prettier/prettier)

## Overview

[AKShare Plus](https://github.com/NageNalock/akshare-plus) requires Python(64 bit) 3.9 or higher.
It keeps the original AKShare data interface surface while making local exploration and integration much easier.

**Write less, integrate more!**

- Keep the familiar AKShare Python API
- Browse and execute functions from a built-in React dashboard
- Expose AKShare through HTTP endpoints for local services
- Connect the same capability set to MCP-compatible clients
- AKShare Plus setup notes: [docs/http_console.md](docs/http_console.md)
- Legacy AKShare docs: [akshare.akfamily.xyz](https://akshare.akfamily.xyz/)
- Original AKShare README: [akfamily/akshare README](https://github.com/akfamily/akshare/blob/main/README.md)

## Installation

### Recommended for AKShare Plus

```shell
git clone https://github.com/NageNalock/akshare-plus.git
cd akshare-plus
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[web,mcp]"
```

如果你希望一次性完成依赖安装、前端构建并启动本地服务，直接执行：

```shell
./scripts/deploy_web_console.sh
```

如果只想安装核心包而不带 Web / MCP 能力，可以执行：

```shell
pip install -e .
```

### Only Need Original AKShare?

如果你只想安装 upstream AKShare，而不是这个带 Dashboard / HTTP / MCP 的增强版 fork，请参考旧文档：

- 原始 README: [https://github.com/akfamily/akshare/blob/main/README.md](https://github.com/akfamily/akshare/blob/main/README.md)
- 官方文档: [https://akshare.akfamily.xyz/](https://akshare.akfamily.xyz/)

对应的安装命令仍然是：

```shell
pip install akshare --upgrade
```

### Docker

当前仓库没有单独维护 `akshare-plus` 的预构建 Docker 镜像，推荐直接使用本仓库的一键部署脚本或本地虚拟环境方式运行。
如果你需要 upstream AKShare/AKTools 的容器镜像，请参考旧 README。

## Usage

### Web Console & MCP

AKShare Plus 的核心增强能力，是在原有 AKShare 接口之上内置了一套可本地部署的控制台与服务层：

- React Web Console: 浏览全部公开接口、自动生成参数表单、直接查看结构化结果
- HTTP API: `GET /api/functions`、`GET /api/functions/{name}`、`POST /api/functions/{name}/execute`
- MCP Endpoint: `http://127.0.0.1:8000/mcp/`

一键部署并启动：

```shell
./scripts/deploy_web_console.sh
```

如果只想完成依赖安装和前端构建、不立即启动服务：

```shell
SKIP_START=1 ./scripts/deploy_web_console.sh
```

手动启动 Web Console：

```shell
./.venv/bin/akshare-web --host 127.0.0.1 --port 8000
```

单独启动 MCP Server：

```shell
./.venv/bin/akshare-mcp --transport stdio
```

或使用 Streamable HTTP 方式启动 MCP：

```shell
./.venv/bin/akshare-mcp --transport streamable-http --host 127.0.0.1 --port 8001
```

将 HTTP MCP Server 接入支持 MCP 的客户端时，可使用：

```shell
claude mcp add --transport http akshare http://127.0.0.1:8000/mcp/
```

### Data

Code:

```python
import akshare as ak

stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol="000001", period="daily", start_date="20170301", end_date='20231022', adjust="")
print(stock_zh_a_hist_df)
```

Output:

```
      日期          开盘   收盘    最高  ...  振幅   涨跌幅  涨跌额  换手率
0     2017-03-01   9.49   9.49   9.55  ...  0.84  0.11  0.01  0.21
1     2017-03-02   9.51   9.43   9.54  ...  1.26 -0.63 -0.06  0.24
2     2017-03-03   9.41   9.40   9.43  ...  0.74 -0.32 -0.03  0.20
3     2017-03-06   9.40   9.45   9.46  ...  0.74  0.53  0.05  0.24
4     2017-03-07   9.44   9.45   9.46  ...  0.63  0.00  0.00  0.17
          ...    ...    ...    ...  ...   ...   ...   ...   ...
1610  2023-10-16  11.00  11.01  11.03  ...  0.73  0.09  0.01  0.26
1611  2023-10-17  11.01  11.02  11.05  ...  0.82  0.09  0.01  0.25
1612  2023-10-18  10.99  10.95  11.02  ...  1.00 -0.64 -0.07  0.34
1613  2023-10-19  10.91  10.60  10.92  ...  3.01 -3.20 -0.35  0.61
1614  2023-10-20  10.55  10.60  10.67  ...  1.51  0.00  0.00  0.27
[1615 rows x 11 columns]
```

### Plot

Code:

```python
import akshare as ak
import mplfinance as mpf  # Please install mplfinance as follows: pip install mplfinance

stock_us_daily_df = ak.stock_us_daily(symbol="AAPL", adjust="qfq")
stock_us_daily_df = stock_us_daily_df.set_index(["date"])
stock_us_daily_df = stock_us_daily_df["2020-04-01": "2020-04-29"]
mpf.plot(stock_us_daily_df, type="candle", mav=(3, 6, 9), volume=True, show_nontrading=False)
```

Output:

![KLine](https://jfds-1252952517.cos.ap-chengdu.myqcloud.com/akshare/readme/home/AAPL_candle.png)

## Features

- **AKShare compatible**: 继续使用熟悉的 `import akshare as ak` 接口调用方式；
- **Dashboard ready**: 自带 React 控制台，可搜索函数、填写参数并查看结构化结果；
- **Service friendly**: 提供本地 HTTP API 和 MCP Server，便于接入自动化系统与 AI 客户端；
- **Python native**: 保持原有 Python 生态兼容性，适合脚本、研究和服务化部署。

## Legacy AKShare References

如果你要查阅原始 AKShare 的大而全数据文档，请使用这些旧入口：

1. [Original README](https://github.com/akfamily/akshare/blob/main/README.md)
2. [Overview](https://akshare.akfamily.xyz/introduction.html)
3. [Installation](https://akshare.akfamily.xyz/installation.html)
4. [Tutorial](https://akshare.akfamily.xyz/tutorial.html)
5. [Data Dict](https://akshare.akfamily.xyz/data/index.html)
6. [Subjects](https://akshare.akfamily.xyz/topic/index.html)

## Contribution

欢迎为 [AKShare Plus](https://github.com/NageNalock/akshare-plus) 提交 issue 和 pull request。
这个 fork 主要关注三类改进：

- AKShare 原有接口的本地可用性与兼容性
- React Dashboard / HTTP API / MCP 集成体验
- 文档、测试和部署脚本的可维护性

> Notice: We use [Ruff](https://github.com/astral-sh/ruff) to format the code

## Statement

1. AKShare Plus 基于开源财经数据接口能力构建，数据仅供学习、研究与开发测试使用；
2. 仓库内提供的任何数据访问能力都不构成投资建议，使用者需自行承担数据质量与使用风险；
3. 上游数据源、网页结构或访问策略变化时，部分接口可能失效、变更或被移除；
4. AKShare Plus 在保留原始 AKShare Python 接口兼容性的同时，额外提供了本地 Dashboard、HTTP API 与 MCP Server；
5. 如需查阅原始 AKShare 的官方说明、安装方式与完整数据文档，请参考旧 README 和旧文档站点：
   [README](https://github.com/akfamily/akshare/blob/main/README.md) /
   [Docs](https://akshare.akfamily.xyz/)

## Show your style

Use the badge in your project's README.md:

```markdown
[![Data: akshare-plus](https://img.shields.io/badge/Data%20Science-AKShare%20Plus-green)](https://github.com/NageNalock/akshare-plus)
```

Using the badge in README.rst:

```
.. image:: https://img.shields.io/badge/Data%20Science-AKShare%20Plus-green
    :target: https://github.com/NageNalock/akshare-plus
```

Looks like this:

[![Data: akshare-plus](https://img.shields.io/badge/Data%20Science-AKShare%20Plus-green)](https://github.com/NageNalock/akshare-plus)

## Citation

Please use this **bibtex** if you want to cite this repository in your publications:

```markdown
@misc{akshare_plus,
    author = {AKShare Plus Contributors},
    title = {AKShare Plus},
    year = {2026},
    publisher = {GitHub},
    journal = {GitHub repository},
    howpublished = {\url{https://github.com/NageNalock/akshare-plus}},
}
```

## Acknowledgement

AKShare Plus is built on top of the original [AKShare](https://github.com/akfamily/akshare) project.
For the original project introduction and historical README, please see:
[https://github.com/akfamily/akshare/blob/main/README.md](https://github.com/akfamily/akshare/blob/main/README.md)

Special thanks [FuShare](https://github.com/LowinLi/fushare) for the opportunity of learning from the project;

Special thanks [TuShare](https://github.com/waditu/tushare) for the opportunity of learning from the project;

Thanks for the data provided by [东方财富网站](http://data.eastmoney.com);

Thanks for the data provided by [新浪财经网站](https://finance.sina.com.cn);

Thanks for the data provided by [金十数据网站](https://www.jin10.com/);

Thanks for the data provided by [生意社网站](http://www.100ppi.com/);

Thanks for the data provided by [中国银行间市场交易商协会网站](http://www.nafmii.org.cn/);

Thanks for the data provided by [99期货网站](http://www.99qh.com/);

Thanks for the data provided by [中国外汇交易中心暨全国银行间同业拆借中心网站](http://www.chinamoney.com.cn/chinese/);

Thanks for the data provided by [和讯财经网站](http://www.hexun.com/);

Thanks for the data provided by [DACHENG-XIU 网站](https://dachxiu.chicagobooth.edu/);

Thanks for the data provided by [上海证券交易所网站](http://www.sse.com.cn/assortment/options/price/);

Thanks for the data provided by [深证证券交易所网站](http://www.szse.cn/);

Thanks for the data provided by [北京证券交易所网站](http://www.bse.cn/);

Thanks for the data provided by [中国金融期货交易所网站](http://www.cffex.com.cn/);

Thanks for the data provided by [上海期货交易所网站](http://www.shfe.com.cn/);

Thanks for the data provided by [大连商品交易所网站](http://www.dce.com.cn/);

Thanks for the data provided by [郑州商品交易所网站](http://www.czce.com.cn/);

Thanks for the data provided by [上海国际能源交易中心网站](http://www.ine.com.cn/);

Thanks for the data provided by [Timeanddate 网站](https://www.timeanddate.com/);

Thanks for the data provided by [河北省空气质量预报信息发布系统网站](http://110.249.223.67/publish/);

Thanks for the data provided by [Economic Policy Uncertainty 网站](http://www.nanhua.net/nhzc/varietytrend.html);

Thanks for the data provided by [申万指数网站](http://www.swsindex.com/idx0120.aspx?columnid=8832);

Thanks for the data provided by [真气网网站](https://www.zq12369.com/);

Thanks for the data provided by [财富网站](http://www.fortunechina.com/);

Thanks for the data provided by [中国证券投资基金业协会网站](http://gs.amac.org.cn/);

Thanks for the data provided by [Expatistan 网站](https://www.expatistan.com/cost-of-living);

Thanks for the data provided by [北京市碳排放权电子交易平台网站](https://www.bjets.com.cn/article/jyxx/);

Thanks for the data provided by [国家金融与发展实验室网站](http://www.nifd.cn/);

Thanks for the data provided by [义乌小商品指数网站](http://www.ywindex.com/Home/Product/index/);

Thanks for the data provided by [百度迁徙网站](https://qianxi.baidu.com/?from=shoubai#city=0);

Thanks for the data provided by [思知网站](https://www.ownthink.com/);

Thanks for the data provided by [Currencyscoop 网站](https://currencyscoop.com/);

Thanks for the data provided by [新加坡交易所网站](https://www.sgx.com/zh-hans/research-education/derivatives);
