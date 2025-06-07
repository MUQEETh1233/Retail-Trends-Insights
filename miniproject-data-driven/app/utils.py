import pandas as pd
import datetime as dt
import os

def validate_sales_csv(df):
    required_columns = {'Customer ID','Gender','Item Purchased' , 'Season', 'Age'}
    return required_columns.issubset(df.columns)

def analyze_sales_dataset(df, name):

    df = df.drop_duplicates()

    if 'Age' in df.columns:
        df['Age Group'] = pd.cut(df['Age'], bins=[0, 18, 30, 50, 80], labels=['Teen', 'Young Adult', 'Middle Age', 'Senior'])
    else:
        df['Age Group'] = 'Unknown'

 
    if 'Previous Purchases' in df.columns:
        df["Last Purchase Date"] = dt.datetime.today() - pd.to_timedelta(df["Previous Purchases"], unit='D')
        df["Days Since Last Purchase"] = (pd.to_datetime("today") - pd.to_datetime(df["Last Purchase Date"])).dt.days
        df["Churn"] = (df["Days Since Last Purchase"] > 30).astype(int)
    else:
        df["Last Purchase Date"] = None
        df["Days Since Last Purchase"] = None
        df["Churn"] = None

    # Calculate CLV
    if 'Purchase Amount (USD)' in df.columns and 'Previous Purchases' in df.columns:
        df["CLV"] = df["Purchase Amount (USD)"] * df["Previous Purchases"]
    else:
        df["CLV"] = None

    # Save processed CSV
    output_path = f'uploads/{name}_summary.csv'
    df.to_csv(output_path, index=False)