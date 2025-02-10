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
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are an AI that finds the correct stock ticker based on a company name."},
                {"role": "user", "content": f"Find the stock ticker for '{company_name}' and return ONLY the ticker symbol."}
            ],
            max_tokens=10
        )
        result = response["choices"][0]["message"]["content"].strip().upper()

        # Check if OpenAI returned a valid ticker
        if " " not in result and 1 <= len(result) <= 6:
            return result
        
        logging.warning(f"OpenAI returned invalid ticker: {result}")
        return None
    except Exception as e:
        logging.error(f"Error fetching ticker from OpenAI: {e}")
        return None

def get_stock_data(ticker):
    """Fetches stock market data, financials, historical details, and company info."""
    try:
        stock = yf.Ticker(ticker)

        # Get fundamental financials
        financials = stock.financials if "Total Revenue" in stock.financials.index else None
        fundamental_details = {
            "Revenue": round(financials.loc["Total Revenue"][0] / 1e9, 2) if financials is not None else "N/A",
            "Net Income": round(financials.loc["Net Income"][0] / 1e9, 2) if financials is not None else "N/A",
            "EPS": round(stock.info.get("trailingEps", 0), 2),
            "Market Cap": round(stock.info.get("marketCap", 0) / 1e9, 2) if stock.info.get("marketCap") else "N/A",
            "P/E Ratio": round(stock.info.get("trailingPE", 0), 2) if stock.info.get("trailingPE") else "N/A"
        }

        # Get historical stock prices (Last 15 Days)
        history = stock.history(period="15d")
        if history.empty:
            return None, None, None

        history = history.reset_index().rename(columns={"Date": "date"})
        history["date"] = history["date"].dt.strftime('%Y-%m-%d')
        historical_prices = history.to_dict(orient="records")

        # Get company info
        company_info = {
            "Name": stock.info.get("longName", "N/A"),
            "Sector": stock.info.get("sector", "N/A"),
            "Industry": stock.info.get("industry", "N/A"),
            "Description": stock.info.get("longBusinessSummary", "N/A")
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
            if search_results and search_results.history(period="1d").empty is False:
                ticker = company_name
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
