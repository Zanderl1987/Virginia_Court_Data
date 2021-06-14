var opts = {
    angle: 0, // The span of the gauge arc
    lineWidth: 0.4, // The line thickness
    radiusScale: 1, // Relative radius
    pointer: {
      length: 0.6, // // Relative to gauge radius
      strokeWidth: 0.035, // The thickness
      color: '#3495eb' // Fill color
    },
    limitMax: true,     // If false, max value increases automatically if value > maxValue
    limitMin: true,     // If true, the min value of the gauge will be fixed
    //percentColors:[[0.0, "#00ff00"],[1.0, "#0000ff"]],
    //colorStart: '#ff0000',   // Colors
    //colorStop: 'linear-gradient(#000000, #ffffff)',
    //colorStop: '#0000ff',    // just experiment with them
    //strokeColor: '#E0E0E0',  // to see which ones work best for you

    generateGradient: true,
    highDpiSupport: true,     // High resolution support
    // renderTicks is Optional
    renderTicks: {
      divisions: 5,
      divWidth: 1.1,
      divLength: 0.7,
      divColor: '#333333',
      subDivisions: 3,
      subLength: 0.5,
      subWidth: 0.6,
      subColor: '#666666'
    },
    staticLabels: {
        font: "14px sans-serif",  // Specifies font
        labels: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],  // Print labels at these values
        color: "#000000",  // Optional: Label text color
        fractionDigits: 0  // Optional: Numerical precision. 0=round off.
      },
        //https://coolors.co/gradient-palette/ed6742-ed4242?number=9
        staticZones: [
         {strokeStyle: "#4C69DA", min: 0, max: 0.3}, //Dodger Blue
         {strokeStyle: "#4E78C4", min: 0.3, max: 0.6}, // Turquoise Surf
         {strokeStyle: "#5186AE", min: 0.6, max: 0.9}, // Caribbean Green
         {strokeStyle: "#539597", min: 0.9, max: 1.2}, // Malachite
         {strokeStyle: "#56A481", min: 1.2, max: 1.5},  // Asparagus
         {strokeStyle: "#58B26B", min: 1.5, max: 1.8}, //Olivine
         {strokeStyle: "#5AC155", min: 1.8, max: 2.1}, // Chinese Green
         {strokeStyle: "#5DCF3E", min: 2.1, max: 2.4}, // Yellow Rose
         {strokeStyle: "#5FDE28", min: 2.4, max: 2.7}, // Tangerine Yellow
         {strokeStyle: "#72DD26", min: 2.7, max: 3.0},  // Orange (RYB)
         {strokeStyle: "#84DB24", min: 3.0, max: 3.3}, // Vivid Orange
         {strokeStyle: "#97DA22", min: 3.3, max: 3.6}, // Ferrari Red
         {strokeStyle: "#AAD921", min: 3.6, max: 3.9},  // Electric Red
         {strokeStyle: "#BCD71F", min: 3.9, max: 4.2},  // Electric Red
         {strokeStyle: "#CFD61D", min: 4.2, max: 4.5},  // Orange (RYB)
         {strokeStyle: "#E1D41B", min: 4.5, max: 4.8}, // Vivid Orange
         {strokeStyle: "#F4D319", min: 4.8, max: 5.1}, // Ferrari Red
         {strokeStyle: "#F1DB2E", min: 5.1, max: 5.5},  // Electric Red
         {strokeStyle: "#EDE342", min: 5.5, max: 5.8},  // Electric Red
         {strokeStyle: "#EDD542", min: 5.8, max: 6.1}, // Vivid Orange
         {strokeStyle: "#EDC742", min: 6.1, max: 6.4}, // Ferrari Red
         {strokeStyle: "#EDBA42", min: 6.4, max: 6.7},  // Electric Red
         {strokeStyle: "#EDBA42", min: 6.7, max: 7.0},  // Electric Red
         {strokeStyle: "#EDAC42", min: 7.0, max: 7.3},  // Orange (RYB)
         {strokeStyle: "#ED9E42", min: 7.3, max: 7.6}, // Vivid Orange
         {strokeStyle: "#ED9042", min: 7.6, max: 7.9}, // Ferrari Red
         {strokeStyle: "#ED8342", min: 7.9, max: 8.2},  // Electric Red
         {strokeStyle: "#ED7542", min: 8.2, max: 8.5},  // Electric Red
         {strokeStyle: "#ED6742", min: 8.5, max: 8.8},  // Electric Red
         {strokeStyle: "#ED6242", min: 8.8, max: 9.1},  // Electric Red
         {strokeStyle: "#ED5E42", min: 9.1, max: 9.4},  // Electric Red
         {strokeStyle: "#ED5942", min: 9.4, max: 9.7},  // Electric Red
         {strokeStyle: "#ED5542", min: 9.7, max: 10.0},  // Electric Red
         {strokeStyle: "#ED5042", min: 10.0, max: 10.3},  // Electric Red
         {strokeStyle: "#ED4B42", min: 10.3, max: 10.6},  // Electric Red
         {strokeStyle: "#ED4242", min: 10.6, max: 11.0}  // Electric Red


       ]
    
  };
  var target = document.getElementById('gauge2'); // your canvas element
  var ctx = target.getContext("2d");
  // Create gradient
  var grd = ctx.createLinearGradient(0, 0, 200, 0);
  grd.addColorStop(0, "red");
  grd.addColorStop(1, "white");
  //var gradientStroke = target.createLinearGradient(500, 0, 100, 0);
  //gradientStroke.addColorStop(0, '#80b6f4');
  //gradientStroke.addColorStop(1, '#f49080');  
  var gauge = new Gauge(target).setOptions(opts); // create sexy gauge!
  gauge.options.colorStop = '#0000ff';
  gauge.maxValue = 11; // set max gauge value
  gauge.setMinValue(0);  // Prefer setter over gauge.minValue = 0
  gauge.animationSpeed = 32; // set animation speed (32 is default value)
  //gauge.createLinearGradient(0, h * 2, w * 2, h * 2);
  gauge.options.pointer.color = "#F2BF6C"
  gauge.set([0, 0]); // set actual value
  
  updateData()

  function updateData() {
    // Send dates to the server and get response
    fetch('/glucMetrics2/gauge2-changed', {
      method: "POST",
      credentials: "include",
      body: JSON.stringify(''),
      cache: "no-cache",
      headers: new Headers({
          "content-type": "application/json"
      })
    })
    .then(function(response) {
        if (response.status !== 200) {
            console.log(`Looks like there was a problem. Status code: ${response.status}`);
            return;
        }
        response.json().then(function(data) {
            
            console.log(data)
            //Select APSystem
            gauge.set([data.gauge2_value1, data.gauge2_value2])
            $("#hypoInd1").html(data.hypoInd);
            $("#hyperInd1").html(data.hyperInd);
            $("#gauge2_title").html(data.gauge2_title);
            
        });
    })
    .catch(function(error) {
        console.log("Fetch error: " + error);
    });
  }