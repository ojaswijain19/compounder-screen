"""Fill company profiles that have no Wikipedia description with SEC registrant data
(SIC industry and business address). Reads the SEC contact from SEC_UA."""
import json, os, subprocess, time, sys
UA=os.environ.get("SEC_UA","").strip()
if "@" not in UA: sys.exit("SEC_UA not set; skipping SEC profile fill.")
p=json.load(open('profiles.json')); u=json.load(open('universe.json'))
miss=[x for x in u if 'ab' not in p.get(x['t'],{}) or p[x['t']].get('src')=='sec']
for x in miss:
    r=subprocess.run(["curl","-sS","-m","30","-A",UA,"--compressed",f"https://data.sec.gov/submissions/CIK{int(x['cik']):010d}.json"],capture_output=True,text=True)
    try: d=json.loads(r.stdout)
    except Exception: continue
    sic=(d.get('sicDescription') or '').strip()
    a=(d.get('addresses') or {}).get('business') or {}
    city=(a.get('city') or '').title(); st=a.get('stateOrCountryDescription') or a.get('stateOrCountry') or ''
    nm=x['name'] if x.get('name') and x['name']!=x['t'] else (d.get('name') or x['t']).title()
    loc=', '.join(v for v in [city,st] if v)
    s=sic[0].lower()+sic[1:] if sic else ''
    q=p.get(x['t'],{})
    q['ab']=f"{nm} is a U.S.-listed company that the SEC classifies under {s}." if s else f"{nm} is a U.S.-listed company."
    q['src']='sec'
    if loc and not q.get('hq'): q['hq']=loc
    p[x['t']]=q; time.sleep(0.12)
json.dump(p,open('profiles.json','w'),ensure_ascii=False)
print('filled from SEC:',len(miss))
