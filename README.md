# AutoTrade — Algorithmic Trading System

A modular, production-structured algorithmic trading system with a Streamlit
dashboard, paper trading via Alpaca, and four independent components.

---

## Architecture

```
autotrade/
├── config/            Settings — Pydantic + .env
├── data/              Market Data Collector (✅ implemented)
│   ├── base.py        DataProvider ABC
│   ├── models.py      Bar, Quote, AssetInfo, Timeframe
│   ├── cache.py       Parquet + in-memory cache
│   └── providers/
│       └── alpaca.py  Alpaca REST + WebSocket provider
├── signals/           Signal Generator (🔧 stub)
│   ├── base.py        Signal, SignalGenerator ABC
│   ├── time_series/   ARIMA, Holt-Winters (TODO)
│   ├── neural/        LSTM, Transformer (TODO)
│   └── llm/           LLM sentiment (TODO)
├── portfolio/         Portfolio + Risk Manager (🔧 stub)
│   ├── base.py        PortfolioManager ABC
│   ├── optimizer.py   MPT, Black-Litterman (TODO)
│   └── risk.py        VaR, Sharpe, drawdown (TODO)
├── backtester/        Backtester (🔧 stub)
│   ├── engine.py      Event-driven engine (TODO)
│   └── metrics.py     CAGR, Sharpe, etc. (TODO)
├── execution/         Trade Execution (🔧 stub)
│   ├── base.py        Broker ABC
│   └── alpaca.py      Alpaca paper orders (TODO)
└── dashboard/         Streamlit App (✅ skeleton)
    ├── app.py         Home / overview
    └── pages/
        ├── 1_Market_Data.py   ✅ Live data
        ├── 2_Portfolio.py     🔧 Placeholder
        ├── 3_Signals.py       🔧 Placeholder
        └── 4_Backtester.py    🔧 Placeholder
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure credentials

```bash
cp .env.example .env
# Edit .env and add your Alpaca paper trading API key + secret
```

Get paper trading keys free at https://app.alpaca.markets/paper-trading

### 3. Run the dashboard

```bash
streamlit run dashboard/app.py
```

---

## Data Feed

The system defaults to Alpaca's **IEX feed** (free tier).  
Switch to `ALPACA_DATA_FEED=sip` in `.env` for real-time SIP data (requires subscription).

---

## Implementation Order

Components are being built in this order:

1. ✅ Project skeleton + abstractions
2. ✅ Market Data Collector (Alpaca provider + cache)
3. 🔧 Signal Generator (time series → neural → LLM → ensemble)
4. 🔧 Portfolio + Risk Manager
5. 🔧 Backtester
6. 🔧 Trade Execution (Alpaca paper orders)
