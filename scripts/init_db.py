import sys, os; sys.path.insert(0, os.getcwd())
from backend import db; from data.seed_players import P
db.init()
with db.conn() as c:
    c.execute("DELETE FROM players")
    for i, (n, co, r, s) in enumerate(P, 1):
        c.execute("INSERT INTO players(id,name,country,role,status,base_lakh,stats,source_urls) VALUES(?,?,?,?,?,?,NULL,'[]')", (i, n, co, r, s, 200))
print(len(P), "players loaded (stats unavailable; not verified as official)")
