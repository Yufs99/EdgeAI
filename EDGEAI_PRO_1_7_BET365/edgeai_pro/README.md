# EDGEAI PRO 1.6 – Streamlit / Bet365

## Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

Add your API-Football key in the sidebar, or use Streamlit secrets `API_FOOTBALL_KEY`. Never publish secrets or API keys in Git.

## Improvements from 1.5

- 1X2 and under-goals candidate models added alongside existing over-goals and BTTS.
- Team corners and cards enabled by default and screened over multiple over/under lines when fixture statistics exist.
- Strict Bet365-only odds matching: exact fixture, market category, side, line and selection. Unsupported and ambiguous market labels are not auto-matched.
- Odds without a parseable timestamp from the last 48 hours are not treated as verified; conflicting latest prices are rejected. These are API snapshots, not guaranteed live Bet365 Sweden prices.
- Verified playable candidates appear ahead of unverified candidates, with deterministic tie-breaking.
- Analysis history can be reopened and exported as JSON.
- Regression checks: `python test_market_matching.py`.

## Important limitations

- API-Football market labels can differ by competition. The strict allowlist may leave genuine prices unverified rather than risk attaching a wrong market.
- The 1X2, goals, corners and cards probability estimates are **not calibrated or backtested**. A high model score is not proof of positive EV.
- Handicap, player shots, player cards and assists are **not yet modeled**. These require appropriate historical/player data and additional validation; no fake coverage is claimed.
- `EDGEAI_DB_PATH` defaults to `edgeai_history.sqlite3` in the working directory. Set it to a persistent mounted disk path to retain history across Streamlit server restarts. Ephemeral Streamlit hosting does not guarantee disk persistence.
- The odds endpoint may not return all Bet365 markets, and its timestamps may be stale. Check the Bet365 app before placing bets.
- Live API verification was not performed in this offline build; check bookmaker ID and market naming using the in-app diagnostic tool.
