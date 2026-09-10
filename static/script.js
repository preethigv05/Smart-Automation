function analyzeUsage() {

    // Get values from website
    const temperature = document.getElementById("temperature").value;
    const occupancy = document.getElementById("occupancy").value;
    const electricity = document.getElementById("electricity").value;
    const hours = document.getElementById("hours").value;

    // Check empty values
    if (!temperature || !occupancy || !electricity || !hours) {
        alert("Please enter all values.");
        return;
    }

    // Send data to Flask + AI model
    fetch("/predict", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            temperature: temperature,
            occupancy: occupancy,
            electricity: electricity,
            hours: hours
        })
    })
    .then(response => response.json())
    .then(data => {

        // Display AI prediction
        document.getElementById("usageLevel").textContent =
            data.usage_level;

        document.getElementById("wastageStatus").textContent =
            data.wastage;

        document.getElementById("recommendation").textContent =
            data.recommendation;

        document.getElementById("efficiencyScore").textContent =
            data.efficiency + "%";

        // Progress bar
        document.getElementById("efficiencyProgress").style.width =
            data.efficiency + "%";
    })
    .catch(error => {
        console.error("Error:", error);
        alert("Unable to connect to AI server.");
    });
}