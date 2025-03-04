import pandas as pd
from time import time
import numpy as np


def loadOptionsData(path:str)->pd.DataFrame:
    df_nifty=pd.read_csv(path,usecols=["datetime", "expiry_date","right" ,"strike_price", "open","high","low","close"],parse_dates=["datetime"]).sort_values("datetime")
    df_nifty["expiry_datetime"] = pd.to_datetime(df_nifty["expiry_date"], utc=True).dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)
    return df_nifty

def loadNiftyData(path:str)->pd.DataFrame:
    df_data=pd.read_csv(path,usecols=["datetime","open","high","low","close"],parse_dates=["datetime"])
    df_data['day_of_week'] = df_data['datetime'].dt.strftime('%A')
    return df_data

def filterDataByRight(df:pd.DataFrame,right:str)->pd.DataFrame:
    # return df[df["right"]==right]
    return df[df["right"].eq(right)]

def calculateSelectedStrikeByRight(close,right:str,moneyness:int):
    # if right=="Call":
    #     return (round(close/50)*50)-(50*moneyness)
    # else:
    #     return (round(close/50)*50)+(50*moneyness)
    rounded_close = np.round(close / 50) * 50
    if right == "Call":
        return rounded_close - (50 * moneyness)
    else:
        return rounded_close + (50 * moneyness)

def filterDataByExcludedDaysAndTradeTime(df:pd.DataFrame,trade_time,excluded_days:list)->pd.DataFrame:
    # return df[
    #         (df.datetime.dt.time==trade_time)
    #         &(~df["day_of_week"].isin(excluded_days))
    #         ]
    mask = (df["datetime"].dt.time == trade_time) & (~df["day_of_week"].isin(excluded_days))
    return df.loc[mask]

def getNearestExpiry(df:pd.DataFrame,datetime):
    # return df.loc[
    #         (df["expiry_datetime"]>=datetime), "expiry_datetime"
    #         ].min()
    sorted_expiries = df["expiry_datetime"].astype("datetime64[ns]").values  # Ensure dtype consistency
    datetime = np.datetime64(datetime)  # Convert input datetime
    
    idx = np.searchsorted(sorted_expiries, datetime, side="left")
    
    return sorted_expiries[idx] if idx < len(sorted_expiries) else None
    

def filterDataByMomentum(df:pd.DataFrame,momentum)->pd.DataFrame:
    # if momentum == 0:
    #     return df

    # if momentum > 0:
    #     condition_met = df["high"] >= (df["close"].iloc[0] + momentum)
    # else:
    #     condition_met = df["low"] <= (df["close"].iloc[0] + momentum)

    # idx = df.index[condition_met].min()
    
    # if pd.isna(idx):
    #     return df.iloc[:0]

    # return df.loc[idx:]
    if momentum == 0:
        return df  # No filtering needed
    
    close_start = df["close"].iloc[0]
    
    if momentum > 0:
        condition_met = np.where(df["high"].values >= (close_start + momentum))[0]
    else:
        condition_met = np.where(df["low"].values <= (close_start + momentum))[0]
    
    if condition_met.size == 0:
        return df.iloc[:0]  # Return empty DataFrame if no match found
    
    return df.iloc[condition_met[0]:]

def continueReEntry(exit_reason_value:int,re_entry,remaining_reentries)->bool:
    if exit_reason_value == -1 or re_entry is None or remaining_reentries <= 0:return False

    if re_entry == "Target" and exit_reason_value == 1:return True

    elif re_entry == "StopLoss" and exit_reason_value==0:return True

    elif re_entry == "Both" and exit_reason_value in {0, 1}:return True

    else:return False

def getExitCondition(df:pd.DataFrame, target_price, stop_loss_price):
    target_mask = df["high"] >= target_price
    stop_mask = df["low"] <= stop_loss_price

    target_idx = np.where(target_mask)[0][0] if target_mask.any() else None
    stop_idx = np.where(stop_mask)[0][0] if stop_mask.any() else None

    if target_idx is not None and (stop_idx is None or target_idx <= stop_idx):
        row = df.iloc[target_idx]
        return row["close"], row["datetime"], "Reached Target", 1
    elif stop_idx is not None:
        row = df.iloc[stop_idx]
        return row["close"], row["datetime"], "Reached Stop Loss", 0
    else:
        last_row = df.iloc[-1]
        return last_row["close"], last_row["datetime"], "Reached Given End Time", -1


def backtest(trade_time,moneyness,right,end_time,exclude_days,momentum=0,target=10,stop_loss=-5,re_entry=None, max_reentries=0):
    
    end_time=pd.to_datetime(end_time).time()
    trade_time=pd.to_datetime(trade_time).time()

    df_nifty_options=loadOptionsData("nifty_unique_options_data.csv")
    df_data_nifty=loadNiftyData("Data.csv")

    st=time()
    df_nifty_options=filterDataByRight(df_nifty_options,right)
    df_nifty_options["date"] = df_nifty_options["datetime"].dt.date
    df_nifty_options["time"] = df_nifty_options["datetime"].dt.time
    df_data_nifty["selected_strike"]=calculateSelectedStrikeByRight(df_data_nifty["close"],right,moneyness)
    df_data_nifty_time_based=filterDataByExcludedDaysAndTradeTime(df_data_nifty,trade_time,exclude_days)
    print("Total Time taken process data based on inputs =",time()-st)

    def processRow(row):
        start_time=time()
        spot_price = row.close
        nearest_expiry = getNearestExpiry(df_nifty_options, row.datetime)
        
        if pd.isna(nearest_expiry):return None  # Skip row if no expiry is found

        remaining_reentries = max_reentries

        # nearest_expiry_df_without_strike = df_nifty_options[
        #     (df_nifty_options.datetime.dt.date == row.datetime.date()) &
        #     (df_nifty_options.datetime.dt.time <= end_time) &
        #     (df_nifty_options.expiry_datetime == nearest_expiry)
        # ]
        mask = (df_nifty_options["date"] == row.datetime.date()) & (df_nifty_options["time"] <= end_time) & (df_nifty_options["expiry_datetime"] == nearest_expiry)

        nearest_expiry_df_without_strike=df_nifty_options.loc[mask]

        selected_strike = row.selected_strike
        exit_time = row.datetime
        trade_logs = []

        while remaining_reentries >= 0:
            nearest_expiry_df = nearest_expiry_df_without_strike[
                (nearest_expiry_df_without_strike.datetime >= exit_time) &
                (nearest_expiry_df_without_strike.strike_price == selected_strike)
            ]

            if nearest_expiry_df.empty:break

            nearest_expiry_df = filterDataByMomentum(nearest_expiry_df, momentum)

            if len(nearest_expiry_df) == 0:break

            entry_row = nearest_expiry_df.iloc[0]
            entry_price = entry_row["close"]
            entry_time = entry_row["datetime"]

            target_price = entry_price + target
            stop_loss_price = entry_price + stop_loss

            exit_price, exit_time, exit_reason, exit_reason_value = getExitCondition(
                nearest_expiry_df.iloc[1:], target_price, stop_loss_price
            )

            pnl = exit_price - entry_price if exit_price else None

            trade_log = {
                "Status": "🟢" if pnl > 0 else "🔴",
                "Spot Price": spot_price,
                "Selected Strike": selected_strike,
                "Entry Time": entry_time,
                "Entry Price": entry_price,
                "Exit Time": exit_time,
                "Exit Price": exit_price,
                "Expiry Date": nearest_expiry,
                "PnL": pnl,
                "Exit Reason": exit_reason
            }
            
            trade_logs.append(trade_log)

            if continueReEntry(exit_reason_value, re_entry, remaining_reentries):
                selected_strike = df_data_nifty[df_data_nifty.datetime == exit_time].selected_strike.iloc[0]
            else:break
            
            remaining_reentries -= 1

        print("Execution Time : ",time()-start_time)
        return trade_logs
    
    print("Total Time taken before processing rows =",time()-st)
    stn=time()
    trades = df_data_nifty_time_based.apply(processRow, axis=1).dropna().explode().tolist()
    print("Total Time taken for processing all rows =",time()-stn)

    stn_new=time()
    trades_df=pd.DataFrame(trades)
    print("time taken to convert trade to pandas = ",time()-stn_new)
    print("Total Time taken=",time()-st)
    return trades_df


df=backtest(trade_time="9:30:00",moneyness=2,right="Call",end_time="15:30:00",exclude_days=["Monday","Friday"],momentum=6,target=10,stop_loss=-5,re_entry="Target", max_reentries=3)
df.to_csv("test1.csv",index=False)