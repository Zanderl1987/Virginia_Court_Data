import pandas as pd
import numpy as np
import pathlib
import datetime
import requests

from IPython.core.interactiveshell import InteractiveShell

InteractiveShell.ast_node_interactivity = 'all'


def convert_path(file_path):
    fp = pathlib.PureWindowsPath(file_path).as_posix()

    return fp


def clean_units(df, col_list):
    for col in col_list:
        if col in list(df.columns):
            df[col] = df[col].str.replace('< 1', '1')
            df[col] = df[col].str.replace('<', '1')
            df[f"{col}_values"] = df[col].str.split(' ').str[0].astype(float)
            df[f"{col}_units"] = df[col].str.split(' ').str[1]

    return df


def nutrition_calcs(df, units='g', carb_ratio=4, protein_ratio=4, fat_ratio=9):
    df['protein_check'] = np.where(df['Protein_units'] == units, 0, 1)
    df['carb_check'] = np.where(df['Total Carbohydrate_units'] == units, 0, 1)
    df['fat_check'] = np.where(df['Total Fat_units'] == units, 0, 1)
    df['carbs_calories'] = df['Total Carbohydrate_values'] * carb_ratio
    df['protein_calories'] = df['Protein_values'] * protein_ratio
    df['fat_calories'] = df['Total Fat_values'] * fat_ratio

    df['f_c_p'] = df['carbs_calories'] + df['protein_calories'] + df['fat_calories']
    df['pct_fat'] = df['fat_calories'] / df['f_c_p']
    df['pct_carbs'] = df['carbs_calories'] / df['f_c_p']
    df['pct_protein'] = df['protein_calories'] / df['f_c_p']

    return df


def indicator_calcs(df, df_col, nutrition_ratio, variance_lower=0.05, variance_higher=0.05):
    variance_higher_calcs = (nutrition_ratio + variance_higher)
    variance_lower_calcs = (nutrition_ratio - variance_lower)

    return np.where(df[df_col].between(variance_lower_calcs, variance_higher_calcs, inclusive=True), 1, 0)


def flatten_json(y):
  out = {}

  def flatten(x, name=''):
    if type(x) is dict:
      for a in x:
        flatten(x[a], name + a + '_')
    elif type(x) is list:
      i = 0
      for a in x:
        flatten(a, name + str(i) + '_')
    else:
      out[name[:-1]] = x

  flatten(y)
  return out

