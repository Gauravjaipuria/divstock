import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

st.title("📅 Dividend Calendar + EPS Tracker")

# --- Inputs ---
ticker = st.text_input("Enter Stock Ticker (e.g., RELIANCE, AAPL)", "RELIANCE").upper()

market = st.radio("Select Market", ["India", "Other"])

# Modify ticker if Indian market is selected
yf_ticker = ticker + ".NS" if market == "India" else ticker

start_date = st.date_input("Start Date", datetime(2022, 1, 1))
end_date = st.date_input("End Date", datetime.today())

# --- Logic ---
if start_date > end_date:
    st.error("Start date must be before end date.")
elif ticker:
    try:
        stock = yf.Ticker(yf_ticker)
        info = stock.info

        # --- EPS Section ---
        eps = info.get("trailingEps") or info.get("forwardEps", "N/A")
        company_name = info.get("shortName", ticker)
        st.subheader(f"📊 EPS for {company_name}:")
        st.markdown(f"**EPS:** {eps}")

        # --- Dividend Section ---
        st.subheader("💰 Dividend Calendar")
        dividends = stock.dividends

        if not dividends.empty:
            filtered_dividends = dividends[(dividends.index.date >= start_date) &
                                           (dividends.index.date <= end_date)]

            if not filtered_dividends.empty:
                df = pd.DataFrame({
                    "Ex-Date": filtered_dividends.index.date,
                    "Dividend": filtered_dividends.values
                })
                df = df.reset_index(drop=True)
                st.success(f"Dividends for {yf_ticker} from {start_date} to {end_date}")
                st.dataframe(df)
            else:
                st.info(f"No dividends for {yf_ticker} in the selected date range.")
        else:
            st.warning(f"No dividend data available for {yf_ticker}.")

    except Exception as e:
        st.error(f"Error fetching data: {e}")
