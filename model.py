import math
from statistics import mean,pstdev
from collections import defaultdict
from .odds import no_vig_two_way,profit_per_unit,fair_american

def ncdf(x,mu,sigma):
    if sigma<=0:return .5
    return .5*(1+math.erf((x-mu)/(sigma*math.sqrt(2))))

def project(h,player,market,line,af=1.0,rf=1.0):
    d=h[(h.player.str.lower()==str(player).lower())&(h.market==market)].copy()
    if len(d)<3:return None
    vals=d.result.astype(float).tolist()
    comps=[mean(vals),mean(vals[-5:]),mean(vals[-3:])]
    mu=.30*comps[0]+.40*comps[1]+.30*comps[2]
    if "minutes" in d.columns:
        xs=d.minutes.dropna().astype(float).tolist()
        if xs and mean(xs)>0: mu*=max(.82,min(1.18,xs[-1]/mean(xs)))
    if "usage" in d.columns:
        xs=d.usage.dropna().astype(float).tolist()
        if xs and mean(xs)>0: mu*=max(.82,min(1.18,xs[-1]/mean(xs)))
    mu*=af*rf
    sigma=max(1.0,pstdev(vals) if len(vals)>1 else abs(mu)*.15)
    p=max(.01,min(.99,1-ncdf(float(line),mu,sigma)))
    conf=min(.97,.48+.035*len(vals))
    disp=pstdev(comps) if len(comps)>1 else 0
    agree=max(0,min(1,1-disp/max(1,abs(mu))/.25))
    unc=min(.24,.035+(sigma/max(1,abs(mu)))*.14+(1-conf)*.10+(1-agree)*.06)
    return {"projection":mu,"p_over":p,"sigma":sigma,"samples":len(vals),"confidence":conf,"agreement":agree,"uncertainty":unc}

def pair_markets(rows):
    g=defaultdict(dict)
    for r in rows:
        if r["line"] is None or not r["player"]: continue
        g[(r["event_id"],r["book"],r["market"],r["player"],float(r["line"]))][r["side"]]=r
    out=[]
    for s in g.values():
        if "Over" not in s or "Under" not in s: continue
        o,u=s["Over"],s["Under"]; mp,_=no_vig_two_way(o["odds"],u["odds"])
        out.append({"event_id":o["event_id"],"matchup":o["matchup"],"book":o["book"],"market":o["market"],
                    "player":o["player"],"line":float(o["line"]),"over_odds":int(o["odds"]),
                    "under_odds":int(u["odds"]),"market_probability":mp})
    return out

def grade(pair,proj,governor_multiplier=1.0):
    raw=proj["p_over"]
    p=.5+(raw-.5)*governor_multiplier
    m=pair["market_probability"]
    edge=p-m; ev=p*profit_per_unit(pair["over_odds"])-(1-p)
    low=max(.01,p-proj["uncertainty"]); high=min(.99,p+proj["uncertainty"])
    robust=max(0,min(1,(low-m)/max(.001,edge))) if edge>0 else 0
    score=round(100*(.30*max(0,min(1,edge/.12))+.23*max(0,min(1,ev/.15))+
                     .18*proj["confidence"]+.13*proj["agreement"]+.11*robust+
                     .05*(1-min(1,proj["uncertainty"]/.22))))
    if proj["confidence"]<.55 or proj["agreement"]<.35:v="MODEL FAILURE"
    elif edge>=.08 and ev>=.08 and low>m and robust>=.55:v="ATTACK"
    elif edge>=.04 and ev>0 and proj["confidence"]>=.64:v="VALUE"
    elif edge>0 and ev>0:v="WATCH"
    else:v="PASS"
    return {**pair,**proj,"raw_probability":raw,"model_probability":p,"edge":edge,"ev":ev,
            "uncertainty_low":low,"uncertainty_high":high,"robustness":robust,
            "fair_odds":fair_american(p),"apex_score":score,"verdict":v,
            "governor_multiplier":governor_multiplier}
