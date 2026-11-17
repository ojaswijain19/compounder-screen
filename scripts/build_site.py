"""Wrap the screen page in a full HTML document for static hosting."""
import os
d=open('data.json').read()
t=open('template.html').read().replace('/*DATA*/null',d)
i=t.index('<div class="page">')
head,body=t[:i],t[i:]
base=("<style>:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}"
      "body{margin:0;font:14px -apple-system,BlinkMacSystemFont,sans-serif}img{max-width:100%}[hidden]{display:none!important}</style>")
desc="US stocks from the S&P 500, MidCap 400 and Nasdaq-100 ranked on growth, quality, value, balance sheet and trend, built from SEC filings."
html=("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
      "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1,viewport-fit=cover\">"
      f"<meta name=\"description\" content=\"{desc}\"><meta property=\"og:title\" content=\"Compounder Screen\"><meta property=\"og:description\" content=\"{desc}\">"
      "<link rel=\"icon\" href=\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='6' fill='%2396661F'/%3E%3Cpath d='M7 22l6-6 4 4 8-9' stroke='%23FBFAF4' stroke-width='3' fill='none' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E\">"
      f"{base}{head}</head><body>{body}</body></html>")
os.makedirs('../site',exist_ok=True)
open('../site/index.html','w').write(html)
open('../site/data.json','w').write(d)
print('site/index.html',len(html))
