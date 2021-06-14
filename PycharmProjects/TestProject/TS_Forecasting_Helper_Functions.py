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


def get_yf_hist(symbol_list,startDate,endDate,interval):
  import matplotlib.pyplot as plt
  import datetime
  import yfinance as yf

  # Get historical pricing data
  data = yf.download(symbol_list, startDate, endDate, interval)

  return data


def get_intraday(symbol_list,period,interval):
  intraday_list = []
  intraday_df = pd.DataFrame()
  for sym in symbol_list:
    intraday = yf.download(tickers=sym,
                           period=period,
                           interval=interval)
    intraday['symbol'] = sym
    intraday_df = pd.concat([intraday_df,intraday])

  return intraday_df

def rolling_zscore(data,return_period,window_length):
  log_returns = (np.log(data / data.shift(return_period)))
  zscore = (log_returns - log_returns.rolling(window_length).mean() / log_returns.rolling(window_length).std())
  #results_dict = dict({'log_returns':log_returns})
  results_df = pd.DataFrame(zscore)

  return results_df


  # convert series to supervised learning
def series_to_supervised(data, n_in=1, n_out=1, dropnan=True):
    n_vars = 1 if type(data) is list else data.shape[1]
    df = pd.DataFrame(data)
    cols, names = list(), list()
    # input sequence (t-n, ... t-1)
    for i in range(n_in, 0, -1):
        cols.append(df.shift(i))
        names += [('var%d(t-%d)' % (j+1, i)) for j in range(n_vars)]
    # forecast sequence (t, t+1, ... t+n)
    for i in range(0, n_out):
        cols.append(df.shift(-i))
        if i == 0:
            names += [('var%d(t)' % (j+1)) for j in range(n_vars)]
        else:
            names += [('var%d(t+%d)' % (j+1, i)) for j in range(n_vars)]
    # put it all together
    agg = pd.concat(cols, axis=1)
    agg.columns = names
    # drop rows with NaN values
    if dropnan:
        agg.dropna(inplace=True)
    return agg


def h_vol(data,col_name,window_length,periods):
  rets = np.log(data[col_name] / data[col_name].shift(1))
  stdev = rets.rolling(window_length).std()
  #hist_vol = np.power(stdev,np.sqrt(periods))
  hist_vol = stdev * np.sqrt(periods)

  return hist_vol

