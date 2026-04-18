# Perpetual Futures Millisecond Data Collector (Modular, English UI)

## What this project does

This tool collects **millisecond-level perpetual futures trade data** and stores it as local files for later analysis.

It is designed for:

- strategy replay and backtesting
- abnormal move investigation
- high-frequency price behavior review
- historical data archiving

The English version runs on port `7891` and provides an English WebUI.

## Data sources

The current implementation uses public Binance and Bybit endpoints:

- Binance trade stream (WebSocket):  
  `wss://fstream.binance.com/ws/{symbol}@aggTrade`
- Bybit trade stream (WebSocket):  
  `wss://stream.bybit.com/v5/public/linear`  
  Subscription topic: `publicTrade.{symbol}`
- Binance funding rate (REST):  
  `https://fapi.binance.com/fapi/v1/premiumIndex`
- Binance funding info (REST):  
  `https://fapi.binance.com/fapi/v1/fundingInfo`
- Binance 24h quote volume (REST):  
  `https://fapi.binance.com/fapi/v1/ticker/24hr`

## Why this is different

Many tools are either script-only or chart-only.  
This project combines both:

- direct WebUI operation for day-to-day use
- clear backend modules for developer extension

It also includes:

- real-time collection tab
- automated funding-window collection
- historical file browser with batch download and replay helpers

## Main highlights

- Millisecond-level trade data collection
- One UI for live collection, funding monitoring, and history replay
- CSV and JSON export support
- Bilingual structure (`zh/` and `en/`)
- Modular codebase that is easier to read and maintain

## WebUI feature guide

The English WebUI has three main tabs:

### Real-time collection

Use this tab to run the main live collector.

- Configure exchange, symbol, file name, save folder, and output format
- Start/stop collection from the control buttons
- Download or clear in-memory data
- Watch live status cards and candle updates
- Adjust candle interval, max candles, and refresh behavior

### Automatic collection of tariff rates

Use this tab for funding-rate ranking and window-based auto collection.

- Configure Top N, pre/post funding window, min interval, min volume filter, save folder, and format
- Choose symbols manually or let the system auto-pick from ranking
- Start/stop monitoring and trigger immediate funding-rate refresh
- View ranking table, current auto-collect list, and collection logs

### Historical files

Use this tab for historical browsing and replay.

- Load CSV/JSON files from a target folder
- Rebuild candles at custom intervals
- Batch select and download files as a zip package
- Use the built-in line-drawing backtest panel for quick replay checks

## How to run

From the `modular_versions/en` directory:

```bash
python app.py
```

Open:

`http://127.0.0.1:7891`

## Installation

Python `3.9+` is recommended.

Install dependencies:

```bash
pip install flask flask-cors websockets
```

## Module layout

- `app.py`: startup entry (`7891`)
- `routes.py`: API routes with English responses
- `runtime.py`: runtime bridge (reuses `../zh/runtime.py`)
- `template.py`: English WebUI template
