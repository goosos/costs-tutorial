"""
costs.py — Part 6 of "Build Your Own Quant Research System".

Honest cost modeling: commissions and slippage. Most "profitable"
backtests die the moment you add realistic costs — this module makes
sure yours don't lie to you.

Design: cost functions return per-side proportional rates that plug
directly into quant_toolkit.backtest.run_backtest(fees=..., slippage=...).
A separate TradeCost dataclass bundles both sides for bookkeeping.

Tutorial: https://goosos.com/slippage-commissions-hidden-tax
Code: https://github.com/goosos/costs-tutorial
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Commissions
# ---------------------------------------------------------------------------

def commission_pct(notional, rate=0.001, min_per_trade=0.0, max_per_trade=float("inf")):
    """
    Proportional commission on a trade's notional value.

    Parameters
    ----------
    notional : float or pd.Series
        Trade notional value ($). Price × shares.
    rate : float
        Commission rate per side. Default 0.1% (10 bps).
        IBKR Pro (2026): ~0.05% with $1 minimum — use rate=0.0005,
        min_per_trade=1.0 to model it.
    min_per_trade : float
        Floor per trade (brokers love minimums). Default 0 (no floor).
    max_per_trade : float
        Cap per trade. Default inf (no cap).

    Returns
    -------
    float or pd.Series — commission in $ for one side.
    """
    comm = np.asarray(notional, dtype=float) * rate
    comm = np.clip(comm, min_per_trade, max_per_trade)
    if isinstance(notional, pd.Series):
        return pd.Series(comm, index=notional.index)
    return float(comm)


def commission_fixed(n_trades=1, per_trade=1.0):
    """
    Flat commission per trade (e.g. $1/trade regardless of size).

    Parameters
    ----------
    n_trades : int
        Number of trades (one side counts as one trade).
    per_trade : float
        Flat fee per trade in $. Default $1.00.

    Returns
    -------
    float — total commission in $.
    """
    return float(n_trades) * per_trade


# ---------------------------------------------------------------------------
# Slippage
# ---------------------------------------------------------------------------

def slippage_fixed(price, bps=5.0):
    """
    Fixed slippage as basis points against the trader.

    You always get a slightly worse fill than the signal price:
    buy higher, sell lower.

    Parameters
    ----------
    price : float or pd.Series
        Signal/reference price.
    bps : float
        Basis points of adverse slippage per side. Default 5 bps (0.05%).

    Returns
    -------
    float or pd.Series — slippage cost in $ per share.
    """
    return price * (bps / 10_000.0)


def slippage_vol(price, returns, k=0.5, window=20):
    """
    Volatility-proportional slippage.

    Slippage scales with recent volatility: calm markets → tight fills,
    wild markets → you pay for immediacy. A common practitioner model.

    cost_per_share = k × rolling_std(returns, window) × price

    Parameters
    ----------
    price : pd.Series
        Asset prices.
    returns : pd.Series
        Per-bar simple returns (aligned with price).
    k : float
        Slippage as a fraction of one rolling std dev. Default 0.5 —
        i.e. you lose half a standard deviation of movement per fill.
    window : int
        Rolling window for volatility estimate. Default 20 bars.

    Returns
    -------
    pd.Series — slippage cost in $ per share, per bar.
    """
    vol = returns.rolling(window).std()
    return k * vol * price


# ---------------------------------------------------------------------------
# Bundled cost model
# ---------------------------------------------------------------------------

@dataclass
class TradeCost:
    """
    One object describing the full per-side cost of trading.

    commission_rate : proportional commission per side (e.g. 0.001 = 10 bps)
    slippage_bps   : adverse slippage in basis points per side
    min_commission : broker minimum per trade in $

    Use .to_backtest_kwargs() to plug straight into run_backtest().
    """
    commission_rate: float = 0.001
    slippage_bps: float = 5.0
    min_commission: float = 0.0

    def per_side_pct(self):
        """Total per-side cost as a fraction (commission + slippage)."""
        return self.commission_rate + self.slippage_bps / 10_000.0

    def round_trip_pct(self):
        """Total round-trip cost as a fraction (both sides)."""
        return 2 * self.per_side_pct()

    def to_backtest_kwargs(self):
        """kwargs for quant_toolkit.backtest.run_backtest()."""
        return {
            "fees": self.commission_rate,
            "slippage": self.slippage_bps / 10_000.0,
        }

    def breakeven_trades_per_year(self, expected_edge_per_trade):
        """
        How many round trips per year this cost structure allows
        before costs eat the entire edge.

        expected_edge_per_trade : expected gross profit per round trip,
            as a fraction (e.g. 0.02 = 2%).
        """
        if expected_edge_per_trade <= 0:
            return 0.0
        rt = self.round_trip_pct()
        if rt <= 0:
            return float("inf")  # no costs → edge never eaten
        return expected_edge_per_trade / rt


# Common presets (per side)
COST_TIERS = {
    # name: TradeCost(commission_rate, slippage_bps)
    "zero": TradeCost(0.0, 0.0),        # fantasy — for comparison only
    "honest": TradeCost(0.001, 5.0),    # 10 bps comm + 5 bps slip = 15 bps/side
    "harsh": TradeCost(0.002, 10.0),    # 20 bps comm + 10 bps slip = 30 bps/side
}
