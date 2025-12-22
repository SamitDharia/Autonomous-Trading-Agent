# Architecture

## System Overview

**Current Champion**: RSI Baseline with Phase 1+2+3 Enhancements (brain **DISABLED**)  
**Status**: Deployed to DigitalOcean cloud (2025-12-18, PID 46592)  
**Backtest Performance**: Phase 1+2 Sharpe 0.80, Win Rate 72.7% (2020-2024)  
**Paper Trading**: Phase 3.1+3.2 monitoring in progress (deployed 18:24 UTC)

```
Market Data (5m bars)
        ↓
   Indicators (RSI, EMA200, BB, ATR, vol_z, volm_z)
        ↓
   Feature Builder
        ↓
   ┌──────────────────────────────────────────────┐
   │  Phase 1 Filters (Quality Gates)            │
   │  ├─ Time-of-day (10:00-15:30 ET)           │
   │  ├─ Volatility regime (vol_z > 0.2)         │
   │  └─ Volume confirmation (volm_z > 0.3)      │
   └──────────────────────────────────────────────┘
        ↓
   ┌──────────────────────────────────────────────┐
   │  Phase 2 Dynamic Logic                       │
   │  ├─ Dynamic RSI thresholds (20/25/30)       │
   │  ├─ Trend filter (ema200_rel > -5%)         │
   │  └─ BB confirmation (bb_z < -0.8)           │
   └──────────────────────────────────────────────┘
        ↓
   ┌──────────────────────────────────────────────┐
   │  Phase 3.2 Multi-TF Confirmation (NEW)       │
   │  └─ 15-min RSI < 50 (skip if >= 50)         │
   └──────────────────────────────────────────────┘
        ↓
   RSI Signal (enter <threshold, exit >75)
        ↓
   Position Sizing (0.25% equity cap)
        ↓
   Risk Guards (30m hold, -1% daily stop)
        ↓
   Order Execution (bracket: 1x ATR stop, 2x ATR TP)
        ↓
   ┌──────────────────────────────────────────────┐
   │  Phase 3.1 Trailing Stops (NEW)              │
   │  └─ Update stop to (price - 1.5*ATR)        │
   │     when profitable, never widen             │
   └──────────────────────────────────────────────┘
```

### Legacy Architecture (Archived)

The original **stacked ensemble** (3 experts → Brain meta-model) achieved AUC 0.50-0.52 and was **not promoted**. Code preserved in `ensemble/` and `experts/` directories for reference. See [archive/TRAINING.md](archive/TRAINING.md) and [DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md) for details.

---

## Module Structure

### Production System (`scripts/alpaca_rsi_bot.py`)
**Platform**: Alpaca Markets API  
**Status**: Deployed Dec 18, 2025 on DigitalOcean droplet (PID 46592)

**Architecture**: Inline RSI strategy (no ML models):
- **Data**: Alpaca WebSocket (1-min bars) + pandas_ta for indicators
- **Strategy**: RSI mean-reversion with 8 filters (Phase 1+2+3 enhancements)
- **Filters**:
  - Time-of-day: 10:00-15:30 ET
  - Volatility: vol_z > 0.2 (20% above baseline)
  - Volume: volm_z > 0.3 (30% above baseline)
  - Trend: ema200_rel > -5% (not in downtrend)
  - Bollinger: bb_z < -0.8 (extreme oversold)
  - RSI thresholds: Dynamic 20/25/30 based on regime
  - Multi-timeframe: 5-min RSI < 25 AND 15-min RSI < 50
  - Trailing stop: 1.5 ATR, only trails when profitable
- **Position Sizing**: Fixed 0.25% equity cap per trade
- **Risk Controls**: 1% daily kill-switch, bracket orders mandatory
- **Logging**: CSV format (alpaca_rsi_log.csv), rsync to local for analysis
- **ML Shadow**: ml/shadow.py infrastructure ready (disabled by default)

**Key Difference from algo.py**: No brain/ensemble models, pure rule-based RSI strategy.

---

### Core Algorithm (`algo.py`) — BACKTESTING ONLY
**Platform**: QuantConnect LEAN Engine  
**Purpose**: Research and backtesting (NOT production)

Main entry point for QuantConnect LEAN. Orchestrates the entire trading pipeline:

- **Initialization**: Load expert models + brain from Object Store (QC) or local JSON files (archived)
- **Data Handling**: Consolidate 1-minute bars → 5-minute bars
- **Indicator Management**: RSI, MACD, EMA(20/50/200), ATR, Bollinger Bands
- **Signal Generation (Legacy)**: Calls feature builder → experts → brain → position sizing (archived approach)
- **Risk Enforcement**: Daily P&L stop, indicator readiness checks, min hold time
- **Order Execution**: Bracket orders (stop-loss + take-profit) with ATR-based levels

**Dependencies** (for backtesting only):
- `features.feature_builder.build_features()`
- `risk.guards.{daily_pnl_stop_hit, indicators_ready}`
- `experts.{rsi,macd,trend}_expert.{load, predict_proba}` (archived)
- `ensemble.brain.{load, predict_proba}` (archived)
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

### Production System (`scripts/alpaca_rsi_bot.py`)
**Platform**: Alpaca Markets API  
**Status**: Deployed Dec 18, 2025 on DigitalOcean droplet (PID 46592)

**Architecture**: Inline RSI strategy (no ML models):
- **Data**: Alpaca WebSocket (1-min bars) + pandas_ta for indicators
- **Strategy**: RSI mean-reversion with 8 filters (Phase 1+2+3 enhancements)
- **Filters**:
  - Time-of-day: 10:00-15:30 ET
  - Volatility: vol_z > 0.2 (20% above baseline)
  - Volume: volm_z > 0.3 (30% above baseline)
  - Trend: ema200_rel > -5% (not in downtrend)
  - Bollinger: bb_z < -0.8 (extreme oversold)
  - RSI thresholds: Dynamic 20/25/30 based on regime
  - Multi-timeframe: 5-min RSI < 25 AND 15-min RSI < 50
  - Trailing stop: 1.5 ATR, only trails when profitable
- **Position Sizing**: Fixed 0.25% equity cap per trade
- **Risk Controls**: 1% daily kill-switch, bracket orders mandatory
- **Logging**: CSV format (alpaca_rsi_log.csv), rsync to local for analysis
- **ML Shadow**: ml/shadow.py infrastructure ready (disabled by default)

**Key Difference from algo.py**: No brain/ensemble models, pure rule-based RSI strategy.

---

### Expert Models (`experts/`) — ARCHIVED

⚠️ **Status**: Not used in production (AUC 0.50-0.52, no edge over RSI baseline). Preserved for reference and future research.

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

### Ensemble Brain (`ensemble/brain.py`) — ARCHIVED

⚠️ **Status**: Not used in production (AUC 0.50-0.52, no edge over RSI baseline). Preserved for reference and future research.

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
3. Backtest in QC Web IDE (validate performance)
4. Deploy to cloud (DigitalOcean droplet, Ubuntu 22.04)
5. Run paper trading 24/7 (`scripts/alpaca_rsi_bot.py`)
6. Promote to live only after 60 days of stable results (Sharpe ≥1.0)

---

## Deployment Architecture

### Local Development
- Python 3.10+ with venv
- Backtests run on QuantConnect LEAN (local or cloud)
- Paper trading via Alpaca API (local script)

### Cloud Production
- **Platform**: DigitalOcean Frankfurt droplet ($6/month)
- **OS**: Ubuntu 22.04 LTS (1GB RAM, 25GB SSD)
- **Process**: nohup background process, survives SSH disconnect
- **Monitoring**: CSV logs (`alpaca_rsi_log.csv`), PID tracking
- **Auto-restart**: Cron job (`@reboot`) for droplet reboots
- **Security**: SSH key auth, firewall (only port 22), API keys in .env

See [CLOUD_DEPLOYMENT.md](CLOUD_DEPLOYMENT.md) for full setup guide.

---

## Enhancement Roadmap

### Phase 1: Quality Filters ✅ (Complete)
- Time-of-day filter (10:00-15:30 ET, avoid open/close volatility)
- Volume confirmation (volm_z > 1.0, only trade on volume spikes)
- Volatility regime (vol_z > 0.5, avoid low-vol chop)
- **Result**: Sharpe -0.09 → 0.41 (turned losing → profitable)

### Phase 2: Dynamic Logic ✅ (Complete)
- Dynamic RSI thresholds (20/25/30 based on trend + volatility)
- Trend filter (ema200_rel > -5%, no entries in downtrends)
- Bollinger Band confirmation (bb_z < -0.8, only extreme oversold)
- **Result**: Sharpe 0.41 → 0.80 (+97% improvement)

### Phase 3: Advanced Techniques ✅ (Deployed Dec 18, 2025)
**Phase 3.1 - Trailing ATR Stop**:
- ATR-based trailing stop via Alpaca order.replace() API
- Only trail when profitable, never move stop down
- Trail distance: 1.5 ATR
- **Status**: Deployed to production (scripts/alpaca_rsi_bot.py)
- **Validation**: Awaiting Jan 2026 volatility for first trades
- **Design**: [PHASE3_TRAILING_STOP_DESIGN.md](PHASE3_TRAILING_STOP_DESIGN.md)

**Phase 3.2 - Multi-Timeframe RSI**:
- 15-min RSI confirmation (5m <25, 15m <50)
- Filters whipsaws when broader trend still bullish
- Pandas resample for bar consolidation
- **Status**: Deployed to production (scripts/alpaca_rsi_bot.py)
- **Validation**: Awaiting Jan 2026 volatility for first trades
- **Design**: [PHASE3_MULTI_TF_RSI_DESIGN.md](PHASE3_MULTI_TF_RSI_DESIGN.md)

**Combined Goal**: Sharpe 0.80 → **1.0+** (required for live deployment)  
**Validation Timeline**: Jan 6-31, 2026 (high-activity period for trades)

### Phase 4: ML Shadow Mode ✅ (Implemented, Disabled by Default)
- **Purpose**: Passive data collection for future ML expectancy filter (Growth Phase 5)
- **Infrastructure**: ml/shadow.py with zero-risk design (ML observes, never influences)
- **Data Format**: JSONL (market state + bot decision + outcome)
- **Status**: Code deployed, disabled by default (ML_SHADOW_ENABLED=false)
- **Timeline**: 
  - Enable after Phase 3 validation (Jan 2026+)
  - Collect 500+ labeled trades over 6 months (Jan-Jun 2026)
  - Analyze if ML can predict which setups to skip (expectancy filter)
- **Key Principle**: Rule-based strategy primary, ML optional future filter
- **Fallback**: Try/except wrapper prevents execution errors
- **Docs**: [ml/README.md](../ml/README.md), [PROJECT_BRIEF.md](PROJECT_BRIEF.md) (Phase 4 section)

---

## Current Status (Dec 22, 2025)

### ✅ Deployed to Production
- **Bot Status**: Running 24/7 on DigitalOcean droplet (PID 46592, Frankfurt, $6/month)
- **Strategy**: RSI mean-reversion with 8 filters (Phase 1+2+3 deployed Dec 18)
- **Performance (Backtest 2020-2024)**: Sharpe 0.80, Win Rate 72.7%, 44 trades
- **Features**:
  - Phase 1: Time/vol/volume filters
  - Phase 2: Dynamic RSI thresholds, trend, Bollinger Band
  - Phase 3.1: 1.5 ATR trailing stops (only trails when profitable)
  - Phase 3.2: Multi-timeframe RSI (5-min + 15-min confirmation)
- **Risk Controls**: 1% daily kill-switch, 0.25% position cap, bracket orders mandatory
- **Logging**: CSV format (alpaca_rsi_log.csv), synced to local for analysis
- **Monitoring**: daily_health_check.ps1, analyze_recent_trades.py

### 🔄 Validation Mode (Dec 22 - Jan 31)
- **Current Behavior**: Bot running, skip_volatility/skip_volume logs (no trades)
- **Reason**: Holiday period low volatility (Dec 18-Jan 3)
- **Expected**: First trades early Jan (TSLA delivery numbers catalyst)
- **Validation Window**: Jan 6-31, 2026 (high-activity period, expect 3-7 trades)
- **Success Criteria**: Phase 3 Sharpe ≥ 0.7, trailing stops work correctly, multi-TF RSI reduces whipsaws

### 📦 Archived (Not in Production)
- Brain ensemble (AUC 0.50-0.52, no edge over RSI baseline)
- Expert models (RSI/MACD/Trend, preserved for reference)
- algo.py brain integration (QuantConnect backtests only)

### ⏳ Planned (2026+)
- **Growth Phase 1** (Feb-Mar 2026): Multi-symbol expansion (5 stocks: TSLA, AAPL, NVDA, SPY, QQQ)
- **Phase 4 ML Shadow** (Jan-Jun 2026): Enable ml/shadow.py, collect 500+ trades
- **Growth Phase 5** (2027+): ML expectancy filter (predict which setups to skip)
- **Live Deployment**: After 60-day paper validation (Sharpe ≥1.0, max drawdown <2%)

---

---

## See Also
- **[PROJECT_BRIEF.md](PROJECT_BRIEF.md)** — System goals and risk controls
- **[GETTING_STARTED.md](GETTING_STARTED.md)** — Setup and run instructions
- **[DEPLOYMENT.md](../DEPLOYMENT.md)** — Local deployment guide
- **[CLOUD_DEPLOYMENT.md](CLOUD_DEPLOYMENT.md)** — Cloud deployment guide (DigitalOcean, AWS, GCP)
- **[RSI_ENHANCEMENTS.md](RSI_ENHANCEMENTS.md)** — Phase 1-4 roadmap and backtest results
- **[PHASE3_TRAILING_STOP_DESIGN.md](PHASE3_TRAILING_STOP_DESIGN.md)** — Trailing stop design
- **[PHASE3_MULTI_TF_RSI_DESIGN.md](PHASE3_MULTI_TF_RSI_DESIGN.md)** — Multi-timeframe RSI design
- **[DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md)** — Recent decisions and results
- **[PLAN.md](PLAN.md)** — 8-week roadmap with status
- **[INDEX.md](INDEX.md)** — Documentation navigation

---

**Last updated**: 2025-12-22
