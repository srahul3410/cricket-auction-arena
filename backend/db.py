import sqlite3, json
from . import config
def conn():
    c = sqlite3.connect(config.DATABASE_PATH, timeout=10); c.row_factory = sqlite3.Row; return c
def init():
    with conn() as c:
        c.executescript("""CREATE TABLE IF NOT EXISTS players(id INTEGER PRIMARY KEY, name TEXT, country TEXT, role TEXT,
          status TEXT, batting TEXT, bowling TEXT, base_lakh INTEGER, stats TEXT, source_urls TEXT, verified_on TEXT, image_url TEXT);
        CREATE TABLE IF NOT EXISTS rooms(code TEXT PRIMARY KEY, state TEXT);
        CREATE TABLE IF NOT EXISTS members(token TEXT PRIMARY KEY, code TEXT, team_id INTEGER, is_host INTEGER, name TEXT);""")
def all_players():
    with conn() as c: return [dict(r) for r in c.execute("SELECT * FROM players")]
def save_state(code, st):
    with conn() as c: c.execute("INSERT OR REPLACE INTO rooms VALUES(?,?)", (code, json.dumps(st)))
def load_state(code):
    with conn() as c:
        r = c.execute("SELECT state FROM rooms WHERE code=?", (code,)).fetchone()
    return json.loads(r["state"]) if r else None
def add_member(token, code, team_id, is_host, name):
    with conn() as c: c.execute("INSERT INTO members VALUES(?,?,?,?,?)", (token, code, team_id, is_host, name))
def member(token):
    with conn() as c:
        r = c.execute("SELECT * FROM members WHERE token=?", (token,)).fetchone()
    return dict(r) if r else None
