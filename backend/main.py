import os
import openai
import yfinance as yf
import pandas as pd
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Initialize Flask App
app = Flask(__name__, template_folder="templates", static_folder="static")

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


def get_ticker_from_name(company_name):
    """Fetches the stock ticker symbol for a given company name using OpenAI API."""
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

        # Get Historical Data (Last 5 Days)
        historical_data = stock.history(period="5d")[['Open', 'High', 'Low', 'Close', 'Volume']]
        historical_data = historical_data.reset_index().to_dict(orient="records")

        return {"historical_data": historical_data}
    except Exception as e:
        return None


@app.route("/get_stock_data", methods=["POST"])
def fetch_stock_data():
    data = request.json
    company_name = data.get("company_name")

    if not company_name:
        return jsonify({"error": "Company name is required!"}), 400

    ticker = get_ticker_from_name(company_name)

    if not ticker:
        return jsonify({"error": "Could not determine the stock ticker. Try again."}), 404

    stock_data = get_stock_data(ticker)

    if not stock_data:
        return jsonify({"error": "Failed to retrieve stock data."}), 500

    return jsonify({
        "company_name": company_name,
        "ticker": ticker,
        "stock_data": stock_data
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
