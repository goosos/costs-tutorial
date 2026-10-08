# Slippage & Commissions Tutorial

**Part 6 of [Build Your Own Quant Research System](https://goosos.com/tutorials/)** — honest cost modeling for backtests.

## What this covers

- Why costs kill strategies (frequency asymmetry)
- Commission models: proportional vs fixed
- Slippage models: fixed bps vs volatility-proportional
- Reality check: MA(20,50) at three cost tiers

## Quick start

```bash
pip install -r requirements.txt
python costs_demo.py
```

## Files

| File | Description |
|---|---|
| `costs.py` | The module: `commission_pct()`, `commission_fixed()`, `slippage_fixed()`, `slippage_vol()`, `TradeCost`, `COST_TIERS` |
| `costs_demo.py` | Runs MA(20,50) at zero/honest/harsh tiers, prints Sharpe decay |
| `backtest.py` | Vendored from Part 1 (so the demo runs standalone) |
| `article.md` | Full tutorial text |

## Results (SPY, 2023-10-09 → 2026-10-07, 751 bars)

| Tier | Total return | Sharpe | Cost/round trip |
|---|---|---|---|
| zero | 29.83% | 1.11 | 0 bps |
| honest | 28.09% | 1.06 | 30 bps |
| harsh | 26.37% | 1.00 | 60 bps |

## License

MIT — learn, fork, build.
