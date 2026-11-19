"""Recent official SEC filings per company (EDGAR submissions API). Reads the SEC contact from SEC_UA."""
import json, os, sys, time, subprocess, datetime as dt, concurrent.futures as cf
UA=os.environ.get("SEC_UA","").strip()
if "@" not in UA or "github" in UA.lower(): sys.exit("Set SEC_UA to 'Name email' (no 'github').")
ITEMS={"1.01":"Entered a material agreement","1.02":"Ended a material agreement","1.03":"Bankruptcy or receivership","1.05":"Cybersecurity incident",
"2.01":"Completed an acquisition or sale of assets","2.02":"Reported results","2.03":"Took on a material financial obligation","2.04":"Triggering event on an obligation",
"2.05":"Exit or restructuring costs","2.06":"Material impairment","3.01":"Listing or delisting notice","3.02":"Unregistered sale of shares","3.03":"Change to shareholder rights",
"4.01":"Changed auditor","4.02":"Prior financials should no longer be relied on","5.01":"Change in control","5.02":"Director or officer change",
"5.03":"Amended articles or bylaws","5.07":"Shareholder vote results","5.08":"Shareholder nomination dates","7.01":"Regulation FD disclosure","8.01":"Other material event","9.01":"Financial statements and exhibits"}
FORMS={"10-K":"Annual report","10-Q":"Quarterly report","8-K":"Current report","4":"Insider trade","S-1":"Registration statement","DEF 14A":"Proxy statement",
"SC 13D":"Activist stake (13D)","SC 13G":"Large passive stake (13G)","SCHEDULE 13D":"Activist stake (13D)","SCHEDULE 13G":"Large passive stake (13G)",
"20-F":"Annual report (foreign issuer)","6-K":"Foreign issuer report","40-F":"Annual report (Canadian issuer)","S-3":"Shelf registration","424B5":"Prospectus supplement (securities offering)","144":"Proposed insider sale"}
KEEP=set(FORMS)|{"10-K/A","10-Q/A","8-K/A"}
u=json.load(open("universe.json")); cut=(dt.date.today()-dt.timedelta(days=120)).isoformat()
def get(x):
    url=f"https://data.sec.gov/submissions/CIK{int(x['cik']):010d}.json"
    for att in range(4):
        r=subprocess.run(["curl","-sS","-m","30","-A",UA,"--compressed",url],capture_output=True,text=True)
        if r.stdout.startswith("{"): break
        time.sleep(2+att*3)
    else: return x['t'],None
    rec=json.loads(r.stdout).get("filings",{}).get("recent",{})
    out=[]; cik=int(x['cik'])
    for i,form in enumerate(rec.get("form",[])):
        d=rec["filingDate"][i]
        if d<cut: break
        if form not in KEEP: continue
        acc=rec["accessionNumber"][i]; doc=rec["primaryDocument"][i]
        items=[s.strip() for s in (rec.get("items",[""]*len(rec["form"]))[i] or "").split(",") if s.strip()]
        base=form.replace("/A","")
        desc=FORMS.get(base,form)
        if base=="8-K":
            labs=[ITEMS[k] for k in items if k in ITEMS and k!="9.01"]
            if labs: desc="; ".join(labs)
        e={"d":d,"f":form,"t":desc,"u":f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace('-','')}/{doc}"}
        if items: e["i"]=items
        out.append(e)
        if len(out)>=25: break
    return x['t'],out
res={}
with cf.ThreadPoolExecutor(4) as ex:
    for t,o in ex.map(get,u):
        if o is not None: res[t]=o
json.dump(res,open("filings.json","w"),separators=(",",":"))
print("filings for",len(res),"companies;",sum(len(v) for v in res.values()),"filings")
if len(res)<0.8*len(u): sys.exit("Too many filings fetch failures")
