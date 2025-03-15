import streamlit as st

from data_utils import read_symbol_data_from_s3
from plot_utils import plot_all
from stock_utils import get_sp500_tickers

st.set_page_config(layout="wide")  # Enable wide mode

import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.title("Candlestick, 50 EMA, RSI, MACD & Fibonacci Levels")


# Functions to compute RSI and MACD
def compute_RSI(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def compute_MACD(series, span_short=12, span_long=26, span_signal=9):
    ema_short = series.ewm(span=span_short, adjust=False).mean()
    ema_long = series.ewm(span=span_long, adjust=False).mean()
    macd = ema_short - ema_long
    signal = macd.ewm(span=span_signal, adjust=False).mean()
    return macd, signal


# List of S&P 500 symbols
symbols = get_sp500_tickers()

col1, col2 = st.columns(2)
with col1:
    symbol = st.selectbox("Select Symbol", symbols)
with col2:
    go_plot = st.button("Plot!")

data_dict = {}

if go_plot:
    df = read_symbol_data_from_s3(symbol=symbol, tf='weekly')
    # Flatten multi-index columns if present
    plot_all(df, symbol)

