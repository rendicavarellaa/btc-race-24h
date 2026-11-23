"""Patient trend rider for the make.fun BTC race (bars-replay/v1).

Strategy, in one paragraph: this bot is long-only and trades rarely. It buys
cbBTC in two halves -- the first half when the 60-minute return first clears
+0.6%, the second half only when the 120-minute return confirms above +0.5%
-- and then it holds. It exits only on a real reversal: price 2% below the
highest close since entry, or an 8% equity drawdown from the run's peak (which
also pauses trading for 60 bars). After any exit it waits 30 bars before it
will enter again. A round trip costs about 30-35 bps in fee, slippage and pool
impact, so the bot never trades chop: it waits for a sustained move, rides it,
and stays out of flat or falling markets.

Why this shape: the dev window is one sharp +3.4% move over two hours followed
by nineteen hours of +/-0.5% chop. Fast EMA-cross and Donchian systems churn
through that chop and give the move back in fees; a patient breakout rider
keeps almost all of it. The same rules were checked on the dev window reversed
in time (a -3.6% day: the bot loses little and its drawdown stays near 2.5%)
and on block-shuffled copies of the window (still clearly profitable).

Deterministic: every decision is a pure function of the closes seen so far and
the account the harness reports. No clock, no network, no files, no random
numbers, no environment reads.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

# --- strategy constants (fractions of price / returns, and bar counts) ---
MOM_WIN = 60          # first-leg entry: 60-minute return above this...
MOM_ENTRY = 0.006     # ... +0.6%
CONFIRM_WIN = 120     # second-leg confirmation: 120-minute return above...
CONFIRM_ENTRY = 0.005  # ... +0.5%
TRAIL_PCT = 0.02      # exit: close 2% below the highest close since entry
GUARD_DD = 0.08       # exit + pause: equity 8% below the run's peak
GUARD_PAUSE = 60      # bars to sit out after the drawdown guard fires
COOLDOWN = 30         # bars to wait after any exit before re-entering
BUY_SLIPPAGE_BPS = 150   # a buy may not fill more than 1.5% above the last close
SELL_SLIPPAGE_BPS = 500  # an exit must go through even in a fast fall


class Rider:
    """The strategy's whole state: closes seen, entry peak, cooldowns."""

    def __init__(self, symbol):
        self.symbol = symbol
        self.closes = []
        self.peak_close = 0
        self.peak_equity = 0
        self.cool_until = -1
        self.second_leg_done = True  # True while flat: no second leg pending

    def on_batch(self, state, batch):
        for bar in batch.get("bars", []):
            if bar.get("symbol") == self.symbol:
                self.closes.append(int(bar["c"]))
        if state.warming_up:
            return []
        if not self.closes:
            return []
        close = self.closes[-1]
        seq = state.seq
        equity = state.equity
        if equity > self.peak_equity:
            self.peak_equity = equity
        holding = state.positions.get(self.symbol)
        qty = holding.qty if holding is not None else 0
        if seq < self.cool_until:
            return []
        # Drawdown guard: flatten and sit out.
        if qty > 0 and equity < self.peak_equity * (1 - GUARD_DD):
            self.cool_until = seq + GUARD_PAUSE
            return [self._sell(qty)]
        if qty == 0:
            return self._maybe_enter(state, close, seq)
        # Holding: second leg first, then the trailing stop.
        if not self.second_leg_done and state.cash >= 1_000_000:
            if len(self.closes) > CONFIRM_WIN:
                r120 = close / self.closes[-1 - CONFIRM_WIN] - 1
                if r120 > CONFIRM_ENTRY:
                    self.second_leg_done = True
                    amount = min(state.cash, state.weight_room(self.symbol))
                    return [self._buy(amount)]
        if close > self.peak_close:
            self.peak_close = close
        if close < self.peak_close * (1 - TRAIL_PCT):
            self.cool_until = seq + COOLDOWN
            return [self._sell(qty)]
        return []

    def _maybe_enter(self, state, close, seq):
        if len(self.closes) <= MOM_WIN:
            return []
        r60 = close / self.closes[-1 - MOM_WIN] - 1
        if r60 <= MOM_ENTRY:
            return []
        self.peak_close = close
        self.second_leg_done = False
        amount = min(state.cash // 2, state.weight_room(self.symbol))
        return [self._buy(amount)]

    @staticmethod
    def _buy(notional):
        return {
            "side": "buy",
            "symbol": SYMBOL,
            "notional_quote_units": int(notional),
            "max_slippage_bps": BUY_SLIPPAGE_BPS,
        }

    @staticmethod
    def _sell(qty):
        return {
            "side": "sell",
            "symbol": SYMBOL,
            "qty": int(qty),
            "max_slippage_bps": SELL_SLIPPAGE_BPS,
        }


SYMBOL = "CBBTC"
_RIDER = None


def on_batch(state, batch):
    global _RIDER
    if _RIDER is None:
        _RIDER = Rider(state.hello["symbols"][0]["symbol"])
    return _RIDER.on_batch(state, batch)


makefun_bars.run(on_batch)
