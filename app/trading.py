import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pandas_ta as ta

class TradingStrategy:
    def __init__(self):
        # during production we can get input of the abbreviated  from the user itself. This is just for demonstration purpose.
        #this data we can get from api or store in a db
        self.companies=[
        "ASIANPAINT.NS -> Asian Paints Ltd.",
        "NESTLEIND.NS -> Nestle India Ltd.",
        "ULTRACEMCO.NS -> UltraTech Cement Ltd.",
        "BAJFINANCE.NS -> Bajaj Finance Ltd.",
        "SUNPHARMA.NS -> Sun Pharmaceutical Industries Ltd.",
        "TATAMOTORS.NS -> Tata Motors Ltd.",
        "HCLTECH.NS -> HCL Technologies Ltd."
        ]

    def getCompanies(self):
        return self.companies

    # will give the stock data for different indicators
    def getStockData(self,stockIndex:int,timeInterval:int,days:int):
        companyName=self.companies[stockIndex].split(" -> ")[0]
        end_date=datetime.now().strftime("%Y-%m-%d")
        start_date=(datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        df=yf.download(companyName, start=start_date, end=end_date, interval=f"{timeInterval}m")
        df.columns=["Close", "High", "Low", "Open", "Volume"]
        df.reset_index(inplace=True)
        return df


    def tradeRSI(self,userRsiDetails:dict,stockIndex:int,timeInterval:int=1,days:int=5):
        df=self.getStockData(stockIndex,timeInterval,days)
        df["Rsi"]=ta.rsi(df["Close"],length=userRsiDetails.get("period",14)) # default value is 14
        entryTime,entryPrice,entryRsi=None,None,None
        logs=[]
        # get dynamic details from user; if null use default
        RSI_BUY_THRESHOLD=userRsiDetails.get("buyThreshold",30)
        RSI_SELL_THRESHOLD=userRsiDetails.get("sellThreshold",70)

        for index, row in df.iterrows():
            if index<userRsiDetails.get("period",14):continue
            time, price, rsi = row["Datetime"], row["Close"], row["Rsi"]
            prevRsi = df.loc[index - 1, "Rsi"]
            if pd.isna(prevRsi) or pd.isna(rsi):continue # check if any rsi value is null
            

            # buy condition
            if prevRsi<RSI_BUY_THRESHOLD and rsi>RSI_BUY_THRESHOLD and entryTime is None:
                entryTime,entryPrice,entryRsi=time,price,rsi
                logs.append(f"🟢 Entry: {entryTime} | Price: {entryPrice} | RSI: {entryRsi}")

            # sell condition
            elif prevRsi>RSI_SELL_THRESHOLD and rsi<RSI_SELL_THRESHOLD and entryTime is not None:
                exitTime, exitPrice, exitRsi=time, price, rsi
                logs.append(f"🔴 Exit: {exitTime} | Price: {exitPrice} | RSI: {exitRsi}")
                
                entryTime, entryPrice, entryRsi=None, None, None # making null again once we sell to get next trade
        
        return logs
        


    # for implementation of other indicators in future
    def tradeMACD(self,userMacdDetails:dict,stockIndex:int,timeInterval:int,days:int):
        df=self.getStockData(stockIndex,timeInterval,days)
        pass

    def tradeROC(self,userRocDetails:dict,stockIndex:int,timeInterval:int,days:int):
        df=self.getStockData(stockIndex,timeInterval,days)
        pass


class  TradeLogger:
    def __init__(self):
        pass

    # these fucntions can be created as a single fucntion once in development
    def logRsiLogs(self,logs,username,company):
        with open(f"trade-log-RSI-{username}-{company}.txt", "w",encoding="utf-8") as file:
            file.write("\n".join(logs))

    # similarly for other companies as well
    def logRocLogs(self,logs,username,company):
        with open(f"trade-log-ROC-{username}-{company}.txt", "w",encoding="utf-8") as file:
            file.write("\n".join(logs))

