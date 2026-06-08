# 🩺 APIPulse-CLI

> **Lightweight Terminal API Health Monitoring Engine**
> 轻量级终端API健康监控引擎

[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Zero Dependencies](https://img.shields.io/badge/Dependencies-Zero-orange.svg)]()
[![Tests](https://img.shields.io/badge/Tests-32%20passed-brightgreen.svg)]()

**[English](#english) · [简体中文](#简体中文) · [繁體中文](#繁體中文)**

---

<a id="简体中文"></a>

## 🎉 项目介绍

**APIPulse-CLI** 是一款零依赖、纯Python实现的终端API健康监控引擎。它能够对单个或多个API端点进行持续健康检测，追踪响应时间，检测异常状态变化，并生成多格式的监控报告。

### 💡 灵感来源

在GitHub Trending上，API测试与监控工具（如Yaak、Hoppscotch）持续火热。然而，大多数工具要么是重量级的GUI应用，要么需要复杂的环境配置。APIPulse-CLI 填补了这一空白——一个**真正轻量、零依赖、开箱即用**的终端API健康监控方案。

### 🌟 自研差异化亮点

- **零依赖**：仅使用Python标准库，无需安装任何第三方包
- **智能告警**：基于连续失败次数和状态变化的智能告警系统
- **响应时间分解**：DNS解析、连接建立、TLS握手的细粒度时间追踪
- **多格式报告**：终端表格、JSON、Markdown三种报告格式
- **YAML零依赖解析**：内置轻量级YAML解析器，无需安装PyYAML

---

## ✨ 核心特性

| 特性 | 描述 |
|------|------|
| 🔍 **单端点检测** | 对任意API端点执行即时健康检查，支持自定义HTTP方法、请求头和请求体 |
| 📡 **多端点监控** | 从配置文件加载多个端点，按间隔持续监控，支持无限运行或定时停止 |
| ⚡ **响应时间追踪** | 细粒度记录DNS、连接、TLS各阶段耗时，精确到毫秒 |
| 🚨 **智能告警** | 连续失败阈值告警、状态降级检测、恢复通知三级告警体系 |
| 📊 **多格式报告** | 终端彩色表格、JSON数据、Markdown文档三种输出格式 |
| 📄 **配置文件** | 支持YAML和JSON配置文件，内置轻量级YAML解析器（无需PyYAML） |
| 🔒 **SSL控制** | 可配置SSL证书验证，适配内网自签名证书场景 |
| 🧪 **完整测试** | 32个单元测试覆盖核心模块，确保功能稳定 |

---

## 🚀 快速开始

### 环境要求

- **Python 3.8+** （无需任何第三方依赖）

### 安装

```bash
# 克隆仓库
git clone https://github.com/gitstq/APIPulse-CLI.git
cd APIPulse-CLI

# 直接运行（零安装）
python healthpulse.py --help
```

### 快速检测单个端点

```bash
# 基本检测
python healthpulse.py check https://api.github.com/zen

# 自定义方法和超时
python healthpulse.py check https://api.example.com/health --method POST --timeout 15

# 连续检测5次，每次间隔10秒
python healthpulse.py check https://api.example.com/health --interval 10 --count 5

# 带自定义请求头
python healthpulse.py check https://api.example.com/health --headers '{"Authorization": "Bearer token"}'
```

### 多端点持续监控

```bash
# 生成示例配置文件
python healthpulse.py init --output my_endpoints.yaml

# 启动监控（每30秒检测一次，持续5分钟）
python healthpulse.py monitor my_endpoints.yaml --interval 30 --duration 300

# 无限监控（直到手动停止）
python healthpulse.py monitor my_endpoints.yaml --interval 60

# JSON格式输出
python healthpulse.py monitor my_endpoints.yaml --output json --report-file results.json
```

### 生成报告

```bash
# 从保存的结果文件生成Markdown报告
python healthpulse.py report results.json --format markdown --output report.md
```

---

## 📖 详细使用指南

### 配置文件格式

```yaml
# 全局设置
interval: 30          # 检测间隔（秒）
duration: 0          # 总监控时长（0=无限）
alert_threshold: 3   # 连续失败告警阈值
output_format: table # 输出格式：table / json / markdown
ssl_verify: true     # SSL证书验证
global_timeout: 10   # 默认请求超时（秒）

# 全局请求头（应用于所有端点）
global_headers:
  Accept: application/json

# 端点定义
endpoints:
  - name: 用户服务
    url: https://api.example.com/users/health
    method: GET
    timeout: 5
    expected_status: 200
    degraded_threshold_ms: 500
    unhealthy_threshold_ms: 2000
    tags:
      - internal
      - critical

  - name: 支付服务
    url: https://api.example.com/payments/health
    method: GET
    timeout: 10
    tags:
      - internal
      - payment
```

### 告警级别

| 级别 | 图标 | 触发条件 |
|------|------|----------|
| 🚨 **CRITICAL** | 严重 | 连续失败达到阈值 / 状态从健康变为不健康 |
| ⚠️ **WARNING** | 警告 | 状态从健康降级 / 响应时间超过不健康阈值 |
| ✅ **RECOVERY** | 恢复 | 端点从不健康/降级恢复为健康 |
| ℹ️ **INFO** | 信息 | 一般性通知 |

### 输出示例

```
🩺 APIPulse Check Result
   Time:     14:30:25
   URL:      https://api.example.com/health
   Method:   GET
   Status:   ✅ HEALTHY
   Code:     200
   Response: 156.32ms
   DNS:      12.05ms
   Connect:  89.27ms
```

---

## 💡 设计思路与迭代规划

### 设计理念

- **极简主义**：零外部依赖，Python标准库即可运行
- **开发者友好**：清晰的终端输出，丰富的表情符号，一目了然
- **可扩展性**：模块化架构，易于添加新的检测策略和报告格式

### 技术选型

| 组件 | 选型 | 原因 |
|------|------|------|
| HTTP客户端 | `urllib.request` | 标准库内置，零依赖 |
| 配置解析 | 自研轻量YAML解析器 | 避免PyYAML依赖 |
| 终端UI | ANSI转义码 | 标准库内置，跨平台彩色输出 |
| 异步支持 | `asyncio` | 为未来并发检测预留 |

### 后续规划

- [ ] 🔜 支持HTTP/2检测
- [ ] 🔜 添加Prometheus指标导出
- [ ] 🔜 Web仪表盘（可选依赖）
- [ ] 🔜 邮件/Slack/Webhook告警通知
- [ ] 🔜 历史数据趋势图表

---

## 📦 安装与部署

### 方式一：直接运行（推荐）

```bash
git clone https://github.com/gitstq/APIPulse-CLI.git
cd APIPulse-CLI
python healthpulse.py check https://api.example.com/health
```

### 方式二：pip安装

```bash
pip install .
apipulse check https://api.example.com/health
```

### 方式三：开发模式

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

### 兼容环境

| 环境 | 支持情况 |
|------|----------|
| Python 3.8+ | ✅ 完全支持 |
| Linux | ✅ 完全支持 |
| macOS | ✅ 完全支持 |
| Windows | ✅ 完全支持 |
| CI/CD | ✅ 推荐 |

---

## 🤝 贡献指南

欢迎贡献代码！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

### 提交规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
feat: 新增功能
fix: 修复问题
docs: 文档更新
refactor: 代码重构
test: 测试相关
chore: 构建/工具链
```

---

## 📄 开源协议

本项目基于 [MIT License](LICENSE) 开源。

---

<a id="繁體中文"></a>

## 🎉 專案介紹

**APIPulse-CLI** 是一款零依賴、純Python實現的終端API健康監控引擎。它能夠對單個或多個API端點進行持續健康檢測，追蹤響應時間，檢測異常狀態變化，並生成多格式的監控報告。

### 💡 靈感來源

在GitHub Trending上，API測試與監控工具（如Yaak、Hoppscotch）持續火熱。然而，大多數工具要麼是重量級的GUI應用，要麼需要複雜的環境配置。APIPulse-CLI 填補了這一空白——一個**真正輕量、零依賴、開箱即用**的終端API健康監控方案。

### 🌟 自研差異化亮點

- **零依賴**：僅使用Python標準庫，無需安裝任何第三方套件
- **智能告警**：基於連續失敗次數和狀態變化的智能告警系統
- **響應時間分解**：DNS解析、連接建立、TLS握手的細粒度時間追蹤
- **多格式報告**：終端表格、JSON、Markdown三種報告格式
- **YAML零依賴解析**：內建輕量級YAML解析器，無需安裝PyYAML

---

## ✨ 核心特性

| 特性 | 描述 |
|------|------|
| 🔍 **單端點檢測** | 對任意API端點執行即時健康檢查，支援自訂HTTP方法、請求標頭和請求體 |
| 📡 **多端點監控** | 從設定檔載入多個端點，按間隔持續監控，支援無限運行或定時停止 |
| ⚡ **響應時間追蹤** | 細粒度記錄DNS、連接、TLS各階段耗時，精確到毫秒 |
| 🚨 **智能告警** | 連續失敗閾值告警、狀態降級檢測、恢復通知三級告警體系 |
| 📊 **多格式報告** | 終端彩色表格、JSON資料、Markdown文件三種輸出格式 |
| 📄 **設定檔** | 支援YAML和JSON設定檔，內建輕量級YAML解析器（無需PyYAML） |
| 🔒 **SSL控制** | 可設定SSL憑證驗證，適配內網自簽名憑證場景 |
| 🧪 **完整測試** | 32個單元測試覆蓋核心模組，確保功能穩定 |

---

## 🚀 快速開始

### 環境要求

- **Python 3.8+** （無需任何第三方依賴）

### 安裝

```bash
# 克隆倉庫
git clone https://github.com/gitstq/APIPulse-CLI.git
cd APIPulse-CLI

# 直接運行（零安裝）
python healthpulse.py --help
```

### 快速檢測單個端點

```bash
# 基本檢測
python healthpulse.py check https://api.github.com/zen

# 自訂方法和逾時
python healthpulse.py check https://api.example.com/health --method POST --timeout 15

# 連續檢測5次，每次間隔10秒
python healthpulse.py check https://api.example.com/health --interval 10 --count 5

# 帶自訂請求標頭
python healthpulse.py check https://api.example.com/health --headers '{"Authorization": "Bearer token"}'
```

### 多端點持續監控

```bash
# 生成範例設定檔
python healthpulse.py init --output my_endpoints.yaml

# 啟動監控（每30秒檢測一次，持續5分鐘）
python healthpulse.py monitor my_endpoints.yaml --interval 30 --duration 300

# 無限監控（直到手動停止）
python healthpulse.py monitor my_endpoints.yaml --interval 60
```

### 生成報告

```bash
# 從儲存的結果檔案生成Markdown報告
python healthpulse.py report results.json --format markdown --output report.md
```

---

## 📖 詳細使用指南

### 設定檔格式

```yaml
# 全域設定
interval: 30          # 檢測間隔（秒）
duration: 0          # 總監控時長（0=無限）
alert_threshold: 3   # 連續失敗告警閾值
output_format: table # 輸出格式：table / json / markdown
ssl_verify: true     # SSL憑證驗證
global_timeout: 10   # 預設請求逾時（秒）

# 全域請求標頭（應用於所有端點）
global_headers:
  Accept: application/json

# 端點定義
endpoints:
  - name: 使用者服務
    url: https://api.example.com/users/health
    method: GET
    timeout: 5
    expected_status: 200
    degraded_threshold_ms: 500
    unhealthy_threshold_ms: 2000
    tags:
      - internal
      - critical
```

### 告警級別

| 級別 | 圖示 | 觸發條件 |
|------|------|----------|
| 🚨 **CRITICAL** | 嚴重 | 連續失敗達到閾值 / 狀態從健康變為不健康 |
| ⚠️ **WARNING** | 警告 | 狀態從健康降級 / 響應時間超過不健康閾值 |
| ✅ **RECOVERY** | 恢復 | 端點從不健康/降級恢復為健康 |
| ℹ️ **INFO** | 資訊 | 一般性通知 |

---

## 💡 設計思路與迭代規劃

### 設計理念

- **極簡主義**：零外部依賴，Python標準庫即可運行
- **開發者友善**：清晰的終端輸出，豐富的表情符號，一目了然
- **可擴展性**：模組化架構，易於新增新的檢測策略和報告格式

### 後續規劃

- [ ] 🔜 支援HTTP/2檢測
- [ ] 🔜 新增Prometheus指標匯出
- [ ] 🔜 Web儀表盤（可選依賴）
- [ ] 🔜 郵件/Slack/Webhook告警通知
- [ ] 🔜 歷史資料趨勢圖表

---

## 📦 安裝與部署

```bash
# 直接運行（推薦）
git clone https://github.com/gitstq/APIPulse-CLI.git
cd APIPulse-CLI
python healthpulse.py check https://api.example.com/health

# pip安裝
pip install .
apipulse check https://api.example.com/health
```

### 相容環境

| 環境 | 支援情況 |
|------|----------|
| Python 3.8+ | ✅ 完全支援 |
| Linux | ✅ 完全支援 |
| macOS | ✅ 完全支援 |
| Windows | ✅ 完全支援 |

---

## 🤝 貢獻指南

歡迎貢獻程式碼！請查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解詳情。

---

## 📄 開源協議

本專案基於 [MIT License](LICENSE) 開源。

---

<a id="english"></a>

## 🎉 Introduction

**APIPulse-CLI** is a zero-dependency, pure Python terminal API health monitoring engine. It performs continuous health checks on single or multiple API endpoints, tracks response times, detects anomalous status changes, and generates monitoring reports in multiple formats.

### 💡 Inspiration

API testing and monitoring tools like Yaak and Hoppscotch have been trending on GitHub. However, most tools are either heavyweight GUI applications or require complex environment setup. APIPulse-CLI fills this gap — a **truly lightweight, zero-dependency, ready-to-use** terminal API health monitoring solution.

### 🌟 Differentiation Highlights

- **Zero Dependencies**: Uses only Python standard library — no third-party packages needed
- **Intelligent Alerting**: Smart alert system based on consecutive failure counts and status changes
- **Response Time Breakdown**: Fine-grained tracking of DNS resolution, connection establishment, and TLS handshake
- **Multi-format Reports**: Terminal table, JSON, and Markdown output formats
- **Zero-dependency YAML Parsing**: Built-in lightweight YAML parser — no PyYAML required

---

## ✨ Core Features

| Feature | Description |
|---------|-------------|
| 🔍 **Single Endpoint Check** | Instant health check on any API endpoint with custom HTTP methods, headers, and body |
| 📡 **Multi-endpoint Monitoring** | Load multiple endpoints from config, monitor at intervals, with timed or infinite execution |
| ⚡ **Response Time Tracking** | Millisecond-precise breakdown of DNS, connection, and TLS phases |
| 🚨 **Intelligent Alerting** | Three-tier alert system: consecutive failure threshold, status degradation, and recovery |
| 📊 **Multi-format Reports** | Colored terminal table, JSON data, and Markdown document output |
| 📄 **Config Files** | YAML and JSON configuration support with built-in lightweight YAML parser |
| 🔒 **SSL Control** | Configurable SSL certificate verification for self-signed certificate scenarios |
| 🧪 **Full Test Coverage** | 32 unit tests covering all core modules |

---

## 🚀 Quick Start

### Requirements

- **Python 3.8+** (no third-party dependencies required)

### Installation

```bash
# Clone the repository
git clone https://github.com/gitstq/APIPulse-CLI.git
cd APIPulse-CLI

# Run directly (zero installation)
python healthpulse.py --help
```

### Check a Single Endpoint

```bash
# Basic check
python healthpulse.py check https://api.github.com/zen

# Custom method and timeout
python healthpulse.py check https://api.example.com/health --method POST --timeout 15

# Repeat 5 times with 10-second intervals
python healthpulse.py check https://api.example.com/health --interval 10 --count 5

# With custom headers
python healthpulse.py check https://api.example.com/health --headers '{"Authorization": "Bearer token"}'
```

### Multi-endpoint Monitoring

```bash
# Generate a sample config file
python healthpulse.py init --output my_endpoints.yaml

# Start monitoring (every 30s, for 5 minutes)
python healthpulse.py monitor my_endpoints.yaml --interval 30 --duration 300

# Infinite monitoring (until manually stopped)
python healthpulse.py monitor my_endpoints.yaml --interval 60

# JSON output with results saved to file
python healthpulse.py monitor my_endpoints.yaml --output json --report-file results.json
```

### Generate Reports

```bash
# Generate Markdown report from saved results
python healthpulse.py report results.json --format markdown --output report.md
```

---

## 📖 Detailed Usage Guide

### Configuration File Format

```yaml
# Global settings
interval: 30          # Check interval (seconds)
duration: 0          # Total monitoring duration (0 = infinite)
alert_threshold: 3   # Consecutive failures before alert
output_format: table # Output format: table / json / markdown
ssl_verify: true     # SSL certificate verification
global_timeout: 10   # Default request timeout (seconds)

# Global headers (applied to all endpoints)
global_headers:
  Accept: application/json

# Endpoint definitions
endpoints:
  - name: User Service
    url: https://api.example.com/users/health
    method: GET
    timeout: 5
    expected_status: 200
    degraded_threshold_ms: 500
    unhealthy_threshold_ms: 2000
    tags:
      - internal
      - critical
```

### Alert Levels

| Level | Icon | Trigger Condition |
|-------|------|-------------------|
| 🚨 **CRITICAL** | Critical | Consecutive failures reach threshold / Status changes from healthy to unhealthy |
| ⚠️ **WARNING** | Warning | Status degrades from healthy / Response time exceeds unhealthy threshold |
| ✅ **RECOVERY** | Recovery | Endpoint recovers from unhealthy/degraded to healthy |
| ℹ️ **INFO** | Info | General notifications |

### Output Example

```
🩺 APIPulse Check Result
   Time:     14:30:25
   URL:      https://api.example.com/health
   Method:   GET
   Status:   ✅ HEALTHY
   Code:     200
   Response: 156.32ms
   DNS:      12.05ms
   Connect:  89.27ms
```

---

## 💡 Design Philosophy & Roadmap

### Design Principles

- **Minimalism**: Zero external dependencies — runs on Python standard library alone
- **Developer-Friendly**: Clear terminal output with rich emoji indicators
- **Extensibility**: Modular architecture for easy addition of new check strategies and report formats

### Technology Choices

| Component | Choice | Reason |
|-----------|--------|--------|
| HTTP Client | `urllib.request` | Built-in standard library, zero dependencies |
| Config Parsing | Custom lightweight YAML parser | Avoids PyYAML dependency |
| Terminal UI | ANSI escape codes | Built-in, cross-platform colored output |
| Async Support | `asyncio` | Reserved for future concurrent checking |

### Roadmap

- [ ] 🔜 HTTP/2 endpoint checking
- [ ] 🔜 Prometheus metrics export
- [ ] 🔜 Web dashboard (optional dependency)
- [ ] 🔜 Email/Slack/Webhook alert notifications
- [ ] 🔜 Historical data trend charts

---

## 📦 Installation & Deployment

### Option 1: Direct Run (Recommended)

```bash
git clone https://github.com/gitstq/APIPulse-CLI.git
cd APIPulse-CLI
python healthpulse.py check https://api.example.com/health
```

### Option 2: pip Install

```bash
pip install .
apipulse check https://api.example.com/health
```

### Option 3: Development Mode

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

### Compatible Environments

| Environment | Support |
|-------------|---------|
| Python 3.8+ | ✅ Full support |
| Linux | ✅ Full support |
| macOS | ✅ Full support |
| Windows | ✅ Full support |
| CI/CD | ✅ Recommended |

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Commit Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: new feature
fix: bug fix
docs: documentation update
refactor: code refactoring
test: test related
chore: build/toolchain
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

**⭐ If you find this project helpful, please give it a star!**
