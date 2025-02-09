import os
import openai
import yfinance as yf
import pandas as pd
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Stock Market Data Finder API Running!"})

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

@app.route("/get_stock", methods=["GET"])
def get_stock():
    company_name = request.args.get("company_name")
    
    if not company_name:
        return jsonify({"error": "Company name not provided"}), 400

    ticker = get_ticker_from_name(company_name)

    if not ticker:
        return jsonify({"error": "Could not determine the stock ticker. Try again."}), 404
    
    historical_data, financials, options = get_stock_data(ticker)

    if historical_data is None:
        return jsonify({"error": "No data found for this ticker"}), 404

    return jsonify({
        "ticker": ticker,
        "historical_data": historical_data.to_dict(),
        "financials": financials.to_dict() if financials is not None else "N/A",
        "options": options if options is not None else "N/A"
    })

if __name__ == "__main__":
    app.run(debug=True)
