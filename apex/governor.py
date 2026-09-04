import math,pandas as pd
from .metrics import summary

def confidence_multiplier(s):
    n=s["n"];b=s["brier"];roi=s["roi"];clv=s["avg_clv"]
    sf=min(1,max(.25,n/75))
    cf=max(.25,min(1,1-(b-.18)*3))
    rf=max(.50,min(1.05,1+roi*.60))
    lf=.90 if pd.isna(clv) else max(.60,min(1.08,1+clv*2.5))
    return max(.20,min(1.05,sf*cf*rf*lf))

def verdict(s):
    n=s["n"];b=s["brier"];roi=s["roi"];clv=s["avg_clv"]
    if n<12:return "LOW SAMPLE"
    if b>.29:return "DISABLE"
    if roi<-.15 and (pd.isna(clv) or clv<=0):return "DISABLE"
    if b>.25 or roi<-.08:return "THROTTLE"
    if not pd.isna(clv) and clv<-.015:return "THROTTLE"
    if b<=.21 and roi>0 and (pd.isna(clv) or clv>=0):return "TRUST"
    return "MONITOR"

def audit_groups(df):
    rows=[]
    for (sport,market),g in df.groupby(["sport","market"]):
        s=summary(g)
        rows.append({"sport":sport,"market":market,**s,
                     "confidence_multiplier":confidence_multiplier(s),
                     "governor_verdict":verdict(s)})
    return pd.DataFrame(rows)

def multiplier_for(audit,sport,market):
    x=audit[(audit.sport==sport)&(audit.market==market)]
    if x.empty:return .70
    r=x.iloc[0]
    if r.governor_verdict=="DISABLE":return 0.0
    return float(r.confidence_multiplier)
