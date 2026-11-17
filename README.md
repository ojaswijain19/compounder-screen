# Compounder Screen

A static stock screener for US equities: S&P 500, S&P MidCap 400 and Nasdaq-100 constituents, ranked on growth, quality, value, balance sheet and trend.

- **Fundamentals:** SEC EDGAR XBRL company facts (10-K / 10-Q, trailing twelve months). Refreshed weekly.
- **Prices:** Yahoo Finance daily chart data. Refreshed every US trading day after the close.
- **Scoring:** percentile ranks across the universe, combined with weights you set in the page.

The site rebuilds itself through GitHub Actions (`.github/workflows/refresh.yml`) and publishes the built page to the `gh-pages` branch, which GitHub Pages serves. If the data fails a sanity check, the run stops and the last good version stays live.

Not investment advice. Figures are as reported (GAAP/IFRS) and unadjusted; foreign filers report annually.
