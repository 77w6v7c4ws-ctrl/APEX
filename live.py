import os,requests
BASE="https://api.the-odds-api.com/v4"
SPORTS={"NBA":"basketball_nba","NFL":"americanfootball_nfl","NCAAF":"americanfootball_ncaaf","MLB":"baseball_mlb"}
MARKETS={
"NBA":["player_points","player_rebounds","player_assists","player_threes"],
"NFL":["player_pass_yds","player_pass_tds","player_rush_yds","player_reception_yds","player_receptions"],
"NCAAF":["player_pass_yds","player_pass_tds","player_rush_yds","player_reception_yds","player_receptions"],
"MLB":["batter_hits","batter_total_bases","batter_home_runs","pitcher_strikeouts"]}

def key(): return os.getenv("THE_ODDS_API_KEY","").strip()
def has_key(): return bool(key())

def upcoming_events(sport_key):
    r=requests.get(f"{BASE}/sports/{sport_key}/events",params={"apiKey":key(),"dateFormat":"iso"},timeout=20)
    r.raise_for_status(); return r.json()

def event_props(sport_key,event_id,markets):
    r=requests.get(f"{BASE}/sports/{sport_key}/events/{event_id}/odds",
        params={"apiKey":key(),"regions":"us","markets":",".join(markets),"oddsFormat":"american","dateFormat":"iso"},timeout=25)
    r.raise_for_status(); return r.json()

def flatten_props(e):
    rows=[]; matchup=f"{e.get('away_team')} @ {e.get('home_team')}"
    for b in e.get("bookmakers",[]):
        for m in b.get("markets",[]):
            for o in m.get("outcomes",[]):
                if o.get("name") not in ("Over","Under"): continue
                rows.append({"event_id":e.get("id"),"matchup":matchup,"book":b.get("title"),
                    "market":m.get("key"),"player":o.get("description") or "",
                    "side":o.get("name"),"line":o.get("point"),"odds":o.get("price")})
    return rows
