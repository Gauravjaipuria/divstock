import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="Dividend Tracker & News", layout="wide")
st.title("📆 Dividend Calendar & 📰 Yahoo Finance News")

# --- Date Selector ---
selected_date = st.date_input("Select a Date for Dividend Calendar", datetime.today())
tickers = ["AAPL", "MSFT", "TSLA", "JNJ", "KO", "T", "VZ", "PG", "PFE", "AMZN"]  # Add more tickers

# --- Dividend Calendar Section ---
st.subheader("🔍 Dividend Calendar")
div_data = []

for ticker in tickers:
    stock = yf.Ticker(ticker)
    try:
        dividends = stock.dividends
        if not dividends.empty:
            div_on_date = dividends[dividends.index.date == selected_date]
            if not div_on_date.empty:
                div_data.append({
                    "Ticker": ticker,
                    "Company Name": stock.info.get("shortName", "N/A"),
                    "Dividend": div_on_date.values[-1],
                    "Ex-Date": div_on_date.index[-1].date()
                })
    except:
        continue

if div_data:
    st.dataframe(pd.DataFrame(div_data))
else:
    st.info("No dividends found on selected date.")

# --- Yahoo Finance News Section ---
st.subheader("🗞️ Latest Yahoo Finance News")

def fetch_yahoo_news(ticker):
    base_url = f"https://finance.yahoo.com/quote/{ticker}?p={ticker}"
    response = requests.get(base_url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(response.text, "html.parser")
    news_items = soup.find_all("li", class_="js-stream-content")
    news = []

    for item in news_items[:5]:  # Limit to top 5 news
        headline_tag = item.find("h3")
        if headline_tag:
            headline = headline_tag.text
            link_tag = item.find("a", href=True)
            if link_tag:
                news.append({
                    "title": headline,
                    "link": "https://finance.yahoo.com" + link_tag["href"]
                })
    return news

ticker_news = st.text_input("Enter a Stock Ticker for News", "AAPL").upper()
if ticker_news:
    news_data = fetch_yahoo_news(ticker_news)
    if news_data:
        for n in news_data:
            st.markdown(f"**[{n['title']}]({n['link']})**")
    else:
        st.warning("No news found or unable to fetch.")

