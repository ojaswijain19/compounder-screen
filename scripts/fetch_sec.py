# Pull SEC companyfacts and keep only the concepts the screener needs.
import json, os, sys, time, subprocess, concurrent.futures as cf
import os
UA=os.environ.get("SEC_UA","compounder-screen github.com/ojaswijain19/compounder-screen")
KEEP={"us-gaap":["RevenueFromContractWithCustomerExcludingAssessedTax","Revenues","SalesRevenueNet","RevenueFromContractWithCustomerIncludingAssessedTax","RevenuesNetOfInterestExpense","InterestAndDividendIncomeOperating",
 "OperatingIncomeLoss","NetIncomeLoss","GrossProfit","NetCashProvidedByUsedInOperatingActivities","NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
 "PaymentsToAcquirePropertyPlantAndEquipment","PaymentsToAcquireProductiveAssets","PaymentsForCapitalImprovements","DepreciationDepletionAndAmortization","DepreciationAndAmortization","DepreciationAmortizationAndAccretionNet",
 "StockholdersEquity","StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest","LongTermDebt","LongTermDebtNoncurrent","LongTermDebtCurrent","DebtCurrent","ShortTermBorrowings","LongTermDebtAndCapitalLeaseObligations","OperatingLeaseLiabilityNoncurrent",
 "CashAndCashEquivalentsAtCarryingValue","CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents","ShortTermInvestments","MarketableSecuritiesCurrent","AvailableForSaleSecuritiesDebtSecuritiesCurrent",
 "WeightedAverageNumberOfDilutedSharesOutstanding","ProfitLoss","NetIncomeLossAvailableToCommonStockholdersBasic","NetIncomeLossAvailableToCommonStockholdersDiluted","Depreciation","AmortizationOfIntangibleAssets","OtherDepreciationAndAmortization","CostOfRevenue","CostOfGoodsAndServicesSold","CommercialPaper","LongTermDebtFairValue","ShareBasedCompensation","IncomeTaxExpenseBenefit","IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest","Assets"],
 "ifrs-full":["Revenue","RevenueFromContractsWithCustomers","ProfitLossFromOperatingActivities","ProfitLoss","ProfitLossAttributableToOwnersOfParent","GrossProfit","CashFlowsFromUsedInOperatingActivities","PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities","PurchaseOfPropertyPlantAndEquipment","DepreciationAndAmortisationExpense","DepreciationAmortisationAndImpairmentLossReversalOfImpairmentLossRecognisedInProfitOrLoss",
 "Equity","EquityAttributableToOwnersOfParent","NoncurrentBorrowings","CurrentBorrowings","Borrowings","CashAndCashEquivalents","CurrentInvestments","ShorttermDeposits","Assets"],
 "dei":["EntityCommonStockSharesOutstanding"]}
os.makedirs("facts",exist_ok=True)
def get(x):
    f=f"facts/{x['t']}.json"
    if os.path.exists(f): return x['t'],'cached'
    url=f"https://data.sec.gov/api/xbrl/companyfacts/CIK{int(x['cik']):010d}.json"
    for att in range(4):
        r=subprocess.run(["curl","-sS","-m","60","-A",UA,"--compressed",url],capture_output=True,text=True)
        if r.stdout.startswith("{"): break
        time.sleep(2+att*3)
    else: return x['t'],'fail:'+r.stdout[:60]+r.stderr[:60]
    d=json.loads(r.stdout); out={}
    for tax,cs in KEEP.items():
        for c in cs:
            node=d.get("facts",{}).get(tax,{}).get(c)
            if not node: continue
            out[f"{tax}:{c}"]={u:[{k:v for k,v in e.items() if k in("start","end","val","fy","fp","form","filed")} for e in arr] for u,arr in node["units"].items()}
    json.dump(out,open(f,"w"))
    return x['t'],'ok'
u=json.load(open("universe.json"))
res={}
with cf.ThreadPoolExecutor(4) as ex:
    for i,(t,s) in enumerate(ex.map(get,u)):
        res[t]=s
        if i%100==0: print(i,t,s,flush=True)
bad={k:v for k,v in res.items() if v.startswith('fail')}
print("done",len(res),"fail",len(bad),list(bad.items())[:10])
