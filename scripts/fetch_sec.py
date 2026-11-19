# Pull SEC companyfacts and keep only the concepts the screener needs.
import json, os, sys, time, subprocess, concurrent.futures as cf
import os
UA=os.environ.get("SEC_UA","").strip()
if "@" not in UA or "github" in UA.lower():
    sys.exit("Set the SEC_UA repository secret to 'CompounderScreen your@email' (SEC requires a contact email and rejects user agents that mention GitHub).")
KEEP={"us-gaap":["RevenueFromContractWithCustomerExcludingAssessedTax","Revenues","SalesRevenueNet","RevenueFromContractWithCustomerIncludingAssessedTax","RevenuesNetOfInterestExpense","InterestAndDividendIncomeOperating",
 "OperatingIncomeLoss","NetIncomeLoss","GrossProfit","NetCashProvidedByUsedInOperatingActivities","NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
 "PaymentsToAcquirePropertyPlantAndEquipment","PaymentsToAcquireProductiveAssets","PaymentsForCapitalImprovements","DepreciationDepletionAndAmortization","DepreciationAndAmortization","DepreciationAmortizationAndAccretionNet",
 "StockholdersEquity","StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest","LongTermDebt","LongTermDebtNoncurrent","LongTermDebtCurrent","DebtCurrent","ShortTermBorrowings","LongTermDebtAndCapitalLeaseObligations","OperatingLeaseLiabilityNoncurrent",
 "CashAndCashEquivalentsAtCarryingValue","CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents","ShortTermInvestments","MarketableSecuritiesCurrent","AvailableForSaleSecuritiesDebtSecuritiesCurrent",
 "WeightedAverageNumberOfDilutedSharesOutstanding","ProfitLoss","NetIncomeLossAvailableToCommonStockholdersBasic","NetIncomeLossAvailableToCommonStockholdersDiluted","Depreciation","AmortizationOfIntangibleAssets","OtherDepreciationAndAmortization","CostOfRevenue","CostOfGoodsAndServicesSold","CommercialPaper","LongTermDebtFairValue","ResearchAndDevelopmentExpense","ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost","SellingGeneralAndAdministrativeExpense","SellingAndMarketingExpense","GeneralAndAdministrativeExpense","OperatingExpenses","CostsAndExpenses","NonoperatingIncomeExpense","InterestExpense","InterestExpenseNonoperating","CostOfGoodsAndServicesSoldExcludingDepreciationDepletionAndAmortization","IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments","ShareBasedCompensation","IncomeTaxExpenseBenefit","IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest","Assets"],
 "ifrs-full":["Revenue","RevenueFromContractsWithCustomers","ProfitLossFromOperatingActivities","ProfitLoss","ProfitLossAttributableToOwnersOfParent","GrossProfit","CashFlowsFromUsedInOperatingActivities","PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities","PurchaseOfPropertyPlantAndEquipment","DepreciationAndAmortisationExpense","DepreciationAmortisationAndImpairmentLossReversalOfImpairmentLossRecognisedInProfitOrLoss",
 "Equity","EquityAttributableToOwnersOfParent","CostOfSales","ResearchAndDevelopmentExpense","SellingGeneralAndAdministrativeExpense","DistributionCosts","AdministrativeExpense","ProfitLossBeforeTax","IncomeTaxExpenseContinuingOperations","FinanceCosts","NoncurrentBorrowings","CurrentBorrowings","Borrowings","CashAndCashEquivalents","CurrentInvestments","ShorttermDeposits","Assets"],
 "dei":["EntityCommonStockSharesOutstanding"]}
import datetime as _dt
os.makedirs("facts",exist_ok=True)
WEEK=_dt.date.today().isoformat()  # refresh daily
MARK="facts/.day-v2"
fresh_week=os.path.exists(MARK) and open(MARK).read().strip()==WEEK
CUTOFF=str(_dt.date.today().year-6)
fails=[0]
def get(x):
    f=f"facts/{x['t']}.json"
    if os.path.exists(f) and fresh_week: return x['t'],'cached'
    if fails[0]>=25 and not os.path.exists(f): return x['t'],'fail:skipped after repeated blocks'
    if fails[0]>=25: return x['t'],'kept-old'
    url=f"https://data.sec.gov/api/xbrl/companyfacts/CIK{int(x['cik']):010d}.json"
    for att in range(4):
        r=subprocess.run(["curl","-sS","-m","60","-A",UA,"--compressed",url],capture_output=True,text=True)
        if r.stdout.startswith("{"): break
        time.sleep(2+att*3)
    else:
        fails[0]+=1
        return (x['t'],'kept-old') if os.path.exists(f) else (x['t'],'fail:'+r.stdout[:60]+r.stderr[:60])
    fails[0]=0
    d=json.loads(r.stdout); out={}
    for tax,cs in KEEP.items():
        for c in cs:
            node=d.get("facts",{}).get(tax,{}).get(c)
            if not node: continue
            out[f"{tax}:{c}"]={u:[{k:v for k,v in e.items() if k in("start","end","val","form","filed")} for e in arr if e.get("end","")>=CUTOFF] for u,arr in node["units"].items()}
    json.dump(out,open(f,"w"))
    return x['t'],'ok'
u=json.load(open("universe.json"))
res={}
with cf.ThreadPoolExecutor(4) as ex:
    for i,(t,s) in enumerate(ex.map(get,u)):
        res[t]=s
        if i%100==0: print(i,t,s,flush=True)
bad={k:v for k,v in res.items() if v.startswith('fail')}
kept=sum(v=='kept-old' for v in res.values())
print("done",len(res),"fail",len(bad),"kept-old",kept,list(bad.items())[:5])
if len(bad)+kept<0.2*len(res): open(MARK,"w").write(WEEK)
if len(bad)>0.2*len(res): sys.exit("SEC fetch mostly failed and no cached data to fall back on")
