# Wallet Risk Scanner

输入一个以太坊 / BSC 地址，自动从黑名单匹配、高风险合约交互、资金来源追踪三个维度进行风险分析，输出 0-100 风险评分及可视化报告。

## 功能概览

- **黑名单匹配** — OFAC 制裁地址、ScamSniffer 钓鱼地址库、Tornado Cash 混币器、已知黑客攻击合约
- **高风险合约交互检测** — GoPlus Security API 检测蜜罐 / Rug Pull / 钓鱼合约，Etherscan 合约验证状态
- **资金来源追踪** — 入账交易来源是否来自混币器、被盗资金地址
- **风险评分** — 0-100 加权评分，四级风险等级（LOW / MEDIUM / HIGH / CRITICAL）
- **多种输出格式** — 终端彩色报告、JSON、HTML 可视化报告
- **Web 前端界面** — 浏览器中输入地址完成扫描，查看风险仪表盘、风险明细和支持链信息
- **前端 API 配置** — 在 Web 页面中直接配置 / 删除 API Key，保存后无需重启即可生效
- **报告导出** — 前端扫描完成后可一键导出 JSON、HTML、CSV 报告到本地
- **API 诊断** — `check-api` 命令和 Web 页面均可验证 API 配置是否正确
- **详细日志** — `--verbose` 模式查看每个 API 调用的详细过程

## 快速开始

### 环境要求

- Python 3.10+
- pip

### 安装

```bash
git clone <repo-url> wallet-risk-scanner
cd wallet-risk-scanner
pip install -r requirements.txt
```

### 基础使用

```bash
# 扫描以太坊地址
python main.py scan 0x1234...abcd

# 扫描 BSC 地址
python main.py scan 0x1234...abcd --chain bsc

# 输出 JSON 报告
python main.py scan 0x1234...abcd --format json --output report.json

# 输出 HTML 报告
python main.py scan 0x1234...abcd --format html --output report.html

# 查看详细 API 调用日志
python main.py scan 0x1234...abcd --verbose

# 验证 API 配置是否正确
python main.py check-api

# 更新本地黑名单缓存
python main.py update-blacklist

# 查看支持的链
python main.py chains

# 启动 Web 前端页面
python main.py web

# 指定端口启动 Web 前端页面
python main.py web --port 8000
```

### 命令行参数

| 命令 | 参数 | 说明 |
|------|------|------|
| `scan` | `ADDRESS` | 要扫描的钱包地址（0x...） |
| `scan` | `--chain, -c` | 区块链名称，默认 `ethereum` |
| `scan` | `--format, -f` | 输出格式：`console`（默认）、`json`、`html` |
| `scan` | `--output, -o` | 输出文件路径（json/html 格式时使用） |
| `scan` | `--verbose, -v` | 显示详细 API 调用日志 |
| `check-api` | — | 诊断所有 API 配置，验证 Key 是否有效 |
| `update-blacklist` | — | 强制更新本地黑名单缓存 |
| `chains` | — | 列出所有支持的链 |
| `web` | `--host, -h` | Web 服务监听地址，默认 `0.0.0.0` |
| `web` | `--port, -p` | Web 服务端口，默认 `8000` |

### Web 前端使用

启动 Web 服务：

```bash
python main.py web --port 8000
```

浏览器打开：

```text
http://localhost:8000
```

Web 页面包含三个主要区域：

- **扫描地址**：输入钱包地址，选择链，点击「开始扫描」后查看风险评分仪表盘、评分明细、黑名单命中、高风险合约、资金来源风险和操作建议
- **API 状态**：查看 GoPlus、Etherscan、BscScan、ChainAbuse、ScamSniffer、OFAC 的可用状态，并可直接配置 API Key
- **支持的链**：查看当前支持的链、Chain ID 以及 Etherscan V2 免费版支持情况

扫描完成后，结果区域底部支持一键导出报告：

| 格式 | 内容 | 适用场景 |
|------|------|----------|
| JSON | 完整原始扫描结果 | 程序处理、二次分析 |
| HTML | 带样式的独立可视化报告 | 本地归档、浏览器查看、分享 |
| CSV | 风险明细表格，支持 Excel 打开 | 表格分析、统计汇总 |

导出文件会保存到浏览器默认下载目录，文件名格式为：

```text
risk-report_{链}_{地址前10位}_{时间戳}.{扩展名}
```

### 支持的链

| 链名称 | Chain ID | 参数值 | Etherscan V2 免费版 |
|--------|----------|--------|-------------------|
| Ethereum | 1 | `ethereum` | ✅ 免费 |
| Polygon | 137 | `polygon` | ✅ 免费 |
| Arbitrum | 42161 | `arbitrum` | ✅ 免费 |
| BSC | 56 | `bsc` | ❌ 需付费或配 BscScan Key |
| Optimism | 10 | `optimism` | ❌ 需付费 |
| Base | 8453 | `base` | ❌ 需付费 |

> **说明**：Etherscan V2 API 统一了多链入口，但 BSC、Optimism、Base 在免费版中不可用。扫描 BSC 链时，代码会自动回退到 BscScan V1 API（需配置 `BSCSCAN_API_KEY`）。

## API 配置

工具依赖多个外部 API，其中 GoPlus Security 和黑名单数据源无需 API Key 即可使用；Etherscan 和 BscScan 需要申请免费 API Key 以获得完整功能。

### 配置方式

支持两种配置方式：

1. 在 Web 页面中配置（推荐给普通用户）
2. 手动编辑项目根目录下的 `.env` 文件

#### 方式一：Web 页面配置

启动 Web 服务后打开浏览器：

```bash
python main.py web --port 8000
```

进入页面中的 **API 状态** 标签页，在 **API Key 配置** 区域填写：

- `ETHERSCAN_API_KEY`：Etherscan V2 API Key
- `BSCSCAN_API_KEY`：BscScan API Key
- `CHAINABUSE_API_KEY`：ChainAbuse API Key

点击「保存配置」后，配置会写入项目根目录的 `.env` 文件，并同步到当前运行中的服务进程，**无需重启 Web 服务即可生效**。

页面中也可以删除已配置的 Key。删除后同样会更新 `.env` 文件，并立即影响后续扫描。

> **安全提示**：Web 页面只显示脱敏后的 Key，例如 `M2VD****N7SE`。不要把 Web 服务暴露到公网环境中，否则别人也可能访问配置页面。

#### 方式二：手动编辑 `.env`

在项目根目录创建 `.env` 文件：

```bash
cp .env.example .env
```

编辑 `.env` 填入 API Key：

```ini
ETHERSCAN_API_KEY=your_etherscan_api_key
BSCSCAN_API_KEY=your_bscscan_api_key
CHAINABUSE_API_KEY=your_chainabuse_api_key
```

### 验证 API 配置

配置完成后，可以通过命令行或 Web 页面验证所有 API 是否正常。

命令行方式：

```bash
python main.py check-api
```

输出示例：

```
┌─────────────────────┬─────────────────────┬────────────┬────────────────────┐
│ API                 │ Key Configured      │ Key Suffix │ Test Result        │
├─────────────────────┼─────────────────────┼────────────┼────────────────────┤
│ GoPlus Security     │ N/A (no key needed) │ -          │ OK                 │
│ Etherscan V2        │ YES                 │ ***N7SE    │ OK                 │
│ BscScan (BSC V1)    │ NOT SET             │ -          │ NOT SET (limited)  │
│ ChainAbuse          │ NOT SET             │ -          │ SKIPPED (no key)   │
│ ScamSniffer         │ N/A (auto-fetch)    │ -          │ OK                 │
│ OFAC SDN            │ N/A (auto-fetch)    │ -          │ OK                 │
└─────────────────────┴─────────────────────┴────────────┴────────────────────┘

Summary:
  ✓ Etherscan V2 API key works (Ethereum/Polygon/Arbitrum free)
  ! BscScan API key is not configured - BSC chain scanning will be limited
  ! ChainAbuse API key is not configured - community reports will be skipped
```

Web 页面方式：

```bash
python main.py web --port 8000
```

打开 `http://localhost:8000`，进入 **API 状态** 标签页即可查看 API 可用状态。Web 端状态检查采用并发请求，Etherscan / BscScan / ChainAbuse / GoPlus 会同时检查；ScamSniffer 和 OFAC 使用本地缓存文件状态判断，避免每次下载大型黑名单文件。

也可以在扫描时加 `--verbose` 查看每个 API 请求的详细日志：

```bash
python main.py scan 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --verbose
```

### 各 API 申请流程

#### 1. GoPlus Security API（无需 API Key）

- **用途**：地址安全检测、代币安全检测（蜜罐/黑名单/空投诈骗等）、Rug Pull 检测
- **费用**：免费
- **调用方式**：通过官方 Python SDK（`pip install goplus`）调用，非 REST API
- **文档**：https://docs.gopluslabs.io/reference/api-overview
- **无需任何配置**，开箱即用

> **注意**：GoPlus 的 REST API 端点（`/contract_security`、`/token_security` 等）已废弃，本工具使用官方 Python SDK 调用，确保兼容性。

#### 2. Etherscan V2 API（推荐配置）

- **用途**：获取交易历史、合约验证状态、交互合约列表
- **费用**：免费版 5 calls/秒
- **覆盖链**：Ethereum、Polygon、Arbitrum（免费）；BSC、Optimism、Base（需付费计划）
- **API 入口**：`https://api.etherscan.io/v2/api`（统一多链入口，通过 `chainid` 参数区分链）
- **申请步骤**：
  1. 访问 https://etherscan.io/register 注册账号
  2. 登录后进入 https://etherscan.io/apidashboard
  3. 点击「Add +」创建新的 API Key
  4. 将 Key 填入 `.env` 的 `ETHERSCAN_API_KEY`

> **重要**：Etherscan 已于 2025 年 8 月废弃 V1 API，本工具使用 V2 API。一个 Key 即可访问所有 V2 支持的链。

> **不配置的影响**：Etherscan V2 强制要求 API Key，不带 Key 的请求会被拒绝。资金来源追踪和合约交互检测功能依赖此 API。

#### 3. BscScan API（扫描 BSC 链时需要）

- **用途**：BSC 链交易历史查询（Etherscan V2 免费版不支持 BSC，代码自动回退到 BscScan V1 API）
- **费用**：免费版 5 calls/秒
- **申请步骤**：
  1. 访问 https://bscscan.com/register 注册账号
  2. 登录后进入 https://bscscan.com/myapikey
  3. 创建 API Key
  4. 将 Key 填入 `.env` 的 `BSCSCAN_API_KEY`

> **不配置的影响**：扫描 BSC 链时，合约交互检测和资金追踪将无法获取数据。不影响其他链。

#### 4. ChainAbuse API（可选）

- **用途**：查询社区举报的恶意地址
- **费用**：基础版免费
- **申请步骤**：
  1. 访问 https://chainabuse.com 注册账号
  2. 在个人设置中获取 API Key
  3. 将 Key 填入 `.env` 的 `CHAINABUSE_API_KEY`

> **不配置的影响**：ChainAbuse 检测将被跳过，不影响其他功能。

#### 5. ScamSniffer 黑名单（自动获取，无需配置）

- **用途**：钓鱼地址黑名单
- **数据源**：https://github.com/scamsniffer/scam-database
- **费用**：免费
- **更新频率**：每日自动同步，本地缓存 24 小时
- **无需任何配置**

#### 6. OFAC SDN 制裁列表（自动获取，无需配置）

- **用途**：美国财政部制裁地址
- **数据源**：https://www.treasury.gov/ofac/downloads/sdn.csv
- **费用**：免费
- **更新频率**：本地缓存 24 小时，过期自动重新下载
- **无需任何配置**

### API Key 配置总结

| API | 是否必须 | 费用 | 需要配置 | 覆盖链 |
|-----|---------|------|---------|--------|
| GoPlus Security | 是（核心） | 免费 | 否 | 所有链 |
| ScamSniffer 黑名单 | 是 | 免费 | 否 | 所有链 |
| OFAC SDN 列表 | 是 | 免费 | 否 | 所有链 |
| Etherscan V2 | 推荐 | 免费 | 是 | ETH / Polygon / Arbitrum |
| BscScan | 按需 | 免费 | 是（BSC 需要） | BSC |
| ChainAbuse | 可选 | 免费 | 是（可选） | 所有链 |

### 不同配置下的功能覆盖

| 配置方案 | 黑名单匹配 | GoPlus 检测 | 合约交互检测 | 资金追踪 | 覆盖率 |
|---------|-----------|------------|------------|---------|--------|
| 无任何 Key | ✅ | ✅ | ❌ | ❌ | ~40% |
| 仅 Etherscan Key | ✅ | ✅ | ✅（ETH/Polygon/Arbitrum） | ✅（同左） | ~90% |
| Etherscan + BscScan Key | ✅ | ✅ | ✅（全部链） | ✅（全部链） | ~95% |
| 全部 Key | ✅ | ✅ | ✅ | ✅ | 100% |

## 技术实现

### 架构设计

```
┌──────────────────────────────────────────────────────────────┐
│                         CLI 入口层                            │
│                    (typer + rich)                             │
├──────────────────────────────────────────────────────────────┤
│                      扫描引擎核心层                           │
│  ┌───────────────┬───────────────┬─────────────────────────┐ │
│  │  Blacklist    │  ContractRisk │   FundTracing           │ │
│  │  Engine       │  Engine       │   Engine                │ │
│  └───────────────┴───────────────┴─────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              RiskScorer（加权评分引擎）                  │ │
│  └─────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────┤
│                       数据服务层                              │
│  ┌───────────────┬───────────────┬─────────────────────────┐ │
│  │  GoPlusClient │  Etherscan    │  BlacklistLoader        │ │
│  │  (SDK)        │  Client (V2   │  + TornadoCashData      │ │
│  │               │  + fallback)  │                         │ │
│  └───────────────┴───────────────┴─────────────────────────┘ │
├──────────────────────────────────────────────────────────────┤
│                        输出层                                 │
│      ConsoleReporter / JsonReporter / HtmlReporter           │
└──────────────────────────────────────────────────────────────┘
```

### Web UI 架构

Web 前端采用 FastAPI + 原生 HTML/CSS/JavaScript 实现，无需 Node.js、npm 或前端构建步骤。

```text
浏览器
  ├── GET /                         → 返回 index.html
  ├── GET /static/style.css         → 前端样式
  ├── GET /static/app.js            → 前端交互逻辑
  ├── POST /api/scan                → 执行地址扫描，返回 AddressRiskReport JSON
  ├── GET /api/check-api            → 并发检查 API 状态
  ├── GET /api/chains               → 返回支持的链列表
  ├── GET /api/config               → 返回 API Key 配置状态（脱敏）
  └── POST /api/config              → 保存 / 删除 API Key 到 .env
```

前端报告导出完全在浏览器端完成，使用 `Blob` 和 `URL.createObjectURL` 生成本地下载文件，不会把报告额外上传到任何服务。

### Etherscan API 路由策略

Etherscan V2 API 统一了多链入口，但免费版并非所有链都可用。`EtherscanClient` 实现了智能路由：

```
扫描请求 → 判断链是否在 V2 免费版中
  ├── 是（Ethereum/Polygon/Arbitrum）→ V2 API + ETHERSCAN_API_KEY
  └── 否（BSC/Optimism/Base）
        ├── 有 fallback_api_key → 回退到 V1 独立 API
        │     ├── BSC → api.bscscan.com + BSCSCAN_API_KEY
        │     ├── Optimism → api-optimistic.etherscan.io + ETHERSCAN_API_KEY
        │     └── Base → api.basescan.org + ETHERSCAN_API_KEY
        └── 无 fallback key → 尝试 V2（可能返回付费限制错误）
```

### 项目结构

```
wallet-risk-scanner/
├── main.py                           # 入口文件
├── requirements.txt                  # 依赖
├── .env.example                      # API Key 配置模板
├── web/
│   ├── server.py                     # FastAPI Web 服务与前端 API
│   └── static/
│       ├── index.html                # Web 前端页面
│       ├── style.css                 # 前端样式
│       └── app.js                    # 前端交互、扫描、配置、导出逻辑
├── scanner/
│   ├── cli.py                        # CLI 命令定义（typer）
│   ├── config.py                     # 配置管理（链配置、API Key、URL）
│   ├── models.py                     # 数据模型（pydantic）
│   ├── engines/                      # 扫描引擎
│   │   ├── blacklist.py              #   黑名单匹配引擎
│   │   ├── contract_risk.py          #   高风险合约交互检测引擎
│   │   ├── fund_tracing.py           #   资金来源追踪引擎
│   │   └── risk_scorer.py            #   风险评分引擎
│   ├── apis/                         # API 客户端封装
│   │   ├── goplus.py                 #   GoPlus Security SDK 封装
│   │   ├── etherscan.py              #   Etherscan V2 + V1 fallback
│   │   └── chainabuse.py             #   ChainAbuse API
│   ├── data/                         # 数据加载与缓存
│   │   ├── blacklist_loader.py       #   黑名单下载与本地缓存
│   │   └── tornado.py                #   Tornado Cash 合约地址集
│   ├── reporters/                    # 报告输出
│   │   ├── console.py                #   Rich 终端彩色报告
│   │   ├── json_reporter.py          #   JSON 结构化输出
│   │   └── html_reporter.py          #   HTML 可视化报告
│   └── utils/                        # 工具函数
│       ├── address.py                #   地址校验与格式化
│       ├── constants.py              #   评分权重与常量定义
│       └── log.py                    #   日志工具（verbose 模式）
├── data/
│   ├── blacklists/                   # 本地黑名单缓存（自动生成）
│   │   ├── scamsniffer_address.json  # ScamSniffer 地址缓存
│   │   ├── scamsniffer_domains.json  # ScamSniffer 域名缓存
│   │   └── ofac_addresses.json       # OFAC 地址缓存
│   └── known_contracts/              # 已知合约地址数据
│       ├── tornado_cash.json
│       └── hacked_contracts.json
└── tests/                            # 单元测试
    ├── test_address.py
    ├── test_blacklist.py
    └── test_risk_scorer.py
```

### 核心数据模型

所有数据模型基于 Pydantic v2 定义，位于 `scanner/models.py`：

```
AddressRiskReport
├── address: str              # 扫描地址
├── chain: str                # 链名称
├── chain_id: int             # Chain ID
├── blacklist_hits            # 黑名单命中列表
│   └── BlacklistHit
│       ├── source: str       # 数据源（OFAC / ScamSniffer / Tornado Cash）
│       ├── hit_type: str     # 命中类型（Sanctioned / Phishing / Mixer）
│       ├── risk_level        # 风险等级
│       └── description: str  # 描述
├── contract_risks            # 合约风险列表
│   └── ContractRisk
│       ├── address: str      # 合约地址
│       ├── risk_type: str    # 风险类型（Honeypot / Rug Pull / Unverified...）
│       ├── risk_level        # 风险等级
│       ├── source: str       # 检测来源（GoPlus / Etherscan）
│       └── detail: str       # 详情
├── fund_source_risks         # 资金来源风险列表
│   └── FundSourceRisk
│       ├── source_address    # 来源地址
│       ├── risk_type: str    # 风险类型（Mixer / Stolen Funds）
│       ├── risk_level        # 风险等级
│       ├── amount: str       # 涉及金额
│       └── tx_hash: str      # 交易哈希
└── risk_score                # 风险评分
    └── RiskScore
        ├── score: int        # 总分（0-100）
        ├── level             # 风险等级（LOW / MEDIUM / HIGH / CRITICAL）
        ├── blacklist_score   # 黑名单维度得分
        ├── contract_score    # 合约维度得分
        ├── fund_source_score # 资金来源维度得分
        └── breakdown: str    # 评分明细
```

### 风险评分算法

评分采用三维度加权累加模型，总分上限 100：

#### 维度一：黑名单命中（上限 40 分）

| 数据源 | 加分 | 触发条件 |
|--------|------|---------|
| OFAC SDN | +40 | 地址在美国财政部制裁名单中 |
| ScamSniffer | +30 | 地址在钓鱼地址库中 |
| ChainAbuse | +25 | 地址被社区举报 |
| Tornado Cash | +20 | 地址是 Tornado Cash 池子合约 |
| 已知黑客合约 | +40 | 地址与已知攻击事件关联 |

#### 维度二：高风险合约交互（上限 30 分）

| 风险类型 | 加分 | 检测来源 |
|---------|------|---------|
| Honeypot（蜜罐） | +15 | GoPlus |
| Rug Pull | +15 | GoPlus |
| Stealing Attack | +15 | GoPlus |
| Phishing | +12 | GoPlus |
| Ownership Takeover | +8 | GoPlus |
| Hidden Owner | +8 | GoPlus |
| Proxy Contract | +8 | GoPlus |
| Mintable | +6 | GoPlus |
| Airdrop Scam | +6 | GoPlus |
| Unverified Contract | +5 | Etherscan / GoPlus |

#### 维度三：资金来源风险（上限 30 分）

| 风险类型 | 加分 | 检测方式 |
|---------|------|---------|
| Stolen Funds（被盗资金） | +25 | 入账来自已知黑客地址 |
| Mixer（混币器） | +20 | 入账来自 Tornado Cash |
| Indirect Stolen | +12 | 间接关联被盗资金 |
| Indirect Mixer | +10 | 间接关联混币器 |

#### 风险等级划分

| 分数范围 | 等级 | 颜色 |
|---------|------|------|
| 0 - 20 | LOW | 绿色 |
| 21 - 50 | MEDIUM | 黄色 |
| 51 - 80 | HIGH | 橙红色 |
| 81 - 100 | CRITICAL | 红色 |

### 扫描流程

一次完整的扫描按以下顺序执行：

1. **黑名单匹配** — 地址与 OFAC、ScamSniffer、Tornado Cash、已知黑客合约进行比对
2. **合约交互检测** — 通过 Etherscan 获取最近 100 笔交易的交互合约，逐个通过 GoPlus 检测安全性（最多检测 10 个合约）
3. **资金来源追踪** — 通过 Etherscan 获取入账交易，检查 from 地址是否在混币器或黑客地址库中
4. **风险评分** — 三维度得分加权累加，判定风险等级
5. **报告输出** — 根据用户选择的格式生成报告

### 速率限制

所有 API 客户端内置请求间隔控制（默认 250ms），避免触发 API 速率限制：

- GoPlus API：无需 Key，自带速率控制
- Etherscan V2 API：免费版 5 calls/秒，带 Key 后可充分利用
- BscScan V1 API：免费版 5 calls/秒
- 黑名单数据：本地缓存 24 小时，避免重复下载

### 黑名单缓存机制

`BlacklistLoader` 实现了本地文件缓存，缓存目录为：

```text
data/blacklists/
```

主要缓存文件包括：

```text
data/blacklists/scamsniffer_address.json
data/blacklists/scamsniffer_domains.json
data/blacklists/ofac_addresses.json
```

缓存规则：

- 首次运行时从远程下载 JSON/CSV 数据到 `data/blacklists/` 目录
- 后续运行检查文件修改时间，超过 24 小时自动重新下载
- 可通过 `python main.py update-blacklist` 强制更新
- 网络不可用时使用本地缓存数据
- Web 页面中的 API 状态检查会读取这些缓存文件的状态，避免每次请求都下载 ScamSniffer / OFAC 的完整数据

## 输出示例

### 终端报告（默认）

```
┌─────────────────────────────────────────────────────────────┐
│ Wallet Risk Scanner                                         │
│                                                             │
│ Address: 0xd8da6bf26964af9d7eed9e03e53415d37aa96045         │
│ Chain:   ethereum (1)                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│   RISK SCORE: 10 / 100                                      │
│   ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  LOW             │
│                                                             │
│   Breakdown: Contracts: +10                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
✓ No blacklist hits found.

                           ⚠ High-Risk Contracts (2)
┌─────────────────┬─────────────────┬────────────┬───────────┐
│ Contract        │ Risk Type       │ Risk Level │ Source    │
├─────────────────┼─────────────────┼────────────┼───────────┤
│ 0x3c7779...284… │ Unverified      │ MEDIUM     │ Etherscan │
│ 0xbad06a...e6d… │ Unverified      │ MEDIUM     │ Etherscan │
└─────────────────┴─────────────────┴────────────┴───────────┘

✓ No risky fund sources detected.

┌─────────────────────────────────────────────────────────────┐
│ 💡 Recommendation: This address appears to be LOW RISK.     │
└─────────────────────────────────────────────────────────────┘
```

### JSON 报告

```json
{
  "address": "0xd8da6bf26964af9d7eed9e03e53415d37aa96045",
  "chain": "ethereum",
  "chain_id": 1,
  "blacklist_hits": [],
  "contract_risks": [],
  "fund_source_risks": [],
  "risk_score": {
    "score": 0,
    "level": "LOW",
    "blacklist_score": 0,
    "contract_score": 0,
    "fund_source_score": 0,
    "breakdown": "No risks detected"
  }
}
```

### Web 前端导出报告

在 Web 页面完成扫描后，结果区域底部会显示「📥 导出报告」按钮组：

- **JSON**：导出完整原始扫描数据
- **HTML**：导出带暗色主题样式的独立报告文件
- **CSV**：导出风险明细表格，已加入 BOM 头，Excel 打开中文不乱码

导出的文件默认进入浏览器下载目录。

### Verbose 日志示例

```bash
python main.py scan 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --verbose
```

日志输出到 stderr，显示每个 API 请求的详细信息：

```
[Etherscan] Chain ethereum (id=1) uses V2 API (free tier)
[GoPlus/SDK] Address.security address=0xd8da6bf2... chain_id=1
[GoPlus/SDK] Address found 0 risks
[Etherscan/V2 chainid=1] GET module=account action=txlist apikey=***N7SE
[Etherscan/V2 chainid=1] Response: status=200
[Etherscan/V2 chainid=1] Result: status=1 message=OK
[Etherscan] Got 100 transactions for 0xd8da6bf2...
[Etherscan] Found 8 interacted contracts for 0xd8da6bf2...
[GoPlus/SDK] Token.security address=0xdac17f958d2ee523a2206206994597c13d831ec7 chain_id=1
[GoPlus/SDK] Token found 0 risks
[GoPlus/SDK] RugPull.security address=0xdac17f958d2ee523a2206206994597c13d831ec7 chain_id=1
[GoPlus/SDK] RugPull found 0 risks
```

## 运行测试

```bash
python -m pytest tests/ -v
```

## 安全声明

- 本工具**仅读取链上公开数据**，绝不请求私钥或助记词
- 所有 API Key 通过 `.env` 文件管理，不硬编码在代码中
- Web 页面配置 API Key 时只展示脱敏值，但不要将 Web 服务暴露到公网
- 用户输入的地址仅用于查询，不记录不上传
- 前端导出报告完全在浏览器本地生成，不会额外上传
- 遵守各 API 的调用频率限制

## 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| 语言 | Python 3.10+ | 类型提示 + 枚举 |
| CLI | typer | 现代 CLI 框架，自带帮助文档 |
| 终端输出 | rich | 彩色表格、面板、进度条 |
| 安全检测 | goplus SDK | GoPlus Security 官方 Python SDK（非 REST API） |
| 区块浏览器 | requests / httpx | Etherscan V2 API + V1 fallback；Web API 状态检查使用 httpx 并发请求 |
| Web 后端 | FastAPI + uvicorn | 提供前端页面和 REST API |
| Web 前端 | HTML / CSS / JavaScript | 原生单页应用，无需构建步骤 |
| 数据模型 | pydantic v2 | 数据验证与序列化 |
| 配置管理 | python-dotenv | .env 文件加载，Web 页面可写入配置 |
| 测试 | pytest | 单元测试 |
