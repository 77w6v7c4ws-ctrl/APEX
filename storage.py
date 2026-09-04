import sqlite3
from datetime import datetime,timezone
DB="apex_unified.db"

def init_db():
    c=sqlite3.connect(DB)
    c.execute("CREATE TABLE IF NOT EXISTS snapshots(id INTEGER PRIMARY KEY AUTOINCREMENT,created_at TEXT,event_id TEXT,book TEXT,market TEXT,player TEXT,line REAL,over_odds INTEGER,under_odds INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS paper_trades(id INTEGER PRIMARY KEY AUTOINCREMENT,created_at TEXT,sport TEXT,event_id TEXT,book TEXT,market TEXT,player TEXT,line REAL,odds INTEGER,model_probability REAL,market_probability REAL,edge REAL,ev REAL,verdict TEXT,result REAL,closing_odds INTEGER)")
    c.commit();c.close()

def save_snapshot(p):
    c=sqlite3.connect(DB)
    c.execute("INSERT INTO snapshots(created_at,event_id,book,market,player,line,over_odds,under_odds) VALUES(?,?,?,?,?,?,?,?)",
      (datetime.now(timezone.utc).isoformat(),p["event_id"],p["book"],p["market"],p["player"],p["line"],p["over_odds"],p["under_odds"]))
    c.commit();c.close()

def previous(event_id,book,market,player):
    c=sqlite3.connect(DB)
    r=c.execute("SELECT created_at,line,over_odds,under_odds FROM snapshots WHERE event_id=? AND book=? AND market=? AND player=? ORDER BY id DESC LIMIT 1 OFFSET 1",
      (event_id,book,market,player)).fetchone();c.close();return r

def add_paper(sport,r):
    c=sqlite3.connect(DB)
    c.execute("INSERT INTO paper_trades(created_at,sport,event_id,book,market,player,line,odds,model_probability,market_probability,edge,ev,verdict) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
      (datetime.now(timezone.utc).isoformat(),sport,r["event_id"],r["book"],r["market"],r["player"],r["line"],r["over_odds"],r["model_probability"],r["market_probability"],r["edge"],r["ev"],r["verdict"]))
    c.commit();c.close()

def ledger():
    c=sqlite3.connect(DB)
    rows=c.execute("SELECT created_at,sport,event_id,book,market,player,line,odds,model_probability,market_probability,edge,ev,verdict,result,closing_odds FROM paper_trades ORDER BY id DESC").fetchall()
    c.close();return rows
