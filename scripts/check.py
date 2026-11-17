"""Fail the run (and keep the last good site) if the data looks broken."""
import json, sys, datetime as dt
d=json.load(open('data.json')); rows=d['rows']; m=d['meta']
mc=sum('mc' in r for r in rows); rg=sum('rg' in r for r in rows)
age=(dt.date.today()-dt.date.fromisoformat(m['px_date'])).days
R={r['t']:r for r in rows}
core=all(all(k in R.get(t,{}) for k in ('rev','rg','mc')) for t in ('MSFT','AAPL','NVDA'))
print(f"rows={len(rows)} with_mc={mc} with_rg={rg} px_date={m['px_date']} age={age}d core_ok={core}")
if mc<850 or rg<800 or age>5 or not core: sys.exit("Sanity check failed; not deploying.")
