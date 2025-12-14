"""
QuantConnect LEAN (Python) algorithm entry point (Phase 1 skeleton).

Adds indicators (RSI, EMA20/50/200, MACD, ATR, Bollinger) with warm-up,
builds a minimal features dict on 5-minute bars, uses a dummy RSI rule
(RSI<30 go long; RSI>70 flatten), with fixed 0.5% equity size and
ATR-based bracket orders. Includes a daily -1% P&L stop and a 15-minute
minimum hold time.
"""

from AlgorithmImports import *
from datetime import timedelta, datetime
from typing import Optional
from experts.rsi_expert import RSIExpert
from experts.macd_expert import MACDExpert
from experts.trend_expert import TrendExpert
from ensemble.brain import Brain
from risk.position_sizing import size_from_prob


class ProbRSISkeleton(QCAlgorithm):
    def Initialize(self) -> None:
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2020, 1, 15)
        self.SetCash(100000)

        self.symbol = self.AddEquity("TSLA", Resolution.Minute).Symbol

        # 5-minute consolidator
        self._consolidator = self.Consolidate(self.symbol, timedelta(minutes=5), self._on_five_minute_bar)

        # Indicators on consolidated 5-minute bars
        self.rsi = RelativeStrengthIndex(14, MovingAverageType.Wilders)
        self.ema20 = ExponentialMovingAverage(20)
        self.ema50 = ExponentialMovingAverage(50)
        self.ema200 = ExponentialMovingAverage(200)
        self.macd = MovingAverageConvergenceDivergence(12, 26, 9, MovingAverageType.Exponential)
        self.atr = AverageTrueRange(14, MovingAverageType.Wilders)
        self.bb = BollingerBands(20, 2, MovingAverageType.Simple)

        # Register indicators so they update from the 5-minute consolidator
        self.RegisterIndicator(self.symbol, self.rsi, self._consolidator)
        self.RegisterIndicator(self.symbol, self.ema20, self._consolidator)
        self.RegisterIndicator(self.symbol, self.ema50, self._consolidator)
        self.RegisterIndicator(self.symbol, self.ema200, self._consolidator)
        self.RegisterIndicator(self.symbol, self.macd, self._consolidator)
        self.RegisterIndicator(self.symbol, self.atr, self._consolidator)
        self.RegisterIndicator(self.symbol, self.bb, self._consolidator)

        # Warm-up history to get indicators ready (sufficient bars for the longest indicator)
        self.SetWarmUp(timedelta(days=30))

        # Risk and execution parameters
        self.edge_size = 0.005  # 0.5% equity position target
        self.min_hold = timedelta(minutes=15)
        self.daily_stop = -0.01  # -1%

        # State
        self._last_entry_time: Optional[datetime] = None
        self._stop_ticket: Optional[OrderTicket] = None
        self._tp_ticket: Optional[OrderTicket] = None
        self._start_of_day_equity = self.Portfolio.TotalPortfolioValue
        self._current_day = self.Time.date()

        # Load tiny expert models from Object Store (placeholders for now)
        # In QC Cloud, pass self.ObjectStore and keys like 'models/rsi_expert.json'
        self.rsi_expert = RSIExpert.load(self.ObjectStore, "models/rsi_expert.json")
        self.macd_expert = MACDExpert.load(self.ObjectStore, "models/macd_expert.json")
        self.trend_expert = TrendExpert.load(self.ObjectStore, "models/trend_expert.json")

        # Load ensemble brain (JSON model; falls back to average if missing)
        self.brain = Brain.load(self.ObjectStore, "models/brain.json")

        # Use the brain (ensemble) mapping by default now that loaders exist.
        self.use_brain = True

        self.Debug("Initialized Phase 1 skeleton with indicators and RSI rule")

    # Consolidated bar handler (5-minute)
    def _on_five_minute_bar(self, bar: TradeBar) -> None:
        # Reset start-of-day equity at the beginning of each day
        if self.Time.date() != self._current_day:
            self._current_day = self.Time.date()
            self._start_of_day_equity = self.Portfolio.TotalPortfolioValue

        # Safety: ensure indicators are ready and not warming up
        if self.IsWarmingUp:
            return
        if not (self.rsi.IsReady and self.macd.IsReady and self.atr.IsReady and self.bb.IsReady):
            return

        # Daily P&L stop
        pnl_today = (self.Portfolio.TotalPortfolioValue - self._start_of_day_equity) / max(1.0, self._start_of_day_equity)
        if pnl_today <= self.daily_stop:
            if self.Portfolio.Invested:
                self.Liquidate(self.symbol, tag="Daily stop hit")
                self._cancel_brackets()
            return

        # Build a minimal features dict (for logging / future use)
        macd_hist = self.macd.Current.Value - self.macd.Signal.Current.Value if self.macd.Signal.IsReady else 0.0
        price = bar.Close
        atr_value = float(self.atr.Current.Value)
        atr_pct = atr_value / price if price > 0 else 0.0
        bb_width = (self.bb.UpperBand.Current.Value - self.bb.LowerBand.Current.Value) if self.bb.IsReady else 0.0
        bb_mid = self.bb.MiddleBand.Current.Value if self.bb.IsReady else price
        bb_z = (price - bb_mid) / (0.5 * bb_width) if bb_width > 0 else 0.0

        features = {
            "rsi": float(self.rsi.Current.Value),
            "macd_hist": float(macd_hist),
            "atr": float(atr_value),
            "atr_pct": float(atr_pct),
            "bb_z": float(bb_z),
            "ema20": float(self.ema20.Current.Value) if self.ema20.IsReady else price,
            "ema50": float(self.ema50.Current.Value) if self.ema50.IsReady else price,
            "ema200": float(self.ema200.Current.Value) if self.ema200.IsReady else price,
        }

        # Expert probabilities (placeholders until models are trained)
        expert_probs = {
            "rsi": float(self.rsi_expert.predict_proba(features)),
            "macd": float(self.macd_expert.predict_proba(features)),
            "trend": float(self.trend_expert.predict_proba(features)),
        }
        self.Log(f"Experts p: {expert_probs}")

        invested = self.Portfolio[self.symbol].Invested

        if not self.use_brain:
            # --- Phase 1: Simple RSI rule ---
            rsi = features["rsi"]
            if invested and rsi > 70:
                if self._last_entry_time is None or (self.Time - self._last_entry_time) >= self.min_hold:
                    self.Liquidate(self.symbol, tag="RSI>70 exit")
                    self._cancel_brackets()
            elif not invested and rsi < 30:
                # Fixed ~0.5% equity position for the dummy rule
                target_value = self.Portfolio.TotalPortfolioValue * self.edge_size
                qty = int(target_value / max(price, 1e-6))
                if qty > 0:
                    self._enter_with_bracket(direction=1, qty=qty, price=price, atr=atr_value)
                    self._last_entry_time = self.Time

            if not self.Portfolio.Invested:
                self._cancel_brackets()
            return

        # --- Phase 3: Brain p->size mapping ---
        regime = {
            "volatility": float(atr_pct),
            "time_of_day": float(self.Time.hour + self.Time.minute / 60.0),
        }
        p = float(self.brain.predict_proba(expert_probs, regime))
        edge = abs(p - 0.5)

        if edge < 0.05:
            if invested and (self._last_entry_time is None or (self.Time - self._last_entry_time) >= self.min_hold):
                self.Liquidate(self.symbol, tag="No edge; flatten")
                self._cancel_brackets()
            if not invested:
                self._cancel_brackets()
            return

        # Determine direction and size (capped at 1% equity, inversely scaled by ATR)
        cap = 0.01
        size = size_from_prob(p, atr_pct=atr_pct, cap=cap)
        direction = 1 if size > 0 else -1
        target_value = self.Portfolio.TotalPortfolioValue * abs(size)
        qty = int(target_value / max(price, 1e-6))

        if qty <= 0:
            return

        if not invested:
            self._enter_with_bracket(direction, qty, price, atr_value)
            self._last_entry_time = self.Time

    # Helpers
    def _enter_with_bracket(self, direction: int, qty: int, price: float, atr: float) -> None:
        # Market entry
        signed_qty = int(direction * qty)
        tag = "Long entry" if direction > 0 else "Short entry"
        self.MarketOrder(self.symbol, signed_qty, tag=tag)

        # ATR-based brackets (naive, not OCO-linked in this skeleton)
        if direction > 0:
            stop_price = max(0.01, price - atr)
            tp_price = price + 2 * atr
            stop_qty = -qty
            tp_qty = -qty
        else:
            stop_price = price + atr
            tp_price = max(0.01, price - 2 * atr)
            stop_qty = qty
            tp_qty = qty

        self._stop_ticket = self.StopMarketOrder(self.symbol, stop_qty, stop_price, tag="Protective Stop")
        self._tp_ticket = self.LimitOrder(self.symbol, tp_qty, tp_price, tag="Take Profit")

    def _cancel_brackets(self) -> None:
        for ticket in (self._stop_ticket, self._tp_ticket):
            if ticket is not None and ticket.Status in [OrderStatus.New, OrderStatus.Submitted, OrderStatus.PartiallyFilled]:
                self.CancelOrder(ticket.OrderId)
        self._stop_ticket = None
        self._tp_ticket = None
