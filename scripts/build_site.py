"""Build the static site: index.html (full document) + data.json + detail.json."""
import os, shutil
t=open('template.html').read()
sb_url=os.environ.get('SUPABASE_URL','').strip(); sb_key=os.environ.get('SUPABASE_ANON_KEY','').strip()
cfg={'data':'data.json','detail':'detail.json'}
if sb_url and sb_key: cfg['sb']={'url':sb_url,'key':sb_key}
import json as _j
t=t.replace('/*CONFIG*/','window.SCREEN_CFG='+_j.dumps(cfg)+';')
i=t.index('<div class="page">')
head,body=t[:i],t[i:]
base=("<style>:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}"
      "body{margin:0;font:14px -apple-system,BlinkMacSystemFont,sans-serif}img{max-width:100%}[hidden]{display:none!important}</style>")
desc="US stocks from the S&P 500, MidCap 400 and Nasdaq-100 ranked on growth, durability, trajectory, value, balance sheet and trend, built from SEC filings."
html=("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
      "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1,viewport-fit=cover\">"
      f"<meta name=\"description\" content=\"{desc}\"><meta property=\"og:title\" content=\"Compounder Screen\"><meta property=\"og:description\" content=\"{desc}\">"
      "<link rel=\"icon\" href=\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='6' fill='%2396661F'/%3E%3Cpath d='M7 22l6-6 4 4 8-9' stroke='%23FBFAF4' stroke-width='3' fill='none' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E\">"
      f"{base}{head}</head><body>{body}</body></html>")
out=os.environ.get('OUT','../site')
os.makedirs(out,exist_ok=True)
open(f'{out}/index.html','w').write(html)
for f in ('data.json','detail.json'): shutil.copy(f,f'{out}/{f}')
print(out, len(html))
