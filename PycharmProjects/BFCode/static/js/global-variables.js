/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Dashboard Tutorial 
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

// Instance tour variable for dashboard tutorial. 
var tour = new Tour({
    name: 'DashboardTutorial',
    debug: true,
    backdrop: true,
    steps: [{
            title: "Welcome to the Web Simulation Tool! ",
            content: "With this tool, you will be able to interact with your diabetes data in a unique way. Let's have a tour of the main dashboard now!",
            orphan: true,
        },
        {
            element: "#datepicker",
            title: "Date Range Picker",
            content: "First, you have to select a date range you would like to interact with.",
            placement: 'bottom',
        },
        {
            element: "#areaGlucose",
            title: "Glucose Chart",
            content: "On this area, you will find your original and simulated glucose traces.",
        },
        {
            element: "#doughnutData",
            title: "Data Quality",
            content: "This pie chart indicates how much data is available in the selected date range.",
        },
        {
            element: "#barTir",
            title: "Time in Range",
            content: "Here, you can check your glucose control.",
        },
        {
            element: "#inputGroupInsType",
            title: "Replay Panel: Insulin Command",
            content: "Here, you can pick the functional insulin parameter (basal, CR, or CF) you would like to modify.",
        },
        {
            element: "#inputGroupInsProfile",
            title: "Replay Panel: Insulin Command",
            content: "Since you can have multiple profiles in the selected date range, you can select a particular profile you want to alter.",
        },

        {
            element: "#ins-timepicker",
            title: "Replay Panel: Insulin Command",
            content: "Select the time range where you would like to make a change.",
        },

        {
            element: "#insSlider",
            title: "Replay Panel: Insulin Command",
            content: "Change your original values.",
        },

        {
            element: "#tempInsUpdate",
            title: "Replay panel: Insulin Command",
            content: "Apply the changes you have made on your insulin data.",
        },
        {
            element: "#lineReplay",
            title: "Replay panel: Insulin Chart",
            content: "Check the changes you have made.",
        },

        {
            element: "#MealSelectDay",
            title: "Replay panel: Meal command",
            content: "Select the day you would like to make changes on meals.",
        },

        {
            element: "#MealSelect",
            title: "Replay panel: Meal command",
            content: "Select a particular meal you would like to modify.",
        },

        {
            element: "#meal-timeslider",
            title: "Replay panel: Meal command",
            content: "Adjust the meal time.",
        },
        {
            element: "#mealSlider",
            title: "Replay panel: Meal command",
            content: "Change the percentage of the original carbohydrates.",
        },
        {
            element: "#tempMealUpdate",
            title: "Replay panel: Meal command",
            content: "Apply the changes when you are ready.",
        },
        {
            element: "#lineReplay",
            title: "Replay panel: Meal Chart",
            content: "Check the changes you have made.",
        },
        {
            element: "#apSel",
            title: "Replay panel: AP System",
            content: "Check the selected AP System.",
        },
        {
            element: "#submit-data",
            title: "Replay panel: Run a simulation",
            content: "You are all set! Run your simulation. This takes only a few seconds.",
        },
        {
            element: "#secondRow",
            title: "Display panel: Original VS Replay",
            content: "Compare your simulated CGM with your original one!",
        },
        {
            element: "#DateList",
            title: "Too much information ?",
            content: "Pick the date(s) you want to analyze in detail. Orange color means you have made changes on the data. Gray color means there is no data. ",
            placement: 'bottom',
        },
        {
            element: "#save-replay",
            title: "Want to check this replay later?",
            content: "You can save all the modifications you have made.",
            placement: 'bottom',
        },
        {
            element: "#generate-report",
            title: "Replay panel: Generate a report",
            content: "Generate a pdf report to compare your original and replay (if any) data.",
        },
        {
            element: "#inputGroupReplay",
            title: "Check your previous replay",
            content: "Select the replay you want to check. The display panel and the replay panel will be updated based on your selection .",
            placement: 'bottom',
        }
    ]
});

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Display Panel 
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Drop-down List
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


// Global variable to track changes in insulin and meal commands.  
var track_change_arr;

// Global variable to check if no data in the selected date range.
var no_data_dcrp;

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Glucose area chart 
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

// Defines glucose chart.
var areaGlucoseCtx = $('#areaGlucose');
var myAreaChart = new Chart(areaGlucoseCtx, {
    type: 'line',
    data: {
        datasets: [{
                label: 'Original-Median',
                data: [{
                    x: new Date(2019, 0, 1, 0, 0, 0, 0),
                    y: NaN
                }, ],
                spanGaps: false,
                borderColor: 'rgba(61,173,217,.7)',
                backgroundColor: 'rgba(61,173,217,.7)',
                fill: false
            },
            {
                label: 'Original-25th Percentile',
                data: [{
                    x: new Date(2019, 0, 1, 0, 0, 0, 0),
                    y: NaN
                }, ],
                spanGaps: false,
                borderColor: 'rgba(61,173,217,.3)',
                backgroundColor: 'rgba(61,173,217,.3)',
                fill: 0
            },
            {
                label: 'Original-75th Percentile',
                data: [{
                    x: new Date(2019, 0, 1, 0, 0, 0, 0),
                    y: NaN
                }, ],
                spanGaps: false,
                borderColor: 'rgba(61,173,217,.3)',
                backgroundColor: 'rgba(61,173,217,.3)',
                fill: 0
            },
            {
                label: 'Replay-Median',
                data: [{
                    x: new Date(2019, 0, 1, 0, 0, 0, 0),
                    y: NaN
                }],
                spanGaps: false,
                borderColor: 'rgba(222,157,117,.7)',
                backgroundColor: 'rgba(222,157,117,.7)',
                fill: false
            },
            {
                label: 'Replay-25th Percentile',
                data: [{
                    x: new Date(2019, 0, 1, 0, 0, 0, 0),
                    y: NaN
                }],
                spanGaps: false,
                borderColor: 'rgba(222,157,117,.3)',
                backgroundColor: 'rgba(222,157,117,.3)',
                fill: 3
            },
            {
                label: 'Replay-75th Percentile',
                data: [{
                    x: new Date(2019, 0, 1, 0, 0, 0, 0),
                    y: NaN
                }],
                spanGaps: false,
                borderColor: 'rgba(222,157,117,.3)',
                backgroundColor: 'rgba(222,157,117,.3)',
                fill: 3
            },
            {
                label: '180 mg/dl',
                data: [{
                    x: new Date(2019, 0, 1, 0, 0, 0, 0),
                    y: 180.0
                }, {
                    x: new Date(2019, 0, 1, 23, 55, 0, 0),
                    y: 180.0
                }
                ],
                spanGaps: false,
                borderColor: 'rgba(130,245,126,.15)',
                backgroundColor: 'rgba(130,245,126,.15)',
                fill: false
            },
            {
                label: '70 mg/dl',
                data: [{
                    x: new Date(2019, 0, 1, 0, 0, 0, 0),
                    y: 70.0
                }, {
                    x: new Date(2019, 0, 1, 23, 55, 0, 0),
                    y: 70.0
                }
                ],
                spanGaps: false,
                borderColor: 'rgba(130,245,126,.15)',
                backgroundColor: 'rgba(130,245,126,.15)',
                fill: 6
            }
        ]
    },
    options: {
        responsive: true,
        scales: {
            xAxes: [{
                type: 'time',
                distribution: 'series',
                time: {
                    unit: 'hour',
                    displayFormats: {
                        hour: 'hA'
                    },
                    tooltipFormat: 'h:mm A',
                    stepSize: 3
                },
                ticks: {
                    maxRotation: 0,
                    minRotation: 0
                }
            }],
            yAxes: [{
                // scaleLabel: {
                //     display: true
                // },
                display: true,
                ticks: {
                    maxRotation: 0,
                    minRotation: 0,
                    min: 0,
                    stepSize: 20
                }
            }]
        },
        legend: {
            display: false,
            position: 'top',
        },
        animation: {
            animateScale: true,
            animateRotate: true
        },
        tooltips: {
            callbacks: {
                label: function(tooltipItem, data) {
                    var label = data.datasets[tooltipItem.datasetIndex].label || '';

                    if (label) {
                        label += ': ';
                    }
                    //label += Math.round(tooltipItem.yLabel * 10) / 10;
                    label += Math.floor(tooltipItem.yLabel);
                    label += ' mg/dl';
                    return label;
                }
            }
        }
    }
});

// A control variable to show/hide chart by click legend
updateGlucDataset = function(orginal) {
    if (orginal == false) {
        datasetIndex = [3, 4, 5];
        var ci = myAreaChart;
        for (var i = 0; i < 3; i++) {
            index = datasetIndex[i];
            var meta = ci.getDatasetMeta(index);
            var result = (meta.hidden == true) ? false : true;
            if (result == true) {
                meta.hidden = true;
                $('#replay-legend').css("text-decoration", "line-through");
            } else {
                $('#replay-legend').css("text-decoration", "");
                meta.hidden = false;
            }
            ci.update();
        }
    } else {
        datasetIndex = [0, 1, 2];
        var ci = myAreaChart;
        for (var i = 0; i < 3; i++) {
            index = datasetIndex[i];
            var meta = ci.getDatasetMeta(index);
            var result = (meta.hidden == true) ? false : true;
            if (result == true) {
                meta.hidden = true;
                $('#original-legend').css("text-decoration", "line-through");
            } else {
                $('#original-legend').css("text-decoration", "");
                meta.hidden = false;
            }
            ci.update();
        }
    }
}



/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Bar - TIR
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

// How close to the top edge bar can be before the value is put inside it
var topThreshold = 5;

var modifyCtx = function(ctx) {
    //ctx.font = Chart.helpers.fontString(Chart.defaults.global.defaultFontSize, 10, Chart.defaults.global.defaultFontFamily);
    ctx.textAlign = 'center';
    ctx.textBaseline = 'bottom';
    return ctx;
};

var fadeIn = function(ctx, obj, x, y) {
    var ctx = modifyCtx(ctx);
    ctx.font = "13px Quicksand";
    ctx.fillText(obj, x, y);
};

var drawValue = function(context, step) {
    var ctx = context.chart.ctx;

    context.data.datasets.forEach(function(dataset) {
        for (var i = 0; i < dataset.data.length; i++) {
            var model = dataset._meta[Object.keys(dataset._meta)[0]].data[i]._model;
            var textY = model.y + 10;
            var textX = model.x;
            //console.log(dataset.data)
            if (model.datasetLabel == '>250 mg/dl') {
                if (model.y == model.base) {
                    textY = textY;
                } else {
                    textX = textX - 20.0;
                    textY = textY - 10;
                }
            }
            if (model.datasetLabel == '70-180 mg/dl') {
                textX = textX - 20.0;
            }
            if (model.datasetLabel == '<70 mg/dl' || model.datasetLabel == '180-250 mg/dl') {
                textX = textX + 20.0;
            }
            if (model.y == model.base) {
                fadeIn(ctx, ' ', textX, textY);
            } else {
                fadeIn(ctx, Math.round(dataset.data[i] * 10) / 10 + '%',textX, textY);
            }
        }
    });
};

// Defines stacked bar graph
var barCtx = $('#barTir');
var tirChart = new Chart(barCtx, {
    type: 'bar',
    data: {
        labels: ['Original', 'Replay'],
        datasets: [{
                label: '<70 mg/dl',
                data: [0, 0],
                backgroundColor: 'rgba(61, 173, 217, 0.75)' // blue
            },
            {
                label: '70-180 mg/dl',
                data: [0, 0],
                backgroundColor: 'rgba(109,237,139,.75)' // green
            },
            {
                label: '180-250 mg/dl',
                data: [0, 0],
                backgroundColor: 'rgba(248,248,87,.75)' // yellow
            },
            {
                label: '>250 mg/dl',
                data: [0, 0],
                backgroundColor: 'rgba(243,50,16,0.75)' // red
            }
        ]
    },
    options: {
        tooltips: {
            enabled: true,
            callbacks: {
                label: function(tooltipItem, data) {
                    var label = data.datasets[tooltipItem.datasetIndex].label || '';

                    if (label) {
                        label += ': ';
                    }
                    label += Math.round(tooltipItem.yLabel * 10) / 10;
                    label += ' %';
                    return label;
                }
            }
        },
        scales: {
            xAxes: [{
                stacked: true,
            }],
            yAxes: [{
                stacked: true,
                ticks: {
                    max: 120,
                    display: false,
                    drawBorder: false
                }
            }]
        },
        legend: {
            display: false,
            position: 'bottom',
        },
        hover: {
            animationDuration: 0
        },
        animation: {
            onComplete: function() {
                this.chart.controller.draw();
                drawValue(this, 1);
            },
            onProgress: function(state) {
                var animation = state.animationObject;
                drawValue(this, animation.currentStep / animation.numSteps);
            }
        }
    }
});



/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Doughnut - Data quality
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


// Defines doughnut chart
var doughnutctx = $('#doughnutData');
var doughnutChart = new Chart(doughnutctx, {
    type: 'doughnut',
    data: {
        datasets: [{
            data: [0, 100],
            backgroundColor: [
                'rgba(61, 173, 217, 1)',
                'rgba(61, 173, 217, 0.5)'
            ],
        }],

        // These labels appear in the legend and in the tooltips when hovering different arcs
        labels: [
            'Playable',
            'Non-Playable'
        ]
    },
    options: {
        tooltips: {
            callbacks: {
                label: function(tooltipItem, data) {
                    var label = data.labels[tooltipItem.index] || '';

                    if (label) {
                        label += ': ';
                    }
                    label += data.datasets[0].data[tooltipItem.index];
                    label += ' %';
                    return label;
                }
            }
        },
        legend: {
            display: false,
            position: 'bottom'
        }
    }
});



/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Bullet graphs
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


// Define bullet graphs
var bgraph_cv = $('#bgraph_cv');
var bgraph_lbgi = $('#bgraph_lbgi');
var bgraph_hbgi = $('#bgraph_hbgi');
var options_bgraph = {
    type: 'bullet',
    height: '50px',
    width: '100px',
    chartRangeMax: '100',
    targetColor: '#3DADD9',
    targetWidth: '8',
    performanceColor: 'rgba(222,157,117,1)',
    rangeColors: ['rgba(211, 211, 211, 1.0)'],
    highlightLighten: .85,
    tooltipFormat: '{{fieldkey:levels}}:  {{value}}',
    tooltipValueLookups: {
        levels: $.range_map({ 'p': 'Replay', 'r': 'Range', 't': 'Original' })
    }
};


/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// DateRangePicker  
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

// Define a global variable to get profile unix times 
var ProfileTimes = [];

// Save date range picker apply results to track reply progress. 
var day1;
var day2;
var original_data;
var replay_data;
var selected_date_dcrp;


// Default Login (As Yesterday)
var firstLogin = true;


/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Replay Panel 
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Insulin Command
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////// 
//Global variable for insulin changes, can be used to return changes to server
var insulin_profile_changes;


/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Insulin Step Line Graph
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

// Defines line graph
var lineReplayCtx = $('#lineReplay');
var lineReplay = new Chart(lineReplayCtx, {
    type: 'line',
    data: {
        datasets: [{
                label: 'Original',
                data: [{
                    x: new Date(2019, 0, 1, 0, 0, 0, 0),
                    y: NaN
                }, ],
                spanGaps: false,
                borderColor: 'rgba(61,173,217,.7)',
                backgroundColor: 'rgba(61,173,217,.7)',
                fill: false,
                steppedLine: 'before'
            },
            {
                label: 'Replay',
                data: [{
                    x: new Date(2019, 0, 1, 0, 0, 0, 0),
                    y: NaN
                }, ],
                spanGaps: false,
                borderColor: 'rgba(222,157,117,.85)',
                backgroundColor: 'rgba(222,157,117,.85)',
                fill: false,
                steppedLine: 'before'
            }
        ]
    },
    options: {
        responsive: true,
        scales: {
            xAxes: [{
                type: 'time',
                distribution: 'series',
                time: {
                    unit: 'hour',
                    displayFormats: {
                        hour: 'hA'
                    },
                    tooltipFormat: 'h:mm A',
                    stepSize: 3
                },
                ticks: {
                    maxRotation: 0,
                    minRotation: 0
                }
            }],
            yAxes: [{
                display: true,
                ticks: {
                    maxRotation: 0,
                    minRotation: 0
                },
                scaleLabel:{
                    display: true,
                    labelString: ' '
                }
            }]
        },
        legend: {
            display: true,
            position: 'top',
            onHover: function(event, legendItem) {
                document.getElementById("lineReplay").style.cursor = 'pointer';
            },
        },
        tooltips: {
            callbacks: {
                label: function(tooltipItem, data) {
                    var label = data.datasets[tooltipItem.datasetIndex].label || '';

                    if (label) {
                        label += ': ';
                    }
                    label += Math.round(tooltipItem.yLabel * 100) / 100;
                    return label;
                }
            }
        }
    }
});


///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Meal Command 
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////// 


// Global variable for meal changes, can be used to return changes to server
var meal_changes;


//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Meal Bar Graph
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

// Defines point graph 
var mealReplayCtx = $('#mealReplay');
var mealReplay = new Chart(mealReplayCtx, {
    type: 'line',
    data: {
        datasets: [{
                label: 'Original Bar',
                data: [{
                    x: new Date(2019, 0, 1, 0, 0, 0, 0),
                    y: NaN
                }, ],
                spanGaps: false,
                borderColor: 'rgba(61,173,217,.7)',
                backgroundColor: 'rgba(61,173,217,.7)',
                fill: 'origin',
                steppedLine: 'before',
                pointRadius: 0,
                pointHoverRadius: 0,
            },
            {
                label: 'Original',
                data: [{
                    x: new Date(2019, 0, 1, 0, 0, 0, 0),
                    y: NaN
                }, ],
                spanGaps: false,
                borderColor: 'rgba(61,173,217,.7)',
                backgroundColor: 'rgba(61,173,217,.7)',
                fill: 'origin',
                steppedLine: 'before',
                pointRadius: 5,
                pointHoverRadius: 5,
                pointStyle: 'circle',
            },
            {
                label: 'Replay Bar',
                data: [{
                    x: new Date(2019, 0, 1, 0, 0, 0, 0),
                    y: NaN
                }, ],
                spanGaps: false,
                borderColor: 'rgba(222,157,117,.85)',
                backgroundColor: 'rgba(222,157,117,.85)',
                fill: 'origin',
                steppedLine: 'before',
                pointRadius: 0,
                pointHoverRadius: 0,
            },
            {
                label: 'Replay',
                data: [{
                    x: new Date(2019, 0, 1, 0, 0, 0, 0),
                    y: NaN
                }, ],
                spanGaps: false,
                borderColor: 'rgba(222,157,117,.85)',
                backgroundColor: 'rgba(222,157,117,.85)',
                fill: 'origin',
                steppedLine: 'before',
                pointRadius: 5,
                pointHoverRadius: 5,
                pointStyle: 'circle',
            }
        ]
    },
    options: {
        responsive: true,

        scales: {
            xAxes: [{
                type: 'time',
                distribution: 'series',
                time: {
                    unit: 'hour',
                    displayFormats: {
                        hour: 'hA'
                    },
                    tooltipFormat: 'h:mm A',
                    stepSize: 3
                },
                ticks: {
                    maxRotation: 0,
                    minRotation: 0
                }
            }],
            yAxes: [{
                display: true,
                ticks: {
                    min: 0,
                    maxRotation: 0,
                    minRotation: 0
                },
                scaleLabel: {
                    display: true,
                    labelString: 'Meals [g]'
                }
            }]
        },
        legend: {
            display: true,
            position: 'top',
            labels: {
                filter: function(item, chart) {
                    // Logic to remove a particular legend item goes here
                    return !item.text.includes('Bar');
                },
            },
            onHover: function(event, legendItem) {
                document.getElementById("mealReplay").style.cursor = 'pointer';
            },
            onClick: function(e, legendItem) {
                var index = legendItem.datasetIndex;
                var ci = this.chart;
                var alreadyHidden = (ci.getDatasetMeta(index).hidden === null) ? false : ci.getDatasetMeta(index).hidden;
                var anyOthersAlreadyHidden = false;


                // figure out the current state of the labels
                if (index == 1) {
                    //check if replay is hidden 
                    if (ci.getDatasetMeta(3).hidden) {
                        anyOthersAlreadyHidden = true;
                    }


                    //if already hidden: show the data now 
                    if (alreadyHidden) {
                        ci.getDatasetMeta(0).hidden = null;
                        ci.getDatasetMeta(1).hidden = null;
                    } else {
                        ci.data.datasets.forEach(function(e, i) {
                            var meta = ci.getDatasetMeta(i);
                            if (![0, 1].includes(parseInt(i))) {
                                // handles logic when we click on visible hidden label and there is currently at least
                                // one other label that is visible and at least one other label already hidden
                                // (we want to keep those already hidden still hidden)
                                if (anyOthersAlreadyHidden) {
                                    meta.hidden = true;
                                } else {
                                    // toggle visibility
                                    meta.hidden = null;
                                }
                            } else {
                                meta.hidden = true;
                            }
                        });
                    }
                } else {
                    if (ci.getDatasetMeta(1).hidden) {
                        anyOthersAlreadyHidden = true;
                    }

                    //if already hidden: show the data now 
                    if (alreadyHidden) {
                        ci.getDatasetMeta(2).hidden = null;
                        ci.getDatasetMeta(3).hidden = null;
                    } else {
                        ci.data.datasets.forEach(function(e, i) {
                            var meta = ci.getDatasetMeta(i);
                            if (![2, 3].includes(i)) {
                                // handles logic when we click on visible hidden label and there is currently at least
                                // one other label that is visible and at least one other label already hidden
                                // (we want to keep those already hidden still hidden)
                                if (anyOthersAlreadyHidden) {
                                    meta.hidden = true;
                                } else {
                                    // toggle visibility
                                    meta.hidden = null;
                                }
                            } else {
                                meta.hidden = true;
                            }
                        });
                    }
                }
                ci.update();
            },
        },
        // tooltips: {
        //     mode: 'x-axis',
        //     filter: function(tooltipItem) {
        //         return [1, 3].includes(tooltipItem.datasetIndex);
        //     }
        // }
        tooltips: {
            mode: 'x-axis',
            filter: function(tooltipItem) {
                return [1, 3].includes(tooltipItem.datasetIndex);
            },
            callbacks: {
                label: function(tooltipItem, data) {
                    var label = data.datasets[tooltipItem.datasetIndex].label || '';

                    if (label) {
                        label += ': ';
                    }
                    //label += Math.round(tooltipItem.yLabel * 10) / 10;
                    label += Math.floor(tooltipItem.yLabel);
                    label += ' g';
                    return label;
                }
            }
        }

    }
});

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Additional Parameters 
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

// Global variables to track insultion adaptation and hypo treament checkboxes.  
var adjIns = false;
var genIns = false;
var adjHTs = false;
var genHTs = false;

var object = {
    key: function(n) {
        return this[Object.keys(this)[n]];
    }
};


/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Save Replay
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


// Global variable to track the replay data and the user changes in multiple replays.  
var replay_list = {};
replay_list['trackDropDown'] = [];
replay_list['mealChanges'] = [];
replay_list['insChanges'] = [];
replay_list['replayResult'] = [];
replay_list["adjIns"] = [];
replay_list["genIns"] = [];
replay_list["adjHTs"] = [];
replay_list["genHTs"] = [];
replay_list["apSel"] = [];