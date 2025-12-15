"""Local paper runner (minimal): loads brain, ingests recent candle(s), builds features, runs inference, and (optionally) places Alpaca bracket orders.
This is a light runner; production runtime should use LEAN algorithm skeleton in `Lean/Algorithm.Python/TeslaBrainAlgo.py`.
"""
from bot.src.model.brain_loader import BrainLoader
from bot.src.features.build_features import build_features
from bot.src.execution.alpaca_orders import AlpacaClientStub
from pathlib import Path
import pandas as pd

BRAIN_PATH = Path("bot/brains/TSLA_1h/brain_latest.json")

def run_once(candles: pd.DataFrame, dry_run=True):
    bl = BrainLoader(str(BRAIN_PATH))
    feat = build_features(candles).iloc[-1].to_dict()
    if not bl.feature_hash_ok(list(build_features(candles).columns)):
        raise RuntimeError("Feature hash mismatch — aborting to prevent silent drift")
    model = bl.get_model()
    from bot.src.model.infer import predict_from_linear_model
    direction, conf, z = predict_from_linear_model(model, feat)
    print("direction", direction, "conf", conf)
    if dry_run:
        return {"direction": direction, "conf": conf}
    client = AlpacaClientStub()
    # placeholder: compute qty, stop, tp via risk module
    return client.place_bracket_order("TSLA", 1, "buy" if direction>0 else "sell", 0, 0)

if __name__ == '__main__':
    # simple demo using last available minute CSV if present
    import sys
    import pandas as pd
    data_path = Path("data/TSLA_1min.csv")
    if not data_path.exists():
        print("No data/TSLA_1min.csv found — run against QC or supply a CSV")
        sys.exit(0)
    df = pd.read_csv(data_path, parse_dates=['timestamp']).set_index('timestamp')
    df5 = df.resample('60min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
    print(run_once(df5.tail(400), dry_run=True))
