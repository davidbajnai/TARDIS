/*eslint no-unused-vars: ["error", { "varsIgnorePattern": "Button" }]*/

/* ############################################################################
############################## Command funtions ###############################
############################################################################ */

// Global variable needed by the JS but not the HTML
var cmd = "";

// Fetch the status string from sendCommand.php
// Send a command to the Arduino or the TILDAS via sendCommand.php
function sendCommand(cmd) {
    $.ajax({
        type: "POST",
        url: "sendCommand.php",
        data: { cmd: cmd },
        async: false,
        success: function (response) {
            // Split the status string
            const statusArr = response.split(","); // The status array is received from serialComm.py via sendCommand.php

            $("#moveStatus").html(statusArr[1]);

            // Display some images based on moveStatus
            if (
                statusArr[1] == "IA" &&
                $("#loadingA").attr("src") != "Images/loading.gif"
            ) {
                $("#loadingA").attr("src", "Images/loading.gif");
            } else if (statusArr[1] != "IA") {
                $("#loadingA").attr("src", "");
            }

            if (
                statusArr[1] == "MX" &&
                $("#motorX").attr("src") == "Images/standing_motor.gif"
            ) {
                $("#motorX").attr("src", "Images/rotating_motor.gif");
            } else if (
                statusArr[1] == "MY" &&
                $("#motorY").attr("src") == "Images/standing_motor.gif"
            ) {
                $("#motorY").attr("src", "Images/rotating_motor.gif");
            } else if (
                statusArr[1] == "MZ" &&
                $("#motorZ").attr("src") == "Images/standing_motor.gif"
            ) {
                $("#motorZ").attr("src", "Images/rotating_motor.gif");
            } else if (
                statusArr[1] == "-" &&
                ($("#motorX").attr("src") == "Images/rotating_motor.gif" ||
                    $("#motorY").attr("src") == "Images/rotating_motor.gif" ||
                    $("#motorZ").attr("src") == "Images/rotating_motor.gif")
            ) {
                $("#motorX").attr("src", "Images/standing_motor.gif");
                $("#motorY").attr("src", "Images/standing_motor.gif");
                $("#motorZ").attr("src", "Images/standing_motor.gif");
            }

            // X bellows
            $("#percentageX_Steps").html(parseFloat(statusArr[2]).toFixed(2)); // bellow expansion based on motor steps
            $("#percentageX_Poti").html(parseFloat(statusArr[3]).toFixed(1)); // bellow expansion based on potentiometer
            $("#bellowsX").css(
                "height",
                parseInt(10 + 0.9 * statusArr[2]) + "px"
            );

            // Y bellows
            $("#percentageY_Steps").html(parseFloat(statusArr[4]).toFixed(2)); // bellow expansion based on motor steps
            $("#percentageY_Poti").html(parseFloat(statusArr[5]).toFixed(1)); // bellow expansion based on potentiometer
            $("#bellowsY").css(
                "height",
                parseInt(10 + 0.9 * statusArr[4]) + "px");

            // Z bellows
            $("#stepsZ").html(parseInt(statusArr[6]));
            $("#percentageZ_Steps").html(parseFloat(statusArr[7]).toFixed(1));
            $("#bellowsZ").css(
                "height",
                parseInt(10 + 0.9 * statusArr[7]) + "px"
            );

            if (
                statusArr[6] != 7980 &&
                $("#warningZ").attr("src") != "Images/warning.png"
            ) {
                $("#warningZ").attr("src", "Images/warning.png");
            } else if (statusArr[6] == 7980) {
                $("#warningZ").attr("src", "");
            }

            // statusArr[8] is a control string "A"

            // X baratron in mbar (max. 5 mbar)
            var pressureX = parseFloat(statusArr[9]);
            $("#pressureX").html(pressureX.toFixed(3));

            // Y baratron in mbar (max. 5 mbar)
            var pressureY = parseFloat(statusArr[10]);
            $("#pressureY").html(pressureY.toFixed(3));

            // A baratron in mbar (max. 500 mbar)
            var pressureA = parseFloat(statusArr[11]);
            $("#pressureA").html(pressureA.toFixed(1));

            // statusArr[12] is a control string "B"

            // Valve status
            var valveArray = statusArr[13];
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
                        "Images/" + positions[i - 1] + "_closed.png"
                    );
                } else {
                    $("#V" + n + i.toString()).attr(
                        "src",
                        "Images/" + positions[i - 1] + "_open.png"
                    );
                }
                i = i + 1;
            }


            // Relay status
            var relayArray = statusArr[14];
            var i = 1;
            while (i <= 2) {
                $("#U" + "0" +  i.toString() + "_label").html(relayArray[i - 1]);
                if (relayArray[i - 1] == 0) {
                    $("#U" + "0" + i.toString()).attr("src", "Images/relay_off.png");
                } else {
                    $("#U" + "0" + i.toString()).attr("src", "Images/relay_on.png");
                }
                i = i + 1;
            }

            // Box humidity
            var roomRH = statusArr[15];
            $("#roomRH").html(roomRH);

            // Box temperature
            var housingT = statusArr[16];
            $("#housingT").html(housingT);

            // Box setpoint temperature
            var SPT = parseFloat(statusArr[17]);
            $("#setPointTemperature").html(SPT.toFixed(1));

            // Fan speed
            var fanSpeed = statusArr[18];
            $("#fanSpeed").html(fanSpeed);

            // Cell pressure from the TILDAS in Torr
            // The cell's baratron is zeroed here
            var baratronTorr =
                parseFloat(statusArr[19]) * 1 + (0.406 + 0.223) / 1.33322;
            $("#baratron").html(baratronTorr.toFixed(3));

            // CO2 mixing ratios from the TILDAS
            var mr1 = statusArr[20];
            $("#mr1").html(parseFloat(mr1).toFixed(3));
            var mr2 = statusArr[21];
            $("#mr2").html(parseFloat(mr2).toFixed(3));
            var mr3 = statusArr[22];
            $("#mr3").html(parseFloat(mr3).toFixed(3));
            var mr4 = statusArr[23];
            $("#mr4").html(parseFloat(mr4).toFixed(3));

            // Edwards vacuum gauge
            var edwards = statusArr[24];
            $("#edwards").html(parseFloat(edwards).toFixed(4));

            // Room humidity
            var roomHumidity = statusArr[25];
            $("#roomHumidity").html(roomHumidity);

            // Room temperature
            var roomTemperature = statusArr[26];
            $("#roomTemperature").html(roomTemperature);

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
    // console.log("Recieved:" + valve + status);
    if (status == "0") {
        cmd = valve + "O";
    } else if (status == "1") {
        cmd = valve + "C";
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
    // console.log("Recieved:" + relay + status);
    if (status == "0") {
        cmd = relay + "O";
    } else if (status == "1") {
        cmd = relay + "C";
    } else {
        cmd = "";
        alert(
            "Invalid command, could not determine the current status of the relay."
        );
    }
    // console.log("Sent: " + cmd);
}

// Start recording data on TILDAS
function startWritingData() {
    cmd = 'TWD1';
    console.log("Starting data recording on TILDAS");
}

// Stop recording data on TILDAS
function stopWritingData() {
    cmd = 'TWD0';
    console.log("Stopping data recording on TILDAS");
}

// Set valves to starting position
function startingPosition() {
    cmd = 'KL';
    console.log("Resetting valves to starting position");
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
    console.log("Moving bellow " + bellow + " to: " + percentage + "%");
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
        url: "uploadMethod.php",
        data: { methodFileName: methodFileName },
        type: "POST",
        success: function (result) {
            console.log("Method loaded successfully");

            $("#method").empty();
            colArr = result.split("|");
            commandsArray = [];
            commandsArray = colArr[0].split(","); // This is a 1D array here
            // console.log("commandsArray",commandsArray); // Log the commands array - for debugging
            parameterArray = colArr[1].split(",");
            // console.log("parameterArray",parameterArray); // Log the parameter array - for debugging
            timeArray = colArr[2].split(",");
            // console.log("timeArray",timeArray); // Log the wait time array - for debugging

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
        url: "uploadMethod.php",
        data: data,
        type: "POST",
        processData: false,
        contentType: false,
        success: function () {
            console.log("Method uploaded successfully");
        },
    });
});

// Upload sequence by user
$("body").on("change", "#uploadSequence", function () {
    var data = new FormData();
    data.append("file", this.files[0]);
    $.ajax({
        url: "uploadSequence.php",
        data: data,
        type: "POST",
        processData: false,
        contentType: false,
        success: function (result) {
            console.log("Sequence uploaded sucessfully");

            // Delete all elements in div sequence
            $("#sequence").empty();
            var colSeqArr = result.split("|");
            let sampleNameArr = colSeqArr[0].split(",");
            // console.log( "Sample array", sampleNameArr ); // Log the sample array - for debugging
            let methodFileArr = colSeqArr[1].split(",");
            // console.log( "Methods file name array", methodFileArr ); // Log the methods file name array - for debugging

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
    console.log("Calling createFolder.php");
    $.ajax({
        type: "POST",
        url: "createFolder.php",
        async: false,
        data: {
            date: $("#timeMeasurementStarted").html(), // Date and time when measurement started in UNIX format & UTC timezone
            sampleName: $("#sampleName").html(),
        },
        success: function (response) {
            console.log(response);
            $("#folderName").html(response);
        },
    });
}

// Write logfile.csv
function writeLogfile(logData, folderName, sampleName) {
    $.ajax({
        type: "POST",
        url: "writeLogfile.php",
        data: {
            sampleName: sampleName,
            logData: logData,
            folderName: folderName,
        },
        success: function (response) {
            if (response != "") {
                console.log(response);
            }
        },
    });
}

// Copy all files with a date younger than timeMeasurementStarted
function copyFiles() {
    console.log("Calling copyFiles.php");
    $.ajax({
        type: "POST",
        url: "copyFiles.php",
        async: false,
        data: {
            date: $("#timeMeasurementStarted").html(), // In UNIX format & UTC timezone
            folderName: $("#folderName").html(), // Something like: Results/230306_123421_sampleName
        },
        success: function (response) {
            console.log(response);
        },
    });
}

// Evaluate data after the measurement is finished
function evaluateData() {
    console.log("Calling evaluateData.php");
    $.ajax({
        type: "POST",
        url: "evaluateData.php",
        async: true,
        data: {
            sampleName: $("#folderName").html(),
            userName: $("#userName").val(),
            polynomial: $("#polynomial").val(),
        },
    }).done(function (result) {
        console.log(result);
    });
}

// Show results button
function showResultsButton() {
    window.open(
        "http://192.168.1.1/isotope/Isotopes_data_list.php?MaxNumber=20&SampleTypeSearch=CO2",
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
    console.log("Sequence started at " + timeButtonPressed);
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
        // For example: when the command is a wait command or the Arduino is busy
        $("#progressBar").css("width", "0px");
        $("#progress").html("0%");
        timeExecuted = new Date().getTime() / 1000;
        timeExecutedStr = new Date(timeExecuted * 1000).toLocaleTimeString();
        moving = "yes";
        executed = "no";
        waiting = "no";
        console.log(
            "Command in line",
            line,
            ":",
            commandsArray[line],
            parameterArray[line],
            "started at",
            timeExecutedStr
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
            "Command in line",
            line,
            ":",
            commandsArray[line],
            parameterArray[line],
            "executed at",
            timeExecutedStr,
            "\nNow wait for",
            timeArray[line],
            "seconds."
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
var currentTimeOld = 0;
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
        if (currentTime % 5 == 0 && currentTime != currentTimeOld && $("#sampleName").html() != "") {
            // Unix -> Mac timestamp, TILDAS uses Mac timestamp
            logData.push([
                parseInt(currentTime + 2082844800 + 3600),
                parseFloat($("#housingT").html()),
                parseFloat($("#setPointTemperature").html()),
                parseFloat($("#roomRH").html()),
                $("#percentageX_Steps").html(),
                $("#percentageY_Steps").html(),
                $("#percentageZ_Steps").html(),
                $("#pressureX").html(),
                $("#pressureY").html(),
                $("#pressureA").html(),
                $("#edwards").html().trim(),
                parseFloat($("#fanSpeed").html()),
                parseFloat($("#roomTemperature").html()),
                parseFloat($("#roomHumidity").html()),
            ]);

            if (currentTime % 30 == 0) {
                // Write data to logfile every 30 seconds
                // console.log("Writing to logfile now."); // Used for debugging
                writeLogfile(logData, $('#folderName').html(), $('#sampleName').html());
                // Reset logfile array
                logData = [];
            }
            currentTimeOld = currentTime;
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

            $("#cellTargetPressure").html($("#baratron").html());
            console.log("Cell target pressure: ", $("#cellTargetPressure").html());

            doThisAfterEveryCommand("executed");
        }

        // Write nitrogen pressure for the first sample on the frontpanel "WA <no parameter>"
        else if (commandsArray[line][0] == "W" && commandsArray[line][1] == "A" && executed == "yes" && moving == "no" && waiting == "no") {
            doThisBeforeEveryCommand();

            $("#nitrogenTargetPressure").html((parseFloat($("#pressureA").html())).toFixed(1));

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
                console.log("Reference pCO2 is: ",$("#reference_pCO2").html());

                if ($("#sample_pCO2").html() != "Sample pCO<sub>2</sub>") {
                    // Adjust the correction factor
                    $("#correction_pCO2").html(($("#sample_pCO2").html() / $("#reference_pCO2").html() * $("#correction_pCO2").html()).toFixed(3));
                    console.log("Correction factor is: ",$("#correction_pCO2").html());
                }
            }
            else if (parameterArray[line] == 1) {
                $("#sample_pCO2").html($("#mr3").html());
                console.log("Sample pCO2 is: ",$("#sample_pCO2").html());

                if ($("#reference_pCO2").html() != "Reference pCO<sub>2</sub>") {
                    // Adjust the correction factor
                    $("#correction_pCO2").html(($("#sample_pCO2").html() / $("#reference_pCO2").html() * $("#correction_pCO2").html()).toFixed(3));
                    console.log("Correction factor is: ",$("#correction_pCO2").html());
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
                console.log("This is cycle #", cycle);
                cycle++;
            }

            doThisAfterEveryCommand("executed");
        }

        // Move bellows (X,Y,Z) "BY 53" with the percentage as parameter BX 34.5
        else if (commandsArray[line][0] == "B" && moving == "no" && executed == "yes" && waiting == "no") {
            doThisBeforeEveryCommand();

            if (parameterArray[line].substr(0, 1) == "+" || parameterArray[line].substr(0, 1) == "-") {
                // Move increment
                // Get current bellows position
                let currentPercent = parseFloat($("#percentage" + commandsArray[line][1] + "_Steps").text());
                // console.log("Current bellows position is: ", currentPercent, "%"); // Used for debugging
                // Calculate the new bellows position
                let newPercent = currentPercent + parseFloat(parameterArray[line]);
                // console.log("New bellows position is: ", newPercent, "%"); // Used for debugging
                $("#setPercentage" + commandsArray[line][1]).val(newPercent.toFixed(1));
            }
            else {
                // Move absolute
                $("#setPercentage" + commandsArray[line][1]).val(parameterArray[line]);
            }

            moveBellows(commandsArray[line][1]);
            // console.log("Move status:", $('#moveStatus').html()); // Used for debugging

            doThisAfterEveryCommand("started");
        }

        // Set bellows to pressure target (X,Y) "PX 1.723"
        else if (commandsArray[line][0] == "P" && executed == "yes" && moving == "no" && waiting == "no") {
            doThisBeforeEveryCommand();

            let pTarget;
            if (commandsArray[line][1] == "X") {
                console.log("Adjusting bellow X to target pressure");
                if ($("#refgasTargetPressure").html() == "Reference target pressure") {
                    console.log("Target pressure recieved from parameter");
                    pTarget = parseFloat(parameterArray[line]);
                }
                else {
                    console.log("Target pressure recived from front panel");
                    pTarget = parseFloat($("#refgasTargetPressure").html());
                }
            }
            else if (commandsArray[line][1] == "Y") {
                console.log("Adjusting bellow Y to target pressure");
                if ($("#samgasTargetPressure").html() == "Sample target pressure") {
                    console.log("Target pressure recieved from parameter");
                    pTarget = parseFloat(parameterArray[line]);
                }
                else {
                    console.log("Target pressure recived from front panel");
                    pTarget = parseFloat($("#samgasTargetPressure").html());
                }
            }
            console.log("The target pressure is: ", pTarget.toFixed(3), "mbar");

            // Here we correct pTarget by the correction_pCO2 factor
            // The corrrection factor is 1.000 by default, and can be adjusted by the CM command
            let factor = parseFloat($("#correction_pCO2").html());
            if (factor != 1.000) {
                console.log("Correction factor is: ",factor);
                pTarget = pTarget * factor;
                console.log("Adjusted target pressure is: ", pTarget.toFixed(3), "mbar");
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
                console.log("Collison gas target pressure from front panel: ", pTarget, " Torr");
            }
            else {
                // Parameter is not 0, regardless that a pressure is given in the nitrogenTargetPressure
                pTarget = parseFloat(parameterArray[line]);
                console.log("Collison gas target pressure from parameter: ", pTarget, " Torr");
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
            let p = parseFloat($("#baratron").text());
            console.log("Current pressure in the cell is: ", p.toFixed(3), "Torr");

            // Check if any pressure is given in the cellTargetPressure window
            let pTarget;
            let effCycle = parseInt($('#cycle').html()) + 1; // Effective cycle number (at this point the cycle number is not yet updated)
            if (parseFloat($("#cellTargetPressure").html()) > 0) {
                console.log("Target pressure on front panel: ", parseFloat($("#cellTargetPressure").html()).toFixed(3), "Torr");
                if ($("#sampleName").html().includes("air") && effCycle > 0 && effCycle % 2 === 0) {
                    // Adjust target pressure for air samples
                    // This is necessary beacuse air samples contain some water vapor
                    console.log("This is an air cycle. Adjusting target pressure by +0.020 Torr.");
                    pTarget = parseFloat($("#cellTargetPressure").html()) + 0.020;
                } else {
                    pTarget = parseFloat($("#cellTargetPressure").html());
                }
            }
            else {
                pTarget = parseFloat(parameterArray[line]);
            }
            console.log("Target pressure is: ", pTarget.toFixed(3), "Torr");

            let percent = parseFloat($("#percentageZ_Steps").text());
            console.log("Current percentage (Z) is: ", percent.toFixed(1), "%");

            let percentTarget = percent + (pTarget - p) / -0.007030;
            percentTarget = parseFloat(percentTarget).toFixed(1);
            console.log("Target percentage is: ", percentTarget, "%");

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
            timeExecuted = new Date().getTime() / 1000;
            timeExecutedStr = new Date(timeExecuted*1000).toLocaleTimeString();
            moving = "no";
            executed = "yes";
            waiting = "yes";
            $("#command" + line).append(" &#10003;");
            console.log(
                "Command in line",
                line,
                ":",
                commandsArray[line],
                parameterArray[line],
                "finished at",
                timeExecutedStr,
                "\nNow wait for",
                timeArray[line],
                "seconds."
            );

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
                console.log("End of method");
                $('#progressBar').css("width", "0px");
                $("#methodStatus").html('Sample finished');
                $("#sample" + sample).append(" &#10003;");
                $("#sample" + sample)[0].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' });
                // Copy files from TILDAS to raspberry folder
                copyFiles();
                // Execute Python script
                evaluateData();

                // Move to the next sample and check if it exists
                sample++;
                if ($('#sample' + sample).length) {
                    // Next sample exists, read out sample name & method file name now
                    console.log("Moving on to next sample in sequence");
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
                    console.log("Sequence finished at " + timeSeqFinished);
                    $('#cycle').html("9¾");
                }
            }
        }
    }

    speedJS = Math.round( (1/((new Date().getTime() - startTimeJS)/1000))/10 )*10;
    $("#infoJS").html("ICE " + cycleJS + "<br>RE " + speedJS);
    // $('#infoJS').text("ICE " + cycleJS);
    cycleJS++;
    startTimeJS = new Date().getTime();
}, 50);