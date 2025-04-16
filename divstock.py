import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

st.title("📅 Dividend Calendar for a Stock")

# --- Inputs ---
ticker = st.text_input("Enter Stock Ticker (e.g., RELIANCE, AAPL)", "RELIANCE").upper()

market = st.radio("Select Market", ["India", "Other"])

# Modify ticker if Indian market is selected
if market == "India":
    ticker += ".NS"

start_date = st.date_input("Start Date", datetime(2022, 1, 1))
end_date = st.date_input("End Date", datetime.today())

# --- Logic ---
if start_date > end_date:
    st.error("Start date must be before end date.")
elif ticker:
    try:
        stock = yf.Ticker(ticker)
        dividends = stock.dividends

        if not dividends.empty:
            # Filter by date range
            filtered_dividends = dividends[(dividends.index.date >= start_date) &
                                           (dividends.index.date <= end_date)]

            if not filtered_dividends.empty:
                df = pd.DataFrame({
                    "Ex-Date": filtered_dividends.index.date,
                    "Dividend": filtered_dividends.values
                })
                df = df.reset_index(drop=True)
                st.success(f"Dividends for {ticker} from {start_date} to {end_date}")
                st.dataframe(df)
            else:
                st.info(f"No dividends for {ticker} in the selected date range.")
        else:
            st.warning(f"No dividend data available for {ticker}.")
    except Exception as e:
        st.error(f"Error fetching data: {e}")
