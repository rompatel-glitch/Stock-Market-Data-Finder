let stockChart;
let stockData = {};

async function fetchStockData() {
    const companyName = document.getElementById("companyName").value;
    const response = await fetch(`/get_stock?company_name=${companyName}`);
    const data = await response.json();

    const resultsDiv = document.getElementById("results");
    resultsDiv.innerHTML = "";

    if (data.error) {
        resultsDiv.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
        return;
    }

    const { ticker, fundamental_details, historical_prices, company_info } = data;
    stockData = historical_prices;

    let historicalDataHTML = "<h3>Historical Prices (Last 30 Days)</h3><table class='table'><tr><th>Date</th><th>Open</th><th>High</th><th>Low</th><th>Close</th></tr>";
    const labels = [], closingPrices = [], openPrices = [], highPrices = [], lowPrices = [];

    historical_prices.forEach(item => {
        labels.push(item.date);
        closingPrices.push(item.Close);
        openPrices.push(item.Open);
        highPrices.push(item.High);
        lowPrices.push(item.Low);
        historicalDataHTML += `<tr><td>${item.date}</td><td>${item.Open.toFixed(2)}</td><td>${item.High.toFixed(2)}</td><td>${item.Low.toFixed(2)}</td><td>${item.Close.toFixed(2)}</td></tr>`;
    });
    historicalDataHTML += "</table>";

    resultsDiv.innerHTML = `
        <div class="company-info">
            <h2>${company_info.Name}</h2>
            <p><strong>Sector:</strong> ${company_info.Sector}</p>
            <p><strong>Industry:</strong> ${company_info.Industry}</p>
            <p>${company_info.Description}</p>
        </div>

        <h3>Fundamental Financials</h3>
        <table class="table table-bordered">
            <tr><th>Revenue (Billion $)</th><td>${fundamental_details.Revenue}</td></tr>
            <tr><th>Net Income (Billion $)</th><td>${fundamental_details.NetIncome}</td></tr>
            <tr><th>EPS</th><td>${fundamental_details.EPS}</td></tr>
            <tr><th>Market Cap (Billion $)</th><td>${fundamental_details.MarketCap}</td></tr>
            <tr><th>P/E Ratio</th><td>${fundamental_details["P/E Ratio"]}</td></tr>
        </table>

        ${historicalDataHTML}

        <div class="chart-container">
            <h3>Stock Price Trend</h3>
            <div class="radio-options">
                <label><input type="radio" name="priceType" value="Close" checked onclick="updateChart()"> Close</label>
                <label><input type="radio" name="priceType" value="Open" onclick="updateChart()"> Open</label>
                <label><input type="radio" name="priceType" value="High" onclick="updateChart()"> High</label>
                <label><input type="radio" name="priceType" value="Low" onclick="updateChart()"> Low</label>
            </div>
            <canvas id="stockChart"></canvas>
        </div>
    `;

    // Initial chart setup (Showing "Close" price initially)
    stockChart = new Chart(document.getElementById("stockChart"), {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Closing Price',
                data: closingPrices,
                borderColor: 'blue',
                fill: false
            }]
        }
    });
}

function updateChart() {
    const selectedType = document.querySelector('input[name="priceType"]:checked').value;
    const datasetMap = {
        "Close": stockData.map(d => d.Close),
        "Open": stockData.map(d => d.Open),
        "High": stockData.map(d => d.High),
        "Low": stockData.map(d => d.Low)
    };
    const colors = {
        "Close": "blue",
        "Open": "green",
        "High": "red",
        "Low": "black"
    };

    stockChart.data.datasets[0].data = datasetMap[selectedType];
    stockChart.data.datasets[0].label = selectedType + " Price";
    stockChart.data.datasets[0].borderColor = colors[selectedType];
    stockChart.update();
}
