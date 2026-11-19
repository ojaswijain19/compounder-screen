"""Build a user's daily digest (pre-market note or after-close recap) from data.json + detail.json.
Plain text, works for Telegram and email. Usage: python digest.py holdings.json [premarket|close]"""
import json, sys, datetime as dt
def money(v):
    a=abs(v); s='-' if v<0 else ''
    return s+'$'+(f'{a/1e6:.2f}M' if a>=1e6 else f'{a:,.0f}')
def pc(v,d=1): return f"{'+' if v>=0 else ''}{v*100:.{d}f}%"
def build(holdings,data,detail,mode='close',site='https://ojaswijain19.github.io/compounder-screen/'):
    R={r['t']:r for r in data['rows']}
    H=[]
    for h in holdings:
        r=R.get(h['t'])
        if not r or 'p' not in r: continue
        v=h['q']*r['p']; day=h['q']*(r['p']-r['pp']) if r.get('pp') else None
        H.append(dict(t=h['t'],r=r,v=v,day=day,cost=h['q']*h.get('c',0)))
    if not H: return None
    tv=sum(x['v'] for x in H); td=sum(x['day'] or 0 for x in H); tc=sum(x['cost'] for x in H if x['cost'])
    pdate=max((x['r'].get('pd') or '') for x in H) or data['meta']['px_date']
    when=dt.date.fromisoformat(pdate).strftime('%a %d %b')
    movers=sorted([x for x in H if x['r'].get('d1') is not None],key=lambda x:x['r']['d1'])
    lines=[]
    if mode=='close':
        lines.append(f"US close recap · {when}")
        lines.append(f"Portfolio {money(tv)} · {('+' if td>=0 else '')}{money(td).lstrip('-') if td>=0 else money(td)} ({pc(td/(tv-td) if tv-td else 0)}) on the day")
        if tc: lines.append(f"Unrealised P&L {money(tv-tc)} ({pc(tv/tc-1)})")
        if movers:
            up=[x for x in movers[::-1] if x['r']['d1']>0][:3]; dn=[x for x in movers if x['r']['d1']<0][:3]
            if up: lines.append("Best: "+", ".join(f"{x['t']} {pc(x['r']['d1'])}" for x in up))
            if dn: lines.append("Worst: "+", ".join(f"{x['t']} {pc(x['r']['d1'])}" for x in dn))
    else:
        lines.append(f"Before the US open · prices as of {when} close")
        lines.append(f"Portfolio {money(tv)}" + (f" · unrealised {pc(tv/tc-1)}" if tc else ""))
        big=[x for x in movers if abs(x['r']['d1'])>=0.04]
        if big: lines.append("Big moves last session: "+", ".join(f"{x['t']} {pc(x['r']['d1'])}" for x in sorted(big,key=lambda x:-abs(x['r']['d1']))[:5]))
    # official filings in the last 2 days
    since=(dt.date.fromisoformat(pdate)-dt.timedelta(days=2)).isoformat()
    fl=[]
    for x in H:
        for f in (detail.get(x['t'],{}).get('fl') or []):
            if f['d']>=since and f['f'] not in ('4','144'): fl.append((f['d'],x['t'],f))
    ins=sum(1 for x in H for f in (detail.get(x['t'],{}).get('fl') or []) if f['d']>=since and f['f']=='4')
    if fl:
        lines.append(""); lines.append("New SEC filings:")
        for d,t,f in sorted(fl,key=lambda z:z[0],reverse=True)[:8]: lines.append(f"• {t} {f['f']}: {f['t']}")
    if ins: lines.append(f"• {ins} insider-trade filing{'s' if ins>1 else ''} (Form 4) across your holdings")
    flags=[x['t'] for x in H if x['r'].get('peak')]
    if flags: lines.append(""); lines.append("Cycle-peak watch: "+", ".join(flags))
    lines.append(""); lines.append(f"Full view: {site}#portfolio")
    lines.append("Data from SEC filings and daily prices. Not investment advice.")
    return "\n".join(lines)
if __name__=='__main__':
    h=json.load(open(sys.argv[1])); mode=sys.argv[2] if len(sys.argv)>2 else 'close'
    print(build(h,json.load(open('data.json')),json.load(open('detail.json')),mode))
