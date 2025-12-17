# Architecture

## System Overview

The Autonomous Trading Agent uses a **stacked ensemble** architecture with strict risk controls:

```
Market Data (5m bars)
        ↓
   Indicators (RSI, MACD, EMA, ATR, BB)
        ↓
   Feature Builder
        ↓
   ┌─────────────────────────────────┐
   │  Level 1: Expert Models         │
   │  ├─ RSI Expert    → p₁ ∈ [0,1] │
   │  ├─ MACD Expert   → p₂ ∈ [0,1] │
   │  └─ Trend Expert  → p₃ ∈ [0,1] │
   └─────────────────────────────────┘
        ↓
   ┌─────────────────────────────────┐
   │  Level 2: Brain (Meta-Model)    │
   │  Inputs: [p₁, p₂, p₃, regime]  │
   │  Output: p_final ∈ [0,1]       │
   └─────────────────────────────────┘
        ↓
   Edge Gate (|p - 0.5| ≥ threshold)
        ↓
   Position Sizing (ATR-scaled, capped)
        ↓
   Risk Guards (daily stop, kill-switches)
        ↓
   Order Execution (bracket orders)
```

---

## Module Structure

### Core Algorithm (`algo.py`)
Main entry point for QuantConnect LEAN. Orchestrates the entire trading pipeline:

- **Initialization**: Load expert models + brain from Object Store (QC) or local JSON files
- **Data Handling**: Consolidate 1-minute bars → 5-minute bars
- **Indicator Management**: RSI, MACD, EMA(20/50/200), ATR, Bollinger Bands
- **Signal Generation**: Calls feature builder → experts → brain → position sizing
- **Risk Enforcement**: Daily P&L stop, indicator readiness checks, min hold time
- **Order Execution**: Bracket orders (stop-loss + take-profit) with ATR-based levels

**Dependencies**:
- `features.feature_builder.build_features()`
- `risk.guards.{daily_pnl_stop_hit, indicators_ready}`
- `experts.{rsi,macd,trend}_expert.{load, predict_proba}`
- `ensemble.brain.{load, predict_proba}`
- `risk.position_sizing.size_from_prob()`

---

### Feature Engineering (`features/feature_builder.py`)

**Purpose**: Transform raw indicators into ML-ready feature dictionary.

**Inputs**:
- QCAlgorithm context with indicator values (RSI, MACD, EMA, ATR, BB, etc.)

**Outputs**:
- Dict with ~15 features:
  - `rsi`: RSI(14) value [0-100]
  - `rsi_slope`: RSI momentum
  - `ema_fast_slow_diff`: EMA(20) - EMA(50) normalized
  - `ema_fast_long_diff`: EMA(20) - EMA(200) normalized
  - `macd`, `macd_signal`, `macd_hist`: MACD components
  - `atr_pct`: ATR / price (volatility measure)
  - `bb_upper`, `bb_lower`: Bollinger Band percentiles
  - `time_of_day`: Normalized market hour [9.5-16]
  - Returns `{}` if indicators not ready (error handling)

**Key Function**:
```python
def build_features(context) -> Dict[str, float]:
    """Build feature dict from QCAlgorithm indicators."""
```

---

### Expert Models (`experts/`)

Three independent logistic regression models, each specialized on different technical patterns:

#### **RSI Expert** (`rsi_expert.py`)
- **Features**: RSI, RSI slope, Bollinger z-score
- **Output**: Probability that RSI oversold/overbought conditions predict positive 60m return
- **Model**: Logistic regression with L2 regularization (C=0.1)

#### **MACD Expert** (`macd_expert.py`)
- **Features**: MACD, signal, histogram, histogram slope
- **Output**: Probability that MACD momentum predicts positive 60m return
- **Model**: Logistic regression with L2 regularization (C=1.0)

#### **Trend Expert** (`trend_expert.py`)
- **Features**: EMA(20/50/200) differences, crossovers, slopes
- **Output**: Probability that trend alignment predicts positive 60m return
- **Model**: Logistic regression with L2 regularization (C=10.0)

**Common Interface**:
```python
class Expert:
    @staticmethod
    def load(object_store, key: str) -> Expert:
        """Load from QC Object Store or local JSON."""
    
    def predict_proba(self, features: Dict[str, float]) -> float:
        """Return probability p ∈ [0,1]."""
```

**Fallback**: If model file missing or load fails, returns 0.5 (neutral) to avoid crashes.

---

### Ensemble Brain (`ensemble/brain.py`)

**Purpose**: Meta-model that combines expert predictions with regime context.

**Inputs**:
- `expert_probs`: Dict with keys `{"rsi": p₁, "macd": p₂, "trend": p₃}`
- `regime`: Dict with keys `{"volatility": atr_pct, "time_of_day": hour}`

**Output**:
- Final probability `p ∈ [0,1]` where:
  - `p < 0.5` = bearish signal
  - `p = 0.5` = neutral (no edge)
  - `p > 0.5` = bullish signal

**Model**: Logistic regression (5 features total: 3 expert probs + 2 regime features)

**Key Functions**:
```python
def load(object_store, key: str) -> Brain:
    """Load from QC Object Store or local JSON."""

def predict_proba(self, expert_probs: Dict, regime: Dict) -> float:
    """Blend expert outputs with regime context."""
```

**Fallback**: If model missing, uses simple average of expert probabilities.

---

### Risk Management (`risk/`)

#### **Position Sizing** (`position_sizing.py`)
Converts probability into position size with ATR-based volatility scaling:

```python
def size_from_prob(p: float, atr_pct: float, cap: float = 0.0020) -> float:
    """
    Returns position size as fraction of equity.
    
    Args:
        p: Brain probability [0,1]
        atr_pct: ATR / price (volatility measure)
        cap: Maximum position size (default 0.20% of equity)
    
    Returns:
        Signed size: positive for long, negative for short
    """
    edge = abs(p - 0.5)
    base_size = edge * 2.0  # Scale edge to [0, 1]
    volatility_adjusted = base_size / max(atr_pct, 0.01)  # Inverse ATR scaling
    capped = min(volatility_adjusted, cap)
    return capped if p > 0.5 else -capped
```

#### **Guards** (`guards.py`)
Safety checks to enforce risk limits:

**1. Daily P&L Stop**:
```python
def daily_pnl_stop_hit(algo, threshold: float = -0.01) -> bool:
    """
    Returns True if daily P&L ≤ threshold (e.g., -1%).
    Tracks start-of-day equity automatically.
    """
```

**2. Indicator Readiness**:
```python
def indicators_ready(*indicators) -> bool:
    """
    Returns True if all indicators have ≥1 sample.
    Prevents errors from uninitialized TradingIndicator objects.
    """
```

**Kill-Switch Triggers** (algo.py logic):
- Daily P&L ≤ -1% → flatten all positions, stop trading
- Data quality errors → flatten and pause
- Broker connection errors → flatten and pause
- Indicators not ready → skip bar (no trades)

---

## Data Flow

### Bar Processing Pipeline
```
1. Market Data (1-minute bars from Alpaca/QC)
        ↓
2. Consolidate → 5-minute bars
        ↓
3. Update Indicators (RSI, MACD, EMA, ATR, BB)
        ↓
4. Check Warm-Up Complete? (30 days)
   NO → Skip bar
   YES ↓
5. Check Indicators Ready?
   NO → Skip bar
   YES ↓
6. Check Daily P&L Stop Hit?
   YES → Flatten + Stop
   NO ↓
7. Build Features (feature_builder.build_features)
        ↓
8. Expert Predictions (rsi/macd/trend → p₁, p₂, p₃)
        ↓
9. Brain Prediction (experts + regime → p_final)
        ↓
10. Edge Gate Check (|p - 0.5| ≥ threshold)?
    NO → Flatten if holding
    YES ↓
11. Position Sizing (p_final + ATR → size)
        ↓
12. Order Execution (market order + brackets)
        ↓
13. Bracket Management (cancel if position closed)
```

---

## Model Storage

### Local Development
```
/models/
├── rsi_expert.json      # RSI expert weights
├── macd_expert.json     # MACD expert weights
├── trend_expert.json    # Trend expert weights
└── brain.json           # Brain ensemble weights
```

### QuantConnect Cloud
Models uploaded to **Object Store**:
- Key: `models/rsi_expert.json`
- Key: `models/macd_expert.json`
- Key: `models/trend_expert.json`
- Key: `models/brain.json`

**Versioning**: Timestamped copies stored in `/brains/TSLA_1h/` for rollback.

---

## Testing Strategy

### Unit Tests (`tests/`)
- **`test_experts_brain.py`**: Expert loading, prediction, fallback behavior
- **`test_local_backtest.py`**: Feature builder, guards, position sizing
- **`test_create_issues_script.py`**: GitHub issue creation utilities

### Integration Tests
- **Local Backtest** (`scripts/local_backtest.py`): End-to-end RSI baseline
- **Paper Trading** (`scripts/paper_trade.py`): Live Alpaca integration

### Model Validation
- **Walk-forward backtests**: Train on N months, validate on next month
- **Baseline comparisons**: Brain must beat RSI-only + do-nothing baselines
- **AUC threshold**: Require ≥0.55 AUC on hold-out set before promoting brain

---

## Dual Runtime Strategy

### QuantConnect (Research/Backtests)
- **Use Case**: Model training, backtesting, research
- **Advantages**: Historical data, Web IDE, integrated backtester
- **Limitations**: Live trading fees, limited API access

### Local (Live/Paper Trading)
- **Use Case**: Paper trading (Alpaca), live trading
- **Advantages**: No QC fees, full control, CSV logging
- **Limitations**: Must manage data feeds, execution logic

**Workflow**:
1. Train models in QC Research notebook
2. Export JSONs to local `/models/`
3. Backtest in QC Web IDE (validate brain performance)
4. Run paper trading locally (`scripts/paper_trade.py`)
5. Promote to live only after 1-2 weeks of stable paper results

---

## Current Status (Dec 2025)

### ✅ Implemented
- Feature builder with 15+ indicators
- 3 expert models (RSI, MACD, Trend) with JSON loaders
- Brain ensemble with regime inputs
- Daily P&L stop + indicator readiness guards
- ATR-based position sizing with caps
- Bracket orders (stop-loss + take-profit)
- Local backtest harness
- Alpaca paper trading script

### 🔄 In Progress
- Brain retraining on 2018-2024 TSLA data (AUC currently ~0.50-0.52)
- Walk-forward validation pipeline
- Paper trading certification (1-2 week run)

### ⏳ Planned
- Multi-symbol support (AAPL, MSFT, SPY)
- Volatility regime detection
- RL-based position sizing
- Automated model promotion workflow
- Trade journal & performance analytics

---

---

## See Also
- **[PROJECT_BRIEF.md](PROJECT_BRIEF.md)** — System goals and risk controls
- **[GETTING_STARTED.md](GETTING_STARTED.md)** — Setup and run instructions
- **[DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md)** — Recent decisions and results
- **[PLAN.md](PLAN.md)** — 8-week roadmap with status
- **[INDEX.md](INDEX.md)** — Documentation navigation

---

**Last updated**: 2025-12-17
