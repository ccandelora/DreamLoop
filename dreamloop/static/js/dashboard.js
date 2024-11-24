// static/js/dashboard.js

// Fetch dream data from API
async function fetchDreamData() {
    const response = await fetch("/api/dreams");
    return await response.json();
}

// Fetch summary data from API
async function fetchSummaryData() {
    const response = await fetch("/api/summary");
    return await response.json();
}

// Initialize dashboard when DOM is loaded
document.addEventListener("DOMContentLoaded", async () => {
    const dreamData = await fetchDreamData();
    const summaryData = await fetchSummaryData();

    updateSummaryCards(summaryData);
    initializeSentimentChart(dreamData);
    initializeLucidityChart(dreamData);
    initializePositionChart(summaryData.position_counts);
    initializeEmotionChart(summaryData.emotion_counts);
    populateDreamsTable(dreamData);
    initializeTabNavigation();
});

// Tab Navigation
function initializeTabNavigation() {
    const tabButtons = document.querySelectorAll(".tab-button");
    const tabContents = document.querySelectorAll(".tab-content");

    tabButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const tabName = button.dataset.tab;

            // Update active button
            tabButtons.forEach((btn) => btn.classList.remove("bg-purple-700"));
            button.classList.add("bg-purple-700");

            // Show selected tab content
            tabContents.forEach((content) => {
                content.style.display =
                    content.id === tabName ? "block" : "none";
            });
        });
    });
}

// Update summary cards with data
function updateSummaryCards(summaryData) {
    document.getElementById("totalDreams").textContent =
        summaryData.total_dreams;
    document.getElementById("avgSentiment").textContent =
        summaryData.avg_sentiment.toFixed(2);
    document.getElementById("avgLucidity").textContent =
        summaryData.avg_lucidity.toFixed(2);

    // Find most common position
    const positions = Object.entries(summaryData.position_counts);
    positions.sort((a, b) => b[1] - a[1]);
    document.getElementById("commonPosition").textContent = positions[0][0];
}

// Initialize Sentiment Chart
function initializeSentimentChart(data) {
    const ctx = document.getElementById("sentimentChart").getContext("2d");

    new Chart(ctx, {
        type: "line",
        data: {
            labels: data.map((dream) => dream.date),
            datasets: [
                {
                    label: "Sentiment Score",
                    data: data.map((dream) => dream.sentiment_score),
                    borderColor: "rgb(99, 102, 241)",
                    backgroundColor: "rgba(99, 102, 241, 0.1)",
                    fill: true,
                },
                {
                    label: "Sentiment Magnitude",
                    data: data.map((dream) => dream.sentiment_magnitude),
                    borderColor: "rgb(147, 51, 234)",
                    backgroundColor: "rgba(147, 51, 234, 0.1)",
                    fill: true,
                },
            ],
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                },
            },
            interaction: {
                intersect: false,
                mode: "index",
            },
        },
    });
}

// Initialize Lucidity Chart
function initializeLucidityChart(data) {
    const ctx = document.getElementById("lucidityChart").getContext("2d");

    new Chart(ctx, {
        type: "bar",
        data: {
            labels: data.map((dream) => dream.date),
            datasets: [
                {
                    label: "Lucidity Level",
                    data: data.map((dream) => dream.lucidity_level),
                    backgroundColor: "rgba(147, 51, 234, 0.5)",
                    borderColor: "rgb(147, 51, 234)",
                    borderWidth: 1,
                },
            ],
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 1,
                },
            },
        },
    });
}

// Initialize Position Chart
function initializePositionChart(positionCounts) {
    const ctx = document.getElementById("positionChart").getContext("2d");

    new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: Object.keys(positionCounts),
            datasets: [
                {
                    data: Object.values(positionCounts),
                    backgroundColor: [
                        "rgba(99, 102, 241, 0.5)",
                        "rgba(147, 51, 234, 0.5)",
                        "rgba(236, 72, 153, 0.5)",
                        "rgba(248, 113, 113, 0.5)",
                    ],
                },
            ],
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: "bottom",
                },
            },
        },
    });
}

// Initialize Emotion Chart
function initializeEmotionChart(emotionCounts) {
    const ctx = document.getElementById("emotionChart").getContext("2d");

    new Chart(ctx, {
        type: "bar",
        data: {
            labels: Object.keys(emotionCounts),
            datasets: [
                {
                    label: "Frequency",
                    data: Object.values(emotionCounts),
                    backgroundColor: "rgba(99, 102, 241, 0.5)",
                    borderColor: "rgb(99, 102, 241)",
                    borderWidth: 1,
                },
            ],
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1,
                    },
                },
            },
            plugins: {
                legend: {
                    display: false,
                },
            },
        },
    });
}

// Populate Dreams Table
function populateDreamsTable(data) {
    const tableBody = document.getElementById("dreamsTableBody");
    tableBody.innerHTML = "";

    data.sort((a, b) => new Date(b.date) - new Date(a.date));

    data.forEach((dream) => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${dream.date}</td>
            <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm font-medium text-gray-900">${dream.title}</div>
                <div class="text-sm text-gray-500">${dream.content.substring(0, 50)}...</div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${dream.mood}</td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                    dream.sentiment_score > 0
                        ? "bg-green-100 text-green-800"
                        : "bg-red-100 text-red-800"
                }">
                    ${dream.sentiment_score.toFixed(2)}
                </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${dream.lucidity_level.toFixed(2)}</td>
        `;
        tableBody.appendChild(row);
    });
}

// Add click handlers for table rows (dream details)
function initializeTableInteractions() {
    const tableRows = document.querySelectorAll("#dreamsTableBody tr");
    tableRows.forEach((row) => {
        row.addEventListener("click", () => {
            // Add dream detail view functionality here
            console.log("Dream details clicked");
        });
    });
}

// Helper function to format dates
function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
    });
}

// Helper function to get color based on sentiment score
function getSentimentColor(score) {
    if (score > 0.5) return "bg-green-100 text-green-800";
    if (score > 0) return "bg-green-50 text-green-600";
    if (score > -0.5) return "bg-red-50 text-red-600";
    return "bg-red-100 text-red-800";
}
