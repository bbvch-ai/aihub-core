document.getElementById("fetchData").addEventListener("click", async () => {
    const responseDisplay = document.getElementById("apiResponse");
    try {
        const response = await fetch("/api/v1/health");
        const data = await response.json();
        responseDisplay.innerText = `API Response: ${JSON.stringify(data)}`;
    } catch (error) {
        responseDisplay.innerText = "Failed to fetch API data!";
        console.error("Error fetching data:", error);
    }
});
