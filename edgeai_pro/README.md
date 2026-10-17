# EDGEAI PRO 1.4

Streamlit app using API-Football. Entry point: `edgeai_pro/app.py` when repository contains the `edgeai_pro` folder.

## New
- Automatically requests available pre-match odds for each eligible fixture (multiple bookmakers, up to four result pages).
- Only attaches a quote when market, selection, team and line can be matched conservatively; otherwise labels it unverified.
- Optional corner and yellow-card screening from per-fixture historical statistics. This option uses many API calls and is off by default.
- Applies 1.50 minimum quoted odds and candidate-specific minimum odds.

## Limitations
- The analysis engine is still a prototype. It does not yet model 1X2, handicaps, player shots or shots on target.
- Odds markets vary by bookmaker and fixture; no guarantee of current executable prices. Only exact recognized market/selection pairs are auto-matched.
- Historical corner/card data may be missing; uncalibrated probability estimates are not validated forecasts.
- SQLite storage on Streamlit Community Cloud is ephemeral; use external database for persistent history.
- API-Football quota usage can be substantial when corner/card analysis is enabled.

## Deploy
Replace `edgeai_pro/app.py`, `edgeai_pro/README.md`, and keep `edgeai_pro/requirements.txt`. Streamlit entry point `edgeai_pro/app.py`.
Keep API keys in Streamlit Secrets, e.g. `API_FOOTBALL_KEY = "..."`, never commit keys.
