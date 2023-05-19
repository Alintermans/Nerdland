//------------------------------------------- Settings -------------------------------------------//
const max_left_threshold = 2;
const min_right_threshold = 3;

// SVG Settings
const width = 500;
const height = 300;
const margin = 20;


//------------------------------------------- Charts Helper Functions -------------------------------------------//

// Initialize the charts
var chart1 = createChart('chart1', 'Car 1', '#007bff');
var chart2 = createChart('chart2', 'Car 2', '#dc3545');
var chart3 = createChart('chart3', 'Car 3', '#ffc107');
var chart4 = createChart('chart4', 'Car 4', '#28a745');

// Connect to the EventSource and update the charts with new data
var source = new EventSource('/stream');
source.onmessage = function(event) {
    var data = JSON.parse(event.data);
    chart1.data.datasets[0].data = data.value_1;
    chart1.data.labels = [...Array(data.value_1.length).keys()];
    chart1.update();
    chart2.data.datasets[0].data = data.value_2;
    chart2.data.labels = [...Array(data.value_2.length).keys()];
    chart2.update();
    chart3.data.datasets[0].data = data.value_3;
    chart3.data.labels = [...Array(data.value_3.length).keys()];
    chart3.update();
    chart4.data.datasets[0].data = data.value_4;
    chart4.data.labels = [...Array(data.value_4.length).keys()];
    chart4.update();

    if (data.value_1.length > 0) {
        state = data.state_1
        if (state === 'RIGHT') {
            document.getElementById('subtitle_1').innerHTML = '<i class="fas fa-arrow-right"></i>';
        } else if (state === 'LEFT' ) {
            document.getElementById('subtitle_1').innerHTML = '<i class="fas fa-arrow-left"></i>';
        } else if (state === 'CENTER') {
            document.getElementById('subtitle_1').innerHTML = '<i class="fas fa-arrow-up"></i>';
        } else if (state === 'CALIBRATING') {
            document.getElementById('subtitle_1').innerHTML = 'CALIBRATING, Please keep your head straight!';
        }
    } else {
        document.getElementById('subtitle_1').innerHTML = 'Stopped';
    }

    if (data.value_2.length > 0) {
        state = data.state_2
        if (state === 'RIGHT') {
            document.getElementById('subtitle_2').innerHTML = '<i class="fas fa-arrow-right"></i>';
        } else if (state === 'LEFT' ) {
            document.getElementById('subtitle_2').innerHTML = '<i class="fas fa-arrow-left"></i>';
        } else if (state === 'CENTER') {
            document.getElementById('subtitle_2').innerHTML = '<i class="fas fa-arrow-up"></i>';
        } else if (state === 'CALIBRATING') {
            document.getElementById('subtitle_2').innerHTML = 'CALIBRATING, Please keep your head straight!';
        }
    } else {
        document.getElementById('subtitle_2').innerHTML = 'Stopped';
    }

    if (data.value_3.length > 0) {
        state = data.state_3
        if (state === 'RIGHT') {
            document.getElementById('subtitle_3').innerHTML = '<i class="fas fa-arrow-right"></i>';
        } else if (state === 'LEFT' ) {
            document.getElementById('subtitle_3').innerHTML = '<i class="fas fa-arrow-left"></i>';
        } else if (state === 'CENTER') {
            document.getElementById('subtitle_3').innerHTML = '<i class="fas fa-arrow-up"></i>';
        } else if (state === 'CALIBRATING') {
            document.getElementById('subtitle_3').innerHTML = 'CALIBRATING, Please keep your head straight!';
        }
    } else {
        document.getElementById('subtitle_3').innerHTML = 'Stopped';
    }

    if (data.value_4.length > 0) {
        state = data.state_4
        if (state === 'RIGHT') {
            document.getElementById('subtitle_4').innerHTML = '<i class="fas fa-arrow-right"></i>';
        } else if (state === 'LEFT' ) {
            document.getElementById('subtitle_4').innerHTML = '<i class="fas fa-arrow-left"></i>';
        } else if (state === 'CENTER') {
            document.getElementById('subtitle_4').innerHTML = '<i class="fas fa-arrow-up"></i>';
        } else if (state === 'CALIBRATING') {
            document.getElementById('subtitle_4').innerHTML = 'CALIBRATING, Please keep your head straight!';
        }
    } else {
        document.getElementById('subtitle_4').innerHTML = 'Stopped';
    }

    
};

// Helper function to create a new line chart
function createChart(canvasId, title, color) {
    var ctx = document.getElementById(canvasId);
    var chart = new Chart(ctx, {
        type: 'line',
        data: {
        labels: ['1', '2', '3', '4', '5', '6'],
        datasets: [{
            label: title,
            data: [0, 1, 5, 3, 2, 3],
            borderWidth: 1,
            borderColor: color,
            fill: false
        }]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        display: false //this will remove only the label
                    }
                },
                y: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        beginAtZero: true
                    },
                    min: 0,
                    max: 5
                }
            },
            layout: {
                padding: 20
            },
            elements: {
                point:{
                    radius: 0
                }
            },
            animation: {
            duration: 0
        }

        }
    });
    return chart;
}

//------------------------------------------- Buttons -------------------------------------------//

function reset_usb_button() {
    fetch('/reset_usb_button_pressed')
    .then(response => response.json())
    .then(data => console.log(data));}


function start_button(val) {
    fetch(`/start_button_pressed?value=${val}`)
    .then(response => response.json())
    .then(data => console.log(data));
}

function stop_button(val) {
    fetch(`/stop_button_pressed?value=${val}`)
    .then(response => response.json())
    .then(data => console.log(data));
}

function download_svg_button(val) {
    fetch(`/download_svg_pressed?value=${val}`)
    .then(response => response.json())
    .then(data => generate_and_download_svg_file(data.value));
}


function speed_slider(index, slider_val) {
    var id = "speed-text-" + (index + 1).toString();
    var new_text = "Speed: Normal"
    var value_to_send = 1.0


    
    if (slider_val == 0) {
        new_text = "Speed: Slow";
        value_to_send = 2.0;
    }  else if (slider_val == 1) {
        new_text = "Speed: Normal";
        value_to_send = 1.0;
    } else if (slider_val == 2) {
        new_text = "Speed: Fast";
        value_to_send = 0.6;
    } else if (slider_val == 3) {
        new_text = "Speed: Very Fast";
        value_to_send = 0.3;
    }

    

    var speed_text = document.getElementById(id);
    speed_text.innerHTML = new_text 

    fetch(`/update_gas_amount?value=${value_to_send}&index=${index}`)
    .then(response => response.json())
    .then(data => console.log(data));
}

//------------------------------------------- SVG Generator Helper Function -------------------------------------------//

function generate_and_download_svg_file(data) {
    if (data.length === 0) {
        alert('SVG not ready yet, wait a few seconds and try again');
        return;
    }
    

    const xScale = d3.scaleLinear()
        .domain([0, data.length - 1])
        .range([margin, width - margin]);

    const yScale = d3.scaleLinear()
        .domain([0, d3.max(data)])
        .range([height - margin, margin]);

    const line = d3.line()
        .x((d, i) => xScale(i))
        .y(d => yScale(d))
        .curve(d3.curveMonotoneX);

    const svg = d3.create("svg")
        .attr("viewBox", `0 0 ${width} ${height}`);

    svg.append("path")
        .datum(data)
        .attr("fill", "none")
        .attr("stroke", "steelblue")
        .attr("stroke-width", 1.5)
        .attr("d", line);
    
        const svgString = new XMLSerializer().serializeToString(svg.node());
        const blob = new Blob([svgString], {type: "image/svg+xml"});
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.download = "graph.svg";
        link.href = url;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
}

//------------------------------------------- Error Box  -------------------------------------------//

var error_box_visible = false;

function showErrorMessage(msg) {
    error_box_visible = true;
    var errorContainer = document.getElementById("error-container");
    errorContainer.innerHTML = "<div class='error-box'>" + msg + " <button class='button button-usb-in-errorbox' onclick='reset_usb_button()'><i class='fas fa-undo'></i> Reset USB</button></div>";
}

function hideErrorMessage() {
    error_box_visible = false;
    var errorContainer = document.getElementById("error-container");
    errorContainer.innerHTML = "";
}

var error_source = new EventSource('/error_stream');
error_source.onmessage = function(event) {
    var data = JSON.parse(event.data);
    if (data.message != "") {
        showErrorMessage(data.message);
    } else if (error_box_visible) {
        hideErrorMessage();
    }
};