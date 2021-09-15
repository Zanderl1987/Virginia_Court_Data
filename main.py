# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import pandas as pd
import numpy as np
import sqlite3
import sqlalchemy
from sqlalchemy import create_engine
import pathlib
import pandasql as sqldf
import seaborn as sns
import matplotlib as mpl
import pyspark
from pyspark.sql import *
# Import data visualization libraries
import altair as alt
import seaborn as sns
import matplotlib.pyplot as plt


#sns.set(style='ticks')

con = sqlite3.connect(r"C:\Users\CDT - Admin\OneDrive - University of Virginia\Databases\Virginia_Court_Case_Database.db")
engine = create_engine('sqlite:///:memory:')
cur = con.cursor()

test_df = pd.read_html('https://github.com/bschoenfeld/virginia-court-data-analysis/blob/master/data/circuit_courts.csv')
print(test_df[0])

def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')



# See PyCharm help at https://www.jetbrains.com/help/pycharm/
