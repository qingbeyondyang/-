# Perpetual Futures Millisecond Data Collector (Modular)

[English](./README.md) | [中文](./README_ZH.md)

## Program overview

This project is built for perpetual futures market data collection, with a focus on **millisecond-level trade records**.

It continuously stores price, quantity, timestamp, and funding-related data to local files, making it practical for:

- strategy backtesting
- market micro-behavior review
- spike/crash post-mortem analysis
- long-term data archiving

Supported exchanges in the current version:

- Binance
- Bybit

Besides live collection, it also provides funding-rate monitoring with automatic collection windows and a historical file viewer.

## Data sources (URLs)

This tool currently connects to the following public endpoints:

- Binance real-time trade stream (perpetual, WebSocket):  
  `wss://fstream.binance.com/ws/{symbol}@aggTrade`
- Bybit real-time trade stream (perpetual, WebSocket):  
  `wss://stream.bybit.com/v5/public/linear`  
  Subscription topic: `publicTrade.{symbol}`
- Binance funding rate (REST):  
  `https://fapi.binance.com/fapi/v1/premiumIndex`
- Binance funding info (REST):  
  `https://fapi.binance.com/fapi/v1/fundingInfo`
- Binance 24h quote volume (REST):  
  `https://fapi.binance.com/fapi/v1/ticker/24hr`

## What makes it different

Compared with many tools that are either script-only or chart-only, this project combines:

- an easy WebUI for operation
- backend logic that is still clean and easy to extend

The modular split also reduces maintenance cost:

- `app.py` for startup
- `routes.py` for APIs
- `runtime.py` for runtime state and collector logic
- `template.py` for UI

Bilingual structure is provided:

- `zh/` Chinese UI (port `7890`)
- `en/` English UI (port `7891`)

## Main strengths

- The primary strength is millisecond-level data capture for fine-grained market observation
- Live collection, funding monitoring, and historical browsing in one UI
- CSV/JSON export for direct analysis
- Bilingual UI and documentation structure
- Cleaner modular code for future feature expansion

## Feature guide (aligned with WebUI)

The WebUI has three tabs: `Real-time collection`, `Automatic collection of tariff rates`, and `Historical files`.

### Real-time collection

This is the main collection workflow.

- Set exchange, symbol, file name, save folder, and output format
- Start/stop collection
- Download collected data or clear in-memory records
- Monitor live status cards and candle count
- Tune candle interval, max candles, and auto-refresh behavior

### Automatic collection of tariff rates

This tab handles funding-rate ranking and collection around funding windows.

- Configure Top N, pre/post funding minutes, min interval, min volume filter, output folder, and format
- Optionally set manual symbols; otherwise auto-select by ranking
- Use start/stop monitoring and immediate refresh actions
- View ranking table, active auto-collect list, and logs

### Historical files

This tab is for history management and replay.

- Browse and load CSV/JSON files
- Rebuild chart candles at selected intervals
- Batch-select and download files as a zip package
- Use the built-in line-drawing backtest panel for quick scenario replay

## How to use

Start either version and open it in a browser:

- Chinese: `http://127.0.0.1:7890`
- English: `http://127.0.0.1:7891`

Typical workflow:

- Start with live collection and confirm data flow
- Export data when needed
- Enable funding monitoring for automated window collection
- Use historical files for replay and batch export

## Installation

Python `3.9+` is recommended.

Install dependencies:

```bash
pip install flask flask-cors websockets
```

Start command:

```bash
python app.py
```
