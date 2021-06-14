import yfinance as yf
import numpy as np
import pandas as pd
import datetime
import keras
import tensorflow as tf
import altair as alt
import seaborn as sns
import sklearn
import keras
from keras.models import Sequential
from keras.callbacks import EarlyStopping, TensorBoard
from keras.layers import Dense, LSTM, GRU, Dropout, Activation
from keras.layers.convolutional import Conv1D, MaxPooling1D
import TS_Forecasting_Helper_Functions as hf


startDate = '1900-01-01'
endDate = datetime.datetime.today()
symbol_list = ['^GSPC']

# Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
interval = '1wk'

df1 = yf.download(tickers=symbol_list,start=startDate,end=endDate,interval=interval)

df = pd.DataFrame(df1)
df['std_4'] = df['Adj Close'].rolling(4).std()
df['std_5'] = df['Adj Close'].rolling(5).std()
df['std_8'] = df['Adj Close'].rolling(8).std()
df['std_12'] = df['Adj Close'].rolling(12).std()

df['rsi_14'] = ta.momentum.rsi(close=df['Adj Close'],window=14)

df['zs_4'] = rolling_zscore(df['Adj Close'],return_period=4,window_length=12)
df['atr_12'] = ta.volatility.average_true_range(high=df['High'],low=df['Low'],close=df['Adj Close'],window=12,fillna=True)

df['hvol_12'] = h_vol(data=df, col_name='Adj Close',window_length=12,periods=252)

# df = df.drop('id',axis=1)

df = df.dropna(axis=0)

print(df.head())
