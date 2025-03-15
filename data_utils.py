import os
import boto3
import pandas as pd
import io
import streamlit as st

# AWS S3 configuration: retrieve credentials from environment variables
# Access your AWS credentials and bucket name from st.secrets
AWS_ACCESS_KEY = st.secrets["AWS"]["AWS_ACCESS_KEY"]
AWS_SECRET_KEY = st.secrets["AWS"]["AWS_SECRET_KEY"]
BUCKET_NAME = st.secrets["AWS"].get("BUCKET_NAME", "stocks-streamlit")
  # For daily data, we use a subfolder "data/1d/"

# Initialize the S3 client
s3 = boto3.client('s3',
                  aws_access_key_id=AWS_ACCESS_KEY,
                  aws_secret_access_key=AWS_SECRET_KEY)


def read_symbol_data_from_s3(symbol, tf):
    """
    Reads a CSV file from S3 using the boto3 client and returns a pandas DataFrame.

    The CSV file is assumed to be stored under the path:
    s3://{BUCKET_NAME}/{PREFIX}{symbol}.csv
    """
    tfs = {
        'hourly': 'h',
        'daily': 'd',
        'weekly': 'w'
    }
    PREFIX = f'data/1{tfs[tf]}/'

    key = f"{PREFIX}{symbol}.csv"  # e.g., "data/1d/AAPL.csv"

    # Retrieve the object from S3
    response = s3.get_object(Bucket=BUCKET_NAME, Key=key)
    data = response['Body'].read()

    # Read the CSV data into a DataFrame.
    df = pd.read_csv(io.BytesIO(data))
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.rename(columns={'Datetime': 'Date'})
    return df
