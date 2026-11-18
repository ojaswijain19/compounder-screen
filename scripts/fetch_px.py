"""Yahoo weekly closes for 5 years (valuation history, charts, trend)."""
import json, os, time, subprocess
u=json.load(open("universe.json")); out={}
if os.path.exists("prices.json"): out=json.load(open("prices.json"))
for i,x in enumerate(u):
    t=x['t']
    if t in out and out[t].get('w'): continue
    r=None
    for att in range(5):
        r=subprocess.run(["curl","-sS","-m","25","-A","Mozilla/5.0",f"https://query1.finance.yahoo.com/v8/finance/chart/{t}?range=5y&interval=1wk"],capture_output=True,text=True)
        if r.stdout.startswith('{"chart"'): break
        time.sleep(5+att*10)
    try:
        d=json.loads(r.stdout)["chart"]["result"][0]; m=d["meta"]
        ts=d["timestamp"]; cl=d["indicators"]["quote"][0]["close"]
        w=[[a,round(c,3)] for a,c in zip(ts,cl) if c is not None]
        out[t]=dict(p=m["regularMarketPrice"],ts=m["regularMarketTime"],hi=m.get("fiftyTwoWeekHigh"),lo=m.get("fiftyTwoWeekLow"),cur=m.get("currency"),w=w)
    except Exception as e:
        out[t]=dict(err=(r.stdout if r else '')[:80])
    if i%50==0:
        print(i,t,'ok' if 'p' in out[t] else out[t],flush=True); json.dump(out,open("prices.json","w"))
    time.sleep(0.25)
json.dump(out,open("prices.json","w"))
print("done",sum(1 for v in out.values() if 'p' in v),"of",len(u))
