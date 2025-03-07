let stockChart;
let stockData = {};

async function fetchStockData() {
    const companyName = document.getElementById("stockInput").value;
    const response = await fetch(`/get_stock?company_name=${companyName}`);
    const data = await response.json();

    // Debugging: Log the API response
    console.log("API Response:", data);

    if (data.error) {
        document.getElementById("errorMessage").innerText = data.error;
        document.getElementById("errorMessage").style.display = "block";
        return;
    }

    // Ensure `historical_prices` exists and has values
    if (!data.historical_prices || data.historical_prices.length === 0) {
        document.getElementById("errorMessage").innerText = "No historical stock data found.";
        document.getElementById("errorMessage").style.display = "block";
        return;
    }

    // Reset error message
    document.getElementById("errorMessage").style.display = "none";

    // Clear previous data
    let labels = [];
    let closingPrices = [];
    let openPrices = [];
    let highPrices = [];
    let lowPrices = [];
    let historicalDataHTML = "";

    data.historical_prices.forEach(item => {
        labels.push(item.date);
        
        // Fix: Use correct key names & provide a default value (0) to avoid undefined errors
        const openPrice = item.Open ?? 0;
        const highPrice = item.High ?? 0;
        const lowPrice = item.Low ?? 0;
        const closePrice = item.close_price ?? 0; // Match backend response key

        closingPrices.push(closePrice);
        openPrices.push(openPrice);
        highPrices.push(highPrice);
        lowPrices.push(lowPrice);

        historicalDataHTML += `<tr>
            <td>${item.date}</td>
            <td>${openPrice.toFixed(2)}</td>
            <td>${highPrice.toFixed(2)}</td>
            <td>${lowPrice.toFixed(2)}</td>
            <td>${closePrice.toFixed(2)}</td>
        </tr>`;
    });

    document.getElementById("historicalData").innerHTML = historicalDataHTML;

    updateChart(labels, closingPrices);
}

// Fix: Ensure chart is updated properly
function updateChart(labels, stockData) {
    const ctx = document.getElementById("stockChart").getContext("2d");

    if (window.stockChartInstance) {
        window.stockChartInstance.destroy(); // Clear previous chart
    }

    window.stockChartInstance = new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [{
                label: "Stock Closing Price",
                data: stockData,
                borderColor: "blue",
                fill: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
}
