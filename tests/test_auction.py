import threading
from backend import auction as A
def mk(purse=1000):
    pl = [dict(id=i, name=f"P{i}", country="India" if i % 2 else "Australia", role="Batter", status="active", base_lakh=200) for i in range(1, 6)]
    st = A.new_state("T", dict(purse=purse, squad=2, countdown=1, auto=False), pl); A.add_team(st, "A"); A.add_team(st, "B"); A.start(st); return st
def test_concurrent_bids_serialised():
    st = mk(); errs = []
    def go(t):
        with A.lock("T"):
            try: A.bid(st, t, 200)
            except A.AuctionError as e: errs.append(e)
    ts = [threading.Thread(target=go, args=(t,)) for t in "12"]
    [t.start() for t in ts]; [t.join() for t in ts]
    assert st["current"]["bid"] == 200 and len(errs) == 1
def test_purse_and_single_sale():
    st = mk(purse=300); turn = "1"; blocked = False
    for _ in range(10):
        try: A.bid(st, turn); turn = "2" if turn == "1" else "1"
        except A.AuctionError: blocked = True; break
    assert blocked  # a bid above remaining purse is rejected
    st["current"]["ends"] = 0; A.tick(st)
    assert len(st["sold"]) == 1 and all(t["purse"] >= 0 for t in st["teams"].values())
def test_unsold_goes_to_reauction():
    st = mk(); st["current"]["ends"] = 0; A.tick(st); assert len(st["unsold"]) == 1 and st["status"] == "between"
