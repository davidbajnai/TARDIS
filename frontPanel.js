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
            var percentageX = statusArr[3];
            $("#bellowsX").css(
                "height",
                parseInt(10 + 0.9 * percentageX) + "px"
            );
            $("#percentageX").html(parseFloat(percentageX).toFixed(1));
            $("#percentageX").css("color", "gray");
            $("#percentageXsteps").html(parseFloat(statusArr[2]).toFixed(2));
            $("#stepsX").html(statusArr[2] + " steps");

            // Y bellows
            var percentageY = statusArr[5];
            $("#bellowsY").css("height", 10 + 0.9 * percentageY + "px");
            $("#percentageY").html(parseFloat(percentageY).toFixed(1));
            $("#percentageY").css("color", "gray");
            $("#percentageYsteps").html(parseFloat(statusArr[4]).toFixed(2));
            $("#stepsY").html(statusArr[4] + " steps");

            // Z bellows
            $("#percentageZsteps").html(parseFloat(statusArr[7]).toFixed(1));
            $("#stepsZ").html(statusArr[6]); //Steps
            $("#bellowsZ").css(
                "height",
                parseFloat(10 + 0.9 * statusArr[7]).toFixed(1) + "px"
            );

            if (
                statusArr[6] != 7980 &&
                $("#warningZ").attr("src") != "Images/warning.png"
            ) {
                $("#warningZ").attr("src", "Images/warning.png");
            } else if (statusArr[6] == 7980) {
                $("#warningZ").attr("src", "");
            }

            // X baratron in mbar (max. 5 mbar)
            var pressureX = parseFloat(statusArr[8]);
            $("#pressureX").html(pressureX.toFixed(3));

            // Y baratron in mbar (max. 5 mbar)
            var pressureY = parseFloat(statusArr[9]);
            $("#pressureY").html(pressureY.toFixed(3));

            // A baratron in mbar (max. 500 mbar)
            var pressureA = parseFloat(statusArr[10]);
            $("#pressureA").html(pressureA.toFixed(1));

            // Valve status
            var valveArray = statusArr[12];
            const positions = [
                "horizontal", // V01
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
                "vertical", // V15
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
                "horizontal", // V28
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

            // Box humidity
            var roomRH = statusArr[13];
            $("#roomRH").html(roomRH);

            // Box temperature
            var housingT = statusArr[14];
            $("#housingT").html(housingT);

            // Fan speed
            var fanSpeed = statusArr[15];
            $("#fanSpeed").html(fanSpeed);

            // Cell pressure from the TILDAS in Torr
            // The cell's baratron is zeroed here
            var baratronTorr =
                parseFloat(statusArr[16]) * 1 + (0.406 + 0.223) / 1.33322;
            $("#baratron").html(baratronTorr.toFixed(3));

            // CO2 mixing ratios from the TILDAS
            var mr1 = statusArr[17];
            $("#mr1").html(parseFloat(mr1).toFixed(1));
            var mr2 = statusArr[18];
            $("#mr2").html(parseFloat(mr2).toFixed(1));
            var mr3 = statusArr[19];
            $("#mr3").html(parseFloat(mr3).toFixed(1));
            var mr4 = statusArr[20];
            $("#mr4").html(parseFloat(mr4).toFixed(1));

            // Edwards vacuum gauge
            var edwards = statusArr[21];
            $("#edwards").html(parseFloat(edwards).toFixed(4));

            // Room humidity
            var roomHumidity = statusArr[22];
            $("#roomHumidity").html(roomHumidity);

            // Room temperature
            var roomTemperature = statusArr[23];
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
    if (status == '0' || status == 'O') {
        cmd = valve + 'O';
    }
    else if (status == '1' || status == 'C') {
        cmd = valve + 'C';
    }
    else {
        cmd = '';
        alert('Invalid command, could not determine the current status of the valve.');
    }
}

// Start recording data on TILDAS
function startWritingData() {
    cmd = 'TWD1';
    console.log(cmd);
}

// Stop recording data on TILDAS
function stopWritingData() {
    cmd = 'TWD0';
    console.log(cmd);
}

// Change the setpoint temperature for the PID
function setHousingTCmd(setTemp) {
    var temp = parseFloat($(setTemp).val()).toFixed(3);
    cmd = 'FS' + temp;
    console.log(cmd);
}

// Set valves to starting position
function startingPosition() {
    cmd = 'KL';
    console.log(cmd);
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
    console.log(cmd);
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
            console.log("Method loaded successfully.");

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
                        ": " +
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
            console.log("Method uploaded successfully.");
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
            console.log("Sequence uploaded sucessfully.");

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
                    $("#sampleName").val(sampleNameArr[i]);
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
    console.log("Creating folder.");
    $.ajax({
        type: "POST",
        url: "createFolder.php",
        async: false,
        data: {
            date: $("#timeMeasurementStarted").html(), // Date and time when measurement started in UNIX format & UTC timezone
            sampleName: $("#sampleName").val(),
        },
        success: function (response) {
            console.log(response);
            $("#folderName").html(response);
        },
    });
}

// Write logfile.csv
function writeLogfile(logData, folderName) {
    $.ajax({
        type: "POST",
        url: "writeLogfile.php",
        data: {
            sampleName: $("#sampleName").val(),
            logData: logData,
            folderName: folderName,
        },
        success: function (response) {
            console.log(response);
        },
    });
}

// Copy all files with a date younger than timeMeasurementStarted
function copyFiles() {
    console.log("Copy files.");
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
    console.log("Starting evaluateData.php");
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
        console.log("Data gotten from evaluateData.php");
    });
}

// Show results button
function showResults() {
    window.open(
        "http://192.168.1.1/isotope/Isotopes_data_list.php?MaxNumber=20&SampleTypeSearch=CO2",
        "_blank"
    );
}

// Start sequence button
function startSequence() {
    const timeMeasurementStarted = parseInt(new Date().getTime() / 1000);
    $("#timeMeasurementStarted").html(timeMeasurementStarted);
    createFolder();
    $("#methodStatus").html("Method running");
    $("#sample0").prepend("&#9758; ");
}

/* ############################################################################
######################## This is the main program loop ########################
############################################################################ */

var timeExecuted = 0; // Time when cmd has been sent to Arduino
var line = 0;
var moving = "no";
var waiting = "no"; // Wait for the delay to goto next command
var executed = "yes";
var cycleJS = 0;
var currentTimeOld = 0;
var logData = [];
var sample = 0;
var cycle = 0;

setInterval(function () {
    sendCommand(cmd);
    console.log('Current cmd', cmd);
    cmd = "";
    getTime(); // Sets the clock

    // Execute the individual commands from the method
    if ($("#methodStatus").text() == "Method running") {
        var currentTime = parseInt(new Date().getTime() / 1000);

        // Save data to logfile array every 5 seconds
        if (currentTime % 5 == 0 && currentTime != currentTimeOld && $("#sampleName").val() != "") {
            // Unix -> Mac timestamp, TILDAS uses Mac timestamp
            logData.push([
                parseInt(currentTime + 2082844800 + 3600),
                parseFloat($("#housingT").html()),
                parseFloat($("#housingTargetT").val()),
                parseFloat($("#roomRH").html()),
                $("#percentageXsteps").html(),
                $("#percentageYsteps").html(),
                $("#percentageZsteps").html(),
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
                // console.log("Writing to logfile now.");
                writeLogfile(logData, $('#folderName').html());
                // Reset logfile array
                logData = [];
            }
            currentTimeOld = currentTime;
        }

        // vvv The command "if" series starts here vvv

        // Open or close valves
        if (commandsArray[line][0] == "V" && executed == "yes" && moving == "no" && waiting == "no") {
            // Do this before every command in method
            if ($("#command" + (line + 2)).length) { $("#command" + (line + 2))[0].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' }); }
            $("#command" + line).prepend("&#9758; ");

            // Valve that needs to be switched
            if (parameterArray[line] == 0) {
                toggleValve(commandsArray[line], "1");
            }
            else {
                toggleValve(commandsArray[line], "0");
            }

            // Do this after every command
            timeExecuted = new Date().getTime() / 1000;
            moving = "no";
            executed = "yes";
            waiting = "yes";
            $("#command" + line).append(" &#10003;");
            // console.log('Command',commandsArray[line],timeExecuted,'started and finished.');
        }

        // Set housing temperature
        else if (commandsArray[line][0] == "F" && commandsArray[line][1] == "S" && executed == "yes" && moving == "no" && waiting == "no") {
            // Do this before every command in method
            if ($("#command" + (line + 2)).length) { $("#command" + (line + 2))[0].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' }); }
            $("#command" + line).prepend("&#9758; ");

            cmd = "FS" + parameterArray[line];

            // Do this after every command
            timeExecuted = new Date().getTime() / 1000;
            moving = "no";
            executed = "yes";
            waiting = "yes";
            $("#command" + line).append(" &#10003;");
            // console.log('Command',commandsArray[line],timeExecuted,'started and finished.');
        }

        // This command opens V15, waits until A target pressure is reached, than closes V15
        else if (commandsArray[line][0] == "I" && commandsArray[line][1] == "A" && executed == "yes" && moving == "no" && waiting == "no") {
            // Do this before every command in method
            if ($("#command" + (line + 2)).length) { $("#command" + (line + 2))[0].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' }); }
            $("#command" + line).prepend("&#9758; ");
            cmd = "IA" + parameterArray[line];

            // Do this after every command
            $("#progressBar").css("width", "0px");
            $("#progress").html("0%");
            timeExecuted = new Date().getTime() / 1000;
            moving = "yes";
            executed = "no";
            waiting = "no";
            // console.log( "moving:",moving,"executed:",executed,"waiting:",waiting )
        }

        // Reset valves to starting position
        else if (commandsArray[line][0] == "K" && commandsArray[line][1] == "L" && executed == "yes" && moving == "no" && waiting == "no") {
            // Do this before every command in method
            if ($("#command" + (line + 2)).length) { $("#command" + (line + 2))[0].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' }); }
            $("#command" + line).prepend("&#9758; ");

            cmd = "KL" + parameterArray[line];

            // Do this after every command
            timeExecuted = new Date().getTime() / 1000;
            moving = "no";
            executed = "yes";
            waiting = "yes";
            $("#command" + line).append(" &#10003;");
            // console.log('Command',commandsArray[line],timeExecuted,'started and finished.');
        }

        // Write cell pressure for the first sample on the front panel: WC,0,10 !Parameter is ignored
        else if (commandsArray[line][0] == "W" && commandsArray[line][1] == "C" && executed == "yes" && moving == "no" && waiting == "no") {
            // Do this before every command in method
            if ($("#command" + (line + 2)).length) { $("#command" + (line + 2))[0].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' }); }
            $("#command" + line).prepend("&#9758; ");

            $("#cellTargetPressure").html($("#baratron").html());

            // Do this after every command
            timeExecuted = new Date().getTime() / 1000;
            moving = "no";
            executed = "yes";
            waiting = "yes";
            $("#command" + line).append(" &#10003;");
            // console.log('Command',commandsArray[line],timeExecuted,'started and finished.');
        }

        // Write nitrogen pressure for the first sample on the frontpanel "WA <no parameter>"
        else if (commandsArray[line][0] == "W" && commandsArray[line][1] == "A" && executed == "yes" && moving == "no" && waiting == "no") {
            // Do this before every command in method
            if ($("#command" + (line + 2)).length) { $("#command" + (line + 2))[0].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' }); }
            $("#command" + line).prepend("&#9758; ");

            $("#nitrogenTargetPressure").html((parseFloat($("#pressureA").html()) + 0.5).toFixed(1));

            // Do this after every command
            timeExecuted = new Date().getTime() / 1000;
            moving = "no";
            executed = "yes";
            waiting = "yes";
            $("#command" + line).append(" &#10003;");
            // console.log('Command',commandsArray[line],timeExecuted,'started and finished.');
        }

        // Write reference gas target pressure for the first sample on the frontpanel "WR <no parameter>"
        else if (commandsArray[line][0] == "W" && commandsArray[line][1] == "R" && executed == "yes" && moving == "no" && waiting == "no") {
            // Do this before every command in method
            if ($("#command" + (line + 2)).length) { $("#command" + (line + 2))[0].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' }); }
            $("#command" + line).prepend("&#9758; ");

            // Keep the target pressure (ref) for all samples in sequence
            if ($("#refgasTargetPressure").html() == "Reference target pressure") {
                $("#refgasTargetPressure").html("1.700");
            }
            else {
                $("#refgasTargetPressure").html((parseFloat($("#refgasTargetPressure").html()) * 1.0026).toFixed(3));
            }

            // Do this after every command
            timeExecuted = new Date().getTime() / 1000;
            moving = "no";
            executed = "yes";
            waiting = "yes";
            $("#command" + line).append(" &#10003;");
            // console.log('Command',commandsArray[line],timeExecuted,'started and finished.');
        }


        // Write sample gas target pressure for the first sample on the frontpanel "WS <no parameter>"
        else if (commandsArray[line][0] == "W" && commandsArray[line][1] == "S" && executed == "yes" && moving == "no" && waiting == "no") {
            // Do this before every command in method
            if ($("#command" + (line + 2)).length) { $("#command" + (line + 2))[0].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' }); }
            $("#command" + line).prepend("&#9758; ");

            // Keep the target pressure (sam) for all samples in sequence
            if ($("#samgasTargetPressure").html() == "Sample target pressure") {
                $("#samgasTargetPressure").html("1.700");
            }
            else {
                $("#samgasTargetPressure").html((parseFloat($("#samgasTargetPressure").html()) * 1.0026).toFixed(3));
            }

            // Do this after every command
            timeExecuted = new Date().getTime() / 1000;
            moving = "no";
            executed = "yes";
            waiting = "yes";
            $("#command" + line).append(" &#10003;");
            // console.log('Command',commandsArray[line],timeExecuted,'started and finished.');
        }

        // Write gas mixing ratio to the frontpanel "CM, 0=Reference 1=Sample"
        else if (commandsArray[line][0] == "C" && commandsArray[line][1] == "M" && executed == "yes" && moving == "no" && waiting == "no") {
            // Do this before every command in method
            if ($("#command" + (line + 2)).length) { $("#command" + (line + 2))[0].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' }); }
            $("#command" + line).prepend("&#9758; ");

            if (parameterArray[line] == 0) {
                $("#reference_pCO2").html($("#mr3").html());

                if ($("#sample_pCO2").html() != "Sample pCO<sub>2</sub>") {
                    // Adjust the correction factor
                    $("#correction_pCO2").html(($("#sample_pCO2").html() / $("#reference_pCO2").html() * $("#correction_pCO2").html()).toFixed(3));
                }
            }
            else if (parameterArray[line] == 1) {
                $("#sample_pCO2").html($("#mr3").html());

                if ($("#reference_pCO2").html() != "Reference pCO<sub>2</sub>") {
                    // Adjust the correction factor
                    $("#correction_pCO2").html(($("#sample_pCO2").html() / $("#reference_pCO2").html() * $("#correction_pCO2").html()).toFixed(3));
                }
            }

            // Do this after every command
            timeExecuted = new Date().getTime() / 1000;
            moving = "no";
            executed = "yes";
            waiting = "yes";
            $("#command" + line).append(" &#10003;");
            // console.log('Command',commandsArray[line],timeExecuted,'started and finished.');
        }

        // Execute command at laser spectrometer: Start writing data to disk "TWD 0"
        else if (commandsArray[line][0] == "T" && commandsArray[line][1] == "W" && commandsArray[line][2] == "D" && executed == "yes" && moving == "no" && waiting == "no") {
            // Do this before every command in method
            if ($("#command" + (line + 2)).length) { $("#command" + (line + 2))[0].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' }); }
            $("#command" + line).prepend("&#9758; ");

            // Execute command at laser spectrometer: Stop writing data to disk
            if (parameterArray[line] == 0) {
                stopWritingData();
            }
            else if (parameterArray[line] == 1) {
                startWritingData();
                $('#cycle').html(cycle);
                cycle++;
            }

            // Do this after every command
            timeExecuted = new Date().getTime() / 1000;
            moving = "no";
            executed = "yes";
            waiting = "yes";
            $("#command" + line).append(" &#10003;");
            // console.log('Command',commandsArray[line],timeExecuted,'started and finished.');
        }

        // Move bellows (X,Y,Z) "BY 53" with the percentage as parameter BX 34.5
        else if (commandsArray[line][0] == "B" && moving == "no" && executed == "yes" && waiting == "no") {
            // Do this before every command in method
            if ($("#command" + (line + 2)).length) { $("#command" + (line + 2))[0].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' }); }
            $("#command" + line).prepend("&#9758; ");

            if (parameterArray[line].substr(0, 1) == "+" || parameterArray[line].substr(0, 1) == "-") {
                // Move increment
                // Get current bellows position
                let currentPercent = parseFloat($("#percentage" + commandsArray[line][1] + "steps").text());
                // Calculate the new bellows position
                let newPercent = currentPercent + parseFloat(parameterArray[line]);
                $("#setPercentage" + commandsArray[line][1]).val(newPercent.toFixed(1));
            }
            else {
                // Move absolute
                $("#setPercentage" + commandsArray[line][1]).val(parameterArray[line]);
            }

            moveBellows(commandsArray[line][1]);
            console.log("Just started to move bellows, move status:", $('#moveStatus').html());

            // Do this after each command
            $("#progressBar").css("width", "0px");
            $("#progress").html("0%");
            timeExecuted = new Date().getTime() / 1000; // Start time of command
            moving = "yes";
            executed = "no";
            waiting = "no";
            // console.log('Command',commandsArray[line],timeExecuted,'started.');
        }

        // Set bellows to pressure target (X,Y) "PX 1.723"
        else if (commandsArray[line][0] == "P" && executed == "yes" && moving == "no" && waiting == "no") {
            // Do this before every command in method
            if ($("#command" + (line + 2)).length) { $("#command" + (line + 2))[0].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' }); }
            $("#command" + line).prepend("&#9758; ");
            if (commandsArray[line][1] == "X") {
                if ($("#refgasTargetPressure").html() == "Reference target pressure") {
                    var pTarget = parseFloat(parameterArray[line]);
                }
                else {
                    var pTarget = parseFloat($("#refgasTargetPressure").html()).toFixed(3);
                }
            }
            else if (commandsArray[line][1] == "Y") {
                if ($("#samgasTargetPressure").html() == "Sample target pressure") {
                    var pTarget = parseFloat(parameterArray[line]);
                }
                else {
                    var pTarget = parseFloat($("#samgasTargetPressure").html()).toFixed(3);
                }
            }

            // Here we correct pTarget by the correction_pCO2 factor
            // The corrrection factor is 1.000 by default, but can be adjusted by the CM command
            var pTarget = pTarget * parseFloat($("#correction_pCO2").html()).toFixed(3);

            console.log("The target pressure is: ", pTarget.toFixed(3), "mbar");
            sendCommand(commandsArray[line][1] + "S" + pTarget.toFixed(3));
            $('#moveStatus').html('M' + commandsArray[line][1]);

            // Do this after every command
            $("#progressBar").css("width", "0px");
            $("#progress").html("0%");
            timeExecuted = new Date().getTime() / 1000;
            moving = "yes";
            executed = "no";
            waiting = "no";
        }

        // Set collision gas pressure to target: SN,366,10
        else if (commandsArray[line][0] == "S" && commandsArray[line][1] == "N" && executed == "yes" && moving == "no" && waiting == "no") {
            // Do this before every command in method
            if ($("#command" + (line + 2)).length) { $("#command" + (line + 2))[0].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' }); }
            $("#command" + line).prepend("&#9758; ");

            // Decide what to do
            if ((parseFloat($("#nitrogenTargetPressure").html()) > 0) && (parseFloat(parameterArray[line]) == 0)) {
                // Pressure is given in the nitrogenTargetPressure window AND parameter is 0
                var pTarget = parseFloat($("#nitrogenTargetPressure").html());
            }
            else {
                // Parameter is not 0, regardless that a pressure is given in the nitrogenTargetPressure
                var pTarget = parseFloat(parameterArray[line]);
            }

            // console.log("The target collison gas pressure (A) is: ", pTarget, " Torr");

            sendCommand("SN" + pTarget.toFixed(1));
            $('#moveStatus').html('SN');

            // Do this after every command					
            $("#progressBar").css("width", "0px");
            $("#progress").html("0%");
            timeExecuted = new Date().getTime() / 1000;
            moving = "yes";
            executed = "no";
            waiting = "no";
        }

        // Refill sample gas from the manifold headspace - can be used after first fill
        else if (commandsArray[line][0] == "R" && commandsArray[line][1] == "S" && executed == "yes" && moving == "no" && waiting == "no") {
            // Do this before every command in method
            if ($("#command" + (line + 2)).length) { $("#command" + (line + 2))[0].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' }); }
            $("#command" + line).prepend("&#9758; ");

            sendCommand("RS" + parseFloat(parameterArray[line]).toFixed(3));
            $('#moveStatus').html('RS');

            // Do this after every command				
            $("#progressBar").css("width", "0px");
            $("#progress").html("0%");
            timeExecuted = new Date().getTime() / 1000;
            moving = "yes";
            executed = "no";
            waiting = "no";
        }

        // Set bellows Z to cell pressure target (40.000 Torr) "QZ,40.1,10"
        else if (commandsArray[line][0] == "Q" && executed == "yes" && moving == "no" && waiting == "no") {
            // Do this before every command in method
            if ($("#command" + (line + 2)).length) { $("#command" + (line + 2))[0].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' }); }
            $("#command" + line).prepend("&#9758; ");

            // Measure the current pressure (in Torr) in the cell
            let p = parseFloat($("#baratron").text());
            console.log("Current pressure in the cell is: ", p.toFixed(3), "Torr");

            // Check if any pressure is given in the cellTargetPressure window
            var pTarget;
            if (parseFloat($("#cellTargetPressure").html()) > 0) {
                pTarget = parseFloat($("#cellTargetPressure").html());
            }
            else {
                pTarget = parseFloat(parameterArray[line]); // Normally about 40 Torr
            }

            // Adjust target pressure for air samples
            if ($("#sampleName").html().includes("air")) {
                pTarget += 0.037;
            }
            console.log("Target pressure is: ", pTarget.toFixed(3), "Torr");

            let percent = parseFloat($("#percentageZsteps").text());
            console.log("Current percentage (Z) is: ", percent.toFixed(1), "%");

            var percentTarget = percent + (pTarget - p) / -0.007030;
            percentTarget = parseFloat(percentTarget).toFixed(1);
            console.log("Target percentage is: ", percentTarget, "%");

            // Move bellows
            $("#setPercentageZ").val(percentTarget);
            console.log("Sends the move Z bellows command.");
            moveBellows("Z");

            // Do this after every command
            $("#progressBar").css("width", "0px");
            $("#progress").html("0%");
            timeExecuted = new Date().getTime() / 1000;
            moving = "yes";
            executed = "no";
            waiting = "no";
            // console.log( "moving:",moving,"executed:",executed,"waiting:",waiting )
        }

        // ^^^ The command "if" series ends here ^^^

        // Check if bellows target position has been reached
        if (moving == "yes" && executed == "no" && waiting == "no" && ($('#moveStatus').html() != "-" || new Date().getTime() / 1000.00 - timeExecuted < 1)) {
            // Case 1: Bellows are currently moving, do nothing
        }
        else if (moving == "yes" && executed == "no" && waiting == "no" && $('#moveStatus').html() == "-") {
            // Case 2: Bellows finished moving, command complete, start waiting
            timeExecuted = new Date().getTime() / 1000;
            moving = "no";
            executed = "yes";
            waiting = "yes";
            $("#command" + line).append(" &#10003;");
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
            console.log("Now goto next line", line);

            if (line == commandsArray.length) {
                console.log("End of method.");
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
                    console.log("Moving on to next sample.");
                    $("#sample" + sample).prepend("&#9758; ");
                    let sampleName = $('#sample' + sample).html().split(",")[1];
                    let methodFileName = $('#sample' + sample).html().split(",")[2];
                    $('#sampleName').val(sampleName);
                    loadMethod(methodFileName);
                    line = 0;
                    cycle = 0;
                    $("#timeMeasurementStarted").html(parseInt(new Date().getTime() / 1000));
                    createFolder();
                    console.log("Folder for next sample created.");
                    $("#methodStatus").html('Method running');
                    $('#cycle').html("0");

                    $("#refgasTargetPressure").html("Reference target pressure");
                    $("#sample_pCO2").html("Sample pCO<sub>2</sub>");
                    $("#reference_pCO2").html("Reference pCO<sub>2</sub>");
                    $("#correction_pCO2").html("1.000");
                }
                else {
                    // No next sample, sequence finished
                    console.log("No more sample to be run.");
                    sample = 0;
                    line = 0;
                    cycle = 0;
                    $('#cycle').html("9¾");

                    $("#refgasTargetPressure").html("Reference target pressure");
                    $("#sample_pCO2").html("Sample pCO<sub>2</sub>");
                    $("#reference_pCO2").html("Reference pCO<sub>2</sub>");
                    $("#correction_pCO2").html("1.000");
                }
            }
        }
    }

    $('#cycleJS').text('ICE ' + cycleJS);
    cycleJS++;
}, 50);