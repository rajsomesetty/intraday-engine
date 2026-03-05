from prometheus_client import Counter, Gauge

# Counters
total_trades = Counter(
    "intraday_total_trades",
    "Total successful trades executed"
)

total_rejections = Counter(
    "intraday_total_rejections",
    "Total rejected trades"
)

# Gauges
current_equity = Gauge(
    "intraday_current_equity",
    "Current account equity"
)

current_exposure = Gauge(
    "intraday_current_exposure",
    "Current portfolio exposure"
)

kill_switch_state = Gauge(
    "intraday_kill_switch_state",
    "Kill switch state (1=enabled, 0=disabled)"
)
