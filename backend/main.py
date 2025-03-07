import os
import openai
import yfinance as yf
import pandas as pd
import logging
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv

# Load API Keys
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Initialize Flask App
app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app)  # Allow CORS for frontend interactions

# Setup logging
logging.basicConfig(level=logging.INFO)

@app.route("/")
def home():
    return render_template("index.html")

def get_ticker_from_name(company_name):
    """Fetches the stock ticker symbol for a given company name using OpenAI API."""
    try:
        logging.info(f"Fetching ticker for: {company_name} using OpenAI")

        client = openai.OpenAI()  # New OpenAI client instance
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are an AI that finds the correct stock ticker based on a company name."},
                {"role": "user", "content": f"Find the stock ticker for '{company_name}' and return ONLY the ticker symbol."}
            ],
            max_tokens=10
        )
        result = response.choices[0].message.content.strip().upper()

        # Ensure response is a valid ticker
        if " " not in result and 1 <= len(result) <= 6:
            logging.info(f"OpenAI returned ticker: {result}")
            return result
        
        logging.warning(f"OpenAI returned invalid ticker: {result}")
        return None
    except Exception as e:
        logging.error(f"Error fetching ticker from OpenAI: {e}")
        return None

import requests
import logging

def get_stock_data(ticker):
    """Fetch stock market data using Alpha Vantage API."""
    API_KEY = "ALPHA_VANTAGE_API_KEY"
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&apikey={API_KEY}"
    
    try:
        response = requests.get(url)
        data = response.json()

        # Check if the response contains stock data
        if "Time Series (Daily)" not in data:
            logging.error(f"Alpha Vantage API returned no data for {ticker}: {data}")
            return None, None, None

        # Extract historical stock prices (Last 15 Days)
        historical_prices = [
            {"date": date, "close_price": values["4. close"]}
            for date, values in sorted(data["Time Series (Daily)"].items(), reverse=True)[:15]
        ]

        # Dummy values for fundamental details (Alpha Vantage free API doesn't provide these)
        fundamental_details = {
            "Revenue": "N/A",
            "Net Income": "N/A",
            "EPS": "N/A",
            "Market Cap": "N/A",
            "P/E Ratio": "N/A"
        }

        # Dummy company info (Alpha Vantage free API doesn't provide this)
        company_info = {
            "Name": ticker,
            "Sector": "N/A",
            "Industry": "N/A",
            "Description": "Stock data retrieved from Alpha Vantage."
        }

        return fundamental_details, historical_prices, company_info

    except Exception as e:
        logging.error(f"Error fetching stock data for {ticker}: {e}")
        return None, None, None

@app.route("/get_stock", methods=["GET"])
def get_stock():
    company_name = request.args.get("company_name")

    if not company_name:
        return jsonify({"error": "Company name not provided"}), 400

    logging.info(f"Fetching stock data for: {company_name}")

    # First, try getting the ticker from OpenAI
    ticker = get_ticker_from_name(company_name)

    # If OpenAI fails, try using Yahoo Finance directly
    if not ticker:
        try:
            search_results = yf.Ticker(company_name)
            if search_results and not search_results.history(period="1d").empty:
                ticker = company_name
                logging.info(f"Using Yahoo Finance as fallback for ticker: {ticker}")
        except Exception as e:
            logging.warning(f"Could not determine ticker from Yahoo Finance: {e}")

    if not ticker:
        return jsonify({"error": "Could not determine the stock ticker. Try again."}), 404

    fundamental_details, historical_prices, company_info = get_stock_data(ticker)

    if fundamental_details is None:
        return jsonify({"error": "No data found for this ticker"}), 404

    return jsonify({
        "ticker": ticker,
        "fundamental_details": fundamental_details,
        "historical_prices": historical_prices,
        "company_info": company_info
    })

if __name__ == "__main__":
    app.run(debug=True)
