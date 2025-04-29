const apiUrl = 'http://localhost:5000/api/data?file=recent';

async function fetchAndPlotCSV() {
  try {
    const response = await fetch(apiUrl);
    const csvText = await response.text();

    // Parse CSV manually
    const rows = csvText.trim().split('\n').map(row => row.split(','));
    const headers = rows.shift();

    // Assuming the first column is X (e.g., Date) and second column is Y (e.g., Value)
    const datetime = [];
    const y = [];

    rows.forEach(row => {
      datetime.push(row[0]);
      y.push(parseFloat(row[1]));
    });

    const trace = {
      x: datetime,
      y: y,
      mode: 'lines+markers',
      type: 'scatter'
    };

    Plotly.newPlot('plot', [trace], {
      title: 'CSV Data Plot',
      xaxis: { title: headers[0] },
      yaxis: { title: headers[1] }
    });
  } catch (error) {
    console.error('Error fetching or plotting CSV:', error);
  }
}

fetchAndPlotCSV();