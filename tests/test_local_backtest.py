from scripts.local_backtest import simulate_short_run


def test_simulate_short_run_returns_metrics():
    m = simulate_short_run()
    assert isinstance(m["net_pnl"], float)
    assert isinstance(m["sharpe"], float)
    assert isinstance(m["trades"], int)

