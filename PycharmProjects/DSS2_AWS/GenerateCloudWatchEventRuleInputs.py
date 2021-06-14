import numpy as np
import pandas as pd
import boto3
import pathlib


def convert_path(fp):
    converted = pathlib.PureWindowsPath(fp).as_posix()

    return converted

imei_tracking_local_path = convert_path(r"C:\Users\CDT - Admin\PycharmProjects\DSS2_AWS\DSS2 Device IMEI Tracking_LOCAL.xlsx")

#imei_tracking_df = pd.read_excel(imei_tracking_local_path,sheet_name='Sheet1')
#imei_tracking_df['Participant ID'] = imei_tracking_df['Participant ID'].astype(int).astype(str)
#imei_tracking_df = imei_tracking_df.dropna(how='all',axis=0)
#print(imei_tracking_df)

subj_id = "77124"
thing_id = "DSS2-77124-353626070749358"

rule_input = {"thing_id":thing_id,
              "subject_id":subj_id}
print(rule_input)