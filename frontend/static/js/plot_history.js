const apiUrl = '/api/data?file=recent';

async function fetchAndPlotCSV() {
  try {
    const response = await fetch(apiUrl);
    const csvText = await response.text();

    // Parse CSV manually
    const rows = csvText.trim().split('\n').map(row => row.split(','));
    const headers = rows.shift();

    // Assuming the first column is X (e.g., Date) and second column is Y (e.g., Value)
    const datetime = [];
    const cols = ['powerstation_percentage','powerstation_inputWAC','powerstation_inputWDC','powerstation_outputWAC','powerstation_outputWDC','relay1_power','relay2_power','relay3_power'];
    const y = {}


    for cols.forEach(c=>{
          y[c] = []
        })

    rows.forEach(row => {
      datetime.push(row[0]);
      cols.forEach(c=>{
        // get col position
        let i = arr.indexOf('banana'); 
        y[c].push(parseFloat(row[i]))
      })
      //y.push(parseFloat(row[1]));
    });

    
    traces = []

    cols.forEach(c=>{
      t = {
        x: datetime,
        y: y[c],
        mode: 'lines+markers',
        type: 'scatter'
      }

      traces.push(t)
    })

    // let trace1 = {
    //   x: datetime,
    //   y: y,
    //   mode: 'lines+markers',
    //   type: 'scatter'
    // };

    // let trace1 = {
    //   x: datetime,
    //   y: y,
    //   mode: 'lines+markers',
    //   type: 'scatter'
    // };

    Plotly.newPlot('plot',traces, {
      title: "Today's Data",
      xaxis: { title: headers[0] },
      yaxis: { title: headers[1] }
    });
  } catch (error) {
    console.error('Error fetching or plotting CSV:', error);
  }
}

fetchAndPlotCSV();