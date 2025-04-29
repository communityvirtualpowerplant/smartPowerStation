const apiUrl = '/api/data?file=recent';

function getColor(){
  r = (Math.floor(Math.random() * 205)+51).toString()
  g = (Math.floor(Math.random() * 205)+51).toString()
  b = (Math.floor(Math.random() * 205)+51).toString()
  a = (.5).toString();
  return 'rgba(${r},${g},${b},${a})'
}

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


    cols.forEach(c=>{
          y[c] = []
        })

    rows.forEach(row => {
      datetime.push(row[0]);
      cols.forEach(c=>{
        // get col position
        let i = headers.indexOf(c); 
        let v = parseFloat(row[i])
        y[c].push(isNaN(v) ? null : v)
      })
      //y.push(parseFloat(row[1]));
    });


    const shapes = []; // Will hold background color blocks
    const positions = ['A','B','C','D','E','F','G','EA','EB','EC','ED','EE','EF','EG','EH'];

    const modeColors = []

    positions.forEach(()=>{
      positionColors.push(getColor())
    })

    // Create background rectangles where mode changes
    let lastPosition = null;
    let startTime = null;

    for (let i = 0; i < datetime.length; i++) {
      const currentPosition = positions[i];
      const currentTime = datetime[i];
      if (currentPosition !== lastPosition) {
        if (lastPosition !== null) {
          // Close previous rectangle
          shapes.push({
            type: 'rect',
            xref: 'x',
            yref: 'paper',
            x0: startTime,
            x1: currentTime,
            y0: 0,
            y1: 1,
            fillcolor: positionColors[lastPosition],
            opacity: 0.3,
            line: { width: 0 }
          });
        }
        startTime = currentTime;
        lastPosition = currentPosition;
      }
    }

    // Add last rectangle
    if (lastPosition !== null) {
      shapes.push({
        type: 'rect',
        xref: 'x',
        yref: 'paper',
        x0: startTime,
        x1: datetime[datetime.length - 1],
        y0: 0,
        y1: 1,
        fillcolor: positionColors[lastPosition],
        opacity: 0.3,
        line: { width: 0 }
      });
    }



    traces = []

    cols.forEach(c=>{
      t = {
        x: datetime,
        y: y[c],
        mode: 'lines+markers',
        type: 'scatter',
        name:c.replace('powerstation','battery').replace('_',' ').replace('percentage','%')
      }

      traces.push(t)
    })

  // var layout = {
  //   title: {text: 'Smart Power Station Data'},
  //   xaxis: {
  //     autorange: true,
  //     range: ['2015-02-17', '2017-02-16'],
  //     rangeselector: {buttons: [
  //         {
  //           count: 1,
  //           label: '1d',
  //           step: 'day',
  //           stepmode: 'backward'
  //         },
  //         {
  //           count: 6,
  //           label: '1w',
  //           step: 'week',
  //           stepmode: 'backward'
  //         },

  //         {step: 'month'}

  //       ]},

  //     rangeslider: {range: ['2015-02-17', '2017-02-16']},
  //     type: 'date'

  //   },

  //   yaxis: {
  //     autorange: true,
  //     range: [86.8700008333, 138.870004167],
  //     type: 'linear'
  //   }
  // };  

    Plotly.newPlot('plot',traces, {
      title: "TSmart Power Station Data - Today",
      xaxis: { title: "Time" },
      yaxis: { title: "Data" },
      shapes: shapes  
    });
  } catch (error) {
    console.error('Error fetching or plotting CSV:', error);
  }
}

fetchAndPlotCSV();