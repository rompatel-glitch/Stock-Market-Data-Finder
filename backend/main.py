import os
import requests
import yfinance as yf
import streamlit as st
from dotenv import load_dotenv
from alpha_vantage.timeseries import TimeSeries
import openai

# Load API keys from .env file
load_dotenv()
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

st.set_page_config(page_title="AI Finance Agent", page_icon="📈")


# Function to get stock ticker from company name using GPT
def get_ticker_from_name(company_name):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a finance assistant helping find stock tickers."},
                {"role": "user", "content": f"What is the stock ticker symbol for {company_name}?"}
            ],
            max_tokens=10
        )
        return response["choices"][0]["message"]["content"].strip().upper()
    except Exception as e:
        return None


# Fetch stock data from Alpha Vantage
def get_stock_info_alpha_vantage(ticker):
    try:
        ts = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format="json")
        data, _ = ts.get_quote_endpoint(symbol=ticker)
        return {
            "Current Price": data.get("05. price", "N/A"),
            "52-Week High": data.get("03. high", "N/A"),
            "52-Week Low": data.get("04. low", "N/A"),
            "Market Cap": "N/A",
            "Volume": data.get("06. volume", "N/A"),
        }
    except Exception as e:
        return {"error": f"❌ Alpha Vantage error: {e}"}


# Fetch stock data from Yahoo Finance
def get_stock_info_yahoo(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.fast_info if hasattr(stock, "fast_info") else {}

        return {
            "Current Price": info.get("last_price", "N/A"),
            "52-Week High": info.get("yearHigh", "N/A"),
            "52-Week Low": info.get("yearLow", "N/A"),
            "Market Cap": info.get("marketCap", "N/A"),
            "Volume": info.get("volume", "N/A"),
        }
    except Exception as e:
        return {"error": f"❌ Yahoo Finance error: {e}"}


# Get company details (5-sentence summary) using GPT
def get_company_overview(company_name):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a finance assistant providing company overviews."},
                {"role": "user", "content": f"Provide a 5-sentence summary about {company_name}."}
            ],
            max_tokens=150
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"❌ Error fetching company overview: {e}"


# Get AI-generated stock analysis using GPT
def get_ai_stock_analysis(ticker, stock_info):
    try:
        stock_details = "\n".join([f"{key}: {value}" for key, value in stock_info.items() if value != "N/A"])
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a financial AI providing stock market insights."},
                {"role": "user",
                 "content": f"Analyze the stock {ticker} using this data:\n{stock_details}\nProvide insights in 3-4 sentences."}
            ],
            max_tokens=200
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"❌ Error fetching AI insights: {e}"


# Aggregate stock data from multiple sources
def get_best_stock_info(ticker):
    alpha_data = get_stock_info_alpha_vantage(ticker)
    yahoo_data = get_stock_info_yahoo(ticker)

    aggregated_info = {}
    sources_used = []
    errors = []

    for key in ["Current Price", "52-Week High", "52-Week Low", "Market Cap", "Volume"]:
        alpha_value = alpha_data.get(key, "N/A")
        yahoo_value = yahoo_data.get(key, "N/A")

        if alpha_value != "N/A":
            aggregated_info[key] = alpha_value
            sources_used.append("Alpha Vantage")
        elif yahoo_value != "N/A":
            aggregated_info[key] = yahoo_value
            sources_used.append("Yahoo Finance")
        else:
            aggregated_info[key] = "N/A"

    if "error" in alpha_data:
        errors.append(alpha_data["error"])
    if "error" in yahoo_data:
        errors.append(yahoo_data["error"])

    return aggregated_info, sources_used, errors


# Streamlit App UI
st.title("📊 AI Finance Agent")

company_name = st.text_input("Enter Company Name (e.g., Tesla, Apple, Google)")

if st.button("Get Stock Info"):
    if company_name:
        with st.spinner("🔍 Fetching stock ticker..."):
            ticker = get_ticker_from_name(company_name)

        if not ticker:
            st.error("❌ Could not determine the stock ticker. Try again.")
        else:
            with st.spinner("🔍 Fetching stock data & AI insights..."):
                company_overview = get_company_overview(company_name)
                stock_info, sources_used, errors = get_best_stock_info(ticker)
                ai_analysis = get_ai_stock_analysis(ticker, stock_info)

            # Display company details
            st.subheader(f"🏢 About {company_name}")
            st.write(company_overview)

            # Display stock data
            st.subheader(f"📌 AI-Generated Stock Overview for {company_name} ({ticker})")

            st.markdown("### 📊 Stock Data")
            for key, value in stock_info.items():
                st.write(f"**{key}:** {value}")

            # Sources used
            st.markdown("### 📌 Sources Used")
            st.write(f"✅ Data collected from: {', '.join(sources_used)}")

            # AI Insights
            st.markdown("### 🤖 AI Insights")
            st.write(ai_analysis)

            # Errors
            if errors:
                st.markdown("### ⚠️ Errors Encountered")
                for error in errors:
                    st.error(error)
    else:
        st.warning("Please enter a company name to proceed.")
