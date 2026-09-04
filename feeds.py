import os, pandas as pd, requests
from io import StringIO

def _remote(url):
    r=requests.get(url,timeout=25); r.raise_for_status()
    if "json" in r.headers.get("content-type","").lower():
        return pd.DataFrame(r.json())
    return pd.read_csv(StringIO(r.text))

def normalize_history(df):
    req=["date","player","team","opponent","market","result"]
    miss=[c for c in req if c not in df.columns]
    if miss: raise ValueError("history missing: "+", ".join(miss))
    d=df.copy()
    d["date"]=pd.to_datetime(d["date"],errors="coerce")
    d["player"]=d["player"].astype(str).str.strip()
    d["market"]=d["market"].astype(str).str.strip()
    d["result"]=pd.to_numeric(d["result"],errors="coerce")
    return d.dropna(subset=["date","player","market","result"]).sort_values("date")

def normalize_availability(df):
    cols=["player","status","availability_factor","role_factor","updated_at","note"]
    d=df.copy()
    for c in cols:
        if c not in d.columns: d[c]="" if c in ["status","updated_at","note"] else 1.0
    d["player"]=d["player"].astype(str).str.strip()
    d["availability_factor"]=pd.to_numeric(d["availability_factor"],errors="coerce").fillna(1).clip(0,1.1)
    d["role_factor"]=pd.to_numeric(d["role_factor"],errors="coerce").fillna(1).clip(0,1.35)
    return d[cols]

def remote_history():
    u=os.getenv("APEX_PLAYER_HISTORY_URL","").strip()
    return normalize_history(_remote(u)) if u else None

def remote_availability():
    u=os.getenv("APEX_AVAILABILITY_URL","").strip()
    return normalize_availability(_remote(u)) if u else None

def player_adjustment(df,player):
    if df is None or df.empty:
        return {"status":"UNKNOWN","availability_factor":1.0,"role_factor":1.0,"note":""}
    x=df[df.player.str.lower()==str(player).lower()]
    if x.empty:
        return {"status":"UNKNOWN","availability_factor":1.0,"role_factor":1.0,"note":""}
    r=x.iloc[-1]
    return {"status":str(r.status),"availability_factor":float(r.availability_factor),
            "role_factor":float(r.role_factor),"note":str(r.note)}
