let stockChartInstance; // Ensure only one Chart.js instance exists

async function fetchStockData() {
    const companyName = document.getElementById("stockInput").value; // Ensure correct ID is used
    document.getElementById("loading").style.display = "block"; // Show loading indicator

    try {
        const response = await fetch(`/get_stock?company_name=${companyName}`);
        const data = await response.json();

        console.log(" API Response:", data); // Debugging

        document.getElementById("loading").style.display = "none"; // Hide loading indicator

        if (data.error) {
            document.getElementById("errorMessage").innerText = data.error;
            document.getElementById("errorMessage").style.display = "block";
            return;
        }

        if (!data.historical_prices || data.historical_prices.length === 0) {
            document.getElementById("errorMessage").innerText = "No historical stock data found.";
            document.getElementById("errorMessage").style.display = "block";
            return;
        }

        document.getElementById("errorMessage").style.display = "none";

        // Prepare data
        let labels = [];
        let closingPrices = [];
        let openPrices = [];
        let highPrices = [];
        let lowPrices = [];
        let historicalDataHTML = "";

        data.historical_prices.forEach(item => {
            labels.push(item.date);

            const openPrice = parseFloat(item.Open ?? 0);
            const highPrice = parseFloat(item.High ?? 0);
            const lowPrice = parseFloat(item.Low ?? 0);
            const closePrice = parseFloat(item.close_price ?? 0); // Match backend response key

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

        // Update the chart
        updateChart(labels, closingPrices);

    } catch (error) {
        console.error(" Error fetching stock data:", error);
        document.getElementById("loading").style.display = "none";
        document.getElementById("errorMessage").innerText = "An error occurred. Please try again.";
        document.getElementById("errorMessage").style.display = "block";
    }
}

// Fix: Ensure the chart updates properly
function updateChart(labels, stockData) {
    const ctx = document.getElementById("stockChart").getContext("2d");

    if (stockChartInstance) {
        stockChartInstance.destroy(); // Clear previous chart before creating a new one
    }

    stockChartInstance = new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [{
                label: "Stock Closing Price",
                data: stockData,
                borderColor: "blue",
                borderWidth: 2,
                fill: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
}
