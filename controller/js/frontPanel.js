/*eslint no-unused-vars: ["error", { "varsIgnorePattern": "Button" }]*/

/* ############################################################################
############################## Command funtions ###############################
############################################################################ */

// Global variable needed by the JS but not the HTML
var cmd = "";
var sampleNameDate = "";


// Fetch the status string from sendCommand.php
// Send a command to the Arduino or the TILDAS via sendCommand.php
function sendCommand(cmd) {
    $.ajax({
        type: "POST",
        url: "controller/php/sendCommand.php",
        data: { cmd: cmd },
        async: false,
        success: function (response) {
            // Split the status string
            const statusArr = response.split(","); // The status array is received from serialComm.py via sendCommand.php

            $("#moveStatus").html(statusArr[1]);

            // Display some images based on moveStatus
            // if (
            //     statusArr[1] == "IA" &&
            //     $("#loadingGIF").attr("src") != "controller/images/loading.gif"
            // ) {
            //     $("#loadingGIF").attr("src", "controller/images/loading.gif");
            // } else if (statusArr[1] != "IA") {
            //     $("#loadingGIF").attr("src", "");
            // }

            if (
                statusArr[1] == "MX" &&
                $("#motorX").attr("src") == "controller/images/standing_motor.gif"
            ) {
                $("#motorX").attr("src", "controller/images/rotating_motor.gif");
            } else if (
                statusArr[1] == "MY" &&
                $("#motorY").attr("src") == "controller/images/standing_motor.gif"
            ) {
                $("#motorY").attr("src", "controller/images/rotating_motor.gif");
            } else if (
                statusArr[1] == "MZ" &&
                $("#motorZ").attr("src") == "controller/images/standing_motor.gif"
            ) {
                $("#motorZ").attr("src", "controller/images/rotating_motor.gif");
            } else if (
                statusArr[1] == "-" &&
                ($("#motorX").attr("src") == "controller/images/rotating_motor.gif" ||
                    $("#motorY").attr("src") == "controller/images/rotating_motor.gif" ||
                    $("#motorZ").attr("src") == "controller/images/rotating_motor.gif")
            ) {
                $("#motorX").attr("src", "controller/images/standing_motor.gif");
                $("#motorY").attr("src", "controller/images/standing_motor.gif");
                $("#motorZ").attr("src", "controller/images/standing_motor.gif");
            }

            // X bellows
            $("#percentageX").html(parseFloat(statusArr[2]).toFixed(2)); // bellow expansion based on motor steps
            $("#percentageX_Poti").html(parseFloat(statusArr[3]).toFixed(1)); // bellow expansion based on potentiometer
            $("#bellowsX").css(
                "height",
                parseInt(10 + 0.9 * statusArr[2]) + "px"
            );

            // Y bellows
            $("#percentageY").html(parseFloat(statusArr[4]).toFixed(2)); // bellow expansion based on motor steps
            $("#percentageY_Poti").html(parseFloat(statusArr[5]).toFixed(1)); // bellow expansion based on potentiometer
            $("#bellowsY").css(
                "height",
                parseInt(10 + 0.9 * statusArr[4]) + "px");

            // Z bellows
            $("#stepsZ").html(parseInt(statusArr[6]));
            $("#percentageZ").html(parseFloat(statusArr[7]).toFixed(1));
            $("#bellowsZ").css(
                "height",
                parseInt(10 + 0.9 * statusArr[7]) + "px"
            );

            if (
                statusArr[6] != 7980 &&
                $("#warningZ").attr("src") != "controller/images/warning.png"
            ) {
                $("#warningZ").attr("src", "controller/images/warning.png");
            } else if (statusArr[6] == 7980) {
                $("#warningZ").attr("src", "");
            }

            // X baratron in Torr (max. 5 Torr)
            var pressureX = parseFloat(statusArr[8]);
            $("#pressureX").html(pressureX.toFixed(3));

            // Y baratron in Torr (max. 5 Torr)
            var pressureY = parseFloat(statusArr[9]);
            $("#pressureY").html(pressureY.toFixed(3));

            // A baratron in Torr (max. 500 Torr)
            var pressureZ = parseFloat(statusArr[10]);
            $("#pressureZ").html(pressureZ.toFixed(1));

            // Valve status
            var valveArray = statusArr[11];
            const positions = [
                "vertical", // V01
                "vertical", // V02
                "horizontal", // V03
                "horizontal", // V04
                "vertical", // V05
                "horizontal", // V06
                "vertical", // V07
                "vertical", // V08
                "horizontal", // V09
                "horizontal", // V10
                "vertical", // V11
                "horizontal", // V12
                "vertical", // V13
                "vertical", // V14
                "horizontal", // V15
                "vertical", // V16
                "horizontal", // V17
                "horizontal", // V18
                "horizontal", // V19
                "horizontal", // V20
                "horizontal", // V21
                "horizontal", // V22
                "vertical", // V23
                "vertical", // V24
                "vertical", // V25
                "vertical", // V26
                "horizontal", // V27
                "vertical", // V28
                "horizontal", // V29
                "horizontal", // V30
                "horizontal", // V31
                "horizontal", // V32
            ];
            var i = 1;
            var n = "0";
            while (i <= 33) {
                if (i < 10) {
                    n = "0";
                } else {
                    n = "";
                }
                $("#V" + n + i.toString() + "_label").html(
                    valveArray.charAt(i - 1)
                );
                if (valveArray.charAt(i - 1) == "0") {
                    $("#V" + n + i.toString()).attr(
                        "src",
                        "controller/images/" + positions[i - 1] + "_closed.png"
                    );
                } else {
                    $("#V" + n + i.toString()).attr(
                        "src",
                        "controller/images/" + positions[i - 1] + "_open.png"
                    );
                }
                i = i + 1;
            }


            // Relay status
            var relayArray = statusArr[12];
            var i = 1;
            while (i <= 2) {
                $("#U" + "0" +  i.toString() + "_label").html(relayArray[i - 1]);
                if (relayArray[i - 1] == 0) {
                    $("#U" + "0" + i.toString()).attr("src", "controller/images/relay_off.png");
                } else {
                    $("#U" + "0" + i.toString()).attr("src", "controller/images/relay_on.png");
                }
                i = i + 1;
            }

            // Box humidity
            var boxHumidity = statusArr[13];
            $("#boxHumidity").html(boxHumidity);

            // Box temperature
            var boxTemperature = statusArr[14];
            $("#boxTemperature").html(boxTemperature);

            // Box setpoint temperature
            var SPT = parseFloat(statusArr[15]);
            $("#boxSetpoint").html(SPT.toFixed(1));

            // Fan speed
            var fanSpeed = statusArr[16];
            $("#fanSpeed").html(fanSpeed);

            // Cell pressure from the TILDAS in Torr
            var cellPressure = parseFloat(statusArr[17]);
            $("#cellPressure").html(cellPressure.toFixed(3));

            // CO2 mixing ratios from the TILDAS
            var mr1 = statusArr[18];
            $("#mr1").html(parseFloat(mr1).toFixed(3));
            var mr2 = statusArr[19];
            $("#mr2").html(parseFloat(mr2).toFixed(3));
            var mr3 = statusArr[20];
            $("#mr3").html(parseFloat(mr3).toFixed(3));
            var mr4 = statusArr[21];
            $("#mr4").html(parseFloat(mr4).toFixed(3));

            // vacuum vacuum gauge
            var vacuum = statusArr[22];
            $("#vacuum").html(parseFloat(vacuum).toFixed(5));

            // Reset the command string
            cmd = "";
        },
        error: function (xhr, status, error) {
            console.error(error);
        },
    });
}


// Switch valves
function toggleValve(valve, status) {
    if (status == "0") {
        cmd = valve + "O";
        console.log(
            `${new Date().toLocaleTimeString()}, ` +
            "Valve " +
            valve.slice(-2) +
            " opened"
        );
    } else if (status == "1") {
        cmd = valve + "C";
        console.log(
            `${new Date().toLocaleTimeString()}, ` +
            "Valve " +
            valve.slice(-2) +
            " closed"
        );
    } else {
        cmd = "";
        alert(
            "Invalid command, could not determine the current status of the valve."
        );
    }
    // console.log("Sent: " + cmd);
}

// Switch relay
function toggleRelay(relay, status) {
    if (status == "0") {
        cmd = relay + "O";
        console.log(
            `${new Date().toLocaleTimeString()}, ` +
            "Relay " +
            relay.slice(-2) +
            " opened"
        );
    } else if (status == "1") {
        cmd = relay + "C";
        console.log(
            `${new Date().toLocaleTimeString()}, ` +
            "Relay " +
            relay.slice(-2) +
            " closed"
        );
    } else {
        cmd = "";
        alert(
            "Invalid command, could not determine the current status of the relay."
        );
    }
}

// Start recording data on TILDAS
function startWritingData() {
    cmd = 'TWD1';
    console.log(`${new Date().toLocaleTimeString()}, Starting data recording on TILDAS`);}

// Stop recording data on TILDAS
function stopWritingData() {
    cmd = 'TWD0';
    console.log(`${new Date().toLocaleTimeString()}, Stopping data recording on TILDAS`);
}

// Suspend background fitting on TILDAS
function suspendFit() {
    cmd = 'BG0';
    console.log(`${new Date().toLocaleTimeString()}, Background fitting suspended on TILDAS`);
}

// Suspend background fitting on TILDAS
function enableFit() {
    cmd = 'BG1';
    console.log(`${new Date().toLocaleTimeString()}, Background fitting enabled on TILDAS`);
}

// Set valves to starting position
function startingPosition() {
    cmd = 'KL';
    console.log(`${new Date().toLocaleTimeString()}, Resetting valves to starting position`);
}

// Move bellows
function moveBellows(bellow) {
    $('#moveStatus').html('M' + bellow);
    var percentage = parseFloat($('#setPercentage' + bellow).val()).toFixed(1);
    if (percentage < 0) {
        percentage = 0.0;
        $('#setPercentage' + bellow).val("0.0");
    }
    if (percentage > 100) {
        percentage = 100.0;
        $('#setPercentage' + bellow).val("100.0");
    }
    cmd = bellow + 'P' + percentage;
    console.log(
        `${new Date().toLocaleTimeString()}, ` +
        "Moving bellow " +
        bellow +
        " to " +
        percentage +
        "%"
    );
}


/* ############################################################################
############################## Backend funtions ###############################
############################################################################ */

// Global variables needed by the JS but not the HTML
var commandsArray = [];
var parameterArray = [];
var timeArray = [];
var colArr = [];

// Load next method in sequence
function loadMethod(methodFileName) {
    $.ajax({
        url: "controller/php/uploadMethod.php",
        data: { methodFileName: methodFileName },
        type: "POST",
        success: function (result) {
            console.log(`${new Date().toLocaleTimeString()}, `+ "Method loaded successfully");

            $("#method").empty();
            colArr = result.split("|");
            commandsArray = [];
            commandsArray = colArr[0].split(","); // This is a 1D array here
            parameterArray = colArr[1].split(",");
            timeArray = colArr[2].split(",");

            // Create list with commands on frontpanel
            var vertical = 0;
            for (let i = 0; i < commandsArray.length; i++) {
                $("#method").append(
                    "<div id='command" +
                        i +
                        "' class='command' style='background-color: white;position:relative;top:" +
                        (vertical + i * 1) +
                        "px;left:0px;'>" +
                        i +
                        ":" +
                        commandsArray[i] +
                        " &rarr; " +
                        parameterArray[i] +
                        " &rarr; wait " +
                        timeArray[i] +
                        " s</div>"
                );
            }
            vertical = vertical + 0;
        },
    });
}

// Upload method by user
$("body").on("change", "#uploadMethod", function () {
    var data = new FormData();
    data.append("file", this.files[0]);
    $.ajax({
        url: "controller/php/uploadMethod.php",
        data: data,
        type: "POST",
        processData: false,
        contentType: false,
        success: function () {
            console.log(`${new Date().toLocaleTimeString()}, `+ "Method uploaded successfully");
        },
    });
});

// Upload sequence by user
$("body").on("change", "#uploadSequence", function () {
    var data = new FormData();
    data.append("file", this.files[0]);
    $.ajax({
        url: "controller/php/uploadSequence.php",
        data: data,
        type: "POST",
        processData: false,
        contentType: false,
        success: function (result) {

            console.log(`${new Date().toLocaleTimeString()}, `+ "Sequence uploaded sucessfully");

            // Delete all elements in div sequence
            $("#sequence").empty();
            var colSeqArr = result.split("|");
            let sampleNameArr = colSeqArr[0].split(",");
            let methodFileArr = colSeqArr[1].split(",");

            // Create list with commands on frontpanel
            var vertical = 0;
            for (let i = 0; i < sampleNameArr.length; i++) {
                if (i == 0) {
                    // Loading the method of the first sample
                    loadMethod(methodFileArr[i]);
                    $("#sampleName").html(sampleNameArr[i]);
                }
                $("#sequence").append(
                    "<div id='sample" +
                        i +
                        "' class='command' style='background-color: white;position:relative;top:" +
                        (vertical + i * 1) +
                        "px;left:0px;'>" +
                        i +
                        "," +
                        sampleNameArr[i] +
                        "," +
                        methodFileArr[i] +
                        "</div>"
                );
            }
            vertical = vertical + 0;
        },
    });
});

// Create a folder for the data
function createFolder() {
    console.log(`${new Date().toLocaleTimeString()}, ` + "Calling createFolder.php");
    $.ajax({
        type: "POST",
        url: "controller/php/createFolder.php",
        async: false,
        data: {
            date: $("#timeMeasurementStarted").html(), // Date and time when measurement started in UNIX format & UTC timezone
            sampleName: $("#sampleName").html(),
        },
        success: function (response) {
            console.log(`${new Date().toLocaleTimeString()}, Folder created: ${response}`);
            $("#folderName").html(response);
            sampleNameDate = response.split("/").pop();
            console.log("Sample name used for the evaluation: " + sampleNameDate);
        },
    });
}

// Write logfile.csv
function writeLogfile(logDataJSON, logFileName) {
    $.ajax({
        type: "POST",
        url: "controller/php/writeLogfile.php",
        data: {
            logDataJSON: encodeURIComponent(logDataJSON),
            logFileName: logFileName,
        },
        success: function (response) {
            if (response != "") {
                // console.log(`${new Date().toLocaleTimeString()}, ` + response);
            }
        },
    });
}

// Copy all files with a date younger than timeMeasurementStarted
function copyFiles(timeMeasurementStarted, folderName) {
    console.log(`${new Date().toLocaleTimeString()}, ` + "Calling copyFiles.php for " + folderName);
    $.ajax({
        type: "POST",
        url: "controller/php/copyFiles.php",
        async: false,
        data: {
            timeMeasurementStarted: timeMeasurementStarted, // In UNIX format & UTC timezone
            folderName: encodeURIComponent(folderName), // Where the sample data is saved
        },
        success: function (response) {
            console.log(`${new Date().toLocaleTimeString()}, ` + response);
        },
    });
}

// Evaluate data after the measurement is finished
function evaluateData(sampleNameDate, userName) {
    console.log(`${new Date().toLocaleTimeString()}, ` + "Calling evaluateData.php for " + sampleNameDate);
    $.ajax({
        type: "POST",
        url: "controller/php/evaluateData.php",
        async: true,
        data: {
            sampleName: encodeURIComponent(sampleNameDate), // something like 240323_092903_DH11
            userName: encodeURIComponent(userName),
        },
    }).done(function (result) {
        console.log(`${new Date().toLocaleTimeString()}, ` + result);
    });
}

// Show results button
function showResultsButton() {
    window.open(
        "http://10.132.1.101/viewer",
        "_blank"
    );
}

// Start sequence button
function startSequenceButton() {
    const timeMeasurementStarted = parseInt(new Date().getTime() / 1000);
    $("#timeMeasurementStarted").html(timeMeasurementStarted);
    createFolder();
    $("#methodStatus").html("Method running");
    $("#sample0").prepend("&#9758; ");
    let timeButtonPressed = new Date(new Date().getTime()).toLocaleTimeString();
    console.log(timeButtonPressed + ", Sequence started");
}

// Do this before every command in method
function doThisBeforeEveryCommand() {
    if ($("#command" + (line + 2)).length) {
        $("#command" + (line + 2))[0].scrollIntoView({
            behavior: "smooth",
            block: "nearest",
            inline: "start",
        });
    }
    $("#command" + line).prepend("&#9758; ");
}

// Do this after every command in method
function doThisAfterEveryCommand(condition) {
    if (condition == "started") {

        // This is when the command is started but not yet finished
        $("#progressBar").css("width", "0px");
        $("#progress").html("0%");
        timeExecuted = new Date().getTime() / 1000;
        timeExecutedStr = new Date(timeExecuted * 1000).toLocaleTimeString();
        moving = "yes";
        executed = "no";
        waiting = "no";
        console.log(
            timeExecutedStr +
            ", Command in line " +
            line +
            " '" +
            commandsArray[line] +
            " " +
            parameterArray[line] +
            "' started"
        );

    } else if (condition == "executed") {

        // This is when the command is executed straight away
        timeExecuted = new Date().getTime() / 1000;
        timeExecutedStr = new Date(timeExecuted * 1000).toLocaleTimeString();
        moving = "no";
        executed = "yes";
        waiting = "yes";
        $("#command" + line).append(" &#10003;");
        console.log(
            timeExecutedStr +
            ", " +
            "Command in line " +
            line +
            " '" +
            commandsArray[line] +
            " " +
            parameterArray[line] +
            "' executed. " +
            "Wait for " +
            timeArray[line] +
            " s."
        );
    }
}

/* ############################################################################
########################## The awesome station clock ##########################
############################################################################ */

function pad(num, size)
{
    num = num.toString();
    while (num.length < size) num = "0" + num;
    return num;
}

function timeIsPassing()
{
    // Get current date and time
    const date = new Date;
    const seconds = date.getSeconds();
    const minutes = date.getMinutes();
    const hour = date.getHours();

    // Calcualte the angles of clock hands
    const minutesAngle = (minutes / 60 * 2 * Math.PI) - 0.5 * Math.PI;
    const secondsAngle = (seconds / 60 * 2 * Math.PI) - 0.5 * Math.PI;
    const hourAngle = ( hour / 12 * 2 * Math.PI + 1/12 * minutes / 60 * 2 * Math.PI ) - 0.5 * Math.PI;

    // Write digital time
    $("#digital").html(`${pad(hour, 2)}:${pad(minutes, 2)}:${pad(seconds, 2)}<br> Göttingen Hbf`);

    // Write on canvas
    const canvas = document.getElementById("Bahnhofsuhr");
    const ctx = canvas.getContext("2d");

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.lineCap = "round";
    ctx.strokeStyle = "#0A1E6E";

    // Draw circle
    ctx.beginPath();
    ctx.lineWidth = 2.8;
    ctx.arc(50, 50, 48, 0, 2 * Math.PI);
    ctx.stroke();

    // Draw minute tickmarks
    ctx.beginPath();
    for (let i = 0; i < 60; i++)
    { 
        const ticksAngle = i * 2 * Math.PI / 60;
        ctx.moveTo( 50 + 43 * Math.cos( ticksAngle ), 50 + 43 * Math.sin( ticksAngle ) );
        ctx.lineTo( 50 + 48 * Math.cos( ticksAngle ), 50 + 48 * Math.sin( ticksAngle ) );
    }
    ctx.lineWidth = 2.2;
    ctx.stroke();

    // Draw hour tickmarks
    ctx.beginPath();
    for (let i = 0; i < 12; i++)
    { 
        const ticksAngle = i * 2 * Math.PI / 12;
        ctx.moveTo( 50 + 38 * Math.cos( ticksAngle ), 50 + 38 * Math.sin( ticksAngle ) );
        ctx.lineTo( 50 + 48 * Math.cos( ticksAngle ), 50 + 48 * Math.sin( ticksAngle ) );
    }
    ctx.lineWidth = 3;
    ctx.stroke();

    // Draw hours hand
    ctx.beginPath();
    ctx.moveTo(50, 50);
    ctx.lineTo( 50 + 31 * Math.cos( hourAngle ), 50 + 31 * Math.sin( hourAngle ) );
    ctx.lineWidth = 6;
    ctx.stroke();

    // Draw minutes hand
    ctx.beginPath();
    ctx.moveTo(50, 50);
    ctx.lineTo( 50 + 42 * Math.cos( minutesAngle ), 50 + 42 * Math.sin( minutesAngle ) );
    ctx.lineWidth = 5;
    ctx.stroke();

    // Draw seconds hand
    ctx.beginPath();
    ctx.moveTo(50, 50);
    ctx.strokeStyle = "#EC0016";
    ctx.lineTo( 50 + 23 * Math.cos( secondsAngle ), 50 + 23 * Math.sin( secondsAngle ) );
    ctx.lineWidth = 2;
    ctx.stroke();
    
    ctx.moveTo(50 + 33 * Math.cos( secondsAngle ), 50 + 33 * Math.sin( secondsAngle ));
    ctx.lineTo( 50 + 42 * Math.cos( secondsAngle ), 50 + 42 * Math.sin( secondsAngle ) );
    ctx.lineWidth = 2;
    ctx.stroke();
    
    ctx.beginPath();
    ctx.arc(50 + 42 / 1.5 * Math.cos( secondsAngle ), 50 + 42 / 1.5 * Math.sin( secondsAngle ), 5, 0, 2 * Math.PI);
    ctx.fillStyle = "#f0ecec00";
    ctx.fill();
    ctx.stroke();

    // Draw a blue circle in the middle
    ctx.beginPath();
    ctx.strokeStyle = "#0A1E6E";
    ctx.fillStyle = "#0A1E6E";
    ctx.moveTo(50, 50);
    ctx.arc(50, 50, 4, 0, 2 * Math.PI);
    ctx.fill();
    ctx.stroke();
}


/* ############################################################################
######################## This is the main program loop ########################
############################################################################ */

var timeExecuted = 0; // Time when cmd was executed in seconds since epoch
var timeExecutedStr = 0; // Time when cmd was executed in human-readable format
var line = 0;
var moving = "no";
var waiting = "no"; // Wait for the delay to goto next command
var executed = "yes";
let cycleJS = 0;
let startTimeJS = new Date().getTime();
let speedJS = 0;
var lastTimeUpdated = 0;
var logData = [];
var sample = 0;
var cycle = 0;

setInterval(function () {
    sendCommand(cmd);
    cmd = "";
    timeIsPassing(); // Sets the clock

    // Execute the individual commands from the method
    if ($("#methodStatus").text() == "Method running") {
        var currentTime = parseInt(new Date().getTime() / 1000);

        // Save data to logfile array every 5 seconds
        if (currentTime % 5 == 0 &&
            currentTime != lastTimeUpdated &&
            $("#sampleName").html() != "" &&
            !$("#sampleName").html().includes("refill")) {
            // Unix -> Mac timestamp, TILDAS uses Mac timestamp
            let logObject = {
                "Time(abs)": parseInt(new Date().getTime() / 1000 + 2082844800 + 3600),
                "SampleName": $("#sampleName").html(),
                "boxTemperature": parseFloat($("#boxTemperature").html()),
                "boxSetpoint": parseFloat($("#boxSetpoint").html()),
                "boxHumidity": parseFloat($("#boxHumidity").html()),
                "percentageX": $("#percentageX").html(),
                "percentageY": $("#percentageY").html(),
                "percentageZ": $("#percentageZ").html(),
                "pressureX": $("#pressureX").html(),
                "pressureY": $("#pressureY").html(),
                "pressureZ": $("#pressureZ").html(),
                "vacuum": $("#vacuum").html().trim(),
                "fanSpeed": parseFloat($("#fanSpeed").html())
            };

            // Convert logObject to JSON string
            let logDataJSON = JSON.stringify(logObject);
            let logFileName = "../../" + $('#folderName').html() + "/logFile.csv";
            writeLogfile(logDataJSON, logFileName);
            var lastTimeUpdated = parseInt(new Date().getTime() / 1000);
        }

        // vvv The command "if" series starts here vvv

        // Open or close valves
        if (commandsArray[line][0] == "V" && executed == "yes" && moving == "no" && waiting == "no") {
            doThisBeforeEveryCommand();

            if (parameterArray[line] == 0) {
                toggleValve(commandsArray[line], "1");
            } else if (parameterArray[line] == 1) {
                toggleValve(commandsArray[line], "0");
            }

            doThisAfterEveryCommand("executed");
        }

        // Open or close relay
        if (commandsArray[line][0] == "U" && executed == "yes" && moving == "no" && waiting == "no") {
            doThisBeforeEveryCommand();

            if (parameterArray[line] == 0) {
                toggleRelay(commandsArray[line], "1");
            } else if (parameterArray[line] == 1) {
                toggleRelay(commandsArray[line], "0");
            }

            doThisAfterEveryCommand("executed");
        }

        // This command opens V15, waits until A target pressure is reached, than closes V15
        else if (commandsArray[line][0] == "I" && commandsArray[line][1] == "A" && executed == "yes" && moving == "no" && waiting == "no") {
            doThisBeforeEveryCommand();

            cmd = "IA" + parameterArray[line];

            doThisAfterEveryCommand("started");
        }

        // Reset valves to starting position
        else if (commandsArray[line][0] == "K" && commandsArray[line][1] == "L" && executed == "yes" && moving == "no" && waiting == "no") {
            doThisBeforeEveryCommand();

            startingPosition();

            doThisAfterEveryCommand("started");
        }

        // Write cell pressure for the first sample on the front panel: WC,0,10 !Parameter is ignored
        else if (commandsArray[line][0] == "W" && commandsArray[line][1] == "C" && executed == "yes" && moving == "no" && waiting == "no") {
            doThisBeforeEveryCommand();

            $("#cellTargetPressure").html($("#cellPressure").html());
            console.log(
                `${new Date().toLocaleTimeString()}, ` +
                "Cell target pressure: " +
                $("#cellTargetPressure").html()
            );

            doThisAfterEveryCommand("executed");
        }

        // Write nitrogen pressure for the first sample on the frontpanel "WA <no parameter>"
        else if (commandsArray[line][0] == "W" && commandsArray[line][1] == "A" && executed == "yes" && moving == "no" && waiting == "no") {
            doThisBeforeEveryCommand();

            $("#nitrogenTargetPressure").html((parseFloat($("#pressureZ").html())).toFixed(1));

            doThisAfterEveryCommand("executed");
        }

        // Write reference gas target pressure for the first sample on the frontpanel "WR <no parameter>"
        else if (commandsArray[line][0] == "W" && commandsArray[line][1] == "R" && executed == "yes" && moving == "no" && waiting == "no") {
            doThisBeforeEveryCommand();

            // Keep the target pressure (ref) for all samples in sequence
            if ($("#refgasTargetPressure").html() == "Reference target pressure") {
                $("#refgasTargetPressure").html("1.700");
            }
            else {
                $("#refgasTargetPressure").html((parseFloat($("#refgasTargetPressure").html())).toFixed(3));
            }

            doThisAfterEveryCommand("executed");
        }


        // Write sample gas target pressure for the first sample on the frontpanel "WS <no parameter>"
        else if (commandsArray[line][0] == "W" && commandsArray[line][1] == "S" && executed == "yes" && moving == "no" && waiting == "no") {
            doThisBeforeEveryCommand();

            // Keep the target pressure (sam) for all samples in sequence
            if ($("#samgasTargetPressure").html() == "Sample target pressure") {
                $("#samgasTargetPressure").html("1.700");
            }
            else {
                $("#samgasTargetPressure").html((parseFloat($("#samgasTargetPressure").html())).toFixed(3));
            }

            doThisAfterEveryCommand("executed");
        }

        // Write gas mixing ratio to the frontpanel "CM, 0=Reference 1=Sample"
        else if (commandsArray[line][0] == "C" && commandsArray[line][1] == "M" && executed == "yes" && moving == "no" && waiting == "no") {
            doThisBeforeEveryCommand();

            if (parameterArray[line] == 0) {
                $("#reference_pCO2").html($("#mr3").html());
                console.log(
                    `${new Date().toLocaleTimeString()}, ` +
                    "Reference pCO2 is: " +
                    $("#reference_pCO2").html()
                );

                if ($("#sample_pCO2").html() != "Sample pCO<sub>2</sub>") {
                    // Adjust the correction factor
                    $("#correction_pCO2").html(($("#sample_pCO2").html() / $("#reference_pCO2").html() * $("#correction_pCO2").html()).toFixed(3));
                    console.log(
                        `${new Date().toLocaleTimeString()}, `+
                        "Correction factor is: " +
                        $("#correction_pCO2").html()
                    );
                }
            }
            else if (parameterArray[line] == 1) {
                $("#sample_pCO2").html($("#mr3").html());
                console.log(
                    `${new Date().toLocaleTimeString()}, ` +
                    "Sample pCO2 is: " +
                    $("#sample_pCO2").html()
                );

                if ($("#reference_pCO2").html() != "Reference pCO<sub>2</sub>") {
                    // Adjust the correction factor
                    $("#correction_pCO2").html(($("#sample_pCO2").html() / $("#reference_pCO2").html() * $("#correction_pCO2").html()).toFixed(3));
                    console.log(
                        `${new Date().toLocaleTimeString()}, ` +
                        "Correction factor is: " +
                        $("#correction_pCO2").html()
                    );
                }
            }

            doThisAfterEveryCommand("executed");
        }

        // Execute command at laser spectrometer: Start writing data to disk "TWD 0"
        else if (commandsArray[line][0] == "T" && commandsArray[line][1] == "W" && commandsArray[line][2] == "D" && executed == "yes" && moving == "no" && waiting == "no") {
            doThisBeforeEveryCommand();

            // Execute command at laser spectrometer: Stop writing data to disk
            if (parameterArray[line] == 0) {
                stopWritingData();
            } else if (parameterArray[line] == 1) {
                startWritingData();
                $("#cycle").html(cycle);

                console.log(
                    `${new Date().toLocaleTimeString()}, ` +
                    "This is cycle #" +
                    cycle
                );

                cycle++;
            }

            doThisAfterEveryCommand("executed");
        }


        // Suspend or enable background fitting on TILDAS
        else if (commandsArray[line][0] == "B" && commandsArray[line][1] == "G" && executed == "yes" && moving == "no" && waiting == "no") {
            doThisBeforeEveryCommand();

            // Execute command at laser spectrometer: Stop writing data to disk
            if (parameterArray[line] == 0) {
                suspendFit();
            } else if (parameterArray[line] == 1) {
                enableFit();
            }

            doThisAfterEveryCommand("executed");
        }

        // Move bellows (X,Y,Z) "BY 53" with the percentage as parameter BX
        else if (commandsArray[line][0] == "B" && moving == "no" && executed == "yes" && waiting == "no") {
            doThisBeforeEveryCommand();

            if (parameterArray[line].substr(0, 1) == "+" || parameterArray[line].substr(0, 1) == "-") {
                // Move increment
                // Get current bellows position
                let currentPercent = parseFloat($("#percentage" + commandsArray[line][1]).text());

                console.log(
                    `${new Date().toLocaleTimeString()}, ` +
                    "Current bellows position is " +
                    currentPercent +
                    "%"
                );

                // Calculate the new bellows position
                let newPercent = currentPercent + parseFloat(parameterArray[line]);

                console.log(
                    `${new Date().toLocaleTimeString()}, ` +
                    "New bellows position is " +
                    newPercent +
                    "%"
                );

                $("#setPercentage" + commandsArray[line][1]).val(newPercent.toFixed(1));
            }
            else {
                // Move absolute
                $("#setPercentage" + commandsArray[line][1]).val(parameterArray[line]);
            }

            moveBellows(commandsArray[line][1]);

            doThisAfterEveryCommand("started");
        }

        // Set bellows to pressure target (X,Y) "PX 1.723"
        else if (commandsArray[line][0] == "P" && executed == "yes" && moving == "no" && waiting == "no") {
            doThisBeforeEveryCommand();

            let pTarget;
            if (commandsArray[line][1] == "X") {
                console.log(`${new Date().toLocaleTimeString()}, `+ "Adjusting bellow X to target pressure");
                if ($("#refgasTargetPressure").html() == "Reference target pressure") {
                    console.log(`${new Date().toLocaleTimeString()}, `+ "Target pressure recieved from parameter");
                    pTarget = parseFloat(parameterArray[line]);
                }
                else {
                    console.log(`${new Date().toLocaleTimeString()}, `+ "Target pressure recived from front panel");
                    pTarget = parseFloat($("#refgasTargetPressure").html());
                }
            }
            else if (commandsArray[line][1] == "Y") {
                console.log(`${new Date().toLocaleTimeString()}, ` + "Adjusting bellow Y to target pressure");
                if ($("#samgasTargetPressure").html() == "Sample target pressure") {
                    console.log(`${new Date().toLocaleTimeString()}, `+ "Target pressure recieved from parameter");
                    pTarget = parseFloat(parameterArray[line]);
                }
                else {
                    console.log(`${new Date().toLocaleTimeString()}, `+ "Target pressure recived from front panel");
                    pTarget = parseFloat($("#samgasTargetPressure").html());
                }
            }
            console.log(
                `${new Date().toLocaleTimeString()}, ` +
                "Target pressure is " +
                pTarget.toFixed(3) +
                " Torr"
            );

            // Here we correct pTarget by the correction_pCO2 factor
            // The corrrection factor is 1.000 by default, and can be adjusted by the CM command
            let factor = parseFloat($("#correction_pCO2").html());
            if (factor != 1.000) {

                console.log(
                    `${new Date().toLocaleTimeString()}, ` +
                    "Correction factor is: " +
                    factor
                );
                
                // Additional empricial adjustment based on the results 
                let mixAdjust = 1.002; 
                pTarget = pTarget * factor * mixAdjust;

                console.log(
                    `${new Date().toLocaleTimeString()}, ` +
                    "Adjusted target pressure is " +
                    pTarget.toFixed(3)+
                    " Torr"
                );

            }
            sendCommand(commandsArray[line][1] + "S" + pTarget.toFixed(3));
            $('#moveStatus').html('M' + commandsArray[line][1]);

            doThisAfterEveryCommand("started");
        }

        // Set collision gas pressure to target: SN,366,10
        else if (commandsArray[line][0] == "S" && commandsArray[line][1] == "N" && executed == "yes" && moving == "no" && waiting == "no") {
            doThisBeforeEveryCommand();

            let pTarget;
            if ((parseFloat($("#nitrogenTargetPressure").html()) > 0) && (parseFloat(parameterArray[line]) == 0)) {
                // Pressure is given in the nitrogenTargetPressure window AND parameter is 0
                pTarget = parseFloat($("#nitrogenTargetPressure").html());

                console.log(
                    `${new Date().toLocaleTimeString()}, ` +
                    "Collison gas target pressure from front panel is " +
                    pTarget.toFixed(1) +
                    " Torr"
                );
            }
            else {
                // Parameter is not 0, regardless that a pressure is given in the nitrogenTargetPressure
                pTarget = parseFloat(parameterArray[line]);

                console.log(
                    `${new Date().toLocaleTimeString()}, ` +
                    "Collison gas target pressure from parameter is " +
                    pTarget.toFixed(1) +
                    " Torr"
                );
            }

            sendCommand("SN" + pTarget.toFixed(1));
            $('#moveStatus').html('SN');

            doThisAfterEveryCommand("started");
        }

        // Refill sample gas from the volume left of V22 "RS,1.700,1"
        else if (commandsArray[line][0] == "R" && commandsArray[line][1] == "S" && executed == "yes" && moving == "no" && waiting == "no") {
            doThisBeforeEveryCommand();

            sendCommand("RS" + parseFloat(parameterArray[line]).toFixed(3));
            $("#moveStatus").html("RS");

            doThisAfterEveryCommand("started");
        }

        // Set bellows Z to cell pressure target (40.000 Torr) "QC,40.1,10"
        else if (commandsArray[line][0] == "Q" && executed == "yes" && moving == "no" && waiting == "no") {
            doThisBeforeEveryCommand();

            // Measure the current pressure (in Torr) in the cell
            let p = parseFloat($("#cellPressure").text());
            console.log(
                `${new Date().toLocaleTimeString()}, ` +
                "Current pressure in the cell is " +
                p +
                " Torr"
            );

            // Check if any pressure is given in the cellTargetPressure window
            let pTarget;
            let effCycle = parseInt($('#cycle').html()) + 1; // Effective cycle number (at this point the cycle number is not yet updated)
            if (parseFloat($("#cellTargetPressure").html()) > 0) {
                
                console.log(
                    `${new Date().toLocaleTimeString()}, ` +
                    "Target pressure on front panel: " +
                    parseFloat($("#cellTargetPressure").html()).toFixed(3) +
                    " Torr"
                    );

                if ($("#sampleName").html().includes("air") && effCycle > 0 && effCycle % 2 === 0) {
                    // Adjust target pressure for air samples
                    // This is necessary beacuse air samples contain some water vapor
                    let pAdjust = 0.040;
                    console.log(
                        `${new Date().toLocaleTimeString()}, ` +
                        "This is an air cycle. Adjusting target pressure by +" + 
                        pAdjust +
                        " Torr");
                    pTarget = parseFloat($("#cellTargetPressure").html()) + pAdjust;
                } else {
                    pTarget = parseFloat($("#cellTargetPressure").html());
                }
            }
            else {
                pTarget = parseFloat(parameterArray[line]);
            }

            console.log(
                `${new Date().toLocaleTimeString()}, ` +
                "Target pressure is " +
                pTarget +
                " Torr"
            );

            let percent = parseFloat($("#percentageZ").text());
            console.log(
                `${new Date().toLocaleTimeString()}, ` +
                "Bellow Z is at " +
                percent +
                "%"
            );
            
            let percentTarget = percent + (pTarget - p) / -0.007030;
            percentTarget = parseFloat(percentTarget).toFixed(1);
            console.log(
                `${new Date().toLocaleTimeString()}, ` +
                "Target percentage is " +
                percentTarget +
                "%");

            // Move bellows
            $("#setPercentageZ").val(percentTarget);
            moveBellows("Z");

            doThisAfterEveryCommand("started");
        }

        // ^^^ The command "if" series ends here ^^^

        // Check if bellows target position has been reached
        if (moving == "yes" && executed == "no" && waiting == "no" && ($('#moveStatus').html() != "-" || new Date().getTime() / 1000.00 - timeExecuted < 1)) {
            // Case 1: Bellows are currently moving, do nothing
        }
        else if (moving == "yes" && executed == "no" && waiting == "no" && $('#moveStatus').html() == "-") {
            // Case 2: Bellows finished moving, command complete, start waiting
            doThisAfterEveryCommand("executed");
        }
        else if (moving == "no" && executed == "yes" && waiting == "yes" && $('#moveStatus').html() == "-" && new Date().getTime() / 1000 - timeExecuted < timeArray[line]) {
            // Case 3: Move the progress bar
            var pbpc = (new Date().getTime() / 1000 - timeExecuted) * 307 / timeArray[line];
            $('#progressBar').css("width", pbpc + "px");
            $("#progress").html(parseInt(pbpc / 3.07) + "%");
        }
        else {
            // Case 4: Nothing moving and waiting is complete: jump to next sample if exists
            waiting = "no";
            line++;

            if (line == commandsArray.length) {
                console.log(`${new Date().toLocaleTimeString()}, ` + "End of method");
                $('#progressBar').css("width", "0px");
                $("#methodStatus").html('Sample finished');
                $("#sample" + sample).append(" &#10003;");
                $("#sample" + sample)[0].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' });
                
                // Evalaute data using Python and upload files to server
                // and copy files from TILDAS to raspberry folder
                if (!$("#sampleName").html().includes("refill") && !$("#sampleName").html().includes("folder")) {
                    copyFiles($("#timeMeasurementStarted").html(), $("#folderName").html());
                    evaluateData(sampleNameDate, $("#userName").val());
                } else {
                    console.log("There will be no data processing.");
                }

                // Move to the next sample and check if it exists
                sample++;
                if ($('#sample' + sample).length) {
                    // Next sample exists, read out sample name & method file name now
                    console.log(`${new Date().toLocaleTimeString()}, ` + "Moving on to next sample in sequence");
                    $("#sample" + sample).prepend("&#9758; ");
                    let sampleName = $('#sample' + sample).html().split(",")[1];
                    let methodFileName = $('#sample' + sample).html().split(",")[2];
                    $('#sampleName').html(sampleName);
                    loadMethod(methodFileName);
                    line = 0;
                    cycle = 0;
                    $("#timeMeasurementStarted").html(parseInt(new Date().getTime() / 1000));
                    createFolder();
                    $("#methodStatus").html('Method running');
                    $('#cycle').html("0");

                    $("#refgasTargetPressure").html("Reference target pressure");
                    $("#sample_pCO2").html("Sample pCO<sub>2</sub>");
                    $("#reference_pCO2").html("Reference pCO<sub>2</sub>");
                    $("#correction_pCO2").html("1.000");
                }
                else {
                    // No next sample, sequence finished
                    let timeSeqFinished = new Date(new Date().getTime()).toLocaleTimeString();
                    console.log(timeSeqFinished + ", Sequence finished");
                    $('#cycle').html("9¾");
                }
            }
        }
    }

    speedJS = Math.round( (1/((new Date().getTime() - startTimeJS)/1000))/10 )*10;
    $("#infoJS").html("ICE " + cycleJS + "<br>RE " + speedJS);
    cycleJS++;
    startTimeJS = new Date().getTime();
}, 50);