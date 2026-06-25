// Subtle hover pulse on metric cards (runs inside Streamlit iframe)
(function () {
  const style = document.createElement("style");
  style.textContent = `
    .metric-card { cursor: default; }
    .metric-value { transition: color 0.3s ease; }
    .metric-card:hover .metric-value { color: #6c63ff; }
  `;
  document.head.appendChild(style);
})();
