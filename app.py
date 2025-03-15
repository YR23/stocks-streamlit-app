import streamlit as st

st.set_page_config(layout="wide")  # Enable wide mode

import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import trendln  # Make sure you have installed this library (pip install trendln)

st.title("Candlestick, 50 EMA, RSI, MACD, Trendlines & Fibonacci Levels")


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


# List of S&P 500 symbols (sample)
symbols = ['AAPL', 'MSFT', 'AMZN']
data_dict = {}
shapes_dict = {}  # For Fibonacci levels (we add these as layout shapes)
trace_info = []  # To store (symbol, start_index, count) info for all traces
current_index = 0

# Download one year of daily data for each symbol, compute indicators, and calculate Fibonacci levels.
# Also, for each symbol compute support/resistance (trendlines) using trendln.
for symbol in symbols:
    df = yf.download(tickers=symbol, period='1y', interval='1d')
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df['RSI'] = compute_RSI(df['Close'])
    df['MACD'], df['MACD_Signal'] = compute_MACD(df['Close'])
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()

    # --- Calculate Fibonacci Retracement Levels ---
    overall_high = df['High'].max()
    overall_low = df['Low'].min()
    diff = overall_high - overall_low
    fib_levels = {
        "0%": overall_high,
        "23.6%": overall_high - 0.236 * diff,
        "38.2%": overall_high - 0.382 * diff,
        "50%": overall_high - 0.5 * diff,
        "61.8%": overall_high - 0.618 * diff,
        "100%": overall_low,
    }
    x0 = df.index.min()
    x1 = df.index.max()
    shapes = []
    for level_name, level_value in fib_levels.items():
        shapes.append(dict(
            type='line',
            xref='x',
            yref='y',
            x0=x0,
            x1=x1,
            y0=level_value,
            y1=level_value,
            line=dict(color='grey', width=1, dash='dash')
        ))
    shapes_dict[symbol] = shapes
    data_dict[symbol] = df

# Create a figure with 3 rows:
# Row 1: Candlestick chart, 50 EMA, and trendlines (support/resistance)
# Row 2: RSI with horizontal lines at 70 and 30
# Row 3: MACD and MACD Signal
fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.02,
                    row_heights=[0.6, 0.2, 0.2])

all_traces = []  # To hold all traces
for symbol in symbols:
    df = data_dict[symbol].reset_index()  # Ensure 'Date' column exists
    traces = []
    # Candlestick trace (Row 1)
    candlestick = go.Candlestick(
        x=df['Date'],
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        increasing_line_color='green',
        decreasing_line_color='red',
        name=f"{symbol} Candlestick"
    )
    traces.append((candlestick, 1))
    # 50 EMA trace (Row 1)
    ema_trace = go.Scatter(
        x=df['Date'],
        y=df['EMA50'],
        mode='lines',
        line=dict(color='magenta', width=2),
        name=f"{symbol} 50 EMA"
    )
    traces.append((ema_trace, 1))

    # --- Trendlines via trendln (Support and Resistance) ---
    # Calculate support/resistance from the close prices.
    try:
        support, resistance = trendln.calc_support_resistance(df.set_index('Date')['Close'])
    except Exception as e:
        support, resistance = [], []
    for sup in support:
        sup_trace = go.Scatter(
            x=sup['x'],
            y=sup['y'],
            mode='lines',
            line=dict(color='green', dash='dot'),
            name=f"{symbol} Support"
        )
        traces.append((sup_trace, 1))
    for res in resistance:
        res_trace = go.Scatter(
            x=res['x'],
            y=res['y'],
            mode='lines',
            line=dict(color='red', dash='dot'),
            name=f"{symbol} Resistance"
        )
        traces.append((res_trace, 1))

    # RSI trace (Row 2)
    rsi_trace = go.Scatter(
        x=df['Date'],
        y=df['RSI'],
        mode='lines',
        line=dict(color='blue'),
        name=f"{symbol} RSI"
    )
    traces.append((rsi_trace, 2))
    # MACD trace (Row 3)
    macd_trace = go.Scatter(
        x=df['Date'],
        y=df['MACD'],
        mode='lines',
        line=dict(color='orange'),
        name=f"{symbol} MACD"
    )
    traces.append((macd_trace, 3))
    # MACD Signal trace (Row 3)
    macd_signal_trace = go.Scatter(
        x=df['Date'],
        y=df['MACD_Signal'],
        mode='lines',
        line=dict(color='purple'),
        name=f"{symbol} MACD Signal"
    )
    traces.append((macd_signal_trace, 3))

    count = len(traces)
    trace_info.append((symbol, current_index, count))
    current_index += count
    for t, row in traces:
        # Initially, only show traces for the first symbol
        t.visible = True if symbol == symbols[0] else False
        fig.add_trace(t, row=row, col=1)
        all_traces.append(t)

# Update x-axis to remove weekend gaps (for daily data)
fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])

# Add horizontal RSI lines at 70 and 30 on RSI subplot (Row 2)
rsi_x0 = data_dict[symbols[0]].index.min()
rsi_x1 = data_dict[symbols[0]].index.max()
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
selected_symbol = st.selectbox("Select Symbol", symbols)

# Update figure: set visible traces based on the selected symbol.
# Our trace_info list tells us which traces (by index) belong to each symbol.
for sym, start, count in trace_info:
    for i in range(start, start + count):
        fig.data[i].visible = (sym == selected_symbol)

# Update layout: add the Fibonacci shapes for the selected symbol and update title.
fig.layout.shapes += tuple(shapes_dict[selected_symbol])
fig.update_layout(
    title=f"Candlestick, 50 EMA, RSI, MACD, Trendlines & Fibonacci Levels for {selected_symbol} - 1 Year of Daily Data",
    xaxis_title="Date",
    yaxis_title="Price",
    xaxis_rangeslider_visible=False,
    template="plotly_white",
    height=800
)

st.plotly_chart(fig, use_container_width=True)
