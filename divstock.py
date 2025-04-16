import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime

st.title("📈 Stock Tracker: EPS + Yearly Dividend + Return % + News")

# --- Inputs ---
ticker = st.text_input("Enter Stock Ticker (e.g., RELIANCE, AAPL)", "RELIANCE").upper()
market = st.radio("Select Market", ["India", "Other"])

# Append .NS for Indian stocks
yf_ticker = ticker + ".NS" if market == "India" else ticker

start_date = st.date_input("Start Date", datetime(2015, 1, 1))
end_date = st.date_input("End Date", datetime.today())

if start_date > end_date:
    st.error("Start date must be before end date.")
elif ticker:
    try:
        stock = yf.Ticker(yf_ticker)
        info = stock.info

        # --- EPS Section ---
        eps = info.get("trailingEps") or info.get("forwardEps", "N/A")
        company_name = info.get("shortName", ticker)
        st.subheader(f"📊 EPS for {company_name}")
        st.markdown(f"**EPS:** {eps}")

        # --- Dividend Calendar ---
        st.subheader("💰 Year-wise Dividend Summary + Return %")
        dividends = stock.dividends

        if not dividends.empty:
            # Filter by date range
            filtered = dividends[(dividends.index.date >= start_date) &
                                 (dividends.index.date <= end_date)]

            if not filtered.empty:
                df = pd.DataFrame({
                    "Ex-Date": filtered.index.date,
                    "Dividend": filtered.values
                })
                df["Year"] = pd.to_datetime(df["Ex-Date"]).dt.year
                yearwise_dividend = df.groupby("Year")["Dividend"].sum().reset_index()

                # Get closing prices on last trading day of each year
                years = yearwise_dividend["Year"].tolist()
                close_prices = []
                for y in years:
                    try:
                        price_data = yf.download(yf_ticker, start=f"{y}-12-20", end=f"{y+1}-01-10")
                        price_data = price_data[price_data["Close"].notnull()]
                        if not price_data.empty:
                            last_price = price_data["Close"].iloc[-1]
                        else:
                            last_price = None
                    except:
                        last_price = None
                    close_prices.append(last_price)

                yearwise_dividend["Year End Price"] = close_prices
                yearwise_dividend["Dividend Yield %"] = (yearwise_dividend["Dividend"] / yearwise_dividend["Year End Price"]) * 100
                yearwise_dividend = yearwise_dividend.round(2)

                st.success(f"Year-wise dividend + return for {yf_ticker}")
                st.dataframe(yearwise_dividend)

                with st.expander("📋 Show Full Dividend Entries"):
                    st.dataframe(df[["Ex-Date", "Dividend"]])
            else:
                st.info(f"No dividends for {yf_ticker} in the selected date range.")
        else:
            st.warning(f"No dividend data available for {yf_ticker}.")

        # --- News Section ---
        st.subheader("📰 Latest News")
        try:
            yahoo_url = f"https://finance.yahoo.com/quote/{yf_ticker}?p={yf_ticker}"
            headers = {"User-Agent": "Mozilla/5.0"}
            res = requests.get(yahoo_url, headers=headers)
            soup = BeautifulSoup(res.text, 'html.parser')

            headlines = soup.find_all("h3", class_="Mb(5px)")
            for h in headlines[:5]:
                a = h.find("a")
                if a:
                    title = a.text.strip()
                    link = "https://finance.yahoo.com" + a['href']
                    st.markdown(f"- [{title}]({link})")
        except Exception as news_err:
            st.error(f"Failed to fetch news: {news_err}")

    except Exception as e:
        st.error(f"Error fetching data: {e}")
