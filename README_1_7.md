# EDGEAI PRO 1.7

Based on EDGEAI PRO 1.6. Start with `pip install -r requirements.txt` and `streamlit run app.py`.

## Changes
- Adds Asian Handicap half-goal candidates (-1.5, -0.5, +0.5, +1.5) from independent Poisson goal-difference distributions.
- Adds player shots and shots-on-target candidates based on historical `/fixtures/players` records, requiring at least five appearances of 20+ minutes. Historical participation does not establish today's starting lineup.
- Adds a manual JSON history importer to complement existing JSON export and SQLite history. For reliable persistence across hosting restarts, configure EDGEAI_DB_PATH to a mounted persistent volume; an ephemeral Streamlit host cannot guarantee it.
- Bet365 odds continue to require exact market matching. Player markets remain unverified until a reliable mapping is available; the app never invents their prices.

## Important limits
- Probability models are heuristic and NOT backtested or calibrated; probability and strength ratings should not be interpreted as proven forecasts.
- Odds endpoint coverage and market labels may vary; Bet365 prices cannot be verified without a live API test with your subscription.
- `/fixtures/players` adds API usage; disable player markets in the UI if coverage is sparse or requests become excessive.
- Only half-goal Asian handicap lines are included (no push or quarter-line settlement).
- No claim of complete player markets or full bookmaker coverage.

Run offline checks: `python test_market_matching.py`.
