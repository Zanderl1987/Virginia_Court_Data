//https://stackoverflow.com/questions/48719873/how-to-get-median-and-quartiles-percentiles-of-an-array-in-javascript-or-php


/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Helper Functions 
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

// Check if a number is odd number 
function isOdd(num) {
    return num % 2;
}

// Sort numbers in an array. 
function Array_Sort_Numbers(inputarray) {
    return inputarray.sort(function(a, b) {
        return a - b;
    });
}

// Calculate Quartile 25, 50 Median, 75. 
function Quartile(data, q) {
    data = Array_Sort_Numbers(data);
    var pos = ((data.length) - 1) * q;
    var base = Math.floor(pos);
    var rest = pos - base;
    if ((data[base + 1] !== undefined)) {
        return data[base] + rest * (data[base + 1] - data[base]);
    } else {
        return data[base];
    }
}

function Median(data) {
    return Quartile50(data);
}

function Quartile25(data) {
    return Quartile(data, 0.25);
}

function Quartile50(data) {
    return Quartile(data, 0.5);
}

function Quartile75(data) {
    return Quartile(data, 0.75);
}

// Check two arrays are same or not. 
function arraysEqual(a, b) {
    if (a === b) {return true};
    if (a == null || b == null) {return false};
    if (a.length != b.length) {return false};

    for (var i = 0; i < a.length; ++i) {
        if (isObject(a[i])) {
            for (var j = 0; j < a[i].length; ++j) {
                if (a[i][j] != b[i][j]) {return false};
            }
        } else {
            if (a[i] != b[i]) {return false};
        }
    }
    return true;
}



// Check if it is an object. 
function isObject(obj) {
    return obj === Object(obj);
}

// Calculate the sum of all the elements in an array 
function Array_Sum(t) {
    return t.reduce(function(a, b) { return a + b; }, 0);
}

// Calculate the average of an array 
function Array_Average(data) {
    return Math.round((Array_Sum(data) / data.length) * 10) / 10;
}

// Return object and index using key.  
function key(obj, idx) {
    return object.key.call(obj, idx);
}

// Convert Unix  Timestamp to date time. 
function UnixTimeConverter(UNIX_timestamp) {
    //var temp = new Date(UNIX_timestamp * 1000);

    // console.log('UnixTimeConverter')
    // console.log(UNIX_timestamp)
    //var temp = moment.unix(UNIX_timestamp).utc();
    var temp1 = moment.unix(UNIX_timestamp);
    var temp = moment.utc(temp1);

    // console.log(temp)
    // console.log(temp.date())
    // console.log(temp.month())
    // console.log(temp.year())
    // console.log(temp1)
    // console.log(temp1.date())
    // console.log(temp1.month())
    // console.log(temp1.year())

    var months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    // var year = temp.getFullYear();
    // var month = months[temp.getMonth()];
    // var date = "0" + temp.getDate();
    var year = temp.year();
    var month = months[temp.month()];
    var date = "0" + temp.date();
    var time = date.substr(-2) + ' ' + month + ' ' + year;
    // console.log(time)
    return time;
}


// Update date format. 
function updateDateFormat(temp) {
    var months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    var year = temp.getFullYear();
    var month = months[temp.getMonth()];
    var date = "0" + temp.getDate();
    var time = date.substr(-2) + ' ' + month + ' ' + year;
    return time;
}

// If nan return 0.
function check_nan(x) {
    if (isNaN(x) || !x) {
        return 0;
    } else {
        return x;
    }
}


// Check if  a list is empty or underfined. 
function noList(list) {
    return list.length == 0;
}

// Check if all elements in a list are 0s.  
function zeroList(list) {
    return list.every((val, i, arr) => val === 0);
}

// Check if all elements in a list exists.
function nullList(list) {
    return list.every((val, i, arr) => !val);
}


/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Genera Functions 
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

// Define time vectors with different sampling time. 
var timeVec_5min = timeGenerator(5); // 24-hour vector with 5-min sampling time -> For the glucose chart
var timeVec_30min = timeGenerator(30); // 24-hour vector with 30-min sampling time -> For the replay chart


// Generates a 24-hour vector with x-min sampling time 
function timeGenerator(samplingTime) {
    var timePivot = new Date(2019, 0, 1, 0, 0, 0, 0);
    var timeVec = [timePivot];

    for (i = 0; i < 1440 / samplingTime; i++) {
        var timePivotMod = new Date(timePivot.getTime() + (i + 1) * samplingTime * 60000);
        timeVec.push(timePivotMod);
    }
    return timeVec
}

// Turn 24 hr in 30 mins interval to indices.  
function time_index() {
    const locale = 'en';
    var hours = {};
    moment.locale(locale); // optional - can remove if you are only dealing with one locale
    var indices = 0;
    for (let hour = 0; hour < 24; hour++) {
        time1 = moment({ hour }).format('HH:mm');
        hours[time1] = indices;
        indices++;
        time2 = moment({ hour, minute: 30 }).format('HH:mm')
        hours[time2] = indices;
        indices++;
    }
    return hours;
}


// Generate time series data from an array of data and an array of times.
function timeDataProc(data, timeVec) {
    var dataV = [];
    for (i = 0; i < data.length; i++) {
        if (data[i] == 0) {
            var dataAux = {
                x: timeVec[i],
                y: NaN
            }
        } else {
            var dataAux = {
                x: timeVec[i],
                y: data[i]
            }
        }
        dataV.push(dataAux)

    }
    return dataV
}

// Update HTML in an element 
function updateText(element, html) {
    $(element).html(html);
}

// Fill text for span elements  
function fillText(span, data) {
    var element = $(span);
    element.text(data);
}

// Use index to select objects in an array. 
function selectIndex(data, index) {
    return index.map(i => data[i]);
}

// Remove all elements in a populated drop down list 
function removePopulatedDropdown(element) {
    for (i = $(element)[0].options.length - 1; i >= 0; i--) {
        $(element)[0].options.remove(i);
    }
}

// Check which dates don't have data in the selected date range. 
function noDataDates(selected_date_array, nonplayable_list) {
    var nodatalist = [];
    for (var i = 0; i < selected_date_array.length; i++) {
        if (nonplayable_list[i] == 100) {
            nodatalist.push(selected_date_array[i]);
        }
    }
    return nodatalist;
}

// Get the last date with data in the selected date range. 
function lastDate(selected_date_array, no_data_dates) {
    for (var i = (selected_date_array.length - 1); i >= 0; i--) {
        if (!no_data_dates.includes(selected_date_array[i])) {
            return selected_date_array[i];
        }
    }
    return selected_date_array[selected_date_array.length - 1];
}



// Check if the values in an array all equals to 100: if every equal to 100, return true, else false 
function checkNoPlay(nonplay_array) {

    const isBelowThreshold = (currentValue) => currentValue == 100;
    return nonplay_array.every(isBelowThreshold);

}

// Check if there is any data in the returned JSON data from the selected date range after clicking apply. 
function checkIfAllNull(data) {
    var result_array = [];
    nolist = ["bProfiles", "cfProfiles", "crProfiles", "glucSeries", "moH", "moM"];
    for (var i = 0; i < nolist.length; i++) {
        result_array.push(noList(data[nolist[i]]));
    }

    zerolist = ["cv", "hbgi", "lbgi", "percentR1", "percentR2", "percentR3", "percentR4"];
    for (var i = 0; i < zerolist.length; i++) {
        result_array.push(zeroList(data.metrics[zerolist[i]]));
    }

    result_array.push(zeroList(data.quality.playable));
    null_list = ["nHT", "tdb", "tdi"];
    for (var i = 0; i < null_list.length; i++) {
        result_array.push(nullList(data[null_list[i]]));
    }
    return result_array.every((val, i, arr) => val === true);
}


/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Warning Settings 
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

// Set up pop-up dialogues. 
function popWarning() {
    warningSetting('#success');
    warningSetting('#warning', success = false);
}

// Define pop-up dialogues. 
function warningSetting(box, success = true) {
    if (success == true) {
        $(box).dialog({
            autoOpen: false,
            dialogClass: 'success-dialog'
        });
    } else {
        $(box).dialog({
            autoOpen: false,
            dialogClass: 'warning-dialog'
        });
    }
}

// Custom content in a pop up dialogue. 
function popText(box, text) {
    if (document.getElementById("flagFirstTUser").innerText == "1" || document.getElementById("flagTutorial").innerText == "1") {
        $(box).html(text);
        $(box).dialog('open');
        setTimeout(function() {
            $(box).dialog('close')
        }, 1500);
    } else {
        $(box).html(text);
        $(box).dialog('open');
        setTimeout(function() {
            $(box).dialog('close')
        }, 2600);
    }
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Display Panel 
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Drop-down List 
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

// Populate the list for the drop down list 
function dateDropDown(selected_date_array, no_data_dates) {
    var str;
    for (var i = 0; i < selected_date_array.length; i++) {
        if (no_data_dates.includes(selected_date_array[i])) {
            str += "<option value=" + i + " disabled='disabled'>" + selected_date_array[i] + "</option>";
        } else {
            str += "<option value=" + i + ">" + selected_date_array[i] + "</option>";
        }
    }
    return str;
}


// Track changes for each day tp change color in the drop down list respectively, 'Jan 1st 2019' = [false,false] 
function trackChanges(selected_date_array) {
    track_change_arr = {};
    for (var i = 0; i < selected_date_array.length; i++) {
        track_change_arr[selected_date_array[i]] = [false, false];
        //first is for insulin, second is for meal 
    }
    return track_change_arr;
}

// Reset track meal changes all to false (No changes)
function resetMealTrack(track_change_array) {
    Object.keys(track_change_array).forEach(function(key) {
        track_change_array[key][1] = false;
    });
}

// Reset track insulin changes all to false (No changes)
function resetInsTrack(track_change_array) {
    Object.keys(track_change_array).forEach(function(key) {
        track_change_array[key][0] = false;
    });
}

// Check insulin update. For each day, check if it's the same with the original data
function checkInsUpdate(org_data, update_data, date_arr) {
    if (arraysEqual(org_data, update_data) == false) {
        date_arr.map(i => track_change_arr[i][0] = true);
    } else {
        date_arr.map(i => track_change_arr[i][0] = false);
    }
}

// Check meal update. For each day, check if it's the same with the original data
function checkMealUpdate(org_data, update_data, date_arr) {
    if (arraysEqual(org_data, update_data) == false) {
        date_arr.map(i => track_change_arr[i][1] = true);
    } else {
        date_arr.map(i => track_change_arr[i][1] = false);
    }
}

// Change the colors of drop down list in the display panel with an attribute onlyslave. 
function formatState(state) {

    if (!state.element) return;
    var os = $(state.element).attr('onlyslave');
    return $('<span onlyslave="' + os + '">' + state.text + '</span>');

}

// Update the colors of the options in drop down date list based on if the meal/insulin data is changed or not.  
function updateDropDown(drop_down, track_change_array, no_data_dates) {
    var str;
    var i = 0;
    for (val in track_change_array) {
        var change_color = ' onlyslave="False"';
        if (track_change_array[val][0] || track_change_array[val][1]) {
            change_color = ' onlyslave="True"';
        }
        if (no_data_dates.includes(val)) {
            str += "<option value=" + i + ' disabled="disabled"' + ">" + val + "</option>";
        } else {
            str += "<option value=" + i + change_color + ">" + val + "</option>";
        }
        i += 1;
    }
    updateText(drop_down, str);
}



// Filter date function based on the drop down list in the display panel 
function dateFilter(data_org, data_replay, date_array) {

    local_data_org = JSON.parse(JSON.stringify(data_org));
    local_data_replay = JSON.parse(JSON.stringify(data_replay));
    display_filter = $('#SelectDisplayDate');
    selected_date_array = JSON.parse(JSON.stringify(date_array))

    display_filter.on("change", function(e) {
        indices = $("#SelectDisplayDate").val();
        displayPanel(local_data_org, local_data_replay, indices, selected_date_array);
        moreDetails(local_data_org, local_data_replay, indices);
    });

}


// Initiate listen events between SELECT ALL box and date drop down list.  
function initDateDropDown() {

    // Define the drop down list and the select all check box in the display panel. 
    var DisplayDropDown = $('#SelectDisplayDate');
    var SelectAllDates = $("#display-all-date");

    //Define the drop down date list in the display panel  
    DisplayDropDown.select2({
        placeholder: 'Select only the dates that you are interested in',
        templateResult: formatState,
    });

    //If all dates with data are selected, the Select All checkbox is checked.  
    DisplayDropDown.on("change", function(e) {
        var allSelected = DisplayDropDown.children('option:not(:selected)').length == DisplayDropDown.children('option:disabled').length;
        if (allSelected == true) {
            SelectAllDates.prop("checked", true);
        } else {
            SelectAllDates.prop("checked", false);
        }
    });

    //If the Select All checkbox is checked, every date with data is selected. 
    SelectAllDates.click(function() {
        if (SelectAllDates.is(':checked')) {
            DisplayDropDown.children('option:enabled').prop('selected', true);
            DisplayDropDown.trigger("change");
        } else {
            DisplayDropDown.children('option:enabled').prop('selected', false);
            // $("#SelectDisplayDate> option").removeAttr("selected");
            DisplayDropDown.trigger("change");
        }
    });

}
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Glucose area chart 
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


// Updates glucose chart's data
function areaChartHandler(chart, gluc_org, gluc_replay) {
    for (i = 0; i < 3; i++) {
        chart.data.datasets[i].data = gluc_org[i];
    }
    var j = 0;
    for (i = 3; i < 6; i++) {
        chart.data.datasets[i].data = gluc_replay[j];
        j = j + 1;
    }
    //console.log(gluc_org)
    chart.update();
}


// Update span element that shows the # of days with data and the # of days without data in the area chart.  
function areaChartDays(show_indices, all_indices) {
    var span_dates = $('#areaDays span');
    var num_days = show_indices.length;
    var no_data_days = all_indices.length - show_indices.length;
    span_dates.html(num_days + ' day(s) with CGM data. </br> ' + no_data_days + ' day(s) with no CGM data');
}


// Calculate median, 25, 75 for glucose arrs. 
function glucPrct(data_arrs) { //input is daily gluc data in an array 
    var median_vals = [];
    var prctile25_vals = [];
    var prctile75_vals = [];

    if (data_arrs.length != 0) {
        for (var i = 0; i < data_arrs[0].length; i++) {

            temp_data = data_arrs.map(function(x) {
                    if (x.length != 0) {
                        return x[i];
                    }
                }) //temp data includes the data of the dates at a  time point

            median_vals.push(Math.round(Median(temp_data) * 100) / 100);
            prctile25_vals.push(Math.round(Quartile25(temp_data) * 100) / 100);
            prctile75_vals.push(Math.round(Quartile75(temp_data) * 100) / 100);
        }
    }

    return [median_vals, prctile25_vals, prctile75_vals];
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Bar - TIR
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


// Updates bar graph's data
function barHandler(chart, data_org, data_replay) {

    // < 70
    chart.data.datasets[0].data[0] = data_org[0]; //original 
    chart.data.datasets[0].data[1] = data_replay[0]; //replay 

    // 70-180
    chart.data.datasets[1].data[0] = data_org[1]; //original 
    chart.data.datasets[1].data[1] = data_replay[1]; //replay 

    // 180-250
    chart.data.datasets[2].data[0] = data_org[2]; //original 
    chart.data.datasets[2].data[1] = data_replay[2]; //replay 

    // > 250
    chart.data.datasets[3].data[0] = data_org[3]; //original 
    chart.data.datasets[3].data[1] = data_replay[3]; //replay 

    chart.update();

}



/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Doughnut - Data quality
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


// Updates doughnut chart's data
function doughnutHandler(chart, newData) {

    chart.data.datasets[0].data[0] = newData[0];
    chart.data.datasets[0].data[1] = newData[1];
    chart.update();

}



/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Bullet graphs
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


// Update bullet graphs
function bgraphHandler(data_org, data_replay) {
    //original  //replay //range 
    bgraph_cv.sparkline([data_org[0], data_replay[0], 100], options_bgraph);
    bgraph_lbgi.sparkline([data_org[1], data_replay[1], 100], options_bgraph);
    bgraph_hbgi.sparkline([data_org[2], data_replay[2], 100], options_bgraph);

}


// Update text under bgraph graph 
function fillTextBgraph(data_org, data_replay) {

    var fillTextlist = ['#diff-var', '#diff-lbgi', '#diff-hbgi']
    track = 0;
    for (var i = 0; i < fillTextlist.length; i++) {

        if (data_replay[track] > 0 && data_org[track] > 0) {
            diff = Math.round((data_replay[track] / data_org[track] - 1) * 100 * 10) / 10;
            if (diff > 0) {
                fillText(fillTextlist[i], '+' + diff + '%');
            } else {
                fillText(fillTextlist[i], diff + '%');
            }
        } else {
            fillText(fillTextlist[i], ' ');
        }

        track = track + 1;

    }

    //   var fillTextlist=['#original-var','#replay-var','#original-lbgi','#replay-lbgi','#original-hbgi','#replay-hbgi']
    //   track_org=0;
    //   track_replay=0;

    //   for (var i=0;i<fillTextlist.length;i++){
    //       if (isOdd(i)==1){
    //           //fill_text(fill_in_list[i],data_replay[track_replay]);
    //           fillText(fillTextlist[i],Math.round(data_replay[track_replay]*10) / 10);
    //           track_replay=track_replay+1; 
    //       }
    //       else {
    //           //fill_text(fill_in_list[i],data_org[track_org]);
    //           fillText(fillTextlist[i],Math.round(data_org[track_org]*10) / 10);
    //           track_org=track_org+1;
    //       }
    //   }
}



/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// More Details 
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

// TO DO : maybe not parse the whole data will improve the performance 
function moreDetails(data_org, data_replay, indices) {

    var parsed_data_org = JSON.parse(JSON.stringify(data_org));
    var parsed_data_replay = JSON.parse(JSON.stringify(data_replay));
    var parsed_indices = JSON.parse(JSON.stringify(indices));
    var show_details = false;
    $('#collapseMoreDetails').hide();

    $("#MoreDetails_control").click(function() {
        if (show_details == false) {
            $('#collapseMoreDetails').show();
            if (parsed_indices == null | parsed_data_org.glucSeries.length == 0) {
                bgraphHandler([0, 0, 0], [0, 0, 0]);
                fillMoreDetails([" ", " ", " "], [" ", " ", " "]);
                fillTextBgraph([" ", " ", " "], [" ", " ", " "]);
            } else if (parsed_indices.length == 0) {
                bgraphHandler([0, 0, 0], [0, 0, 0]);
                fillMoreDetails([" ", " ", " "], [" ", " ", " "]);
                fillTextBgraph([" ", " ", " "], [" ", " ", " "]);
            } else if (parsed_indices.length == 1) {
                index = parsed_indices[0];
                bgraphHandler([parsed_data_org.metrics.cv[index], parsed_data_org.metrics.lbgi[index], parsed_data_org.metrics.hbgi[index]], [parsed_data_replay.metrics.cv[index], parsed_data_replay.metrics.lbgi[index], parsed_data_replay.metrics.hbgi[index]]);

                fillTextBgraph([parsed_data_org.metrics.cv[index], parsed_data_org.metrics.lbgi[index], parsed_data_org.metrics.hbgi[index]], [parsed_data_replay.metrics.cv[index], parsed_data_replay.metrics.lbgi[index], parsed_data_replay.metrics.hbgi[index]]);

                fillMoreDetails([parsed_data_org.tdi[index], parsed_data_org.tdb[index], parsed_data_org.nHT[index]], [parsed_data_replay.tdi[index], parsed_data_replay.tdb[index], parsed_data_replay.nHT[index]])

            } else {
                var new_indices = [];
                for (var i = 0; i < parsed_indices.length; i++) {
                    if (parsed_data_org.metrics.cv[parsed_indices[i]] != null) {
                        new_indices.push(parsed_indices[i]);
                    }
                }
                // Update bullet graphs
                bgraphHandler([Array_Average(selectIndex(parsed_data_org.metrics.cv, new_indices)), Array_Average(selectIndex(parsed_data_org.metrics.lbgi, new_indices)), Array_Average(selectIndex(parsed_data_org.metrics.hbgi, new_indices))], [Array_Average(selectIndex(parsed_data_replay.metrics.cv, new_indices)), Array_Average(selectIndex(parsed_data_replay.metrics.lbgi, new_indices)), Array_Average(selectIndex(parsed_data_replay.metrics.hbgi, new_indices))]);

                fillTextBgraph([Array_Average(selectIndex(parsed_data_org.metrics.cv, new_indices)), Array_Average(selectIndex(parsed_data_org.metrics.lbgi, new_indices)), Array_Average(selectIndex(parsed_data_org.metrics.hbgi, new_indices))], [Array_Average(selectIndex(parsed_data_replay.metrics.cv, new_indices)), Array_Average(selectIndex(parsed_data_replay.metrics.lbgi, new_indices)), Array_Average(selectIndex(parsed_data_replay.metrics.hbgi, new_indices))]);

                fillMoreDetails([Array_Average(selectIndex(parsed_data_org.tdi, new_indices)), Array_Average(selectIndex(parsed_data_org.tdb, new_indices)), Array_Average(selectIndex(parsed_data_org.nHT, new_indices))], [Array_Average(selectIndex(parsed_data_replay.tdi, new_indices)), Array_Average(selectIndex(parsed_data_replay.tdb, new_indices)), Array_Average(selectIndex(parsed_data_replay.nHT, new_indices))])

            }
            show_details = true;
        } else {
            $('#collapseMoreDetails').hide();
            show_details = false;
        }
    });
}

// Fill the span elements in the more details section in display panel.
function fillMoreDetails(data_org, data_replay) {

    var fillTextList = ['#original-tdi', '#replay-tdi', '#original-tdb', '#replay-tdb', '#original-ht', '#replay-ht']
    track_org = 0;
    track_replay = 0;

    for (var i = 0; i < fillTextList.length; i++) {
        if (isOdd(i) == 1) {
            //fill_text(fillTextList[i],data_replay[track_replay]);
            fillText(fillTextList[i], Math.round(data_replay[track_replay] * 10) / 10);
            track_replay = track_replay + 1;
        } else {
            //fill_text(fill_in_list[i],data_org[track_org]);
            fillText(fillTextList[i], Math.round(data_org[track_org] * 10) / 10);
            track_org = track_org + 1;
        }
    }
}


/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Display Panel Function 
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

// Set display panel as null
function noDisplayPanel() {

    bgraphHandler([0, 0, 0], [0, 0, 0]);
    // Update doughnut    
    doughnutHandler(doughnutChart, [0, 100]);
    // Update stacked bars
    barHandler(tirChart, [], []);
    // Update area graph
    areaChartHandler(myAreaChart, [], []);
    //Update areaDays span element 
    $('#areaDays span').html('');

}


// Display panel function 
function displayPanel(data_org, data_replay, indices, date_array) {

    //When there is no data or select no dates, no display panel 
    if (indices == null | data_org.glucSeries.length == 0) {
        noDisplayPanel();
    } else if (indices.length == 0) {
        noDisplayPanel();
    }

    //When only select one day 
    else if (indices.length == 1) {

        index = indices[0];
        var glucIndex = [];
        var j = 0;
        var flagWhile = true;
        while (flagWhile) {
            if (data_org['glucSeries'][j][0]==date_array[index]){
                glucIndex = j.toString();
                flagWhile = false;
            }
            ++j;
        }

        //If there is no gluc data, no display panel
        if (typeof data_org.glucSeries[glucIndex] == 'undefined') {
            noDisplayPanel();
        } 
        // if (typeof data_org.glucSeries[index] == 'undefined') {
        //     noDisplayPanel();
        // }

        //else 
        else {
            doughnutHandler(doughnutChart, [data_org.quality.playable[index], data_org.quality.nonplayable[index]])
            barHandler(tirChart, [data_org.metrics.percentR1[index], data_org.metrics.percentR2[index], data_org.metrics.percentR3[index], data_org.metrics.percentR4[index]], [data_replay.metrics.percentR1[index], data_replay.metrics.percentR2[index], data_replay.metrics.percentR3[index], data_replay.metrics.percentR4[index]])

            //data_gluc_org = data_org.glucSeries[index];
            data_gluc_org = data_org.glucSeries[glucIndex];
            glucOrig = timeDataProc(data_gluc_org[1], timeVec_5min);
            glucOrig25 = timeDataProc(Array(288).fill(0), timeVec_5min);
            glucOrig75 = timeDataProc(Array(288).fill(0), timeVec_5min);

            //When there is no replay data, fill with 0 or original data. 
            // if (typeof data_replay.glucSeries[index] == 'undefined') {
            //     data_gluc_replay = Array(288).fill(0);
            // } else {
            //     data_gluc_replay = data_replay.glucSeries[index][1];
            // }
            if (typeof data_replay.glucSeries[glucIndex] == 'undefined') {
                data_gluc_replay = Array(288).fill(0);
            } else {
                data_gluc_replay = data_replay.glucSeries[glucIndex][1];
            }

            glucReplay = timeDataProc(data_gluc_replay, timeVec_5min);
            glucReplay25 = timeDataProc(Array(288).fill(0), timeVec_5min)
            glucReplay75 = timeDataProc(Array(288).fill(0), timeVec_5min)

            gluc_org_arr = [glucOrig, glucOrig25, glucOrig75];
            gluc_rly_arr = [glucReplay, glucReplay25, glucReplay75];

            areaChartHandler(myAreaChart, gluc_org_arr, gluc_rly_arr);
            areaChartDays([index], [index])
        }
    }

    //When there are multiple dates selected 
    else {
        original_indices = indices.slice();
        
        //remove the indices that do not have data 
        var new_indices = [];
        for (var i = 0; i < indices.length; i++) {
            if (data_org.metrics.cv[indices[i]] != null) {
                new_indices.push(indices[i]);
            }
        }

        //adjust gluc indices 
        var filtered_dates_gluc = [];
        for (i = 0; i < new_indices.length; i++) {
            filtered_dates_gluc[i] = date_array[new_indices[i]];
        }
        var new_indices_gluc = [];
        var indTracker = 0;
        var j = 0;
        var flagWhile = true;
        for (i = 0; i < filtered_dates_gluc.length; i++) {
            j = 0;
            flagWhile = true;
            while (flagWhile) {
                if (data_org['glucSeries'][j][0]==filtered_dates_gluc[i]){
                    new_indices_gluc[indTracker] = j;
                    ++indTracker;
                    flagWhile = false;
                }
                ++j;
            }
        }
        
        // Update doughnut
        doughnutHandler(doughnutChart, [Array_Average(original_indices.map(i => data_org.quality.playable[i])), Array_Average(original_indices.map(i => data_org.quality.nonplayable[i]))]);

        // Update stacked bars
        var tirOrig = [Array_Average(selectIndex(data_org.metrics.percentR1, new_indices)), Array_Average(selectIndex(data_org.metrics.percentR2, new_indices)),
            Array_Average(selectIndex(data_org.metrics.percentR3, new_indices)), Array_Average(selectIndex(data_org.metrics.percentR4, new_indices))];
        if (tirOrig[0]+tirOrig[1]+tirOrig[2]+tirOrig[3]>0.0) {
            tirOrig[1] = Math.max(100.0-(tirOrig[0]+tirOrig[2]+tirOrig[3]),0.0);
        } 
        var tirReplay = [Array_Average(selectIndex(data_replay.metrics.percentR1, new_indices)), Array_Average(selectIndex(data_replay.metrics.percentR2, new_indices)),
            Array_Average(selectIndex(data_replay.metrics.percentR3, new_indices)), Array_Average(selectIndex(data_replay.metrics.percentR4, new_indices))];
        if (tirReplay[0]+tirReplay[1]+tirReplay[2]+tirReplay[3]>0.0) {
            tirReplay[1] = Math.max(100.0-(tirReplay[0]+tirReplay[2]+tirReplay[3]),0.0);
        }
        barHandler(tirChart, tirOrig, tirReplay);
        // barHandler(tirChart, [Array_Average(selectIndex(data_org.metrics.percentR1, new_indices)), Array_Average(selectIndex(data_org.metrics.percentR2, new_indices)),
        //     Array_Average(selectIndex(data_org.metrics.percentR3, new_indices)), Array_Average(selectIndex(data_org.metrics.percentR4, new_indices))
        // ], [Array_Average(selectIndex(data_replay.metrics.percentR1, new_indices)), Array_Average(selectIndex(data_replay.metrics.percentR2, new_indices)),
        //     Array_Average(selectIndex(data_replay.metrics.percentR3, new_indices)), Array_Average(selectIndex(data_replay.metrics.percentR4, new_indices))
        // ]);


        // gluc_org_arr = returnGlucArr(data_org.glucSeries, new_indices, date_array);
        // gluc_rly_arr = returnGlucArr(data_replay.glucSeries, new_indices, date_array);
        gluc_org_arr = returnGlucArr(data_org.glucSeries, new_indices_gluc, filtered_dates_gluc);
        gluc_rly_arr = returnGlucArr(data_replay.glucSeries, new_indices_gluc, filtered_dates_gluc);

        // Update area chart 
        areaChartHandler(myAreaChart, gluc_org_arr, gluc_rly_arr);
        areaChartDays(new_indices, indices);
    }

}

// Recalculate Median, Quartile25, Quartile75 glucose values based on new selected dates. 
function returnGlucArr(gluc_input, new_indices, date_array) {
    // Update area graph

    gluc_data = JSON.parse(JSON.stringify(gluc_input));

    //save data into dictionary  gluc_dict[date]: data 
    var gluc_dict = {};
    for (var i = 0; i < gluc_data.length; i++) {
        gluc_dict[gluc_data[i][0]] = gluc_data[i][1];
    }

    //get the selected date from the selected indices 
    //var gluc_keys = new_indices.map(i => date_array[i]);
    var gluc_keys = JSON.parse(JSON.stringify(date_array));

    var gluc_array = [];
    //get the data from the selected indices 
    for (var i = 0; i < gluc_keys.length; i++) {
        if (gluc_keys[i] in gluc_dict) {
            gluc_array.push(gluc_dict[gluc_keys[i]])
        } else {
            gluc_array.push([])
        }
    }

    calculated_result = glucPrct(gluc_array);
    var glucOrigMedian = timeDataProc(calculated_result[0], timeVec_5min)
    var glucOrig25 = timeDataProc(calculated_result[1], timeVec_5min)
    var glucOrig75 = timeDataProc(calculated_result[2], timeVec_5min)

    glucOriginal = [glucOrigMedian, glucOrig25, glucOrig75]
    return glucOriginal;

}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// DateRangePicker  
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

// Show date range text for date range picker 
function cb_drp(start, end) {
    var span_dates = $('#datepicker span');
    if (start && end) {
        span_dates.html(start.format('MM/DD/YY') + ' - ' + end.format('MM/DD/YY'));
    }
}

// Get a list of days between the start date and end date 
function createDayList(startDate, endDate) {
    var DateArray = [];
    var currentDate = moment(startDate);
    var stopDate = moment(endDate);
    while (currentDate <= stopDate) {
        DateArray.push(moment(currentDate).format('DD MMM YYYY'));
        currentDate = moment(currentDate).add(1, 'days');
    }
    return DateArray;
}

// Get yesterday when yesterday is selected    
function createOneDayList(startDateUnix) {
    var DateArray = [];
    var currentDate = new Date(startDateUnix * 1000);
    currentDate.setDate(currentDate.getDate() - 1);
    DateArray.push(currentDate.toLocaleDateString("en-US"));
    return DateArray;
}


// Create data objects for insulins 
function insulinData(data_obj) {
    var Profiles = [];
    var Timestamps = [];
    var InsulinProfileTime = [];
    for (var i = 0; i < data_obj.length; i++) {
        Profiles.push(timeDataProc(data_obj[i].slice(1, ), timeVec_30min))
        Timestamps.push(UnixTimeConverter(data_obj[i][0]));
        InsulinProfileTime.push(data_obj[i][0]);
    }
    if (InsulinProfileTime.length != 0) { ProfileTimes.push(InsulinProfileTime); }
    return [Profiles, Timestamps];
}

// Change meal data format to {'date':(time,carb)}. Example: {'Jan 1st 2019': [1200, 100]}
function createMealDict(meal_data, selected_date_array) {
    var meal_array = {};
    if (meal_data.length == 0) {
        for (var i = 0; i < selected_date_array.length; i++) {
            meal_array[selected_date_array[i]] = [];
        }
    } else {
        meal_data.forEach(function(item) {
            meal_array[item[0]] = [timeDataProc(item[1], timeVec_5min)]; //first array is the time and carbs for chart; 
            meal_array[item[0]].push(checkMealInfo(item[1])); //second array is the meal counts and meal index; 
        });
    }
    return meal_array;
}

// Check the index of the meals and the carbs of meals for each day 
function checkMealInfo(meal_array_one_day) {
    index_arr = [];
    for (var i = 0; i < meal_array_one_day.length; i++) {
        if (meal_array_one_day[i] != 0) {
            index_arr.push([i, meal_array_one_day[i]]);
        }
    }
    return index_arr;
}

// Defines date range picker
function drpHandler(firstLogin) {

    if (firstLogin == false) {
        var drp_el = $('#datepicker');

        drp_el.daterangepicker({
            maxDate: moment().subtract(1, 'days'),
            ranges: {
                'Yesterday': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
                'Last 7 Days': [moment().subtract(7, 'days'), moment().subtract(1, 'days')],
                'Last 30 Days': [moment().subtract(30, 'days'), moment().subtract(1, 'days')],
                'This Month': [moment().startOf('month'), moment().endOf('month')],
                'Last Month': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')]
            },
            "maxSpan": {
                "days": 60
            },
        }, cb_drp);


        // Events
        drp_el.on('apply.daterangepicker', function(ev, datepicker) { // Listener

            ProfileTimes = [];
            // Get start and end dates in unix format
            var dateRange = {
                //d1: datepicker.startDate.unix(),
                d1: datepicker.startDate.set({ hour: 0, minute: 0, second: 0, millisecond: 0 }).unix()+datepicker.startDate.set({ hour: 0, minute: 0, second: 0, millisecond: 0 }).utcOffset()*60,
                //d2: datepicker.endDate.unix()
                d2: datepicker.endDate.set({ hour: 23, minute: 59, second: 59, millisecond: 0 }).unix()+datepicker.endDate.set({ hour: 23, minute: 59, second: 59, millisecond: 0 }).utcOffset()*60
            };
            // day1 = datepicker.startDate.unix();
            // day2 = datepicker.endDate.unix();
            day1 = datepicker.startDate.set({ hour: 0, minute: 0, second: 0, millisecond: 0 }).unix()+datepicker.startDate.set({ hour: 0, minute: 0, second: 0, millisecond: 0 }).utcOffset()*60;
            day2 = datepicker.endDate.set({ hour: 23, minute: 59, second: 59, millisecond: 0 }).unix()+datepicker.endDate.set({ hour: 23, minute: 59, second: 59, millisecond: 0 }).utcOffset()*60;

            var selected_date_array = createDayList(datepicker.startDate, datepicker.endDate);
            selected_date_dcrp = selected_date_array;


            // Send dates to the server and get response
            fetch('/dashboard/calendar-changed', {
                    method: "POST",
                    credentials: "include",
                    body: JSON.stringify(dateRange),
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

                        defaultReplay(checkNoPlay(data.quality.nonplayable));
                        original_data = JSON.parse(JSON.stringify(data));
                        replay_data = {
                            "bProfiles": [],
                            "cfProfiles": [],
                            "crProfiles": [],
                            "glucSeries": [],
                            "metrics": {
                                "cv": Array(original_data.metrics.cv.length).fill(0),
                                "hbgi": Array(original_data.metrics.hbgi.length).fill(0),
                                "lbgi": Array(original_data.metrics.lbgi.length).fill(0),
                                "percentR1": Array(original_data.metrics.percentR1.length).fill(0),
                                "percentR2": Array(original_data.metrics.percentR2.length).fill(0),
                                "percentR3": Array(original_data.metrics.percentR3.length).fill(0),
                                "percentR4": Array(original_data.metrics.percentR4.length).fill(0)
                            },
                            "moH": [],
                            "moM": [],
                            "nHT": Array(original_data.nHT.length).fill(0),
                            "quality": { "nonplayable": [100], "playable": [0] },
                            "tdb": Array(original_data.tdb.length).fill(0),
                            "tdi": Array(original_data.tdi.length).fill(0)
                        }

                        if (checkIfAllNull(original_data)) {
                            popText("#warning", "<img class='center' src='../static/img/NoDataDinosaur.jpg')}}'> <p class='text-center text-dark my-5 p-2'> There are no data in the selected date range.</br> Please make a new selection. </p>");
                        }

                        track_change_arr = trackChanges(selected_date_array);
                        no_data_dcrp = noDataDates(selected_date_array, original_data.quality.nonplayable);

                        updateText('#MealSelectDay', mealDropDown(selected_date_array));
                        updateText('#SelectDisplayDate', dateDropDown(selected_date_array, no_data_dcrp));

                        displayPanel(original_data, replay_data, [...selected_date_array.keys()], selected_date_array);
                        moreDetails(original_data, replay_data, [...selected_date_array.keys()]);
                        dateFilter(original_data, replay_data, selected_date_array);

                        //Reset Panel
                        resetInsPanel();
                        resetSaveReplay();

                        // Update insuline profile selector options 
                        insulinProfileGenerator(data.bProfiles.length, data.crProfiles.length, data.cfProfiles.length);

                        // Change the meal input array to a dictionary using dates as keys 
                        var meal_array = createMealDict(data.moM, selected_date_array);
                        // Generate the meal bar chart
                        selectMeal(mealReplay, meal_array);

                        //Create insulin profile data
                        basalProfile_data = insulinData(data.bProfiles);
                        crProfile_data = insulinData(data.crProfiles);
                        cfProfile_data = insulinData(data.cfProfiles);

                        insulin_profile = [basalProfile_data[0], crProfile_data[0], cfProfile_data[0]];
                        insulin_times = [basalProfile_data[1], crProfile_data[1], cfProfile_data[1]];
                        insulin_times.map(i => i.push(lastDate(selected_date_array, no_data_dcrp)));

                        //Update insulin chart 
                        selectInsulin(lineReplay, insulin_profile, insulin_times);

                        //Select APSystem
                        $('#apSel').val(original_data.apSystem);
                        $('#apSel').change();
                    });
                })
                .catch(function(error) {
                    console.log("Fetch error: " + error);
                });


        });
    } else {

        var dat_opt = {
            maxDate: moment().subtract(1, 'days'),
            startDate: moment().subtract(1, 'days'),
            endDate: moment().subtract(1, 'days'),
            ranges: {
                'Yesterday': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
                'Last 7 Days': [moment().subtract(7, 'days'), moment().subtract(1, 'days')],
                'Last 30 Days': [moment().subtract(30, 'days'), moment().subtract(1, 'days')],
                'This Month': [moment().startOf('month'), moment().endOf('month')],
                'Last Month': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')]
            },
            "maxSpan": {
                "days": 60
            },
        };

        $('#datepicker').daterangepicker(dat_opt, cb_drp);
        cb_drp(dat_opt.startDate, dat_opt.endDate);

        // Get start and end dates in unix format
        var dateRange = {
            //d1: dat_opt.startDate.set({ hour: 0, minute: 0, second: 0, millisecond: 0 }).unix(),
            //d2: dat_opt.startDate.set({ hour: 24, minute: 0, second: 0, millisecond: 0 }).unix(),
            d1: dat_opt.startDate.set({ hour: 0, minute: 0, second: 0, millisecond: 0 }).unix()+dat_opt.startDate.set({ hour: 0, minute: 0, second: 0, millisecond: 0 }).utcOffset()*60,
            d2: dat_opt.startDate.set({ hour: 23, minute: 59, second: 59, millisecond: 0 }).unix()+dat_opt.startDate.set({ hour: 23, minute: 59, second: 59, millisecond: 0 }).utcOffset()*60,
        };

        // day1 = dat_opt.startDate.set({ hour: 0, minute: 0, second: 0, millisecond: 0 }).unix();
        // day2 = dat_opt.startDate.set({ hour: 24, minute: 0, second: 0, millisecond: 0 }).unix();
        day1 = dat_opt.startDate.set({ hour: 0, minute: 0, second: 0, millisecond: 0 }).unix()+dat_opt.startDate.set({ hour: 0, minute: 0, second: 0, millisecond: 0 }).utcOffset()*60;
        day2 = dat_opt.startDate.set({ hour: 23, minute: 59, second: 59, millisecond: 0 }).unix()+dat_opt.startDate.set({ hour: 23, minute: 59, second: 59, millisecond: 0 }).utcOffset()*60;

        //var selected_date_array = createOneDayList(day1);
        var selected_date_array = createDayList(moment().subtract(1, 'days'), moment().subtract(1, 'days'));
        selected_date_dcrp = selected_date_array;

        // Send dates to the server and get response
        fetch('/dashboard/calendar-changed', {
                method: "POST",
                credentials: "include",
                body: JSON.stringify(dateRange),
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

                    defaultReplay(checkNoPlay(data.quality.nonplayable));
                    original_data = JSON.parse(JSON.stringify(data));
                    replay_data = {
                        "bProfiles": [],
                        "cfProfiles": [],
                        "crProfiles": [],
                        "glucSeries": [],
                        "metrics": {
                            "cv": Array(original_data.metrics.cv.length).fill(0),
                            "hbgi": Array(original_data.metrics.hbgi.length).fill(0),
                            "lbgi": Array(original_data.metrics.lbgi.length).fill(0),
                            "percentR1": Array(original_data.metrics.percentR1.length).fill(0),
                            "percentR2": Array(original_data.metrics.percentR2.length).fill(0),
                            "percentR3": Array(original_data.metrics.percentR3.length).fill(0),
                            "percentR4": Array(original_data.metrics.percentR4.length).fill(0)
                        },
                        "moH": [],
                        "moM": [],
                        "nHT": Array(original_data.nHT.length).fill(0),
                        "quality": { "nonplayable": [100], "playable": [0] },
                        "tdb": Array(original_data.tdb.length).fill(0),
                        "tdi": Array(original_data.tdi.length).fill(0)
                    }

                    if (checkIfAllNull(original_data)) {
                        popText("#warning", "<img class='center' src='../static/img/NoDataDinosaur.jpg')}}'> <p class='text-center text-dark my-5 p-2'> There are no data in the selected date range.</br> Please make a new selection. </p>");
                    }

                    //track_change_arr = trackChanges(selected_date_array[0]);
                    track_change_arr = trackChanges(selected_date_array);
                    no_data_dcrp = noDataDates(selected_date_array, original_data.quality.nonplayable);
                    updateText('#MealSelectDay', mealDropDown(selected_date_array));
                    updateText('#SelectDisplayDate', dateDropDown(selected_date_array, no_data_dcrp));

                    displayPanel(original_data, replay_data, [...selected_date_array.keys()], selected_date_array);
                    moreDetails(original_data, replay_data, [...selected_date_array.keys()]);
                    dateFilter(original_data, replay_data, selected_date_array);

                    //Reset Panel
                    resetInsPanel();
                    resetSaveReplay();

                    // Update insuline profile selector options 

                    insulinProfileGenerator(data.bProfiles.length, data.crProfiles.length, data.cfProfiles.length);

                    // Change the meal input array to a dictionary using dates as keys 
                    var meal_array = createMealDict(data.moM, selected_date_array);
                    // Geneate the meal bar chart
                    selectMeal(mealReplay, meal_array);

                    //Create insulin profile data
                    
                    basalProfile_data = insulinData(data.bProfiles);
                    crProfile_data = insulinData(data.crProfiles);
                    cfProfile_data = insulinData(data.cfProfiles);
                
                    insulin_profile = [basalProfile_data[0], crProfile_data[0], cfProfile_data[0]];
                    insulin_times = [basalProfile_data[1], crProfile_data[1], cfProfile_data[1]];
                    insulin_times.map(i => i.push(lastDate(selected_date_array, no_data_dcrp)));
                      
                    //Update insulin chart 
                    selectInsulin(lineReplay, insulin_profile, insulin_times);
                    
                    //Select APSystem
                    $('#apSel').val(original_data.apSystem);
                    $('#apSel').change();

                });
            })
            .catch(function(error) {
                console.log("Fetch error: " + error);
            });

    }

};


/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Replay Panel 
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Insulin Command
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////// 


// Generate insulin profile options based on the value of selector InsType 
function insulinProfileGenerator(data_b, data_cr, data_cf) {

    $("#inputGroupInsType").change(function() {
        var val = $(this).val();
        if (val == "B") {
            if (data_b == 0) {
                var str = "<option value='' disabled selected>No Profiles</option>";
                $("#inputGroupInsProfile").html(str);
            } else {
                //var str="<option value='' disabled selected>Select Profile</option> <option value='all'> All </option>";
                var str = "<option value='all' selected> All </option>";
                for (var i = 0; i < data_b; i++) {
                    str += "<option value=" + i + "> Profile" + (i + 1) + "</option>"
                }
                $("#inputGroupInsProfile").html(str);
            }
        } else if (val == "CR") {
            if (data_cr == 0) {
                var str = "<option value='' disabled selected>No Profiles</option>";
                $("#inputGroupInsProfile").html(str);
            } else {
                //var str="<option value='' disabled selected>Select Profile</option> <option value='all'> All </option>";
                var str = "<option value='all' selected> All </option>";
                for (var i = 0; i < data_cr; i++) {
                    str += "<option value=" + i + "> Profile" + (i + 1) + "</option>"
                }
                $("#inputGroupInsProfile").html(str);
            }
        } else if (val == "CF") {
            if (data_cf == 0) {
                var str = "<option value='' disabled selected>No Profiles</option>";
                $("#inputGroupInsProfile").html(str);
            } else {
                //var str="<option value='' disabled selected>Select Profile</option> <option value='all'> All </option>";
                var str = "<option value='all' selected> All </option>";
                for (var i = 0; i < data_cf; i++) {
                    str += "<option value=" + i + "> Profile" + (i + 1) + "</option>"
                }
                $("#inputGroupInsProfile").html(str);
            }
        } else if (val == "all") {
            var str = "<option value='all' selected> All </option>";
            $("#inputGroupInsProfile").html(str);
        }
    });
}


// Defines insulin time range picker
function trpHandler() {

    var trp_el = $('#ins-timepicker');

    trp_el.daterangepicker({
        startDate: moment("0000", 'hmm').format("HH:mm"),
        endDate: moment("0000", 'hmm').format("HH:mm"),
        timePicker: true,
        timePicker24Hour: true,
        timePickerIncrement: 30,
        timePickerSeconds: false,
        locale: {
            format: 'HH:mm'
        }
    });

    // Events
    trp_el.on('show.daterangepicker', function(ev, timepicker) { // Listener
        timepicker.container.find(".calendar-table").hide();
    });

    trp_el.on('showCalendar.daterangepicker', function(ev, timepicker) { // Listener
        timepicker.container.find(".calendar-table").remove();
    });

    trp_el.on('apply.daterangepicker', function(ev, timepicker) { // Listener

        var tPivot = new Date();
        tPivot.setHours(0);
        tPivot.setMinutes(0);
        tPivot.setSeconds(0);

        var tIni = Math.round(timepicker.startDate.diff(tPivot, 'minutes') / 30);
        var tEnd = Math.round(timepicker.endDate.diff(tPivot, 'minutes') / 30);

        cb_trp(timepicker.startDate, timepicker.endDate)

    });

};

// Select entire day in the insulin command from 0:00 - 23:30 
function selectEntireDay() {

    var date = "1971-01-01";
    var start_time = "00:00";
    var end_time = "23:30";
    startDate = moment(date + ' ' + start_time)
    endDate = moment(date + ' ' + end_time)

    if ($("#EntireDay").is(':checked')) {
        $('#ins-timepicker').daterangepicker({

            startDate: startDate.format("HH:mm"),
            endDate: endDate.format("HH:mm"),
            timePicker: true,
            timePicker24Hour: true,
            timePickerIncrement: 30,
            timePickerSeconds: false,
            locale: {
                format: 'HH:mm'
            },

        });

        // Events
        $('#ins-timepicker').on('show.daterangepicker', function(ev, timepicker) { // Listener
            timepicker.container.find(".calendar-table").hide();
        });

        $('#ins-timepicker').on('showCalendar.daterangepicker', function(ev, timepicker) { // Listener
            timepicker.container.find(".calendar-table").remove();
        });

        $('#ins-timepicker').data('daterangepicker').hide()
        cb_trp(startDate, endDate);
    } else {
        cb_trp(startDate, startDate);
        trpHandler();
    }

}

// Show text of the time range picker in the insulin command 
function cb_trp(start, end) {
    var span_time = $('#ins-timepicker span');
    span_time.html(start.format('HH:mm') + ' - ' + end.format('HH:mm'));
}


// Defines insulin slider
function insSliderHandler(value) {

    var insSlider = $("#insSlider");
    var insSliderV = $("#insSliderValue");
    insSlider.prop('value', value);
    insSliderV.text(value);

    // Events
    insSlider.on('change click', function(ev) {
        preValue = parseInt(insSliderV.text());
        insSliderV.text(this.value);
    });

}

// Generate the profile time range based on server return.   
function profileTimeArr(start_date, end_date) {

    var DateArray = [];
    var currentDate = new Date(Date.parse(start_date));
    var stopDate = new Date(Date.parse(end_date));
    while (currentDate <= stopDate) {
        DateArray.push(updateDateFormat(currentDate));
        currentDate.setDate(currentDate.getDate() + 1);
    }

    return DateArray;

}

// Select insulin type, update charts and insulin changes.  
function selectInsulin(chart, data, data_time) {

    var updated_data_insulin = JSON.parse(JSON.stringify(data)); //copy data 
    var profile_time = JSON.parse(JSON.stringify(data_time));
    var updated_y_values;

    //When insulin type changes: 
    $("#inputGroupInsType").change(function() {

        $('#ProfileTimeSection').hide();
        changeToggle('Insulin');

        var val = $(this).val();
        if (val == "B") {
            data_obj = data[0]; //associated with the original data 
            DisableInsCommand(data_obj);
            updated_data_obj_ins = updated_data_insulin[0]; //asssociated with the copied data 
            insulin_time = profile_time[0];
            selectInsProfile(chart, data_obj, updated_data_obj_ins, insulin_time,'Basal rate [U/h]');
        } else if (val == "CR") {
            data_obj = data[1];
            DisableInsCommand(data_obj);
            updated_data_obj_ins = updated_data_insulin[1];
            insulin_time = profile_time[1];
            selectInsProfile(chart, data_obj, updated_data_obj_ins, insulin_time,'Carbohydrate Ratio [g/U]');
        } else if (val == "CF") {
            data_obj = data[2];
            DisableInsCommand(data_obj);
            updated_data_obj_ins = updated_data_insulin[2];
            insulin_time = profile_time[2];
            selectInsProfile(chart, data_obj, updated_data_obj_ins, insulin_time,'Correction Factor [mg/dl/U]');
        } else if (val == "all") {
            data_obj = data; //all data objects 
            DisableInsCommand(data_obj);
            $('#ProfileTimeSection span').html('');
            updated_data_obj_ins = updated_data_insulin; //all data objects 
            insulin_time = profile_time[0]; //randomly use one 
            selectInsProfile(chart, [], [], [],' ');
        }

        selectEntireDay();
        $('#EntireDay').prop('checked', false);
        $('#ins-timepicker span').html('00:00 - 00:00');
        insSliderHandler(100);

    });

    //When Reset Button is clicked, updated value is changed back to the original data. 
    $("#tempInsReset").click(function() {

        changeToggle('Insulin');
        updated_data_insulin = JSON.parse(JSON.stringify(data));
        popText("#success", "<br> <p>Basal, CR and CF are all reset to original values.</p>");
        $("#inputGroupInsType").val([]); //reset Insulin selectors 
        $("#inputGroupInsProfile").val([]);
        updateInsChart(chart, [], []);
        resetInsTrack(track_change_arr);
        updateDropDown('#SelectDisplayDate', track_change_arr, no_data_dcrp);
        insulin_profile_changes = updated_data_insulin;
        selectEntireDay();
        $('#EntireDay').prop('checked', false);
        $('#ins-timepicker span').html('00:00 - 00:00');
        insSliderHandler(100);
        removePopulatedDropdown("#inputGroupInsProfile"); //remove all populated drop down list 
        document.getElementById("save-replay").disabled = true;
    });

    //When Apply Changes is clicked, 
    $("#tempInsUpdate").click(function() {

        changeToggle('Insulin');
        var start_time = $('#ins-timepicker').data('daterangepicker').startDate.format('HH:mm');
        var end_time = $('#ins-timepicker').data('daterangepicker').endDate.format('HH:mm');
        hour_dic = time_index();
        begin_index = parseInt(hour_dic[start_time]);
        end_index = parseInt(hour_dic[end_time]);

        document.getElementById("save-replay").disabled = true;

        if ($("#inputGroupInsType").val() == 'all' & $("#inputGroupInsProfile").val() == "all") {
            var changeValue = false;
            var first_loop = true;
            for (var i = 0; i < updated_data_obj_ins.length; i++) {
                insulin_type_data = data_obj[i];
                insulin_type_updated_data = updated_data_obj_ins[i]; //loop through all insulin types
                for (var j = 0; j < insulin_type_data.length; j++) { //loop through all profiles 
                    original_y_values = insulin_type_data[j].map(a => a.y);
                    updated_y_values = insulin_type_updated_data[j].map(a => a.y);
                    for (var k = begin_index; k <= end_index; k++) {
                        var ori_val = original_y_values[k];
                        var new_value = ori_val * (parseInt($("#insSlider").val()) / 100.0);
                        if (first_loop) {
                            if (ori_val != new_value) {
                                changeValue = true;
                            }
                            first_loop = false;
                        }
                        //updated_y_values[k] = parseFloat(new_value.toFixed(2));
                        updated_y_values[k] = new_value;
                    }
                    updateInsValues(insulin_type_updated_data[j], updated_y_values);
                }
            }
            //update track changes for all days 
            if (changeValue == true) {
                checkInsUpdate([true], [false], profileTimeArr(insulin_time[0], insulin_time[insulin_time.length - 1]));
                updateDropDown('#SelectDisplayDate', track_change_arr, no_data_dcrp);
            } else {
                checkInsUpdate([false], [false], profileTimeArr(insulin_time[0], insulin_time[insulin_time.length - 1]));
                updateDropDown('#SelectDisplayDate', track_change_arr, no_data_dcrp);
            }

            popText("#success", "<br> <p>Basal, CR and CF are all selected and all profiles have been updated.</p>");
            updateInsChart(chart, [], []);
        } else if ($("#inputGroupInsType").val() != 'all' & $("#inputGroupInsProfile").val() == "all") {

            var show_profile_chart = false;
            if (updated_data_obj_ins.length == 1) {
                show_profile_chart = true;
            }

            if (show_profile_chart == false) {
                updateInsChart(chart, [], []);
                $('#ProfileTimeSection').hide();

            }

            var changeValue = false;
            var first_loop = true;
            for (var j = 0; j < updated_data_obj_ins.length; j++) { //loop through all profiles 
                original_y_values = data_obj[j].map(a => a.y);
                updated_y_values = updated_data_obj_ins[j].map(a => a.y);
                //track if made changes or not, only run once
                for (var k = begin_index; k <= end_index; k++) {
                    var ori_val = original_y_values[k];
                    var new_value = ori_val * (parseInt($("#insSlider").val()) / 100.0);
                    //updated_y_values[k] = parseFloat(new_value.toFixed(2));
                    updated_y_values[k] = new_value;
                    if (first_loop) {
                        if (ori_val != new_value) {
                            changeValue = true;
                        }
                        first_loop = false;
                    }
                }
                updateInsValues(updated_data_obj_ins[j], updated_y_values);

                //If there is a single profile, display the profile 
                if (show_profile_chart == true) {
                    $('#inputGroupInsProfile').val(j);
                    updateInsChart(chart, data_obj[j], updateInsValues(updated_data_obj_ins[j], updated_y_values));
                }
            }
            ///update track changes for all days 
            if (changeValue == true) {
                checkInsUpdate([true], [false], profileTimeArr(insulin_time[0], insulin_time[insulin_time.length - 1]));
                updateDropDown('#SelectDisplayDate', track_change_arr, no_data_dcrp);
            } else {
                checkInsUpdate([false], [false], profileTimeArr(insulin_time[0], insulin_time[insulin_time.length - 1]));
                updateDropDown('#SelectDisplayDate', track_change_arr, no_data_dcrp);
            }

            popText("#success", "<br> <p>All insulin profiles have been updated. You can check them individually through the Insulin Command.</p>");


        } else if ($("#inputGroupInsProfile").val() == null) {
            popText("#warning", "<br> <p>Please select a profile.</p>");
        } else {
            var changeValue = false;
            var first_loop = true;
            selected_profile = $("#inputGroupInsProfile").val();
            original_y_values = data_obj[selected_profile].map(a => a.y); //get the y values from 
            updated_y_values = updated_data_obj_ins[selected_profile].map(a => a.y);
            for (var i = begin_index; i <= end_index; i++) {
                var ori_val = original_y_values[i];
                var new_value = ori_val * (parseInt($("#insSlider").val()) / 100.0);
                //updated_y_values[i] = parseFloat(new_value.toFixed(2));
                updated_y_values[i] = new_value;
                if (first_loop) {
                    if (ori_val != new_value) {
                        changeValue = true;
                    }
                    first_loop = false;
                }
            }

            //global variable track_changes will change with the associated profile dates; 
            if (changeValue == true) {
                checkInsUpdate([true], [false], profileTimeArr(insulin_time[selected_profile], insulin_time[parseInt(selected_profile) + 1]));
                updateDropDown('#SelectDisplayDate', track_change_arr, no_data_dcrp);
            } else {
                checkInsUpdate([false], [false], profileTimeArr(insulin_time[selected_profile], insulin_time[parseInt(selected_profile) + 1]));
                updateDropDown('#SelectDisplayDate', track_change_arr, no_data_dcrp);
            }
            updateInsChart(chart, data_obj[selected_profile], updateInsValues(updated_data_obj_ins[selected_profile], updated_y_values));
        }
    });
    insulin_profile_changes = updated_data_insulin;
}

// Update insulin chart while the insulin profile selector changes. 
function selectInsProfile(chart, data, updated_data, profile_time,yLabel) {

    chart.options.scales.yAxes[0].scaleLabel.labelString = yLabel;
    var data_time = JSON.parse(JSON.stringify(profile_time));
    updateInsChart(chart, data, updated_data);

    $('#inputGroupInsProfile').change(function() {
        changeToggle('Insulin');
        $('#ProfileTimeSection').show();
        if ($('#inputGroupInsProfile').val() == 'all') {
            $('#ProfileTimeSection span').html('');
        }
        var selected_option = parseInt($('#inputGroupInsProfile').val());
        updateInsChart(chart, data[selected_option], updated_data[selected_option])
        showProfileTime(data_time[selected_option], data_time[parseInt(selected_option + 1)]);
    });
}

// Update insulin profile data based on user inputs 
function updateInsValues(data, y_values) {
    for (var i in data) {
        data[i].y = y_values[i];
    }
    return data;
}


// Disable insulin command when there is no profiles for a insulin type selected. 
function DisableInsCommand(data_obj) {
    $('#ins-timepicker').show();
    $('#ins-slider-section').show();
    $('#ins-changes-section').show();
    $('#disable-content-ins').hide();
    if (data_obj.length == 0) {
        $('#ins-timepicker').hide();
        $('#ins-slider-section').hide();
        $('#ins-changes-section').hide();
        $('#disable-content-ins').show();
    } else {
        $('#ins-timepicker').show();
        $('#ins-slider-section').show();
        $('#ins-changes-section').show();
        $('#disable-content-ins').hide();
    }
}



///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Insulin Graph
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////// 

function showProfileTime(start_time, end_time) {
    var span_dates = $('#ProfileTimeSection span');
    if (start_time && end_time) {
        span_dates.html(start_time + ' - ' + end_time);
    }
}

// Update meal chart 
function updateInsChart(chart, original_data, new_data) {
    chart.data.datasets[0].data = original_data;
    chart.data.datasets[1].data = new_data;
    chart.update();
}

///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Meal Command
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////// 



// Populate Date List for Meal Date List
function mealDropDown(selected_date_array) {

    var str = "<option value='' disabled selected>Select Date</option> <option value='all'> All </option>";

    for (var i = 0; i < selected_date_array.length; i++) {
        str += "<option value=" + i + ">" + selected_date_array[i] + "</option>";
    }

    return str;
}

// Define meal time slider.
function timeSliderHandler(value) {

    var timeSlider = $("#meal-timeslider");
    var timeSliderV = $("#meal-timeslider-val");
    timeSlider.prop('value', value);
    timeSliderV.text(value);

    // Events
    timeSlider.on('change click', function() {
        preValue = Number(timeSliderV.text());
        timeSliderV.text(this.value);
    });

}

// Defines meal value slider.
function mealSliderHandler(value) {

    var mealSlider = $("#mealSlider");
    var mealSliderV = $("#mealSliderValue");
    mealSlider.prop('value', value);
    mealSliderV.text(value);

    // Events
    mealSlider.on('change click', function() {
        preValue = parseInt(mealSliderV.text());
        mealSliderV.text(this.value);
    });
}

// Change time / change carb value 
function selectMeal(chart, meal_array) { //data meal is the meal information 

    var updated_data_meal = JSON.parse(JSON.stringify(meal_array));
    var data_obj;

    $("#MealSelectDay").change(function() {
        changeToggle('Meal');
        var val = $(this).find("option:selected").text();

        //Find the value associated with the day 
        if (val in meal_array) {

            if (meal_array[val].length == 0) {

                data_ori_whole = [];
                data_updated_whole = [];
                data_obj = []; //meal data is selected based on the selected day
                updated_data_obj = [];
                data_ct_org = [];
                data_ct_new = [];

            } else {

                data_ori_whole = meal_array[val];
                data_updated_whole = updated_data_meal[val];

                data_obj = data_ori_whole[1];
                updated_data_obj = data_updated_whole[1]; //meal data is selected based on the selected day

                data_ct_org = data_ori_whole[0];
                data_ct_new = data_updated_whole[0];

                //Display Chart Information 

                updateMealChart(chart, mealBarArray(data_ori_whole[1], timeVec_5min), data_ori_whole[0], mealBarArray(data_updated_whole[1], timeVec_5min), data_updated_whole[0]);
            }

        } else {
            data_ori_whole = meal_array;
            data_updated_whole = updated_data_meal;
            data_obj = [];
            updated_data_obj = []; //meal data is selected based on the selected day   
            data_ct_org = [];
            data_ct_new = [];

        }

        //Populate the meals associated with the day 
        if (val == ' All ') { //If all meals selected all 
            var str = "<option value='all' selected> All </option>";
            DisableMealCommand(0);
            updateMealChart(chart, [], [], [], []);
        } else if (data_obj.length == 0) { //If the date has no meals 
            var str = "<option value='' disabled selected>No Meals</option>"; //disable slider and change button if there is no meal data associated with the selected day
            updateMealChart(chart, [], [], [], []);
        } else {
            //var str="<option value='' disabled selected>Select Meal</option> <option value='all'> All </option>";
            var str = "<option value='all' selected> All </option>";
        }

        for (var i = 0; i < data_obj.length; i++) {
            str += "<option value=" + i + "> Meal" + (i + 1) + "</option>";
        }

        $("#MealSelect").html(str);


        //Disable meal changes when No meals 
        if ($("#MealSelect").find("option:selected").text() == 'No Meals') {
            DisableMealCommand([]);
        } else {
            DisableMealCommand(0);
        }

        //Reset Slider 
        mealSliderHandler(100);
        timeSliderHandler(0);

    });


    $("#MealSelect").change(function() {
        changeToggle('Meal');
    });

    $("#tempMealReset").click(function() {
        changeToggle('Meal');
        updated_data_meal = JSON.parse(JSON.stringify(meal_array));
        popText("#success", "<br> <p>All meals are reset to original values.</p>");
        $("#MealSelectDay").val([]);
        $("#MealSelect").val([]);
        updateMealChart(chart, [], [], [], []);
        resetMealTrack(track_change_arr);
        updateDropDown('#SelectDisplayDate', track_change_arr, no_data_dcrp);
        meal_changes = updated_data_meal;
        removePopulatedDropdown("#MealSelect");
        document.getElementById("save-replay").disabled = true;
    });

    $("#tempMealUpdate").unbind("click").click(function() {
        changeToggle('Meal');
        document.getElementById("save-replay").disabled = true;
        if ($("#MealSelectDay").val() == 'all' & $("#MealSelect").val() == "all") {
            //loop through all days      

            var show_profile_chart = false;
            if (Object.keys(data_ori_whole).length == 1) {
                show_profile_chart = true;
            }

            if (show_profile_chart == false) {
                updateMealChart(chart, [], [], [], []);
            }

            for (val in data_ori_whole) {
                // for each day
                data_ori_whole_meal = data_ori_whole[val];
                data_updated_whole_meal = data_updated_whole[val];
                data_obj_meal = data_ori_whole_meal[1];
                updated_data_obj_meal = data_updated_whole_meal[1]; //meal data is selected based on the selected day
                data_ct_org_meal = data_ori_whole_meal[0];
                data_ct_new_meal = data_updated_whole_meal[0];
                // update selected-day track changes;   
                //loop through all meals 

                for (var i = 0; i < data_obj_meal.length; i++) {
                    var ori_index_carb = data_obj_meal[i]; //data_obj has the meal index and carb values of the selected day in an array 
                    var new_index = ori_index_carb[0] + ($("#meal-timeslider").val() / 5.0);
                    var new_carb = parseInt(ori_index_carb[1] * (parseInt($("#mealSlider").val()) / 100.0));
                    updated_data_obj_meal[i] = [new_index, new_carb];
                }

                checkMealUpdate(data_obj_meal, updated_data_obj_meal, [val]);

                //updated the values for each day 
                updated_ct_new_meal = new Array(288).fill(NaN);
                for (var i = 0; i < updated_data_obj_meal.length; i++) {
                    updated_ct_new_meal[updated_data_obj_meal[i][0]] = updated_data_obj_meal[i][1];
                }

                data_ct_new_meal = timeDataProc(updated_ct_new_meal, timeVec_5min); //update the value in updated_data_meal;               
                data_updated_whole[val] = [data_ct_new_meal, updated_data_obj_meal];

                if (show_profile_chart == true) {
                    updateMealChart(chart, mealBarArray(data_obj_meal, timeVec_5min), data_ct_org_meal, mealBarArray(updated_data_obj_meal, timeVec_5min), data_ct_new_meal);
                }

            }

            updateDropDown('#SelectDisplayDate', track_change_arr, no_data_dcrp);
            popText('#success', "<br> <p>All meals have been updated. You can check them individually through the Meal Command.</p>");

        } else if ($("#MealSelectDay").val() != 'all' & $("#MealSelect").val() == "all") {

            //loop through all meals 
            for (var i = 0; i < data_obj.length; i++) {
                var ori_index_carb = data_obj[i]; //data_obj has the meal index and carb values of the selected day in an array 
                var new_index = ori_index_carb[0] + ($("#meal-timeslider").val() / 5.0);
                var new_carb = parseInt(ori_index_carb[1] * (parseInt($("#mealSlider").val()) / 100.0));
                updated_data_obj[i] = [new_index, new_carb];
            }

            //updated the values
            updated_ct_new = new Array(288).fill(NaN);
            for (var i = 0; i < updated_data_obj.length; i++) {
                updated_ct_new[updated_data_obj[i][0]] = updated_data_obj[i][1];
            }

            data_ct_new = timeDataProc(updated_ct_new, timeVec_5min); //update the value in updated_data_meal; 
            data_updated_whole[0] = data_ct_new;
            data_updated_whole[1] = updated_data_obj;

            // update selected-day track changes;  
            var selected_day = $("#MealSelectDay :selected").text();
            checkMealUpdate(data_obj, updated_data_obj, [selected_day]);
            updateDropDown('#SelectDisplayDate', track_change_arr, no_data_dcrp);

            //Display Chart Information 
            updateMealChart(chart, mealBarArray(data_ori_whole[1], timeVec_5min), data_ori_whole[0], mealBarArray(data_updated_whole[1], timeVec_5min), data_updated_whole[0]);
        } else if ($("#MealSelect").val() == null) {
            popText("#warning", "<br> <p>Please select a meal.</p");
        } else {
            var ori_index_carb = data_ori_whole[1][$("#MealSelect").val()]; //data_obj has the meal index and carb values of the selected day in an array 
            var new_index = ori_index_carb[0] + ($("#meal-timeslider").val() / 5.0);
            var new_carb = parseInt(ori_index_carb[1] * (parseInt($("#mealSlider").val()) / 100.0));
            updated_data_obj[$("#MealSelect").val()] = [new_index, new_carb];
            //updated the chart 
            updated_ct_new = new Array(288).fill(NaN);
            for (var i = 0; i < updated_data_obj.length; i++) {
                updated_ct_new[updated_data_obj[i][0]] = updated_data_obj[i][1];
            }
            data_ct_new = timeDataProc(updated_ct_new, timeVec_5min); //update the value in updated_data_meal; 
            data_updated_whole[0] = data_ct_new;
            data_updated_whole[1] = updated_data_obj;

            // update selected-day track changes;  
            var selected_day = $("#MealSelectDay :selected").text();
            checkMealUpdate(data_obj, updated_data_obj, [selected_day]);

            updateDropDown('#SelectDisplayDate', track_change_arr, no_data_dcrp);

            //Display Chart Information 

            updateMealChart(chart, mealBarArray(data_ori_whole[1], timeVec_5min), data_ori_whole[0], mealBarArray(data_updated_whole[1], timeVec_5min), data_updated_whole[0]);

        }
    });

    meal_changes = updated_data_meal;
}


// Disable meal slider and save change button 
function DisableMealCommand(data_obj) {

    $('#meal-slider-section').show();
    $('#meal-changes-section').show();
    $('#disable-content-meal').hide();

    if (data_obj.length == 0) {
        $('#meal-slider-section').hide();
        $('#meal-changes-section').hide();
        $('#disable-content-meal').show();
    } else {
        $('#meal-slider-section').show();
        $('#meal-changes-section').show();
        $('#disable-content-meal').hide();

    }
}

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Meal Bar Graph
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


// Takes a 288 elements as an array. If a element has value, fill the elements before and after it with the same value.  
function fillBeforeandAfter(meal_data_array) {
    meal_data_array.forEach(function(value, i) {
        if (!isNaN(value) & isNaN(meal_data_array[i - 1])) {
            meal_data_array[i - 1] = value;
            meal_data_array[i + 1] = value;
        }
    });
}

// Takes the individual meal points (time of meal and meal values) and change it to an array with 288 values.   
function mealBarArray(meal_data_obj, timeVec_5min) {
    meal_data_array = new Array(288).fill(NaN);
    for (var i = 0; i < meal_data_obj.length; i++) {
        meal_data_array[meal_data_obj[i][0]] = meal_data_obj[i][1];
    }
    fillBeforeandAfter(meal_data_array);
    meal_data_new = timeDataProc(meal_data_array, timeVec_5min);
    return meal_data_new;
}



// Update meal chart 
function updateMealChart(chart, original_bar_ct_data, original_ct_data, new_bar_ct_data, new_ct_data) {
    chart.data.datasets[0].data = original_bar_ct_data;
    chart.data.datasets[1].data = original_ct_data;
    chart.data.datasets[2].data = new_bar_ct_data;
    chart.data.datasets[3].data = new_ct_data;
    chart.update();
}

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Disable Replay Panel when No Data
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////// 


function defaultReplay(check_no_play) {
    disableReplayPanel(check_no_play);
}

function disableReplayPanel(check_no_play) {

    document.getElementById("inputGroupInsType").disabled = check_no_play;
    document.getElementById("inputGroupInsProfile").disabled = check_no_play;
    document.getElementById("EntireDay").disabled = check_no_play;
    document.getElementById("ins-timepicker").disabled = check_no_play;
    document.getElementById("insSlider").disabled = check_no_play;
    document.getElementById("tempInsUpdate").disabled = check_no_play;
    document.getElementById("tempInsReset").disabled = check_no_play;
    document.getElementById("MealSelectDay").disabled = check_no_play;
    document.getElementById("MealSelect").disabled = check_no_play;
    document.getElementById("meal-timeslider").disabled = check_no_play;
    document.getElementById("mealSlider").disabled = check_no_play;
    document.getElementById("tempMealUpdate").disabled = check_no_play;
    document.getElementById("tempMealReset").disabled = check_no_play;
    document.getElementById("apSel").disabled = check_no_play;
    document.getElementById("adjIns").disabled = check_no_play;
    document.getElementById("genIns").disabled = check_no_play;
    document.getElementById("adjHTs").disabled = check_no_play;
    document.getElementById("genHTs").disabled = check_no_play;
    document.getElementById("inputGroupReplay").disabled = check_no_play;
    document.getElementById("submit-data").disabled = check_no_play;
    document.getElementById("save-replay").disabled = check_no_play;
    document.getElementById("generate-report").disabled = check_no_play;

}

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Toggle Button
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////// 

function toggleMeal() {
    $('#lineReplay').show();
    $('#mealReplay').hide();
    $('input[type=radio][name=view]').change(function() {
        if (this.value == 'Insulin_Toggle') {
            $('#lineReplay').show();
            $('#mealReplay').hide();
        } else if (this.value == 'Meal_Toggle') {
            $('#lineReplay').hide();
            $('#mealReplay').show();
            $('#ProfileTimeSection').hide();

        }
    });
}

function changeToggle(choice) {
    if (choice == "Insulin" | choice == null) {
        $("#Insulin_Toggle").prop("checked", true).trigger("click");
        $('#lineReplay').show();
        $('#mealReplay').hide();
        $('#ProfileTimeSection').show();
    }
    if (choice == "Meal") {
        $("#Meal_Toggle").prop("checked", true).trigger("click");
        $('#lineReplay').hide();
        $('#mealReplay').show();
        $('#ProfileTimeSection').hide();
    }
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Additional Parameters 
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

// Track checkboxes for additional parameters. 
function simExtraFeatures() {

    $("#genIns").click(function() {
        if ($("#genIns").is(':checked')) {
            genIns = true;
        } else {
            genIns = false;
        }
    });

    $("#adjIns").click(function() {
        if ($("#adjIns").is(':checked')) {
            adjIns = true;
        } else {
            adjIns = false;
        }
    });

    $("#genHTs").click(function() {
        if ($("#genHTs").is(':checked')) {
            genHTs = true;
        } else {
            genHTs = false;
        }
    });

    $("#adjHTs").click(function() {
        if ($("#adjHTs").is(':checked')) {
            adjHTs = true;
        } else {
            adjHTs = false;
        }
    });
}


/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Reset Replay Panel 
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

// Reset replay panel. 
function resetInsPanel() {
    mealSliderHandler(100);
    timeSliderHandler(0);
    insSliderHandler(100);
    cb_trp(moment("0000", "hmm"), moment("0000", "hmm"));
    $('#ins-timepicker span').html('00:00 - 00:00');
    $('#EntireDay').prop('checked', false);

    insulinProfileGenerator([], [], []);
    $("#inputGroupInsType").val([]); //reset all selectors 
    $("#MealSelectDay").val([]);


    removePopulatedDropdown("#inputGroupInsProfile"); //remove all populated drop down list 
    removePopulatedDropdown("#MealSelect");
    removePopulatedDropdown("#inputGroupReplay");

    DisableMealCommand(0); //reset disable 
    DisableInsCommand(0);
    popWarning();


    updateMealChart(mealReplay, NaN, NaN, NaN, NaN) //reset all graphs 
    updateInsChart(lineReplay, NaN, NaN);
    $('#ProfileTimeSection').hide();
    $('#ProfileTimeSection span').html('');
    resetProgressBar();
}

// Reset progress bar 
function resetProgressBar() {
    var element = document.getElementById("myprogressBar");
    element.style.width = 0 + '%';
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Click Run: 
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

function submit_run() {
    $("#submit-data").click(function() {

        var element = document.getElementById("myprogressBar");

        element.style.width = 1 + '%';

        var return_data = {};
        return_data["d1"] = day1;
        return_data["d2"] = day2;
        return_data["apSel"] = $('#apSel').val();
        return_data["adjIns"] = adjIns;
        return_data["genIns"] = genIns;
        return_data["adjHTs"] = adjHTs;
        return_data["genHTs"] = genHTs;
        if (insulin_profile_changes[0].length > 0) {
            return_data["bProfiles"] = insulin_profile_changes[0].map(profile => profile.map(i => i.y));
            for (var i = 0; i < return_data["bProfiles"].length; i++) {
                return_data["bProfiles"][i].unshift(ProfileTimes[0][i]);
            }
            return_data["crProfiles"] = insulin_profile_changes[1].map(profile => profile.map(i => i.y));
            for (var i = 0; i < return_data["crProfiles"].length; i++) {
                return_data["crProfiles"][i].unshift(ProfileTimes[1][i]);
            }
            return_data["cfProfiles"] = insulin_profile_changes[2].map(profile => profile.map(i => i.y));
            for (var i = 0; i < return_data["cfProfiles"].length; i++) {
                return_data["cfProfiles"][i].unshift(ProfileTimes[2][i]);
            }
        } else {
            return_data["bProfiles"] = [];
            return_data["crProfiles"] = [];
            return_data["cfProfiles"] = [];
        }
        var keys = Object.keys(meal_changes);
        var meal_arr = keys.map(i => meal_changes[i][0]);
        if (meal_arr.length == 1 && typeof meal_arr[0] == 'undefined') {
            return_data['moM'] = [];
            return_data["moH"] = [];
        } else {
            return_data['moM'] = keys.map(i => [i, meal_changes[i][0].map(j => check_nan(j.y))]);
            return_data["moH"] = [];
        }

        element.style.width = 50 + '%';
        $("#warning").html("<img class='center' src='../static/img/simRunning.png')}}'> <p class='text-center text-dark my-5 p-2'> WST is running the simulation.</br> Please do not close the browser, results will be displayed soon. </p>");
        $("#warning").dialog('open');
        // Send dates to the server and get response
        fetch('/dashboard/run-replay', {
            method: "POST",
            credentials: "include",
            body: JSON.stringify(return_data),
            cache: "no-cache",
            headers: new Headers({
                "content-type": "application/json"
            })
        })

        .then(function(response) {
                if (response.status !== 200) {
                    console.log(`Looks like there was a problem. Status code: ${response.status}`);
                    popText("#warning", "<br> <p>There is a status error.</p");
                    element.style.width = 0 + '%';
                    return;
                }

                response.json().then(function(data) {
                    $("#warning").dialog('close');
                    element.style.width = 100 + '%';
                    replay_data = JSON.parse(JSON.stringify(data));
                    displayPanel(original_data, replay_data, [...selected_date_dcrp.keys()], selected_date_dcrp);
                    moreDetails(original_data, replay_data, [...selected_date_dcrp.keys()]);
                    dateFilter(original_data, replay_data, selected_date_dcrp);
                    $("#display-all-date").removeAttr("checked");
                    document.getElementById("save-replay").disabled = false;
                    element.style.width = 0 + '%';
                });
            })
            .catch(function(error) {
                console.log("Fetch error: " + error);
                element.style.width = 0 + '%';
            });

    });
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Replay Drop Down List 
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

// Populate Options for Replay Drop Down 
function replayDropDown(replay_array) {
    //var str = "<option value='' disabled selected>New Replay</option>";
    var str = "<option value=-1 selected>New Replay</option>";
    for (var i = 0; i < replay_array.length; i++) {
        str += "<option value=" + i + ">" + "Replay " + (i + 1) + " </option>";
    }
    return str;
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Generate Report: 
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


function generate_report() {
    $("#generate-report").click(function() {
        var return_data = {};
        return_data["d1"] = day1;
        return_data["d2"] = day2;
        return_data["apSel"] = $('#apSel').val();
        return_data["adjIns"] = adjIns;
        return_data["genIns"] = genIns;
        return_data["adjHTs"] = adjHTs;
        return_data["genHTs"] = genHTs;
        if (insulin_profile_changes[0].length > 0) {
            return_data["bProfiles"] = insulin_profile_changes[0].map(profile => profile.map(i => i.y));
            for (var i = 0; i < return_data["bProfiles"].length; i++) {
                return_data["bProfiles"][i].unshift(ProfileTimes[0][i]);
            }
            return_data["crProfiles"] = insulin_profile_changes[1].map(profile => profile.map(i => i.y));
            for (var i = 0; i < return_data["crProfiles"].length; i++) {
                return_data["crProfiles"][i].unshift(ProfileTimes[1][i]);
            }
            return_data["cfProfiles"] = insulin_profile_changes[2].map(profile => profile.map(i => i.y));
            for (var i = 0; i < return_data["cfProfiles"].length; i++) {
                return_data["cfProfiles"][i].unshift(ProfileTimes[2][i]);
            }
        } else {
            return_data["bProfiles"] = [];
            return_data["crProfiles"] = [];
            return_data["cfProfiles"] = [];
        }
        return_data["original"] = original_data;
        return_data["replay"] = replay_data;
        var keys = Object.keys(meal_changes);
        var meal_arr = keys.map(i => meal_changes[i][0]);
        if (meal_arr.length == 1 && typeof meal_arr[0] == 'undefined') {
            return_data['moM'] = [];
            return_data["moH"] = [];
        } else {
            return_data['moM'] = keys.map(i => [i, meal_changes[i][0].map(j => check_nan(j.y))]);
            return_data["moH"] = [];
        }

        // Send dates to the server and get response
        fetch('/dashboard/generate-report', {
                method: "POST",
                credentials: "include",
                body: JSON.stringify(return_data),
                cache: "no-cache",
                headers: new Headers({
                    "content-type": "application/json"
                })
            })
            .then(function(response) {
                if (response.status !== 200) {
                    console.log(`Looks like there was a problem. Status code: ${response.status}`);
                    popText("#warning", "<br> <p>There is a status error.</p");
                    return;
                }
                response.json().then(function(data) {
                    pdfEncode = data.pdf
                    var byteCharacters = atob(pdfEncode);
                    var byteNumbers = new Array(byteCharacters.length);
                    for (var i = 0; i < byteCharacters.length; i++) {
                        byteNumbers[i] = byteCharacters.charCodeAt(i);
                    }
                    var byteArray = new Uint8Array(byteNumbers);
                    var blob = new Blob([byteArray], {
                        type: 'application/pdf'
                    });
                    if (window.navigator && window.navigator.msSaveOrOpenBlob) {
                        window.navigator.msSaveOrOpenBlob(blob, "report.pdf"); // Edge
                        return;
                    } else {
                        var linkSource = `data:application/pdf;base64,${pdfEncode}`;
                        var downloadLink = document.createElement("a");
                        document.body.appendChild(downloadLink);
                        downloadLink.setAttribute("type", "hidden")
                        var fileName = "report.pdf";
                        downloadLink.href = linkSource;
                        downloadLink.download = fileName;
                        if (confirm("Do you want to download the report?")) {
                            downloadLink.click();
                            return;
                        } else {
                            if (confirm("Do you want to open the report?")) {
                                window.open(window.URL.createObjectURL(blob), '_blank');
                                return;
                            }
                        }
                    }
                });

            })
            .catch(function(error) {
                console.log("Fetch error: " + error);
            });
    });
}


/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Save Replay
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

// Reset Save Replay 
function resetSaveReplay() {
    replay_list['trackDropDown'] = [];
    replay_list['mealChanges'] = [];
    replay_list['insChanges'] = [];
    replay_list['replayResult'] = [];
    replay_list['apSel'] = [];
    replay_list["adjIns"] = [];
    replay_list["genIns"] = [];
    replay_list["adjHTs"] = [];
    replay_list["genHTs"] = [];
    updateText('#inputGroupReplay', replayDropDown(replay_list['adjIns']));
}

// Inititate Save Replay 
function initSaveReplay() {
    // Define Save Replay button
    saveReplay = $('#save-replay');

    // When clicks save replay
    saveReplay.click(function() {

        // Can't save more than three replays 
        if (replay_list["adjIns"].length == 3) {
            popText('#warning', "<br> <p>Sorry, you only can save up to 3 replay results.</p>")
        }

        // Saving Replay 
        else if (replay_list['adjIns'].length == 0) {
            if (replay_data["glucSeries"].length == 0) {
                popText('#warning', "<br> <p>Sorry, you need to run a simulation first.</p>")
            } else {
                replay_list['trackDropDown'].push(JSON.parse(JSON.stringify(track_change_arr)));
                replay_list['mealChanges'].push(JSON.parse(JSON.stringify(meal_changes)));
                replay_list['insChanges'].push(JSON.parse(JSON.stringify(insulin_profile_changes)));
                replay_list['replayResult'].push(JSON.parse(JSON.stringify(replay_data)));
                replay_list['apSel'].push(JSON.parse(JSON.stringify($('#apSel').val())));
                replay_list["adjIns"].push(JSON.parse(JSON.stringify(adjIns)));
                replay_list["genIns"].push(JSON.parse(JSON.stringify(genIns)));
                replay_list["adjHTs"].push(JSON.parse(JSON.stringify(adjHTs)));
                replay_list["genHTs"].push(JSON.parse(JSON.stringify(genHTs)));
                updateText('#inputGroupReplay', replayDropDown(replay_list['adjIns']));
                $('#inputGroupReplay').val(-1)
                $('#inputGroupReplay').change()
                popText('#success', "<br> <p>Your simulation results were successfully saved. This simulation has been appended to the replay drop-down list.</p>");
            }
        } else if (replay_list["adjIns"].length > 0) {
            //if (JSON.stringify(replay_data["glucSeries"]) === JSON.stringify(replay_list["replayResult"][replay_list["replayResult"].length - 1]["glucSeries"])) {
            if (replay_data["glucSeries"].length == 0) {
                popText('#warning', "<br> <p>You need to run a simulation first to save the replay.</p>");
            } else {
                replay_list['trackDropDown'].push(JSON.parse(JSON.stringify(track_change_arr)));
                replay_list['mealChanges'].push(JSON.parse(JSON.stringify(meal_changes)));
                replay_list['insChanges'].push(JSON.parse(JSON.stringify(insulin_profile_changes)));
                replay_list['replayResult'].push(JSON.parse(JSON.stringify(replay_data)));
                replay_list['apSel'].push(JSON.parse(JSON.stringify($('#apSel').val())));
                replay_list["adjIns"].push(JSON.parse(JSON.stringify(adjIns)));
                replay_list["genIns"].push(JSON.parse(JSON.stringify(genIns)));
                replay_list["adjHTs"].push(JSON.parse(JSON.stringify(adjHTs)));
                replay_list["genHTs"].push(JSON.parse(JSON.stringify(genHTs)));
                updateText('#inputGroupReplay', replayDropDown(replay_list['adjIns']));
                $('#inputGroupReplay').val(-1)
                $('#inputGroupReplay').change()
                popText('#success', "<br> <p>Your simulation results were successfully saved. Select the replay session drop down list to check your saved simulation sesssion.</p>");
            }
        }
    });

}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Select Replay Drop Down
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

// When select replay drop down, the selected value of the option will be passed as index to select the corresponding objects in the replay list, 
// and update display and replay panel based on the selected replay data.

function initSelectReplay() {

    // Define the replay drop down list 
    var selectReplay = $('#inputGroupReplay');

    // When an option is selected in the drop down list 
    selectReplay.change(function() {

        if ($('#inputGroupReplay option:selected').text()!='New Replay'){
            var index = parseInt($('#inputGroupReplay').val());

            defaultReplay(checkNoPlay(original_data.quality.nonplayable));

            // Update the variables based on the selected index in the drop down list. 
            replay_data = replay_list['replayResult'][index];
            track_change_arr = replay_list['trackDropDown'][index];
            passValues(meal_changes, replay_list['mealChanges'][index]);
            passValues(insulin_profile_changes, replay_list['insChanges'][index]);
            //meal_changes = JSON.parse(JSON.stringify(replay_list['mealChanges'][index]));
            //insulin_profile_changes = JSON.parse(JSON.stringify(replay_list['insChanges'][index]));
            //selectInsulin(lineReplay, replay_list['insChanges'][index], insulin_times);

            $('#apSel').val(replay_list['apSel'][index]);
            $('#apSel').change();
            adjIns = replay_list['adjIns'][index];
            genIns = replay_list['genIns'][index];
            adjHTs = replay_list['adjHTs'][index];
            genHTs = replay_list['genHTs'][index];

            document.getElementById("EntireDay").disabled = true;
            document.getElementById("ins-timepicker").disabled = true;
            document.getElementById("insSlider").disabled = true;
            document.getElementById("tempInsUpdate").disabled = true;
            document.getElementById("tempInsReset").disabled = true;
            document.getElementById("meal-timeslider").disabled = true;
            document.getElementById("mealSlider").disabled = true;
            document.getElementById("tempMealUpdate").disabled = true;
            document.getElementById("tempMealReset").disabled = true;
            document.getElementById("apSel").disabled = true;
            document.getElementById("adjIns").disabled = true;
            document.getElementById("genIns").disabled = true;
            document.getElementById("adjHTs").disabled = true;
            document.getElementById("genHTs").disabled = true;
            document.getElementById("submit-data").disabled = true;
            document.getElementById("save-replay").disabled = true;

        } 
        else {
            var index = parseInt($('#inputGroupReplay').val());

            track_change_arr = trackChanges(selected_date_array);
            no_data_dcrp = noDataDates(selected_date_array, original_data.quality.nonplayable);
            replay_data = {
                "bProfiles": [],
                "cfProfiles": [],
                "crProfiles": [],
                "glucSeries": [],
                "metrics": {
                    "cv": Array(original_data.metrics.cv.length).fill(0),
                    "hbgi": Array(original_data.metrics.hbgi.length).fill(0),
                    "lbgi": Array(original_data.metrics.lbgi.length).fill(0),
                    "percentR1": Array(original_data.metrics.percentR1.length).fill(0),
                    "percentR2": Array(original_data.metrics.percentR2.length).fill(0),
                    "percentR3": Array(original_data.metrics.percentR3.length).fill(0),
                    "percentR4": Array(original_data.metrics.percentR4.length).fill(0)
                },
                "moH": [],
                "moM": [],
                "nHT": Array(original_data.nHT.length).fill(0),
                "quality": { "nonplayable": [100], "playable": [0] },
                "tdb": Array(original_data.tdb.length).fill(0),
                "tdi": Array(original_data.tdi.length).fill(0)
            }
            var meal_array = createMealDict(original_data.moM, selected_date_array);
            //updated_data_meal = JSON.parse(JSON.stringify(meal_array));
            //meal_changes = updated_data_meal;
            selectMeal(mealReplay, meal_array)
            //insulin_profile_changes = passValues(insulin_profile_changes, insulin_profile);
            //insulin_profile_changes = insulin_profile;
            //updated_data_insulin = JSON.parse(JSON.stringify(insulin_profile));
            //insulin_profile_changes = updated_data_insulin;
            selectInsulin(lineReplay, insulin_profile, insulin_times);
            
            $('#apSel').val(original_data.apSystem);
            $('#apSel').change();
            adjIns = false;
            genIns = false;
            adjHTs = false;
            genHTs = false;

            document.getElementById("EntireDay").disabled = false;
            document.getElementById("ins-timepicker").disabled = false;
            document.getElementById("insSlider").disabled = false;
            document.getElementById("tempInsUpdate").disabled = false;
            document.getElementById("tempInsReset").disabled = false;
            document.getElementById("meal-timeslider").disabled = false;
            document.getElementById("mealSlider").disabled = false;
            document.getElementById("tempMealUpdate").disabled = false;
            document.getElementById("tempMealReset").disabled = false;
            document.getElementById("apSel").disabled = false;
            document.getElementById("adjIns").disabled = false;
            document.getElementById("genIns").disabled = false;
            document.getElementById("adjHTs").disabled = false;
            document.getElementById("genHTs").disabled = false;
            document.getElementById("submit-data").disabled = false;
            document.getElementById("save-replay").disabled = false;
        }

        $('#adjIns').prop('checked', adjIns);
        $('#genIns').prop('checked', genIns);
        $('#adjHTs').prop('checked', adjHTs);
        $('#genHTs').prop('checked', genHTs);

        // Update the date drop down list in the display panel
        // Update display panel 
        // Update more details 
        updateDropDown('#SelectDisplayDate', track_change_arr, no_data_dcrp);
        displayPanel(original_data, replay_data, [...selected_date_array.keys()], selected_date_array);
        moreDetails(original_data, replay_data, [...selected_date_array.keys()]);
        dateFilter(original_data, replay_data, selected_date_array);

        // Reset all the selectors, sliders and checkboxes in the insulin command.
        mealSliderHandler(100);
        timeSliderHandler(0);
        insSliderHandler(100);
        cb_trp(moment("0000", "hmm"), moment("0000", "hmm"));
        $('#ins-timepicker span').html('00:00 - 00:00');
        $('#EntireDay').prop('checked', false);
        $("#inputGroupInsType").val([]);
        $("#MealSelectDay").val([]);
        updateMealChart(mealReplay, [], [], [], []);
        updateInsChart(lineReplay, [], []);
        removePopulatedDropdown("#inputGroupInsProfile");
        removePopulatedDropdown("#MealSelect");

        // Pass by reference to renew values.
        function passValues(data, new_data) {
            var new_data_aux = new_data;
            for (var i in data) {
                data[i] = new_data_aux[i];
            }
            return data;
        }
    });

}