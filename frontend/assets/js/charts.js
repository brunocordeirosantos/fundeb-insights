/**
 * charts.js — reusable chart factory using Plotly.js.
 * Each function receives a container ID and data, returns a Plotly chart.
 */

function renderBarChart(containerId, { labels, values, title }) {
  Plotly.newPlot(containerId, [{
    type: "bar",
    x: labels,
    y: values,
    marker: { color: "#4f8ef7" },
  }], {
    title: { text: title, font: { color: "#e8eaf0" } },
    paper_bgcolor: "#1a1d27",
    plot_bgcolor: "#1a1d27",
    font: { color: "#8b8fa8" },
    margin: { t: 40, b: 40, l: 40, r: 20 },
  });
}

function renderScatterChart(containerId, { x, y, labels, title }) {
  Plotly.newPlot(containerId, [{
    type: "scatter",
    mode: "markers",
    x,
    y,
    text: labels,
    marker: { color: "#00d4aa", size: 7, opacity: 0.8 },
  }], {
    title: { text: title, font: { color: "#e8eaf0" } },
    paper_bgcolor: "#1a1d27",
    plot_bgcolor: "#1a1d27",
    font: { color: "#8b8fa8" },
    margin: { t: 40, b: 40, l: 40, r: 20 },
  });
}
