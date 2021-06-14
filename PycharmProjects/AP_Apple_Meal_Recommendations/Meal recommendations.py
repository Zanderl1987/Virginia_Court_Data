import pandas as pd
import numpy as np
import pathlib

def convert_path(file_path):
    fp = pathlib.PureWindowsPath(file_path).as_posix()

    return fp

def clean_units(df, col_list):
    for col in col_list:
        if col in list(df.columns):
            df[col] = df[col].str.replace('< 1', '1')
            df[col] = df[col].str.replace('<', '1')
            df[f"{col}_values"] = nd_df[col].str.split(' ').str[0].astype(float)
            df[f"{col}_units"] = nd_df[col].str.split(' ').str[1]

    return df


def nutrition_calcs(df, units='g', carb_ratio=4, protein_ratio=4,
                    fat_ratio=9, pct_fat=0.30, pct_carbs=0.55, pct_protein=0.15,
                    variance_upper=0.05, variance_lower=0.05):
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

    def indicator_calcs(df, df_col, nutrition_ratio):
        if df[df_col] >= (nutrition_ratio - variance_lower) & df[df_col] <= (nutrition_ratio + variance_higher):
            output_col = 1
        else:
            output_col = 0

        return output_col

    df['fat_indicator'] = indicator_calcs(df=df, df_col='pct_fat', nutrition_ratio=fat_ratio)

    return df

food_data_path = convert_path(r"C:\Users\CDT - Admin\PycharmProjects\AP_Apple_Meal_Recommendations\CalorieKing_Dataset_Cleaned_20210128 (1).csv")

# List select columns that we want to clean
col_list = ['Alcohol','Calcium','Cholesterol','Dietary Fiber','Iron',
            'Protein','Saturated Fat','Sodium','Sugars','Total Carbohydrate',
            'Total Fat','Vitamin A','Vitamin C','Potassium','Trans Fat','Monounsaturated Fat',
           'Polyunsaturated Fat','Omega- Fatty Acids','Caffeine']

food_df = pd.read_csv(food_data_path)

