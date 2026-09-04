# APEX UNIFIED

APEX UNIFIED merges the full stack:
- one-tap live prop scanning
- upcoming event discovery
- player-history projections
- availability / injury / role adjustments
- no-vig sportsbook probabilities
- edge / EV / fair odds
- line-movement snapshots
- paper-trade ledger
- backtesting
- calibration
- Brier score
- log loss
- simulated ROI
- CLV
- Governor confidence throttling

## Secrets
THE_ODDS_API_KEY=...
APEX_PLAYER_HISTORY_URL=https://...
APEX_AVAILABILITY_URL=https://...

## Player history format
Required:
date,player,team,opponent,market,result

Optional:
minutes,usage,availability

## Availability format
player,status,availability_factor,role_factor,updated_at,note

## Run
pip install -r requirements.txt
streamlit run app.py

APEX is probabilistic research / paper-trading software.
It does not guarantee outcomes or profit.
