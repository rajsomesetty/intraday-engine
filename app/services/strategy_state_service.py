strategy_states = {}


def register_strategy_state(name):

    if name not in strategy_states:
        strategy_states[name] = {
            "enabled": True,
            "peak_pnl": 0,
            "current_pnl": 0
        }


def update_strategy_pnl(name, pnl):

    state = strategy_states[name]

    state["current_pnl"] += pnl

    if state["current_pnl"] > state["peak_pnl"]:
        state["peak_pnl"] = state["current_pnl"]


def check_drawdown(name, max_drawdown_pct=5):

    state = strategy_states[name]

    peak = state["peak_pnl"]
    current = state["current_pnl"]

    if peak == 0:
        return True

    drawdown = ((peak - current) / peak) * 100

    if drawdown > max_drawdown_pct:
        state["enabled"] = False
        return False

    return True


def is_strategy_enabled(name):

    return strategy_states.get(name, {}).get("enabled", True)
