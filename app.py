import streamlit as st

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
    df = yf.download(tickers=symbol, period='1y', interval='1d')
    # Flatten multi-index columns if present
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    # Compute RSI, MACD, and the 50 EMA
    df['RSI'] = compute_RSI(df['Close'])
    df['MACD'], df['MACD_Signal'] = compute_MACD(df['Close'])
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()

    df = df.reset_index()

    st.dataframe(df)
    # Create a figure with 3 rows:
    # Row 1: Candlestick chart with the 50 EMA and Fibonacci levels,
    # Row 2: RSI, and
    # Row 3: MACD and MACD Signal.
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.02,
                        row_heights=[0.6, 0.2, 0.2])

    # We will add 5 traces per symbol:
    # 1. Candlestick (row 1)
    # 2. 50 EMA (row 1)
    # 3. RSI (row 2)
    # 4. MACD (row 3)
    # 5. MACD Signal (row 3)
    num_traces_per_symbol = 5


    # Add traces for all symbols (default: only first symbol is visible)
    # Candlestick trace
    fig.add_trace(
        go.Candlestick(
            x=df['Date'],
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            increasing_line_color='green',
            decreasing_line_color='red',
            name=symbol,
        ),
        row=1, col=1
    )
    # 50 EMA trace
    fig.add_trace(
        go.Scatter(
            x=df['Date'],
            y=df['EMA50'],
            mode='lines',
            line=dict(color='magenta', width=2),
            name=f"{symbol} 50 EMA",
        ),
        row=1, col=1
    )
    # RSI trace
    fig.add_trace(
        go.Scatter(
            x=df['Date'],
            y=df['RSI'],
            mode='lines',
            line=dict(color='blue'),
            name=f"{symbol} RSI",
        ),
        row=2, col=1
    )
    # MACD trace
    fig.add_trace(
        go.Scatter(
            x=df['Date'],
            y=df['MACD'],
            mode='lines',
            line=dict(color='orange'),
            name=f"{symbol} MACD",
        ),
        row=3, col=1
    )
    # MACD Signal trace
    fig.add_trace(
        go.Scatter(
            x=df['Date'],
            y=df['MACD_Signal'],
            mode='lines',
            line=dict(color='purple'),
            name=f"{symbol} MACD Signal",
        ),
        row=3, col=1
    )

    # Optionally, update the x-axis to remove weekend gaps (for daily data)
    fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])

    # --- Add Horizontal RSI Lines at 70 and 30 to the RSI subplot (row 2) ---
    rsi_x0 = df.Date.min()
    rsi_x1 = df.Date.max()
    fig.add_shape(
        type="line",
        xref="x",
        yref="y2",
        x0=rsi_x0,
        x1=rsi_x1,
        y0=70,
        y1=70,
        line=dict(color="black", dash="dot", width=1)
    )
    fig.add_shape(
        type="line",
        xref="x",
        yref="y2",
        x0=rsi_x0,
        x1=rsi_x1,
        y0=30,
        y1=30,
        line=dict(color="black", dash="dot", width=1)
    )

    # --- Use a Streamlit selectbox to choose a symbol ---

    # # Update figure: set visible traces based on the selected symbol
    # for i, trace in enumerate(fig.data):
    #     # Each symbol has num_traces_per_symbol traces in order
    #     if (i // num_traces_per_symbol) == selected_index:
    #         trace.visible = True
    #     else:
    #         trace.visible = False

    # Update layout with the corresponding Fibonacci shapes and title
    fig.update_layout(
        title=f"Candlestick, 50 EMA, RSI, MACD & Fibonacci Levels for {symbol}",
        xaxis_title="Date",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        template="plotly_white",
        height=800)

    # Display the Plotly chart in Streamlit
    st.plotly_chart(fig, use_container_width=True)

