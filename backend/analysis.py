"""Deterministic, explainable team scoring. Gemini only explains these numbers; it never changes them."""
import json, urllib.request
from . import config
WEIGHTS = {"T20": dict(batting=25, bowling=25, allrounders=15, balance=15, bench=10, budget=10),
           "ODI": dict(batting=25, bowling=30, allrounders=10, balance=15, bench=10, budget=10),
           "Test": dict(batting=30, bowling=35, allrounders=5, balance=15, bench=10, budget=5)}
def _cap(x): return max(0, min(100, x))
def analyse(squad, purse_left, purse_total, fmt="T20"):
    w = WEIGHTS[fmt]; r = lambda role: [p for p in squad if p["role"] == role]
    bat, bowl, ar, wk = r("Batter"), r("Bowler"), r("All-rounder"), r("Wicketkeeper")
    have = sum(1 for p in squad if p.get("stats"))
    cat = {
     "batting": (_cap((len(bat) + len(wk) + 0.6 * len(ar)) / 6 * 100), f"{len(bat)} batters, {len(wk)} keeper(s), {len(ar)} all-rounders; target ~6 batting options"),
     "bowling": (_cap((len(bowl) + 0.6 * len(ar)) / 6 * 100), f"{len(bowl)} bowlers + {len(ar)} all-rounders; target ~6 options"),
     "allrounders": (_cap(len(ar) / 3 * 100), f"{len(ar)} all-rounders; target 3"),
     "balance": (_cap(100 - (0 if wk else 40) - abs(len(bat) - len(bowl)) * 8), "Keeper available" if wk else "No wicketkeeper (-40)"),
     "bench": (_cap((len(squad) - 11) / 4 * 100), f"{len(squad)} players, {max(0, len(squad)-11)} beyond a Playing XI"),
     "budget": (_cap(purse_left / max(1, purse_total) * 200), f"₹{purse_left/100:g} cr left of ₹{purse_total/100:g} cr")}
    total = round(sum(cat[k][0] * w[k] for k in w) / sum(w.values()), 1)
    return dict(format=fmt, total=total, weights=w, categories={k: dict(score=round(v[0], 1), why=v[1]) for k, v in cat.items()},
                confidence="low" if have < len(squad) / 2 else "medium",
                data_note=f"Career statistics available for {have}/{len(squad)} players; otherwise scores use roles only.",
                playing_xi=suggest_xi(squad),
                missing=[n for n, ok in (("Wicketkeeper", wk), ("Specialist bowlers", len(bowl) >= 3), ("All-rounders", len(ar) >= 2)) if not ok])
def suggest_xi(squad):
    pick, order = [], ["Wicketkeeper", "Batter", "All-rounder", "Bowler"]
    for role, n in (("Wicketkeeper", 1), ("Batter", 4), ("All-rounder", 2), ("Bowler", 4)):
        pick += [p for p in squad if p["role"] == role and p not in pick][:n]
    pick += [p for p in squad if p not in pick][:11 - len(pick)]
    pick.sort(key=lambda p: order.index(p["role"]) if p["role"] in order else 9)
    return [dict(name=p["name"], role=p["role"], reason=f"Fills a {p['role']} slot in a balanced XI") for p in pick[:11]]
def explain(results):
    fb = {n: f"{r['total']}/100 ({r['confidence']} confidence). " + "; ".join(f"{k}: {v['score']}" for k, v in r["categories"].items()) for n, r in results.items()}
    if not config.GEMINI_API_KEY: return dict(source="deterministic", text=fb)
    try:
        body = json.dumps({"contents": [{"parts": [{"text": "Explain these cricket team scores in 2 sentences per team as JSON {team: text}. Use only the numbers given; invent no statistics.\n" + json.dumps(results)}]}],
                           "generationConfig": {"responseMimeType": "application/json"}}).encode()
        req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent", body,
                                     {"Content-Type": "application/json", "x-goog-api-key": config.GEMINI_API_KEY})
        data = json.loads(json.load(urllib.request.urlopen(req, timeout=15))["candidates"][0]["content"]["parts"][0]["text"])
        if set(data) == set(results) and all(isinstance(v, str) for v in data.values()): return dict(source="gemini", text=data)
    except Exception: pass
    return dict(source="deterministic", text=fb)
