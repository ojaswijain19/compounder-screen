# Turn SEC facts + Yahoo closes into screener rows.
import json, os, datetime as dt, math
D=lambda s: dt.date.fromisoformat(s)
TODAY=dt.date.today()
OKFORM=('10-K','10-Q','20-F','40-F','10-KT','10-QT')
def dedupe(arr):
    m={}
    for e in arr:
        if not str(e.get('form','')).startswith(OKFORM): continue
        k=(e.get('start'),e['end'])
        if k not in m or e.get('filed','')>m[k].get('filed',''): m[k]=e
    return list(m.values())
def series(F,keys,unit_pref=('USD',)):
    """Return (entries, unit, concept) for the first concept available, preferring most recent end."""
    best=None
    for k in keys:
        if k not in F: continue
        units=F[k]
        u=next((x for x in unit_pref if x in units),None) or next(iter(units))
        arr=dedupe(units[u])
        if not arr: continue
        le=max(e['end'] for e in arr)
        if best is None or le>best[3]: best=(arr,u,k,le)
    return best
def ttm_at(arr,E):
    dur=[e for e in arr if e.get('start')]
    def dd(e): return (D(e['end'])-D(e['start'])).days
    for e in dur:
        if e['end']==E and 350<=dd(e)<=380: return e['val']
    # four quarters
    qs=sorted([e for e in dur if 80<=dd(e)<=100],key=lambda e:e['end'])
    qm={e['end']:e for e in qs}
    if E in qm:
        chain=[qm[E]]; cur=D(E)
        for _ in range(3):
            cand=[e for e in qs if abs((cur-D(e['end'])).days-91)<=12 and D(e['end'])<cur]
            if not cand: break
            c=max(cand,key=lambda e:e['end']); chain.append(c); cur=D(c['end'])
        if len(chain)==4: return sum(e['val'] for e in chain)
    for y in [e for e in dur if e['end']==E and 80<=dd(e)<=290]:
        S=D(y['start']); L=dd(y)
        A=[e for e in dur if 350<=dd(e)<=380 and abs((D(e['end'])-S).days)<=6]
        P=[e for e in dur if abs((D(e['end'])-(D(E)-dt.timedelta(days=364))).days)<=12 and abs(dd(e)-L)<=12]
        if A and P: return A[0]['val']+y['val']-P[0]['val']
    return None
def ttm(arr):
    if not arr: return None,None,None
    ends=sorted({e['end'] for e in arr if e.get('start')},reverse=True)
    for E in ends[:6]:
        v=ttm_at(arr,E)
        if v is not None:
            prev=None
            for E2 in ends:
                if abs((D(E)-D(E2)).days-364)<=15:
                    prev=ttm_at(arr,E2)
                    if prev is not None: break
            return v,prev,E
    return None,None,None
def ttm_on(arr,E):
    """TTM for a concept at a given period end (so all flows share one period)."""
    if not arr: return None
    v=ttm_at(arr,E)
    if v is None:  # allow a few days mismatch
        for e in {x['end'] for x in arr}:
            if abs((D(e)-D(E)).days)<=6:
                v=ttm_at(arr,e)
                if v is not None: break
    return v
def annual_cagr(arr,yrs=3):
    an=[e for e in arr if e.get('start') and 350<=(D(e['end'])-D(e['start'])).days<=380]
    if not an: return None
    a0=max(an,key=lambda e:e['end'])
    old=[e for e in an if abs((D(a0['end'])-D(e['end'])).days-365*yrs)<=25]
    if not old or old[0]['val']<=0 or a0['val']<=0: return None
    return (a0['val']/old[0]['val'])**(1/yrs)-1
def inst(F,keys,date=None,unit='USD'):
    for k in keys:
        if k not in F: continue
        arr=dedupe(F[k].get(unit) or next(iter(F[k].values())))
        arr=[e for e in arr if not e.get('start')] or arr
        if date: 
            m=[e for e in arr if abs((D(e['end'])-D(date)).days)<=6]
            if m: return max(m,key=lambda e:e.get('filed',''))['val']
            continue
        if arr: e=max(arr,key=lambda e:(e['end'],e.get('filed',''))); return e['val']
    return None
def latest_inst_date(F,keys,unit):
    best=None
    for k in keys:
        if k in F:
            arr=F[k].get(unit) or next(iter(F[k].values()))
            for e in arr:
                if not e.get('start') and (best is None or e['end']>best): best=e['end']
    return best
G='us-gaap:'; I='ifrs-full:'
REV=[G+x for x in ["RevenueFromContractWithCustomerExcludingAssessedTax","Revenues","SalesRevenueNet","RevenueFromContractWithCustomerIncludingAssessedTax","RevenuesNetOfInterestExpense"]]+[I+"Revenue",I+"RevenueFromContractsWithCustomers"]
OPI=[G+"OperatingIncomeLoss",I+"ProfitLossFromOperatingActivities"]
NI=[G+"NetIncomeLoss",G+"NetIncomeLossAvailableToCommonStockholdersBasic",G+"ProfitLoss",I+"ProfitLossAttributableToOwnersOfParent",I+"ProfitLoss"]
GP=[G+"GrossProfit",I+"GrossProfit"]
OCF=[G+"NetCashProvidedByUsedInOperatingActivities",G+"NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",I+"CashFlowsFromUsedInOperatingActivities"]
CPX=[G+"PaymentsToAcquirePropertyPlantAndEquipment",G+"PaymentsToAcquireProductiveAssets",G+"PaymentsForCapitalImprovements",I+"PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities",I+"PurchaseOfPropertyPlantAndEquipment"]
DA=[G+"DepreciationDepletionAndAmortization",G+"DepreciationAndAmortization",G+"DepreciationAmortizationAndAccretionNet",G+"OtherDepreciationAndAmortization",I+"DepreciationAndAmortisationExpense",I+"DepreciationAmortisationAndImpairmentLossReversalOfImpairmentLossRecognisedInProfitOrLoss"]
SBC=[G+"ShareBasedCompensation"]
EQ=[G+"StockholdersEquity",G+"StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",I+"EquityAttributableToOwnersOfParent",I+"Equity"]
CASH=[G+"CashAndCashEquivalentsAtCarryingValue",G+"CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",I+"CashAndCashEquivalents"]
STI=[G+"ShortTermInvestments",G+"MarketableSecuritiesCurrent",G+"AvailableForSaleSecuritiesDebtSecuritiesCurrent",I+"CurrentInvestments",I+"ShorttermDeposits"]
def merged(F,keys,unit,order_by_latest=False):
    parts=[]
    for k in keys:
        if k in F and unit in F[k]:
            arr=dedupe(F[k][unit])
            if arr:
                le=max(e['end'] for e in arr)
                parts.append(((le,max(e['val'] for e in arr if e['end']==le)),arr))
    if order_by_latest: parts.sort(key=lambda p:p[0],reverse=True)
    m={}
    for _,arr in parts:
        for e in arr:
            key=(e.get('start'),e['end'])
            if key not in m: m[key]=e
    return list(m.values())
def pick_rev_merged(F):
    units=set()
    for k in REV:
        if k in F: units|=set(F[k])
    unit='USD' if 'USD' in units else (sorted(units)[0] if units else None)
    if not unit: return None
    arr=merged(F,REV,unit,order_by_latest=True)
    v,p,E=ttm(arr)
    if not v: return None
    return (E,v,p,arr,unit,'merged')
def pick_rev(F):
    """Revenue concept with the latest TTM; if several share that end, the largest value."""
    cands=[]
    for k in REV:
        if k not in F: continue
        units=F[k]; u='USD' if 'USD' in units else next(iter(units))
        arr=dedupe(units[u]); v,p,E=ttm(arr)
        if v: cands.append((E,v,p,arr,u,k))
    if not cands: return None
    E=max(c[0] for c in cands)
    c=max([c for c in cands if c[0]==E],key=lambda c:c[1])
    # prefer a prior-year value from any concept on the same basis if missing
    return c
def flow(F,keys,E,unit):
    arr=merged(F,keys,unit)
    return ttm_on(arr,E) if arr else None
def shares(F):
    k='dei:EntityCommonStockSharesOutstanding'
    if k not in F: return None,None
    arr=next(iter(F[k].values()))
    if not arr: return None,None
    lf=max(e.get('filed','') for e in arr)
    grp=[e for e in arr if e.get('filed','')==lf]
    le=max(e['end'] for e in grp)
    vals={}
    for e in grp:
        if e['end']==le: vals[(e['val'])]=1
    return sum(vals.keys()),le
def closes_stats(w,p):
    c=[x[1] for x in (w or [])]
    if len(c)<30: return {}
    c[-1]=p; r={}
    if len(c)>27: r['r6']=p/c[-27]-1
    if len(c)>53: r['r12']=p/c[-53]-1
    if len(c)>=40: r['ma200']=p/(sum(c[-40:])/40)-1
    if len(c)>157: r['r36']=cagr(c[-157],p,3)
    r['spark']=[round(x,2) for x in c[-53:]]
    return r
# ---------- history & durability ----------
def dur(e): return (D(e['end'])-D(e['start'])).days
def annual_map(arr):
    """fiscal-year end -> value from ~1-year duration entries."""
    m={}
    for e in arr:
        if e.get('start') and 350<=dur(e)<=380:
            m[e['end']]=e['val']
    return m
def quarter_map(arr):
    """quarter end -> 3-month value; derives missing quarters from YTD differences."""
    q={}
    for e in arr:
        if e.get('start') and 80<=dur(e)<=100: q[e['end']]=e['val']
    groups={}
    for e in arr:
        if e.get('start') and 80<=dur(e)<=380: groups.setdefault(e['start'],[]).append(e)
    for s,es in groups.items():
        es=sorted(es,key=lambda e:e['end'])
        prev=None
        for e in es:
            if prev is not None:
                gap=(D(e['end'])-D(prev['end'])).days
                if 80<=gap<=100 and e['end'] not in q: q[e['end']]=e['val']-prev['val']
            prev=e
    return q
def share_map(arr):
    """period end -> weighted diluted shares (3-month preferred, else annual). Never differenced."""
    m={}
    for e in arr:
        if e.get('start') and 350<=dur(e)<=380: m[e['end']]=e['val']
    for e in arr:
        if e.get('start') and 80<=dur(e)<=100: m[e['end']]=e['val']
    return m
def ttm_series(q):
    """quarter end -> trailing-4-quarter sum when the 4 quarters are consecutive."""
    ends=sorted(q); out={}
    for i in range(3,len(ends)):
        w=ends[i-3:i+1]
        if all(80<=(D(w[j+1])-D(w[j])).days<=100 for j in range(3)):
            out[ends[i]]=sum(q[x] for x in w)
    return out
def nearest(m,date,tol=10):
    best=None
    for k in m:
        d=abs((D(k)-D(date)).days)
        if d<=tol and (best is None or d<best[0]): best=(d,k)
    return m[best[1]] if best else None
def inst_map(F,keys,unit):
    m={}
    for k in keys:
        if k in F and unit in F[k]:
            for e in dedupe(F[k][unit]):
                if not e.get('start') and e['end'] not in m: m[e['end']]=e['val']
    return m
def debt_at(F,date,unit):
    ltd=inst(F,[G+"LongTermDebt"],date,unit)
    if ltd is None:
        nc=inst(F,[G+"LongTermDebtNoncurrent",G+"LongTermDebtAndCapitalLeaseObligations"],date,unit)
        cu=inst(F,[G+"LongTermDebtCurrent",G+"DebtCurrent"],date,unit)
        ltd=(nc or 0)+(cu or 0) if (nc is not None or cu is not None) else None
    if ltd is None:
        b1=inst(F,[I+"NoncurrentBorrowings"],date,unit); b2=inst(F,[I+"CurrentBorrowings"],date,unit)
        ltd=(b1 or 0)+(b2 or 0) if (b1 is not None or b2 is not None) else inst(F,[I+"Borrowings"],date,unit)
    stb=inst(F,[G+"ShortTermBorrowings"],date,unit)
    return (ltd or 0)+(stb or 0)
def cash_at(F,date,unit):
    c=inst(F,CASH,date,unit) or 0
    sti=[inst(F,[k],date,unit) for k in STI]
    return c+max([v for v in sti if v] or [0])
def cagr(a,b,yrs):
    if a and b and a>0 and b>0: return (b/a)**(1/yrs)-1
    return None
def std(v):
    if len(v)<3: return None
    m=sum(v)/len(v); return (sum((x-m)**2 for x in v)/(len(v)-1))**.5
SHR=[G+'WeightedAverageNumberOfDilutedSharesOutstanding']
def extras(F,x,row,unit,E,P,fin):
    det={}
    rev_arr=merged(F,REV,unit,order_by_latest=True)
    ra=annual_map(rev_arr)
    if row.get('revbad'): return det
    ends=sorted(ra)[-7:]
    if not ends: return det
    def amap(keys):
        a=merged(F,keys,unit); return annual_map(a) if a else {}
    oa=amap(OPI); na=amap(NI); ca=amap(OCF); xa=amap(CPX); sa=amap(SBC); ga=amap(GP)
    sh_arr=merged(F,SHR,'shares') if any(k in F for k in SHR) else []
    if not sh_arr:
        for k in SHR:
            if k in F: sh_arr=dedupe(next(iter(F[k].values())))
    sha=annual_map(sh_arr) if sh_arr else {}
    shq=share_map(sh_arr) if sh_arr else {}
    eqm=inst_map(F,EQ,unit)
    yrs=[]
    for e in ends:
        r=ra[e]; y={'e':e,'rev':r}
        o=oa.get(e); n=na.get(e); c=ca.get(e); cx=xa.get(e); s=sa.get(e); g=ga.get(e)
        if o is not None: y['opi']=o; y['opm']=o/r if r else None
        if n is not None: y['ni']=n
        if c is not None: y['fcf']=c-(cx or 0); y['fcfm']=y['fcf']/r if r else None
        if s is not None: y['sbc']=s
        if g is not None and r: y['gm']=g/r
        shv=nearest(sha,e,15)
        if shv: y['sh']=shv
        eq=nearest(eqm,e,10)
        if o is not None and eq is not None and not fin:
            ic=eq+debt_at(F,e,unit)-cash_at(F,e,unit)
            if ic>0.05*r: y['roic']=o*0.79/ic
        if fin and n is not None and eq and eq>0: y['roe']=n/eq
        yrs.append(y)
    det['y']=yrs
    revs=[y['rev'] for y in yrs]
    if len(revs)>=6: row['cagr5']=cagr(revs[-6],revs[-1],5)
    gr=[revs[i]/revs[i-1]-1 for i in range(1,len(revs)) if revs[i-1]>0]
    if len(gr)>=3:
        last=gr[-5:]; row['gcons']=sum(1 for g in last if g>0)/len(last)
        row['worstg']=min(gr)
    om=[y['opm'] for y in yrs[-5:] if y.get('opm') is not None]
    if len(om)>=3 and not fin:
        row['opm5']=sum(om)/len(om); row['opmsd']=std(om)
        if row.get('opm') is not None and len(yrs)>=4 and yrs[-4].get('opm') is not None:
            row['dopm3']=row['opm']-yrs[-4]['opm']
    rk='roe' if fin else 'roic'
    rv=[y[rk] for y in yrs[-5:] if y.get(rk) is not None]
    if rv: row['ret5']=sum(rv)/len(rv)
    if row.get('rg') is not None and row.get('cagr3') is not None: row['accel']=row['rg']-row['cagr3']
    # share count change, 3y annualised (quarterly if available)
    qe=sorted(shq)
    if qe:
        last=qe[-1]; old=nearest(shq,(D(last)-dt.timedelta(days=1095)).isoformat(),25)
        if old: row['shch3']=cagr(old,shq[last],3)
    if 'shch3' not in row and len(yrs)>=4 and yrs[-1].get('sh') and yrs[-4].get('sh'):
        row['shch3']=cagr(yrs[-4]['sh'],yrs[-1]['sh'],3)
    # SBC-adjusted FCF
    if row.get('fcf') is not None and not fin:
        s=row.get('sbc',0) or 0
        fa=row['fcf']-s*row['rev']; row['fcfa']=fa; row['fcfam']=fa/row['rev']
        if row.get('mc'): row['fya']=fa/row['mc']
    # quarterly revenue + yoy, op margin
    qr=quarter_map(rev_arr); qo=quarter_map(merged(F,OPI,unit)) if any(k in F for k in OPI) else {}
    qends=sorted(qr)[-13:]
    qs=[]
    for e in qends[-12:]:
        d={'e':e,'rev':qr[e]}
        py=nearest(qr,(D(e)-dt.timedelta(days=364)).isoformat(),12)
        if py and py>0: d['yoy']=qr[e]/py-1
        o=qo.get(e)
        if o is not None and qr[e]: d['opm']=o/qr[e]
        qs.append(d)
    det['q']=qs
    # valuation history: P/S at each quarter end from weekly prices x diluted shares / TTM revenue
    w=P.get('w') or []
    if w and unit=='USD' and P.get('cur')=='USD' and not fin:
        ttmr=ttm_series(qr)
        pts=[]
        wd=[(dt.datetime.utcfromtimestamp(a).date(),c) for a,c in w]
        for e,tr in sorted(ttmr.items()):
            de=D(e)
            if de<wd[0][0]: continue
            pr=min(wd,key=lambda z:abs((z[0]-de).days))
            if abs((pr[0]-de).days)>10: continue
            shv=nearest(shq,e,15)
            if shv and shv>0 and tr>0: pts.append([e,round(pr[1]*shv/tr,3)])
        if pts:
            med=sorted(p[1] for p in pts)[len(pts)//2]
            pts=[p for p in pts if p[1]>0.05 and med/5<p[1]<med*5]
        if len(pts)>=8 and row.get('ps'):
            hist=[p[1] for p in pts]
            row['psh']=sum(1 for v in hist if v<row['ps'])/len(hist)
            srt=sorted(hist); row['psmed']=srt[len(srt)//2]
        det['ps']=pts
    # cyclical-peak flag
    cyc=(row.get('worstg') is not None and row['worstg']<=-0.10)
    if cyc and not fin and x.get('sector')!='Real Estate' and (row.get('opm5') or 0)>0.02:
        reasons=[]
        opm,opm5,sd=row.get('opm'),row.get('opm5'),row.get('opmsd') or 0
        hot=opm is not None and opm>opm5+max(0.08,1.5*sd) and opm>1.5*opm5
        if hot: reasons.append(f'operating margin {opm*100:.0f}% vs a 5-year average of {opm5*100:.0f}%')
        if (row.get('rg') or 0)>0.5 and opm is not None and opm>opm5+0.04: reasons.append(f'revenue up {row["rg"]*100:.0f}% in a year')
        if reasons: row['peak']=1; row['peakwhy']=' and '.join(reasons)
        row['cyc']=1
    # price history (every 2nd week) for charts
    if w: det['px']=[[dt.datetime.utcfromtimestamp(a).strftime('%Y-%m-%d'),c] for a,c in w[::2]]+([[dt.datetime.utcfromtimestamp(w[-1][0]).strftime('%Y-%m-%d'),w[-1][1]]] if len(w)%2==0 else [])
    return det
# ---------- end history ----------

BANKISH={'Regional Banks','Diversified Banks','Property & Casualty Insurance','Life & Health Insurance','Multi-line Insurance','Reinsurance','Consumer Finance','Mortgage REITs','Commercial & Residential Mortgage Finance','Investment Banking & Brokerage','Multi-Sector Holdings','Diversified Financial Services','Asset Management & Custody Banks'}
def bank_like(x):
    if x.get('sub'): return x['sub'] in BANKISH
    return x['t'] in {'SOFI','NU'} or (x['sector']=='Financials')
u=json.load(open('universe.json')); px=json.load(open('prices.json'))
held=set() if os.environ.get("PUBLIC")=="1" else {"MSFT","UNH","NVDA","ASML","META","NBIS","CRWD","OSCR","AMZN","ANET","PLTR","ZETA","NOW","KRYS","MELI","BABA","ISRG","SOFI","VST","TEM","CRWV","HIMS","NU","CRSP","LI","XPEV","MSTR","FLNC"}
watch=set() if os.environ.get("PUBLIC")=="1" else {"AVGO","ETN","GEV","MA"}
rows=[]; issues={}; details={}
for x in u:
    t=x['t']; row=dict(t=t,n=x['name'],s=x['sector'] or '',sub=x.get('sub',''),ix=x['idx'],cik=x['cik'])
    if t in held: row['own']='held'
    elif t in watch: row['own']='watch'
    P=px.get(t,{})
    if 'p' in P:
        row['p']=P['p']; row['hi']=P.get('hi'); row['off']=(P['p']/P['hi']-1) if P.get('hi') else None
        row.update(closes_stats(P.get('w'),P['p']))
    f=f'facts/{t}.json'
    if not os.path.exists(f): issues[t]='no facts'; rows.append(row); continue
    F=json.load(open(f))
    pr=pick_rev_merged(F) or pick_rev(F)
    if not pr: issues[t]='no revenue'; rows.append(row); continue
    E,rev,revp,arr,unit,rk=pr
    row.update(rev=rev,cur=unit,pe_end=E)
    if revp and revp>0: row['rg']=rev/revp-1
    allan=merged(F,REV,unit,order_by_latest=True)
    byend={}
    for e in allan:
        if e.get('start') and 350<=(D(e['end'])-D(e['start'])).days<=380:
            if e['end'] not in byend or e['val']>byend[e['end']]['val']: byend[e['end']]=e
    row['cagr3']=annual_cagr(list(byend.values()))
    opi=flow(F,OPI,E,unit)
    if opi is None:
        opi=flow(F,[G+'IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest'],E,unit)
        if opi is not None: row['opx']=1
    ni=flow(F,NI,E,unit); gp=flow(F,GP,E,unit)
    ocf=flow(F,OCF,E,unit); cpx=flow(F,CPX,E,unit); da=flow(F,DA,E,unit); sbc=flow(F,SBC,E,unit)
    if opi is not None: row['opm']=opi/rev
    if gp is None:
        cor=flow(F,[G+'CostOfRevenue',G+'CostOfGoodsAndServicesSold'],E,unit)
        if cor is not None and 0<cor<rev: gp=rev-cor
    if gp is not None: row['gm']=gp/rev
    if ni is not None: row['nm']=ni/rev
    if ocf is not None:
        fcf=ocf-(cpx or 0); row['fcf']=fcf; row['fcfm']=fcf/rev
    if sbc is not None: row['sbc']=sbc/rev
    bd=latest_inst_date(F,EQ,unit)
    eq=inst(F,EQ,bd,unit) if bd else None
    # debt at the balance-sheet date
    debt=None
    if bd:
        ltd=inst(F,[G+"LongTermDebt"],bd,unit)
        if ltd is None:
            nc=inst(F,[G+"LongTermDebtNoncurrent",G+"LongTermDebtAndCapitalLeaseObligations"],bd,unit)
            cu=inst(F,[G+"LongTermDebtCurrent",G+"DebtCurrent"],bd,unit)
            ltd=(nc or 0)+(cu or 0) if (nc is not None or cu is not None) else None
        if ltd is None:
            b1=inst(F,[I+"NoncurrentBorrowings"],bd,unit); b2=inst(F,[I+"CurrentBorrowings"],bd,unit)
            ltd=(b1 or 0)+(b2 or 0) if (b1 is not None or b2 is not None) else inst(F,[I+"Borrowings"],bd,unit)
        stb=inst(F,[G+"ShortTermBorrowings"],bd,unit)
        debt=(ltd or 0)+(stb or 0) if (ltd is not None or stb is not None) else 0.0
        cash=(inst(F,CASH,bd,unit) or 0)
        sti=[inst(F,[k],bd,unit) for k in STI]; cash+=max([v for v in sti if v] or [0])
        row['bs_end']=bd; row['netdebt']=debt-cash
        fin=bank_like(x)
        if opi is not None and not fin:
            ic=(eq or 0)+debt-cash
            if eq is not None and ic>0.05*rev: row['roic']=opi*0.79/ic
        if ni is not None and eq and eq>0: row['roe']=ni/eq
        if da is None:
            dep=flow(F,[G+'Depreciation'],E,unit); am=flow(F,[G+'AmortizationOfIntangibleAssets'],E,unit)
            if dep is not None: da=dep+(am or 0)
        if opi is not None and da is not None:
            ebitda=opi+da; row['ebitda']=ebitda
            if ebitda>0: row['nde']=(debt-cash)/ebitda
        if 'nde' not in row and opi is not None and opi>0:
            row['nde']=(debt-cash)/opi; row['ndx']=1
    # valuation (USD reporters only)
    sh,sd=shares(F)
    if not sh:
        w=F.get(G+'WeightedAverageNumberOfDilutedSharesOutstanding')
        if w:
            arr=[e for e in dedupe(next(iter(w.values()))) if e.get('start') and 80<=(D(e['end'])-D(e['start'])).days<=100]
            if arr: sh=max(arr,key=lambda e:e['end'])['val']; row['shx']=1
    if t=='BRK-B':
        sh=None
        w=F.get(G+'WeightedAverageNumberOfDilutedSharesOutstanding')
        if w: sh=max(dedupe(next(iter(w.values()))),key=lambda e:e['end'])['val']*1500
    if sh and 'p' in row and unit=='USD' and P.get('cur')=='USD':
        mc=sh*row['p']; row['mc']=mc
        if 'fcf' in row: row['fy']=row['fcf']/mc
        if ni is not None: row['ey']=ni/mc
        row['ps']=mc/rev
    assets=inst(F,[G+'Assets',I+'Assets'],None,unit)
    if (assets and rev<0.03*assets and not bank_like(x)) or (row.get('ps') or 0)>60:
        row['revbad']=1
        for k in ('rg','cagr3','opm','gm','nm','fcfm','sbc','ps'): row.pop(k,None)
    fin=bank_like(x)
    row['bank']=1 if fin else None
    if fin:
        for k in ('fcf','fcfm','fy','nde','opm'): row.pop(k,None)
    row['ret']=row.get('roe') if fin else row.get('roic')
    try:
        det=extras(F,x,row,unit,E,P,fin)
    except Exception as ex:
        det={}; issues[t]='history: '+str(ex)[:60]
    if fin: row.pop('fya',None)
    if det: details[t]=det
    rows.append(row)
def clean(v):
    if isinstance(v,float):
        if math.isnan(v) or math.isinf(v): return None
        return float(f"{v:.4g}")
    return v
rows=[{k:clean(v) for k,v in r.items() if v is not None} for r in rows]
meta=dict(filings_to=max(r['pe_end'] for r in rows if 'pe_end' in r),built=dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),px_date=max(dt.datetime.utcfromtimestamp(v['ts']).strftime('%Y-%m-%d') for v in px.values() if 'ts' in v),n=len(rows))
json.dump(dict(meta=meta,rows=rows),open('data.json','w'),separators=(',',':'))
def cl(o):
    if isinstance(o,dict): return {k:cl(v) for k,v in o.items() if v is not None}
    if isinstance(o,list): return [cl(v) for v in o]
    return clean(o)
json.dump(cl(details),open('detail.json','w'),separators=(',',':'))
print(meta, 'issues',len(issues),list(issues.items())[:15])
print('with mc',sum('mc' in r for r in rows),'with rg',sum('rg' in r for r in rows),'with roic',sum('roic' in r for r in rows),'with fy',sum('fy' in r for r in rows))
