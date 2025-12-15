import pandas as pd
import numpy as np
from .feature_spec import FEATURE_LIST_H1

# Minimal implementation mirroring QC feature set used in training script

def build_features(df):
    close = df['close']
    ret1 = close.pct_change()
    rsi = (100 - (100/(1 + (ret1.clip(lower=0).ewm(alpha=1/14).mean() / (-ret1.clip(upper=0)).ewm(alpha=1/14).mean()+1e-9))))
    ema20 = close.ewm(span=20).mean()
    bb_mid = close.rolling(20).mean()
    bb_std = close.rolling(20).std()
    bb_z = (close - bb_mid) / (2*bb_std + 1e-9)
    atr = (df['high'] - df['low']).ewm(alpha=1/14).mean()
    vol20 = ret1.rolling(20).std()
    vol_z = (vol20 - vol20.rolling(100).mean()) / (vol20.rolling(100).std() + 1e-9)
    df_feat = pd.DataFrame({
        'rsi': rsi,
        'macd': close.ewm(span=12).mean() - close.ewm(span=26).mean(),
        'bb_z': bb_z,
        'atr': atr,
        'ema20_rel': close/ema20 - 1,
        'vol_z': vol_z.fillna(0),
    }, index=df.index)
    return df_feat
