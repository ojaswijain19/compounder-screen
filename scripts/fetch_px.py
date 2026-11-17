import json, os, time, subprocess, datetime
u=json.load(open("universe.json")); out={}
if os.path.exists("prices.json"): out=json.load(open("prices.json"))
for i,x in enumerate(u):
    t=x['t']
    if t in out and out[t].get('c'): continue
    for att in range(4):
        r=subprocess.run(["curl","-sS","-m","25","-A","Mozilla/5.0",f"https://query1.finance.yahoo.com/v8/finance/chart/{t}?range=1y&interval=1d"],capture_output=True,text=True)
        if r.stdout.startswith('{"chart"'): break
        time.sleep(5+att*10)
    try:
        d=json.loads(r.stdout)["chart"]["result"][0]; m=d["meta"]
        cl=[c for c in d["indicators"]["quote"][0]["close"] if c is not None]
        out[t]=dict(p=m["regularMarketPrice"],ts=m["regularMarketTime"],hi=m.get("fiftyTwoWeekHigh"),lo=m.get("fiftyTwoWeekLow"),cur=m.get("currency"),c=[round(c,3) for c in cl])
    except Exception as e:
        out[t]=dict(err=r.stdout[:80])
    if i%50==0:
        print(i,t,'ok' if 'p' in out[t] else out[t],flush=True); json.dump(out,open("prices.json","w"))
    time.sleep(0.25)
json.dump(out,open("prices.json","w"))
print("done",sum(1 for v in out.values() if 'p' in v),"of",len(u))
