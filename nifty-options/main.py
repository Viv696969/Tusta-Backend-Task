import pandas as pd
from time import time


def loadOptionsData(path:str)->pd.DataFrame:
    df_nifty=pd.read_csv(path,usecols=["datetime", "expiry_date","right" ,"strike_price", "open","high","low","close"],parse_dates=["datetime"]).sort_values("datetime")
    df_nifty["expiry_datetime"] = pd.to_datetime(df_nifty["expiry_date"], utc=True).dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)
    return df_nifty

def loadNiftyData(path:str)->pd.DataFrame:
    df_data=pd.read_csv(path,usecols=["datetime","open","high","low","close"],parse_dates=["datetime"])
    df_data['day_of_week'] = df_data['datetime'].dt.strftime('%A')
    return df_data


def filterDataByRight(df:pd.DataFrame,right:str)->pd.DataFrame:
    return df[df["right"]==right]

def calculateSelectedStrikeByRight(close,right:str,moneyness:int)->pd.DataFrame:
    if right=="Call":
        return (round(close/50)*50)-(50*moneyness)
    else:
        return (round(close/50)*50)+(50*moneyness)

def filterDataByExcludedDaysAndTradeTime(df:pd.DataFrame,trade_time,excluded_days:list)->pd.DataFrame:
    return df[
            (df.datetime.dt.time==trade_time)
            &(~df["day_of_week"].isin(excluded_days))
            ]

def getNearestExpiry(df:pd.DataFrame,datetime):
    return df.loc[
            (df["expiry_datetime"]>=datetime), "expiry_datetime"
            ].min()


def filterDataByMomentum(df:pd.DataFrame,momentum)->pd.DataFrame:
    if momentum == 0:
        return df

    if momentum > 0:
        condition_met = df["high"] >= (df["close"].iloc[0] + momentum)
    else:
        condition_met = df["low"] <= (df["close"].iloc[0] + momentum)

    idx = df.index[condition_met].min()
    
    if pd.isna(idx):
        return df.iloc[:0]

    return df.loc[idx:]

def continueReentry(exit_reason_value:int,re_entry,remaining_reentries)->bool:
    if exit_reason_value == -1 or re_entry is None or remaining_reentries <= 0:return False

    if re_entry == "Target" and exit_reason_value == 1:return True

    elif re_entry == "StopLoss" and exit_reason_value==0:return True

    elif re_entry == "Both" and exit_reason_value in {0, 1}:return True

    else:return False

def backtest(trade_time,moneyness,right,end_time,exclude_days,momentum=0,target=10,stop_loss=-5,re_entry=None, max_reentries=0):
    
    end_time=pd.to_datetime(end_time).time()
    trade_time=pd.to_datetime(trade_time).time()

    df_nifty=loadOptionsData("nifty_unique_options_data.csv")
    df_data=loadNiftyData("Data.csv")
    st=time()
    df=filterDataByRight(df_nifty,right)
    df_data["selected_strike"]=calculateSelectedStrikeByRight(df_data["close"],right,moneyness)  # change required
    df_data_time_based=filterDataByExcludedDaysAndTradeTime(df_data,trade_time,exclude_days)

    trades=[]

    for _,row in df_data_time_based.iterrows():
        spot_price=row.close
        selected_strike=row.selected_strike

        nearest_expiry=getNearestExpiry(df,row.datetime)
        if pd.isna(nearest_expiry):continue

        remaining_reentries = max_reentries
        
        nearest_expiry_df_without_strike=df[
            #   (df.datetime>=row.datetime)&
            #   (df.strike_price==row.selected_strike)&
              (df.datetime.dt.date==row.datetime.date())&
              (df.datetime.dt.time<=end_time)&
              (df.expiry_datetime==nearest_expiry)
            ]
        nearest_expiry_df=pd.DataFrame()
        selected_strike=row.selected_strike
        exit_time=row.datetime

        while remaining_reentries >= 0:
    
          
            nearest_expiry_df=nearest_expiry_df_without_strike[
                (nearest_expiry_df_without_strike.datetime>=exit_time)&
                (nearest_expiry_df_without_strike.strike_price==selected_strike)
                ]
           
            if nearest_expiry_df.empty :break
            nearest_expiry_df=filterDataByMomentum(nearest_expiry_df,momentum)

            if len(nearest_expiry_df)==0:break

            entry_row = nearest_expiry_df.iloc[0]
            entry_price = entry_row["close"]
            entry_time = entry_row["datetime"]
            
            target_price =entry_price + target
            stop_loss_price =entry_price + stop_loss

            exit_time = None
            exit_price = None
            exit_reason=None
            exit_reason_value=None

            for i in range(1, len(nearest_expiry_df)):
                expiry_df_row = nearest_expiry_df.iloc[i]
                if expiry_df_row["high"] >= target_price:
                    exit_time = expiry_df_row["datetime"]
                    # exit_price = expiry_df_row["high"]
                    exit_price = expiry_df_row["close"]
                    exit_reason="Reached Target"
                    exit_reason_value=1
                    break
                elif expiry_df_row["low"] <= stop_loss_price:
                    exit_time = expiry_df_row["datetime"]
                    # exit_price = expiry_df_row["low"]
                    exit_price = expiry_df_row["close"]
                    exit_reason="Reached Stop Loss"
                    exit_reason_value=0
                    break

            if exit_reason==None:
                exit_reason="Reached Given End Time"
                exit_time=nearest_expiry_df.iloc[-1].datetime
                exit_price=expiry_df_row["close"]
                exit_reason_value=-1

            pnl = exit_price - entry_price if exit_price else None

            trade_log = {
                "Status":"🟢" if pnl>0 else "🔴",
                "Spot Price":spot_price,
                "Selected Strike":selected_strike,
                "Entry Time": entry_time,
                "Entry Price": entry_price,
                "Exit Time": exit_time,
                "Exit Price": exit_price,
                "Expiry Date":nearest_expiry,
                "PnL": pnl,
                "Exit Reason":exit_reason
            }

            trades.append(trade_log)

            if continueReentry(exit_reason_value,re_entry,remaining_reentries):
                # nearest_expiry_df=nearest_expiry_df.iloc[i].datetime
                selected_strike=df_data[df_data.datetime==exit_time].selected_strike.iloc[0]
            else:break

            remaining_reentries -= 1
            
                
    trades_df=pd.DataFrame(trades)
    print("Time taken=",time()-st)
    return trades_df

df=backtest(trade_time="9:30:00",moneyness=2,right="Call",end_time="15:30:00",exclude_days=["Tuesday"],momentum=6,target=10,stop_loss=-5,re_entry="Target", max_reentries=5)
df.to_csv("test1.csv",index=False)
