from .live import upcoming_events,event_props,flatten_props
from .model import pair_markets,project,grade
from .feeds import player_adjustment
from .storage import save_snapshot,previous
from .governor import multiplier_for

def scan(sport_name,sport_key,markets,history,availability,audit,max_events=10):
    ranked=[];errors=[]
    for e in upcoming_events(sport_key)[:max_events]:
        try:pairs=pair_markets(flatten_props(event_props(sport_key,e["id"],markets)))
        except Exception as ex:
            errors.append(f"{e.get('id')}: {ex}");continue
        for pair in pairs:
            prior=previous(pair["event_id"],pair["book"],pair["market"],pair["player"])
            save_snapshot(pair)
            adj=player_adjustment(availability,pair["player"])
            proj=project(history,pair["player"],pair["market"],pair["line"],adj["availability_factor"],adj["role_factor"])
            if not proj:continue
            mult=multiplier_for(audit,sport_name,pair["market"])
            if mult==0:continue
            r=grade(pair,proj,mult)
            r.update(status=adj["status"],note=adj["note"],availability_factor=adj["availability_factor"],role_factor=adj["role_factor"])
            r["line_move"]=pair["line"]-float(prior[1]) if prior else 0.0
            r["market_warning"]=bool(r["line_move"]>=1 and r["verdict"] in ("ATTACK","VALUE"))
            if r["market_warning"]:
                r["apex_score"]=max(0,r["apex_score"]-8)
                if r["verdict"]=="ATTACK":r["verdict"]="VALUE"
            ranked.append(r)
    ranked.sort(key=lambda x:(x["apex_score"],x["ev"]),reverse=True)
    return ranked,errors
