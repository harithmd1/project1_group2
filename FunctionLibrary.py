# Initial imports
import os
import requests
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi
import matplotlib.pyplot as plt
import hvplot.pandas
%matplotlib inline

def backtest(symbol, timeframe, start_date, end_date, api, shares):
    #download data
    df_symbol=api.get_bars(
    symbol,
    timeframe,
    start=start_date,
    end=end_date
    ).df
    
    # Reorganize the DataFrame
    df_symbol.drop(['high','low','trade_count','volume','vwap','symbol','open'], axis=1, inplace=True)
    ### Establishing control benchmark
    df_symbol['return'] = df_symbol['close'].pct_change() + 1
    df_symbol['return'].iat[0] = 1
    fund = shares*df_symbol['close'][0]
    df_symbol['benchmark'] = fund * df_symbol['return'].cumprod()
    
    ### Creating new Dataframe for MACD calculations
    df_macd = pd.DataFrame()
    df_macd['MACD'] =  df_symbol['close'].ewm(halflife=12).mean() - df_symbol['close'].ewm(halflife=26).mean()
    df_macd['Signal'] = df_macd['MACD'].ewm(halflife=9).mean()
    df_macd['histogram'] = df_macd['MACD'] - df_macd['Signal']

    # Creating signals
    # Finding long or short trades
    df_macd["X"]=np.where(df_macd["MACD"]>df_macd["Signal"],1,0) 
    df_macd["X"]=df_macd["X"].diff() 
    df_macd['close'] = df_symbol['close']
    

    # Extracting the timestamps that indicate bullish signals (Signals where we buy) and that indicate bearish signals (signals where we sell)
    Xreturns=df_macd[df_macd["X"].isin([1,-1])] 


    # Dataframe with trade signals and dates
    Xreturns['Lcashflow'] = -Xreturns['X'] * Xreturns['close'] * shares
    Xreturns['Scashflow'] = Xreturns['X'] * Xreturns['close'] * shares
    cashflowl = Xreturns["Lcashflow"].sum()
    cashflows = Xreturns["Scashflow"].sum()

    return cashflowl

