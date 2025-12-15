from AlgorithmImports import *
import json, math

class TeslaBrainAlgo(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2023,1,1)
        self.SetCash(100000)
        self.SetBrokerageModel(BrokerageName.Alpaca, AccountType.Margin)
        self.symbol = self.AddEquity("TSLA", Resolution.Minute).Symbol
        self.consolidator = TradeBarConsolidator(timedelta(hours=1))
        self.SubscriptionManager.AddConsolidator(self.symbol, self.consolidator)
        self.consolidator.DataConsolidated += self.OnBar
        self.rsi = self.RSI(self.symbol, 14, MovingAverageType.Wilders, Resolution.Minute)
        self.atr = self.ATR(self.symbol, 14, MovingAverageType.Wilders, Resolution.Minute)
        self.cooldown = timedelta(minutes=60)
        self.next_trade_time = self.Time
        self.brain_path = "brains/TSLA_1h/brain_latest.json"
        self.brain = None
        self.LoadBrain()

    def LoadBrain(self):
        with open(self.brain_path,'r') as f:
            self.brain = json.load(f)
        self.Log(f"Loaded brain {self.brain.get('brain_version')} trained {self.brain.get('trained_utc')}")

    def OnBar(self, sender, bar: TradeBar):
        if not (self.rsi.IsReady and self.atr.IsReady):
            return
        if self.Time < self.next_trade_time:
            return
        if self.Portfolio[self.symbol].Invested:
            return
        price = float(bar.Close)
        features = {
            'rsi': float(self.rsi.Current.Value),
            'ema20_rel': 0.0,
            'atr': float(self.atr.Current.Value),
        }
        z = self.brain.get('model',{}).get('bias',0.0)
        for k,w in self.brain.get('model',{}).get('weights',{}).items():
            z += float(w) * float(features.get(k,0.0))
        conf = 1.0/(1.0+math.exp(-z))
        if conf < 0.6:
            return
        direction = 1 if z >= 0 else -1
        stop_atr = 1.5
        qty = int((self.Portfolio.TotalPortfolioValue * self.brain.get('risk_profile',{}).get('max_risk_per_trade',0.002)) / max(1e-6, stop_atr * features['atr']))
        if qty <= 0:
            return
        qty = qty if direction > 0 else -qty
        self.MarketOrder(self.symbol, qty)
        self.next_trade_time = self.Time + self.cooldown
