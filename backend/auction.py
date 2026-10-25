"""Server-authoritative auction engine. All amounts are integer lakh (100 lakh = 1 crore)."""
import random, threading, time
_LOCKS = {}
def lock(code): return _LOCKS.setdefault(code, threading.RLock())
class AuctionError(Exception): pass
DEFAULTS = dict(purse=10000, squad=15, increment=25, countdown=15, overseas_limit=0, auto=True, pool="mixed", teams=2)
def new_state(code, settings, players):
    s = {**DEFAULTS, **settings}
    if s["teams"] not in (2, 3, 4): raise AuctionError("Teams must be 2, 3 or 4")
    if s["pool"] == "active": players = [p for p in players if p["status"] == "active"]
    elif s["pool"] == "retired": players = [p for p in players if p["status"] == "retired"]
    ids = [p["id"] for p in players]; random.shuffle(ids)
    return dict(code=code, settings=s, status="lobby", teams={}, queue=ids, unsold=[], current=None, sold=[], log=[],
                players={str(p["id"]): p for p in players}, paused_left=None)
def log(st, msg): st["log"].append(dict(t=int(time.time()), msg=msg)); st["log"] = st["log"][-80:]
def add_team(st, name):
    if st["status"] != "lobby": raise AuctionError("Auction already started")
    if len(st["teams"]) >= st["settings"]["teams"]: raise AuctionError("Room is full")
    tid = str(len(st["teams"]) + 1)
    st["teams"][tid] = dict(name=(name or f"Team {tid}")[:24], purse=st["settings"]["purse"], squad=[], overseas=0)
    return tid
def next_lot(st):
    if not st["queue"]:
        if st["unsold"] and not st.get("reauction_done"):
            st["queue"], st["unsold"], st["reauction_done"] = st["unsold"], [], True; log(st, "Re-auctioning unsold players")
        else: st["status"], st["current"] = "finished", None; log(st, "Auction finished"); return
    pid = str(st["queue"].pop(0)); p = st["players"][pid]
    st["current"] = dict(pid=pid, bid=0, bidder=None, ends=time.time() + st["settings"]["countdown"]); st["status"] = "live"
    log(st, f"Up for auction: {p['name']} (base ₹{p['base_lakh']/100:g} cr)")
def start(st):
    if st["status"] != "lobby": raise AuctionError("Already started")
    if len(st["teams"]) < 2: raise AuctionError("Need at least 2 teams")
    next_lot(st)
def min_next(st):
    c = st["current"]; p = st["players"][c["pid"]]
    return p["base_lakh"] if c["bidder"] is None else c["bid"] + st["settings"]["increment"]
def bid(st, tid, amount=None):
    if st["status"] != "live": raise AuctionError("No live lot")
    c = st["current"]
    if time.time() > c["ends"]: raise AuctionError("Time is up")
    t = st["teams"].get(tid)
    if not t: raise AuctionError("Unknown team")
    need = min_next(st)
    if amount is not None and amount != need: raise AuctionError(f"Bid must be exactly {need} lakh")
    if c["bidder"] == tid: raise AuctionError("You already hold the highest bid")
    if len(t["squad"]) >= st["settings"]["squad"]: raise AuctionError("Squad is full")
    if need > t["purse"]: raise AuctionError("Not enough purse")
    p = st["players"][c["pid"]]; lim = st["settings"]["overseas_limit"]
    if lim and p["country"] != "India" and t["overseas"] >= lim: raise AuctionError("Overseas limit reached")
    c["bid"], c["bidder"] = need, tid
    c["ends"] = max(c["ends"], time.time() + min(st["settings"]["countdown"], 8))
    log(st, f"{t['name']} bids ₹{need/100:g} cr for {p['name']}")
def close_lot(st):
    c = st["current"]; p = st["players"][c["pid"]]
    if c["bidder"]:
        t = st["teams"][c["bidder"]]; t["purse"] -= c["bid"]; t["squad"].append(c["pid"])
        if p["country"] != "India": t["overseas"] += 1
        st["sold"].append(dict(pid=c["pid"], team=c["bidder"], price=c["bid"])); log(st, f"SOLD {p['name']} to {t['name']} for ₹{c['bid']/100:g} cr")
    else: st["unsold"].append(c["pid"]); log(st, f"UNSOLD {p['name']}")
    st["current"], st["status"] = None, "between"
def tick(st):
    if st["status"] == "live" and time.time() >= st["current"]["ends"]: close_lot(st); st["_at"] = time.time(); return True
    if st["status"] == "between" and st["settings"]["auto"] and time.time() - st.get("_at", 0) > 4: next_lot(st); return True
    return False
def pause(st):
    if st["status"] == "live": st["paused_left"] = st["current"]["ends"] - time.time(); st["status"] = "paused"; log(st, "Auction paused")
def resume(st):
    if st["status"] == "paused": st["current"]["ends"] = time.time() + st["paused_left"]; st["status"] = "live"; log(st, "Auction resumed")
def public(st):
    c = st["current"]; out = {k: st[k] for k in ("code", "settings", "status", "teams", "sold", "unsold", "log")}
    out["current"] = None
    if c:
        left = st["paused_left"] if st["status"] == "paused" else c["ends"] - time.time()
        out["current"] = dict(c, player=st["players"][c["pid"]], next_bid=min_next(st), left=max(0, round(left, 1)))
    out["squads"] = {tid: [st["players"][p] for p in t["squad"]] for tid, t in st["teams"].items()}
    return out
