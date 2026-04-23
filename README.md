# bseindia 1.0.0

A Python library for fetching publicly available market data from the [BSE India](https://www.bseindia.com/) website and API endpoints. It wraps the CSV/JSON/HTML feeds that power bseindia.com and returns clean `pandas` DataFrames (or Python dicts) ready for analysis.

> Tested on Python 3.9+. Data is scraped from public BSE endpoints — be mindful of request rates.

---

## Installation

Fresh install:

```bash
pip install bseindia
```

Upgrade:

```bash
pip install bseindia --upgrade
```

### Dependencies

Installed automatically via `pip`:

- `requests`
- `pandas` (>= 2.0.0)
- `numpy`
- `beautifulsoup4`
- `lxml`
- `xlrd`

---

## Quick start

```python
import bseindia

# Trading holiday calendar for the equity segment
holidays = bseindia.trading_holiday_calendar()

# Full BSE equity security master (cached locally to bse_security_list.csv)
securities = bseindia.all_listed_securities()

# Historical price/volume for a stock
from bseindia import equity
hist = equity.historical_stock_data(symbol="SBIN", period="1M")

# Today's bulk deals
deals = equity.bulk_deal_as_on_today()

# Derivatives bhavcopy for a given trade date
from bseindia import derivatives
fo_bhav = derivatives.derivative_bhav_copy(trade_date="01-07-2024")
```

Dates are always `dd-mm-YYYY` strings (e.g. `"10-06-2024"`).

---

## API reference

### Top level — `bseindia`

| Function | Purpose |
| --- | --- |
| `trading_holiday_calendar(year=None)` | BSE equity-segment holiday list. Optional `year` filter. |
| `all_listed_securities(refresh=False)` | Equity security master (`security_code`, `symbol`, `isin_no`, `group`, …). Cached locally; pass `refresh=True` to re-download. |

### Equity — `bseindia.equity`

| Function | Purpose |
| --- | --- |
| `historical_stock_data(symbol, from_date=None, to_date=None, period=None)` | Historical OHLCV for a symbol. Supply either `from_date`/`to_date` or `period` (`1D`, `1W`, `1M`, `3M`, `6M`, `1Y`). |
| `stock_info(symbol)` | Quote-header dict for a symbol (face value, group, market cap, 52w high/low, …). |
| `equity_bhav_copy(trade_date)` | CM-UDiFF bhavcopy for the given trade date, as a DataFrame. |
| `equity_turnover()` | Year-wise equity turnover key statistics. |
| `equity_segment_history()` | Yearly equity-segment history (listed companies, trades, turnover) from 1997‑98 onwards. |
| `category_wise_turnover(period='monthly', month='01', year='2026', from_date=..., to_date=...)` | Category-wise turnover. `period` can be `'monthly'`, `'yearly'`, or range-based (provide `from_date`/`to_date`). |
| `market_cap()` | Yearly market-capitalisation key statistics. |
| `market_capitalisation()` | Current market cap by instrument type (Equity, REIT/INVIT, ETF, MF, Corporate Bonds, CP). Values in ₹ Crores. |
| `top_market_cap()` | Top 100 companies by market capitalisation. |
| `gross_delivery(trade_date)` | Gross delivery report for the given date (scrip-wise delivery qty, value, turnover, %). |
| `bulk_deal_as_on_today()` | Today's bulk deals. |
| `block_deal_as_on_today()` | Today's block deals. |

### Derivatives — `bseindia.derivatives`

| Function | Purpose |
| --- | --- |
| `market_summary()` | F&O market summary. Returns a tuple `(index_df, equity_df)`. |
| `derivative_bhav_copy(trade_date)` | Derivatives UDiFF bhavcopy for the given trade date. |

---

## Examples

**Holidays for a specific year**

```python
bseindia.trading_holiday_calendar(year=2026)
```

**Historical data by date range**

```python
from bseindia import equity

equity.historical_stock_data(
    symbol="SBIN",
    from_date="01-06-2023",
    to_date="10-06-2023",
)
```

**Historical data by period**

```python
equity.historical_stock_data(symbol="TCS", period="6M")
```

**Bhavcopy**

```python
equity.equity_bhav_copy(trade_date="01-07-2024")
```

**Derivatives market summary**

```python
from bseindia import derivatives

index_df, equity_df = derivatives.market_summary()
```

**Look up a scrip code**

`all_listed_securities()` returns the full master. Pass `refresh=True` to bypass the local cache and re-fetch from BSE.

```python
bseindia.all_listed_securities(refresh=True)
```

---

## Notes & gotchas

- BSE endpoints sometimes rate-limit or time out; functions raise `NSEdataNotFound` or `CalenderNotFound` in those cases. Retry after a short pause.
- `historical_stock_data` resolves a symbol to a BSE scrip code via the cached security master, with a live smart-search fallback if the symbol is missing. Numeric inputs (e.g. `"500325"`) are treated as scrip codes directly.
- The security master is cached at `bseindia/bse_security_list.csv` inside the installed package directory.
- All date inputs use the `dd-mm-YYYY` format unless otherwise noted.

---

## Contributing

Issues and pull requests are welcome on the [GitHub repo](https://github.com/RuchiTanmay/bseindia).

- **Bug reports / feature requests** — open an issue at <https://github.com/RuchiTanmay/bseindia/issues>.
- **Patches** — fork, branch, commit, open a PR against `main`.
- **Docs & examples** — blog posts, notebooks and Q&A help the community; please share links in issues so they can be referenced.

---

## Changelog

See [CHANGE_LOG.md](CHANGE_LOG.md) for release history.

## License

Distributed under the terms of the [LICENSE](LICENSE) bundled with this repository.
