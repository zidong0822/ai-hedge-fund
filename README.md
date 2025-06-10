# AI 对冲基金

> 本项目是基于 [virattt/ai-hedge-fund](https://github.com/virattt/ai-hedge-fund) 的改进版本，主要增加了对中国 A 股市场的支持。

[![Twitter Follow](https://img.shields.io/twitter/follow/chynnahe1?style=social)](https://x.com/chynnahe1)

这是一个 AI 驱动的对冲基金概念验证项目。该项目旨在探索使用人工智能进行交易决策。本项目仅供**教育目的**使用，不用于实际交易或投资。

## 社区交流

### 社交媒体

- Twitter：[@chynnahe1](https://x.com/chynnahe1)

### 微信交流群

<div align="center">
  <img src="docs/images/wechat_group_qr.jpg" alt="微信交流群" width="200"/>
  
  > 扫码加入微信交流群（如果二维码过期，请在 Issues 中联系我们获取最新二维码）
</div>

## A 股市场支持

本版本在原项目基础上增加了以下功能：

- 支持 A 股市场数据获取和分析
  - 实时行情和历史数据
  - 财务报表数据
  - 公司公告信息
  - 行业分类数据
- 适配中国股市交易规则和限制
  - 涨跌停限制
  - T+1 交易规则
  - 交易时间和休市规则
  - 融资融券规则
- 增加 A 股特有指标分析
  - 北向资金流向
  - 融资融券数据
  - 龙虎榜数据
  - 股东增减持
- 支持沪深两市股票代码
  - 上交所：600xxx、601xxx、603xxx、688xxx
  - 深交所：000xxx、002xxx、300xxx、301xxx

## 系统架构

本系统由多个协同工作的智能代理组成：

1. Aswath Damodaran 代理 - 估值专家，专注于故事、数字和严格的估值
2. Ben Graham 代理 - 价值投资之父，只买具有安全边际的隐藏瑰宝
3. Bill Ackman 代理 - 激进投资者，采取大胆立场并推动变革
4. Cathie Wood 代理 - 成长股投资女王，相信创新和颠覆的力量
5. Charlie Munger 代理 - 沃伦·巴菲特的搭档，只在合理价格买入优质企业
6. Michael Burry 代理 - "大空头"逆向投资者，寻找深度价值
7. Peter Lynch 代理 - 实用投资者，在日常企业中寻找"十倍股"
8. Phil Fisher 代理 - 严谨的成长型投资者，使用深度"小道消息"研究
9. Rakesh Jhunjhunwala 代理 - 印度大牛市专家
10. Stanley Druckenmiller 代理 - 宏观传奇，寻找具有成长潜力的不对称机会
11. Warren Buffett 代理 - 奥马哈先知，寻找合理价格的优质公司
12. 估值代理 - 计算股票内在价值并生成交易信号
13. 情绪代理 - 分析市场情绪并生成交易信号
14. 基本面代理 - 分析基本面数据并生成交易信号
15. 技术面代理 - 分析技术指标并生成交易信号
16. 风险管理器 - 计算风险指标并设置仓位限制
17. 投资组合管理器 - 做出最终交易决策并生成订单

**注意**：系统仅模拟交易决策，不进行实际交易。

## 免责声明

本项目仅供**教育和研究目的**使用。

- 不用于实际交易或投资
- 不提供投资建议或保证
- 创建者不承担任何财务损失责任
- 投资决策请咨询专业理财顾问
- 过往业绩不代表未来表现

使用本软件即表示您同意仅将其用于学习目的。

## 目录

- [安装设置](#安装设置)
  - [使用 Poetry](#使用-poetry)
  - [使用 Docker](#使用-docker)
- [使用方法](#使用方法)
  - [运行对冲基金](#运行对冲基金)
  - [运行回测系统](#运行回测系统)
- [贡献](#贡献)
- [功能请求](#功能请求)
- [许可证](#许可证)

## 安装设置

### 使用 Poetry

克隆仓库：

```bash
git clone https://github.com/[your-username]/ai-hedge-fund.git
cd ai-hedge-fund
```

1. 安装 Poetry（如果尚未安装）：

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. 安装依赖：

```bash
poetry install
```

3. 设置环境变量：

```bash
# 创建 API 密钥的 .env 文件
cp .env.example .env
```

4. 设置 API 密钥：

```bash
# OpenAI LLMs (gpt-4o, gpt-4o-mini 等)
# 从 https://platform.openai.com/ 获取 OpenAI API 密钥
OPENAI_API_KEY=your-openai-api-key

# Groq LLMs (deepseek, llama3 等)
# 从 https://groq.com/ 获取 Groq API 密钥
GROQ_API_KEY=your-groq-api-key

# 获取金融数据
# 从 https://financialdatasets.ai/ 获取 Financial Datasets API 密钥
FINANCIAL_DATASETS_API_KEY=your-financial-datasets-api-key

# A股数据接口密钥
# 从相应数据提供商处获取
ASTOCK_API_KEY=your-astock-api-key
```

### 使用 Docker

1. 确保系统已安装 Docker。如果没有，请从[Docker 官网](https://www.docker.com/get-started)下载。

2. 克隆仓库：

```bash
git clone https://github.com/[your-username]/ai-hedge-fund.git
cd ai-hedge-fund
```

3. 设置环境变量：

```bash
# 创建 API 密钥的 .env 文件
cp .env.example .env
```

4. 按上述说明编辑 .env 文件添加 API 密钥。

5. 进入 docker 目录：

```bash
cd docker
```

6. 构建 Docker 镜像：

```bash
# Linux/Mac:
./run.sh build

# Windows:
run.bat build
```

**重要提示**：系统运行需要设置 `OPENAI_API_KEY`、`GROQ_API_KEY`、`ANTHROPIC_API_KEY` 或 `DEEPSEEK_API_KEY` 中的至少一个。如果想使用所有 LLM 提供商的服务，需要设置所有 API 密钥。

美股数据方面，AAPL、GOOGL、MSFT、NVDA 和 TSLA 的数据是免费的，不需要 API 密钥。

对于其他美股代码，需要在 .env 文件中设置 `FINANCIAL_DATASETS_API_KEY`。

对于 A 股数据，需要设置 `ASTOCK_API_KEY`。

## 使用方法

### 运行对冲基金

#### 使用 Poetry

```bash
# 美股
poetry run python src/main.py --ticker AAPL,MSFT,NVDA

# A股
poetry run python src/main.py --ticker 600519,000858,300750 --market CN
```

#### 使用 Docker

**注意**：所有 Docker 命令必须在 `docker/` 目录下运行。

```bash
# 进入 docker 目录
cd docker

# Linux/Mac:
# 美股
./run.sh --ticker AAPL,MSFT,NVDA main
# A股
./run.sh --ticker 600519,000858,300750 --market CN main

# Windows:
# 美股
run.bat --ticker AAPL,MSFT,NVDA main
# A股
run.bat --ticker 600519,000858,300750 --market CN main
```

您可以使用 `--ollama` 标志来使用本地 LLMs 运行 AI 对冲基金。

```bash
# 使用 Poetry:
# 美股
poetry run python src/main.py --ticker AAPL,MSFT,NVDA --ollama
# A股
poetry run python src/main.py --ticker 600519,000858,300750 --market CN --ollama

# 使用 Docker (在 docker/ 目录下):
# Linux/Mac:
# 美股
./run.sh --ticker AAPL,MSFT,NVDA --ollama main
# A股
./run.sh --ticker 600519,000858,300750 --market CN --ollama main

# Windows:
# 美股
run.bat --ticker AAPL,MSFT,NVDA --ollama main
# A股
run.bat --ticker 600519,000858,300750 --market CN --ollama main
```

您可以使用 `--show-reasoning` 标志在控制台打印每个代理的推理过程。

```bash
# 使用 Poetry:
poetry run python src/main.py --ticker 600519,000858,300750 --market CN --show-reasoning

# 使用 Docker (在 docker/ 目录下):
# Linux/Mac:
./run.sh --ticker 600519,000858,300750 --market CN --show-reasoning main

# Windows:
run.bat --ticker 600519,000858,300750 --market CN --show-reasoning main
```

您可以选择指定开始和结束日期来针对特定时期做出决策。

```bash
# 使用 Poetry:
poetry run python src/main.py --ticker 600519,000858,300750 --market CN --start-date 2024-01-01 --end-date 2024-03-01

# 使用 Docker (在 docker/ 目录下):
# Linux/Mac:
./run.sh --ticker 600519,000858,300750 --market CN --start-date 2024-01-01 --end-date 2024-03-01 main

# Windows:
run.bat --ticker 600519,000858,300750 --market CN --start-date 2024-01-01 --end-date 2024-03-01 main
```

### 运行回测系统

#### 使用 Poetry

```bash
# 美股
poetry run python src/backtester.py --ticker AAPL,MSFT,NVDA

# A股
poetry run python src/backtester.py --ticker 600519,000858,300750 --market CN
```

#### 使用 Docker

```bash
# 进入 docker 目录
cd docker

# Linux/Mac:
# 美股
./run.sh --ticker AAPL,MSFT,NVDA backtester
# A股
./run.sh --ticker 600519,000858,300750 --market CN backtester

# Windows:
# 美股
run.bat --ticker AAPL,MSFT,NVDA backtester
# A股
run.bat --ticker 600519,000858,300750 --market CN backtester
```

您也可以为回测系统指定时间范围：

```bash
# 使用 Poetry:
poetry run python src/backtester.py --ticker 600519,000858,300750 --market CN --start-date 2023-01-01 --end-date 2023-12-31

# 使用 Docker (在 docker/ 目录下):
# Linux/Mac:
./run.sh --ticker 600519,000858,300750 --market CN --start-date 2023-01-01 --end-date 2023-12-31 backtester

# Windows:
run.bat --ticker 600519,000858,300750 --market CN --start-date 2023-01-01 --end-date 2023-12-31 backtester
```

## 数据来源说明

- 美股数据：通过 Financial Datasets API 获取
- A 股数据：支持多个数据源
  - TuShare Pro
  - AKShare
  - BaoStock
  - 新浪财经
  - 东方财富

请在 `.env` 文件中配置相应的 API 密钥。

## 注意事项

1. A 股市场特殊规则

   - 股票代码前需要加市场标识（sh/sz）
   - 考虑涨跌停限制
   - 遵守 T+1 交易规则
   - 注意节假日休市安排

2. 数据时效性

   - A 股实时数据有 15 分钟延迟
   - 历史数据通常在交易日收盘后更新
   - 财务数据按季度更新

3. 使用限制
   - API 调用频率限制
   - 数据使用许可范围
   - 模型训练数据时效性

## 贡献

1. Fork 本仓库
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

**重要提示**：请保持 pull requests 小而集中。这将使审查和合并更容易。

## 功能请求

如果您有功能请求，请开启一个[issue](https://github.com/[your-username]/ai-hedge-fund/issues)并确保标记为 `enhancement`。

## 许可证

本项目采用 MIT 许可证 - 详见 LICENSE 文件。
