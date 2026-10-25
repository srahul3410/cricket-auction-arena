import secrets, random, string, logging, time
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit, join_room

from . import config, db, auction as A, analysis

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"

app = Flask(
    __name__,
    static_folder=str(FRONTEND_DIR / "static"),
    static_url_path="/static"
)
app.config["SECRET_KEY"] = config.SECRET_KEY
sio = SocketIO(app, async_mode="threading")

logging.basicConfig(level=logging.INFO)
db.init()

_rate = {}
_tickers = set()

def limited(token, n=8, per=2.0):
    q = [t for t in _rate.get(token, []) if time.time() - t < per]
    q.append(time.time())
    _rate[token] = q
    return len(q) > n

def broadcast(code, st):
    sio.emit("state", A.public(st), to=code)

def ticker(code):
    while True:
        sio.sleep(0.5)
        with A.lock(code):
            st = db.load_state(code)
            if not st or st["status"] == "finished":
                _tickers.discard(code)
                return
            if A.tick(st):
                db.save_state(code, st)
                broadcast(code, st)

def ensure_ticker(code):
    if code not in _tickers:
        _tickers.add(code)
        sio.start_background_task(ticker, code)

@app.get("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.get("/api/players")
def players():
    q, role, country = request.args.get("q", "").lower(), request.args.get("role"), request.args.get("country")
    return jsonify([
        p for p in db.all_players() 
        if q in p["name"].lower() and (not role or p["role"] == role) and (not country or p["country"] == country)
    ])

@app.post("/api/rooms")
def create_room():
    d = request.get_json(force=True)
    code = "".join(random.choices(string.ascii_uppercase, k=5))
    with A.lock(code):
        try:
            st = A.new_state(code, {k: d[k] for k in A.DEFAULTS if k in d}, db.all_players())
            tid = A.add_team(st, d.get("team"))
        except (A.AuctionError, TypeError) as e:
            return jsonify(error=str(e)), 400
        token = secrets.token_urlsafe(24)
        db.save_state(code, st)
        db.add_member(token, code, int(tid), 1, d.get("team", ""))
    ensure_ticker(code)
    return jsonify(code=code, token=token, team=tid, host=True)

@app.post("/api/rooms/<code>/join")
def join(code):
    d = request.get_json(force=True)
    code = code.upper()
    with A.lock(code):
        st = db.load_state(code)
        if not st:
            return jsonify(error="Room not found"), 404
        try:
            tid = A.add_team(st, d.get("team"))
        except A.AuctionError as e:
            return jsonify(error=str(e)), 400
        token = secrets.token_urlsafe(24)
        db.save_state(code, st)
        db.add_member(token, code, int(tid), 0, d.get("team", ""))
        broadcast(code, st)
    ensure_ticker(code)
    return jsonify(code=code, token=token, team=tid, host=False)

@sio.on("hello")
def hello(d):
    m = db.member(d.get("token", ""))
    if not m:
        return emit("err", "Invalid session")
    join_room(m["code"])
    ensure_ticker(m["code"])
    emit("state", A.public(db.load_state(m["code"])))
    emit("me", dict(team=str(m["team_id"]), host=bool(m["is_host"])))

@sio.on("action")
def action(d):
    m = db.member(d.get("token", ""))
    if not m:
        return emit("err", "Invalid session")
    if limited(d["token"]):
        return emit("err", "Slow down")
    code, kind = m["code"], d.get("kind")
    with A.lock(code):
        st = db.load_state(code)
        try:
            if kind == "bid":
                A.bid(st, str(m["team_id"]), d.get("amount"))
            elif kind in ("start", "pause", "resume", "next"):
                if not m["is_host"]:
                    raise A.AuctionError("Host only")
                if kind == "start":
                    A.start(st)
                elif kind == "pause":
                    A.pause(st)
                elif kind == "resume":
                    A.resume(st)
                elif st["status"] == "between":
                    A.next_lot(st)
            else:
                raise A.AuctionError("Unknown action")
        except A.AuctionError as e:
            return emit("err", str(e))
        db.save_state(code, st)
        broadcast(code, st)

@app.get("/api/rooms/<code>/analysis")
def room_analysis(code):
    st = db.load_state(code.upper())
    fmt = request.args.get("format", "T20")
    if not st or fmt not in analysis.WEIGHTS:
        return jsonify(error="Not found"), 404
    res = {
        t["name"]: analysis.analyse([st["players"][p] for p in t["squad"]], t["purse"], st["settings"]["purse"], fmt)
        for t in st["teams"].values()
    }
    return jsonify(
        results=res,
        explanation=analysis.explain(res),
        disclaimer="Estimate from the chosen scoring model, not a prediction of match results."
    )

if __name__ == "__main__":
    sio.run(app, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True)