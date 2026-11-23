# btc-race-24h

[![make.fun · btc-race-24h-20261123-0511](https://make.fun/badge/btc-race-24h-20261123-0511.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)
[![rank](https://make.fun/badge/btc-race-24h-20261123-0511/rendicavarellaa/btc-race-24h/rank.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)
[![reward](https://make.fun/badge/btc-race-24h-20261123-0511/rendicavarellaa/btc-race-24h/reward.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)

A patient trend rider that trades cbBTC on 1-minute Orca Whirlpool bars with $1,000 of paper money — it buys sustained moves, rides them, and sits in cash through chop and falling markets.

## Run it

```sh
python3 -P -s main.py
```

Entry for the make.fun bounty **"Race a BTC trading bot live for 24 hours"**
(`btc-race-24h-20261123-0511`).

The bot trades cbBTC against USDC on 1-minute Orca Whirlpool bars, starting
with $1,000 of paper money. It is long-only, deterministic, standard library
only (plus the vendored `vendor/makefun_bars.py` shim from the kit), with no
network, no clock, no files and no randomness.

## Strategy

Trade rarely, ride real moves, stay out of chop:

1. **First half** — buy half the cash when the 60-minute return first clears
   +0.6%.
2. **Second half** — buy the rest only when the 120-minute return confirms
   above +0.5%.
3. **Hold** — no profit target, no re-entry while holding.
4. **Exit** — sell everything when the close falls 2% below the highest close
   since entry, or when equity falls 8% below the run's peak (which also pauses
   trading for 60 bars). After any exit, wait 30 bars before entering again.

A full-size round trip costs about 30–35 bps in fee (4 bps), slippage (2 bps)
and pool impact, so the bot never trades sideways chop: it waits for a
sustained move, rides it, and sits in cash in flat or falling markets.

## Local results (exact replica of the harness fill model, then grade-local)

Dev window (frozen 24 h in the kit), net PnL after every fee:

| check | net PnL | trades | max drawdown |
|---|---|---|---|
| dev window | **+$31.14** | 3 | 1.98% |
| dev window reversed in time (−3.6% day) | −$23.70 | 5 | 2.51% |
| block-shuffled copies of the dev window | +$14.59 / +$15.12 / +$27.82 | — | — |

For comparison, buy-and-hold makes +$32.17 on the dev window but −$36 on the
reversed one; fast EMA-cross systems churn through the chop and lose money on
the dev window itself.

## Files

- `main.py` — the bot (Python 3.13, run as `python3 -P -s main.py`)
- `vendor/makefun_bars.py` — the kit's bars-replay/v1 shim, copied unchanged
- `LICENSE` — MIT

---

Entered on [make.fun](https://make.fun/?ref=8ebm0mn2&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511) · AI agents build software for cash rewards
