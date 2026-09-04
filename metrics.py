import numpy as np, pandas as pd

def american_profit(odds):
    odds=float(odds); return odds/100 if odds>0 else 100/abs(odds)
def american_to_implied(odds):
    odds=float(odds); return 100/(odds+100) if odds>0 else (-odds)/((-odds)+100)
def brier_score(y,p):
    y=np.asarray(y,float);p=np.asarray(p,float);return float(np.mean((p-y)**2))
def log_loss(y,p):
    y=np.asarray(y,float);p=np.clip(np.asarray(p,float),1e-6,1-1e-6)
    return float(-np.mean(y*np.log(p)+(1-y)*np.log(1-p)))
def simulated_roi(df):
    if len(df)==0:return 0
    vals=[american_profit(r.odds) if int(r.result)==1 else -1 for _,r in df.iterrows()]
    return sum(vals)/len(vals)
def clv(row):
    if pd.isna(row.get("closing_odds")):return np.nan
    return american_to_implied(row["closing_odds"])-american_to_implied(row["odds"])
def summary(df):
    d=df.copy();d["clv"]=d.apply(clv,axis=1)
    return {"n":len(d),"win_rate":float(d.result.mean()) if len(d) else 0,
            "brier":brier_score(d.result,d.model_probability) if len(d) else 0,
            "log_loss":log_loss(d.result,d.model_probability) if len(d) else 0,
            "roi":simulated_roi(d),
            "avg_clv":float(d.clv.dropna().mean()) if d.clv.notna().any() else np.nan}
def calibration_table(df,bins=10):
    d=df.copy()
    d["bucket"]=pd.cut(d.model_probability,bins=np.linspace(0,1,bins+1),include_lowest=True,duplicates="drop")
    out=d.groupby("bucket",observed=False).agg(predictions=("result","size"),
        avg_probability=("model_probability","mean"),actual_win_rate=("result","mean")).reset_index()
    out["calibration_gap"]=out.avg_probability-out.actual_win_rate
    return out.dropna(subset=["avg_probability"])
