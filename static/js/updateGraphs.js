// services/static/js/updateGraphs.js

/**
 * Call backend to update graphs for a location and render with Plotly
 * @param {string} location - e.g. "Bismarck"
 * @param {string} dataset - e.g. "Gauge Height"
 * @param {string} modalId - the ID of the modal containing the graph
 */
async function fetchAndUpdateGraph(location, dataset, modalId) {
    try {
      // 👉 This URL must point to your backend view that triggers update.py
      // For example, if the backend exposes /update/ or /api/timeseries/
      const resp = await fetch(
        `/api/timeseries/?location=${encodeURIComponent(location)}&dataset=${encodeURIComponent(dataset)}`
      );
      const json = await resp.json();
  
      // Find the modal
      const modal = document.getElementById(modalId);
  
      // Look for a Plotly container or create one
      let plotDiv = modal.querySelector(".plotly-graph");
      if (!plotDiv) {
        plotDiv = document.createElement("div");
        plotDiv.className = "plotly-graph";
        modal.querySelector(".modal-content").appendChild(plotDiv);
      }
  
      // Build trace
      const trace = {
        x: json.times,
        y: json.values,
        type: "scatter",
        mode: "lines+markers",
        name: `${json.location} ${json.dataset}`,
      };
  
      const layout = {
        title: `${json.location} - ${json.dataset}`,
        xaxis: { title: "Time" },
        yaxis: { title: "Value" },
      };
  
      // Render or update
      Plotly.react(plotDiv, [trace], layout);
    } catch (err) {
      console.error("Graph update failed:", err);
    }
  }
  
  /**
   * Hook for map pin clicks
   */
  function attachMapPinHandler(pinElement, location, dataset, modalId) {
    pinElement.addEventListener("click", () => {
      document.getElementById(modalId).style.display = "block"; // open modal
      fetchAndUpdateGraph(location, dataset, modalId); // update graph
    });
  }
  