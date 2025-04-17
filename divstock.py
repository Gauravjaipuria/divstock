import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Dividend Calendar", layout="wide")
st.title("💰 Year-wise Dividend Summary + Return %")

# --- Inputs ---
ticker = st.text_input("Enter Stock Ticker (e.g., RELIANCE, AAPL)", "RELIANCE").upper()
market = st.radio("Select Market", ["India", "Other"])

# Modify ticker if Indian market is selected
if market == "India":
    ticker += ".NS"

start_date = st.date_input("Start Date", datetime(2020, 1, 1))
end_date = st.date_input("End Date", datetime.today())

if start_date > end_date:
    st.error("Start date must be before end date.")
else:
    try:
        stock = yf.Ticker(ticker)
        dividends = stock.dividends
        price_data = stock.history(start=start_date, end=end_date)

        if not dividends.empty:
            df = pd.DataFrame({"Ex-Date": dividends.index.date, "Dividend": dividends.values})
            df["Year"] = pd.to_datetime(df["Ex-Date"]).dt.year
            yearly_div = df.groupby("Year")["Dividend"].sum().reset_index()

            # Get year-end price for each year
            yearly_prices = []
            for year in yearly_div["Year"]:
                end_of_year = pd.Timestamp(f"{year}-12-31")
                next_day = end_of_year + pd.Timedelta(days=5)
                hist = stock.history(start=end_of_year, end=next_day)
                if not hist.empty:
                    close_price = hist["Close"].iloc[0]
                    yearly_prices.append(round(close_price, 2))
                else:
                    yearly_prices.append(None)

            yearly_div["Year End Price"] = yearly_prices
            yearly_div["Dividend Yield %"] = round((yearly_div["Dividend"] / yearly_div["Year End Price"]) * 100, 2)

            st.success(f"Year-wise dividend + return for {ticker}")
            st.dataframe(yearly_div)

            with st.expander("📅 Show Full Dividend Entries"):
                st.dataframe(df)
        else:
            st.warning(f"No dividend data available for {ticker}.")

        # --- EPS Fetch ---
        st.subheader("📊 Earnings Per Share (EPS)")
        try:
            info = stock.info
            eps = info.get("trailingEps")
            st.write(f"EPS: {eps if eps else 'Not available'}")
        except:
            st.warning("Unable to fetch EPS.")

        # --- 📰 Yahoo News ---
        st.subheader("📰 Latest News")
        try:
            news = stock.news
            for item in news[:5]:
                st.markdown(f"- [{item['title']}]({item['link']})")
        except:
            st.warning("Unable to fetch news.")

        # --- 📉 Transaction History & Dividend Tracker ---
        st.markdown("---")
        st.subheader("📊 Track Multiple Transactions & Total Dividends")

        if 'transactions' not in st.session_state:
            st.session_state.transactions = []

        with st.form("add_transaction"):
            col1, col2, col3 = st.columns(3)
            with col1:
                txn_date = st.date_input("Transaction Date", value=datetime(2022, 1, 1), key="date")
            with col2:
                quantity = st.number_input("Quantity", value=10, min_value=1)
            with col3:
                price = st.number_input("Price per Share", value=100.0, min_value=0.01)

            submitted = st.form_submit_button("➕ Add Transaction")
            if submitted:
                st.session_state.transactions.append({
                    "Date": txn_date,
                    "Quantity": quantity,
                    "Price": price
                })
                st.success("Transaction added!")

        # Display all transactions
        if st.session_state.transactions:
            st.markdown("### 📃 Your Transactions")
            txn_df = pd.DataFrame(st.session_state.transactions)

            # Calculate total dividend per transaction
            results = []
            for txn in st.session_state.transactions:
                txn_date = txn["Date"]
                qty = txn["Quantity"]
                price = txn["Price"]

                try:
                    hist_price = stock.history(start=txn_date, end=txn_date + pd.Timedelta(days=5))
                    txn_price = hist_price["Close"].iloc[0] if not hist_price.empty else price
                except:
                    txn_price = price

                dividends_after = dividends[dividends.index.date >= txn_date]
                total_div = round(dividends_after.sum() * qty, 2)
                return_pct = round((dividends_after.sum() / txn_price) * 100, 2)

                results.append({
                    "Transaction Date": txn_date,
                    "Quantity": qty,
                    "Price/Share": round(txn_price, 2),
                    "Total Dividend": total_div,
                    "Dividend Return %": return_pct
                })

            results_df = pd.DataFrame(results)
            st.dataframe(results_df)

            total_dividends = results_df["Total Dividend"].sum()
            st.success(f"💸 Total Dividend Received from All Transactions: ₹{round(total_dividends, 2)}")
        else:
            st.info("Add your stock transactions to see dividend earnings.")

    except Exception as e:
        st.error(f"Error fetching data: {e}")
