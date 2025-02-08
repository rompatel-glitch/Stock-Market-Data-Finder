import os
import streamlit as st
import openai
import yfinance as yf
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

st.set_page_config(page_title="Stock Market Data Finder", page_icon="📊")
st.title("📊 Stock Market Data Finder")

company_name = st.text_input("Enter Company Name (e.g., Tesla, Apple, Google)")


def get_ticker_from_name(company_name):
    """
    Fetches the stock ticker symbol for a given company name using OpenAI API.
    Returns the best match or a list of possible matches if available.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system",
                 "content": "You are an AI that finds the correct stock ticker based on a company name."},
                {"role": "user",
                 "content": f"Find the stock ticker for '{company_name}'. If multiple results exist, provide a list of possible companies with their tickers. Use the format 'Company Name (TICKER)' for each entry."}
            ],
            max_tokens=100
        )

        result = response["choices"][0]["message"]["content"].strip()
        matches = [line.strip() for line in result.split("\n") if "(" in line and ")" in line]

        return matches[0].split("(")[-1].strip(")") if matches else None
    except Exception as e:
        return None


def get_stock_data(ticker):
    """ Fetches stock market data from Yahoo Finance. """
    try:
        stock = yf.Ticker(ticker)
        historical_data = stock.history(period="5d")[
            ['Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits']]
        financials = stock.financials
        options = stock.options
        return historical_data, financials, options
    except Exception as e:
        return None, None, None


if st.button("Get Stock Data"):
    if company_name:
        with st.spinner("🔍 Fetching stock ticker..."):
            ticker = get_ticker_from_name(company_name)

        if not ticker:
            st.error("❌ Could not determine the stock ticker. Try again.")
        else:
            with st.spinner("🔍 Fetching stock data..."):
                historical_data, financials, options = get_stock_data(ticker)

            st.markdown(f"### 📌 Stock Data for {company_name} ({ticker})")

            if historical_data is not None:
                st.markdown("### 📜 Historical Market Data (Last 5 Days)")
                st.dataframe(historical_data)

            if financials is not None:
                st.markdown("### 💰 Financial Statements")
                st.dataframe(financials)

    else:
        st.warning("⚠️ Please enter a company name.")
