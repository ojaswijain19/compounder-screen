"""Company profiles from Wikipedia: short description, founding year, HQ, source link.
Run occasionally (profiles change rarely); output profiles.json is committed."""
import json, re, time, subprocess, urllib.parse, sys, os
from bs4 import BeautifulSoup
UA="CompounderScreen/1.0 (https://ojaswijain19.github.io/compounder-screen/)"
u=json.load(open('universe.json'))
want={x['t'] for x in u}
info={}
def tab(fname,idx):
    s=BeautifulSoup(open(fname).read(),'lxml')
    for t in s.find_all('table',class_='wikitable'):
        hdr=[th.get_text(' ',strip=True) for th in t.find('tr').find_all(['th','td'])]
        if 'Symbol' not in hdr: continue
        ci={h:i for i,h in enumerate(hdr)}
        for tr in t.find_all('tr')[1:]:
            tds=tr.find_all(['td','th'])
            if len(tds)<len(hdr)-1: continue
            sym=tds[ci['Symbol']].get_text(strip=True).replace('.','-')
            sec=tds[ci['Security']]; a=sec.find('a')
            d=info.setdefault(sym,{})
            h=a.get('href','') if a else ''
            if '/wiki/' in h: d['wt']=urllib.parse.unquote(h.split('/wiki/',1)[1])
            if 'Headquarters Location' in ci: d['hq']=tds[ci['Headquarters Location']].get_text(' ',strip=True)
            if 'Founded' in ci: d['fd_raw']=tds[ci['Founded']].get_text(' ',strip=True)
        break
tab('sp500.html','SP500'); tab('sp400.html','SP400')
manual={"ASML":"ASML_Holding","NBIS":"Nebius_Group","OSCR":"Oscar_Health","ZETA":"Zeta_Global","KRYS":"Krystal_Biotech","MELI":"Mercado_Libre","BABA":"Alibaba_Group","SOFI":"SoFi","TEM":"Tempus_AI","CRWV":"CoreWeave","HIMS":"Hims_%26_Hers_Health","NU":"Nubank","CRSP":"CRISPR_Therapeutics","LI":"Li_Auto","XPEV":"XPeng","MSTR":"Strategy_Inc","FLNC":"Fluence_Energy","AVGO":"Broadcom","ETN":"Eaton_Corporation","GEV":"GE_Vernova","MA":"Mastercard","GOOG":"Alphabet_Inc.","ALAB":"Astera_Labs","ARM":"Arm_Holdings","CCEP":"Coca-Cola_Europacific_Partners","FER":"Ferrovial","PDD":"PDD_Holdings","RKLB":"Rocket_Lab","SHOP":"Shopify","TRI":"Thomson_Reuters","SPCX":"SpaceX","ALNY":"Alnylam_Pharmaceuticals"}
for k,v in manual.items():
    d=info.setdefault(k,{})
    if 'wt' not in d: d['wt']=urllib.parse.unquote(v)
def get(url):
    for att in range(4):
        r=subprocess.run(["curl","-sS","-m","25","-A",UA,"-w","\n%{http_code}",url],capture_output=True,text=True)
        body,_,code=r.stdout.rpartition("\n")
        if code=="404": return ""
        if code=="200" and not body.lstrip().startswith("<!DOCTYPE"): return body
        time.sleep(3+att*5)
    return ""
def years(s):
    ys=[int(y) for y in re.findall(r'(?<!\d)(1[6-9]\d\d|20[0-2]\d)(?!\d)',s or '')]
    return min(ys) if ys else None
def clean_wiki(s):
    s=re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]*)\]\]',r'\1',s); s=re.sub(r'\{\{[^{}]*\}\}','',s); s=re.sub(r'<[^>]+>','',s)
    return re.sub(r'\s+',' ',s).strip(' ,;')
def strip_templates(s):
    out=[];depth=0;i=0
    while i<len(s):
        if s.startswith('{{',i): depth+=1; i+=2; continue
        if s.startswith('}}',i) and depth: depth-=1; i+=2; continue
        if depth==0: out.append(s[i])
        i+=1
    return ''.join(out)
def strip_files(s):
    out=[];i=0
    while i<len(s):
        m=re.match(r'\[\[(?:File|Image):',s[i:],re.I)
        if m:
            depth=0;j=i
            while j<len(s):
                if s.startswith('[[',j): depth+=1; j+=2; continue
                if s.startswith(']]',j):
                    depth-=1; j+=2
                    if depth==0: break
                    continue
                j+=1
            i=j; continue
        out.append(s[i]); i+=1
    return ''.join(out)
def lead_text(raw):
    raw=strip_files(raw)
    s=re.sub(r'<!--.*?-->','',raw,flags=re.S)
    s=re.sub(r'<ref[^>/]*/>','',s); s=re.sub(r'<ref[^>]*>.*?</ref>','',s,flags=re.S)
    s=strip_templates(s)
    s=re.sub(r'\[\[(?:File|Image):[^\]]*(?:\[\[[^\]]*\]\][^\]]*)*\]\]','',s)
    s=re.sub(r'\{\|.*?\|\}','',s,flags=re.S)
    paras=[p.strip() for p in s.split('\n') if p.strip() and not p.strip().startswith(('|','!','{','}','[[Category','__'))]
    txt=' '.join(paras[:3])
    txt=re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]",r'\1',txt); txt=re.sub(r"\[https?://\S+ ([^\]]*)\]",r'\1',txt)
    txt=re.sub(r"'''?",'',txt); txt=re.sub(r'<[^>]+>','',txt); txt=txt.replace('&nbsp;',' ')
    txt=re.sub(r'\(\s*[;,]?\s*\)','',txt); txt=re.sub(r'\s+',' ',txt).strip()
    txt=re.sub(r'\s+([,.;])',r'\1',txt)
    return txt
def trim(ex):
    ex=re.sub(r'\s*\([^()]*(?:NYSE|NASDAQ|Nasdaq|/|ⓘ|listen|pronounced|stylized|abbreviated|commonly referred)[^()]*\)','',ex)
    ex=re.sub(r'\s+',' ',ex).strip()
    prot=re.sub(r'\b(Inc|Co|Corp|Ltd|Jr|Sr|St|Mr|Dr|No|vs|U\.S|N\.A|[A-Z])\.',lambda m:m.group(0).replace('.','§'),ex)
    sents=[x.replace('§','.') for x in re.split(r'(?<=[.!?])\s+(?=[A-Z])',prot)]
    out=''
    for i,x in enumerate(sents):
        if out and (len(out)+len(x)>420 or (i>=2 and len(out)>200)): break
        out=(out+' '+x).strip()
        if i==0 and len(out)>=170: break
    return out
prof={} if os.environ.get('FRESH') else (json.load(open('profiles.json')) if os.path.exists('profiles.json') else {})
names={x['t']:x['name'] for x in u}
def name_titles(n):
    base=re.sub(r'\b(Inc\.?|Corporation|Corp\.?|Company|Co\.|Holdings?|Group|plc|N\.V\.|Ltd\.?|Class [A-C])\b','',n).strip(' ,.')
    return [n,base,base+' (company)',base+' Inc.',base+' Corporation']
BIZ=re.compile(r'\b(company|corporation|conglomerate|manufacturer|provider|operator|trust|REIT|bank|insurer|firm|holding|developer|producer|retailer|maker|chain|business|organization|lessor|utility)\b',re.I)
for t in want:
    info.setdefault(t,{}).setdefault('wt',names.get(t,t))
todo=[t for t in sorted(want) if t not in prof or 'ab' not in prof[t]]
print('to fetch',len(todo),'missing title',[t for t in want if t not in info or not info[t].get('wt')])
for i,t in enumerate(todo):
    d=info[t]; title=d['wt']
    raw=get('https://en.wikipedia.org/w/index.php?title='+urllib.parse.quote(title.replace(' ','_'),safe='')+'&action=raw&section=0')
    m=re.match(r'\s*#REDIRECT\s*\[\[([^\]|#]+)',raw,re.I)
    if m:
        title=m.group(1).strip(); raw=get('https://en.wikipedia.org/w/index.php?title='+urllib.parse.quote(title.replace(' ','_'),safe='')+'&action=raw&section=0')
    p={'wt':title.replace('_',' ')}
    lt=lead_text(raw)
    trusted=bool(d.get('hq') or d.get('fd_raw') or t in manual) and len(lt)>60 and 'may refer to' not in lt[:200]
    if not trusted and (len(lt)<=40 or not BIZ.search(lt[:400])):
        for nt in name_titles(names.get(t,'')):
            r2=get('https://en.wikipedia.org/w/index.php?title='+urllib.parse.quote(nt.replace(' ','_'),safe='')+'&action=raw&section=0')
            m=re.match(r'\s*#REDIRECT\s*\[\[([^\]|#]+)',r2,re.I)
            if m: nt=m.group(1).strip(); r2=get('https://en.wikipedia.org/w/index.php?title='+urllib.parse.quote(nt.replace(' ','_'),safe='')+'&action=raw&section=0')
            l2=lead_text(r2)
            if len(l2)>40 and BIZ.search(l2[:400]) and 'may refer to' not in l2[:200]:
                raw,lt,title=r2,l2,nt; p['wt']=nt; break
    if trusted or (len(lt)>40 and BIZ.search(lt[:400])): p['ab']=trim(lt)
    fd=years(d.get('fd_raw'))
    m=re.search(r'^\|\s*(?:founded|foundation|established|formation)\s*=\s*(.+)$',raw,re.M|re.I)
    if m:
        y=years(m.group(1)); fd=min(fd,y) if fd and y else (fd or y)
    if fd: p['fd']=fd
    hq=d.get('hq')
    if not hq:
        m=re.search(r'^\|\s*(?:hq_location_city|hq_location|location_city|headquarters)\s*=\s*(.+)$',raw,re.M|re.I)
        if m: hq=clean_wiki(m.group(1))
    if hq: p['hq']=re.sub(r'\s+,',',',hq)[:60]
    prof[t]=p
    if i%50==0: print(i,t,p.get('fd'),(p.get('ab') or '')[:70],flush=True); json.dump(prof,open('profiles.json','w'))
    time.sleep(0.05)
json.dump(prof,open('profiles.json','w'),ensure_ascii=False)
print('done',len(prof),'with about',sum('ab' in p for p in prof.values()),'with founded',sum('fd' in p for p in prof.values()))
