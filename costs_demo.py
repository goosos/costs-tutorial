"""
costs_demo.py — Part 6 demo: what do costs do to our MA strategy?

Runs the Part 1 MA(20,50) backtest on SPY at three cost tiers:
  zero   — fantasy (no costs, for comparison)
  honest — 10 bps commission + 5 bps slippage per side
  harsh  — 20 bps commission + 10 bps slippage per side

Usage:  python costs_demo.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
import yfinance as yf

from backtest import run_backtest, ma_crossover_signals
from costs import COST_TIERS


def main():
    print("Downloading SPY (2023-10-09 → 2026-10-07)...")
    df = yf.download("SPY", start="2023-10-09", end="2026-10-07",
                     auto_adjust=True, progress=False)
    price = df["Close"]["SPY"] if ("Close", "SPY") in df.columns else df["Close"]
    price = price.dropna()
    print(f"  {len(price)} bars")

    entries, exits = ma_crossover_signals(price, fast=20, slow=50)
    entries = entries.vbt.signals.fshift(1)
    exits = exits.vbt.signals.fshift(1)

    print()
    print(f"{'Tier':<10} {'Total ret':>10} {'Sharpe':>8} {'MaxDD':>8} "
          f"{'Trades':>7} {'Cost/trade':>11}")
    print("-" * 62)
    for name, tier in COST_TIERS.items():
        kw = tier.to_backtest_kwargs()
        pf = run_backtest(price, entries, exits, freq="1D", **kw)
        n = int(pf.trades.count())
        rt_cost = tier.round_trip_pct() * 100  # in %
        print(f"{name:<10} {pf.total_return() * 100:>9.2f}% "
              f"{pf.sharpe_ratio():>8.2f} {pf.max_drawdown() * 100:>7.2f}% "
              f"{n:>7} {rt_cost:>10.2f}%")

    # Frequency asymmetry: how many round trips before costs eat a 2% edge
    print()
    print("Round trips per year a 2%-edge strategy survives:")
    for name, tier in COST_TIERS.items():
        n = tier.breakeven_trades_per_year(0.02)
        print(f"  {name:<10} {n:>6.1f} round trips/yr")


if __name__ == "__main__":
    main()
