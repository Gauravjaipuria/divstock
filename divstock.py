import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# Page setup
st.set_page_config(page_title="Dividend Calendar + Return Tracker", layout="wide")
st.title("💰 Year-wise Dividend Summary + Return %")

# --- Inputs ---
ticker_input = st.text_input("Enter Stock Ticker (e.g., RELIANCE, AAPL)", "RELIANCE").upper()
market = st.radio("Select Market", ["India", "Other"])
ticker = ticker_input + ".NS" if market == "India" else ticker_input

start_date = st.date_input("Start Date", datetime(2021, 1, 1))
end_date = st.date_input("End Date", datetime.today())

# --- Validation ---
if start_date > end_date:
    st.error("Start date must be before end date.")
else:
    try:
        stock = yf.Ticker(ticker)
        dividends = stock.dividends

        if dividends.empty:
            st.warning(f"No dividend data available for {ticker}.")
        else:
            # Filter dividends by date
            filtered_dividends = dividends[(dividends.index.date >= start_date) &
                                           (dividends.index.date <= end_date)]

            if filtered_dividends.empty:
                st.info("No dividends in selected date range.")
            else:
                # Year-wise dividend
                dividends_df = filtered_dividends.reset_index()
                dividends_df["Year"] = dividends_df["Date"].dt.year
                yearwise_div = dividends_df.groupby("Year")["Dividends"].sum().reset_index()

                # Get year-end price
                prices = stock.history(start=start_date, end=end_date)
                prices["Year"] = prices.index.year
                year_end_prices = prices.groupby("Year")["Close"].last().reset_index()

                # Merge and calculate yield
                summary = pd.merge(yearwise_div, year_end_prices, on="Year", how="left")
                summary.columns = ["Year", "Dividend", "Year End Price"]
                summary["Dividend Yield %"] = (summary["Dividend"] / summary["Year End Price"]) * 100
                summary = summary.round(2)

                st.success(f"Year-wise dividend + return for {ticker}")
                st.dataframe(summary)

                # Expandable to show full dividend events
                with st.expander("📋 Show Full Dividend Entries"):
                    st.dataframe(dividends_df[["Date", "Dividends"]])

                # --- Client Transaction-Based Return ---
                st.markdown("---")
                st.subheader("📥 Dividend Return Since Your Purchase Date")
                transaction_date = st.date_input("Enter your stock purchase date")

                if start_date <= transaction_date <= end_date:
                    hist_price = stock.history(start=transaction_date, end=transaction_date + pd.Timedelta(days=5))
                    if not hist_price.empty:
                        txn_price = hist_price["Close"].iloc[0]
                        dividends_since_txn = dividends[dividends.index.date >= transaction_date]
                        total_dividend = dividends_since_txn.sum()
                        return_pct = (total_dividend / txn_price) * 100

                        st.success(f"🧾 From {transaction_date} to {end_date}:")
                        st.write(f"• Total Dividends Received: ₹{round(total_dividend, 2)}")
                        st.write(f"• Purchase Price: ₹{round(txn_price, 2)}")
                        st.write(f"• 📊 Return from Dividends: **{round(return_pct, 2)}%**")

                        st.markdown("### 🧾 Dividend Events Since Purchase")
                        st.dataframe(dividends_since_txn)

                    else:
                        st.warning("No price data found for the transaction date. Try a nearby date.")
                else:
                    st.info("Pick a transaction date within the selected date range.")

                # --- EPS Data (TTM) ---
                st.markdown("---")
                st.subheader("🧮 Earnings per Share (EPS)")
                info = stock.info
                if "trailingEps" in info:
                    eps = info["trailingEps"]
                    st.success(f"Trailing EPS: ₹{eps}")
                else:
                    st.warning("EPS data not available.")

                # --- News Section ---
                st.markdown("---")
                st.subheader("📰 Latest News")
                try:
                    news_url = f"https://finance.yahoo.com/quote/{ticker}"
                    headers = {"User-Agent": "Mozilla/5.0"}
                    response = requests.get(news_url, headers=headers)
                    soup = BeautifulSoup(response.text, "html.parser")

                    headlines = soup.find_all("h3", limit=5)
                    for h in headlines:
                        link = h.find("a")
                        if link and link.text:
                            st.markdown(f"🔹 [{link.text}](https://finance.yahoo.com{link['href']})")
                except Exception as e:
                    st.error(f"Could not fetch news: {e}")
    except Exception as e:
        st.error(f"Error fetching data: {e}")
