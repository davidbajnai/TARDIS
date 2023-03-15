// This JavaScript file...
// declares the functions which respond to specific commands

// Show results button
function showResults() {
    window.open('http://192.168.1.1/isotope/Isotopes_data_list.php?MaxNumber=20&SampleTypeSearch=CO2', '_blank');
}

// Start sequence button
function startSequence() {
    const timeMeasurementStarted = parseInt(new Date().getTime() / 1000);
    $("#timeMeasurementStarted").html(timeMeasurementStarted);
    createFolder();
    $("#methodStatus").html("Method running");
    $("#sample0").prepend("&#9758; ");
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

// Create a folder for the data
function createFolder() {
    console.log("Creating folder.");
    $.ajax({
        type: "POST",
        url: 'createFolder.php',
        async: false,
        data: {
            date: $('#timeMeasurementStarted').html(), // Date and time when measurement started in UNIX format & UTC timezone
            sampleName: $('#sampleName').val()
        },
        success: function (response) {
            console.log(response);
            $('#folderName').html(response);
        }
    });
}

// Write logfile.csv
function writeLogfile(logData, folderName) {
    $.ajax({
        type: "POST",
        url: 'writeLogfile.php',
        data: {
            sampleName: $('#sampleName').val(),
            logData: logData,
            folderName: folderName
        },
        success: function (response) {
            console.log(response);
        }
    });
}

// Copy all files with a date younger than timeMeasurementStarted
function copyFiles() {
    console.log("Copy files.");
    $.ajax({
        type: "POST",
        url: 'copyFiles.php',
        async: false,
        data: {
            date: $('#timeMeasurementStarted').html(), // Date and time when measurement started in UNIX format & UTC timezone
            folderName: $('#folderName').html() // Something like: Results/230306_123421_sampleName
        },
        success: function (response) {
            console.log(response);
        }
    });
}

function evaluateData() {
    console.log("Starting evaluateData.php")
    $.ajax({
        type: "POST",
        url: "evaluateData.php",
        async: true,
        data: {
            sampleName: $('#folderName').html(),
            userName: $('#userName').val(),
            polynomial: $('#polynomial').val()
        }
    }).done(function (result) {
        console.log(result);
        console.log("Data gotten from evaluateData.php");
    });
}

function startWritingData() {
    cmd = 'TWD1';
    console.log(cmd);
}

function stopWritingData() {
    cmd = 'TWD0';
    console.log(cmd);
}

function setHousingTCmd(setTemp) {
    var temp = parseFloat($(setTemp).val()).toFixed(3);
    cmd = 'FS' + temp;
    console.log(cmd);
}

function startingPosition() {
    cmd = 'KL';
    console.log(cmd);
}

// Move bellows
function moveBellows(bellow) {
    $('#moveStatus').html('M' + bellow);
    const percentage = parseFloat($('#setPercentage' + bellow).val()).toFixed(1);
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

// Fetch the status string from sendCommand.php
// Send a command to the Arduino or the TILDAS via sendCommand.php
function sendCommand(cmd) {
    $.ajax({
        type: "POST",
        url: 'sendCommand.php',
        data: { cmd: cmd },
        async: false,
        success: function (response) {

            // Split the status string
            const statusArr = response.split(","); // The status array is received from serialComm.py via sendCommand.php
            
            $('#moveStatus').html(statusArr[1]);

            // Display some images based on moveStatus
            if (statusArr[1] == "AX" && $('#loadingA').attr('src') != 'Images/loading.gif') {
                $('#loadingA').attr('src', 'Images/loading.gif');
            }
            else if (statusArr[1] != "AX") {
                $('#loadingA').attr('src', "");
            }

            if (statusArr[1] == "MX" && $('#motorX').attr('src') == 'Images/standing_motor.gif') {
                $('#motorX').attr('src', 'Images/rotating_motor.gif');
            }
            else if (statusArr[1] == "MY" && $('#motorY').attr('src') == 'Images/standing_motor.gif') {
                $('#motorY').attr('src', 'Images/rotating_motor.gif');
            }
            else if (statusArr[1] == "MZ" && $('#motorZ').attr('src') == 'Images/standing_motor.gif') {
                $('#motorZ').attr('src', 'Images/rotating_motor.gif');
            }
            else if (statusArr[1] == "-" && ($('#motorX').attr('src') == 'Images/rotating_motor.gif' || $('#motorY').attr('src') == 'Images/rotating_motor.gif' || $('#motorZ').attr('src') == 'Images/rotating_motor.gif')) {
                $('#motorX').attr('src', 'Images/standing_motor.gif');
                $('#motorY').attr('src', 'Images/standing_motor.gif');
                $('#motorZ').attr('src', 'Images/standing_motor.gif');
            }

            // X bellows
            var percentageX = statusArr[3];
            $('#bellowsX').css('height', parseInt( 10 + 0.9 * percentageX ) + 'px');
            $('#percentageX').html( parseFloat(percentageX).toFixed(1) );
            $('#percentageX').css("color","gray");
            $('#percentageXsteps').html( parseFloat(statusArr[2]).toFixed(2) );
            $('#stepsX').html( statusArr[2] + ' steps' );

            // Y bellows
            var percentageY = statusArr[5];
            $('#bellowsY').css('height', (10 + 0.9 * percentageY) + 'px');
            $('#percentageY').html(parseFloat(percentageY).toFixed(1));
            $('#percentageY').css("color", "gray");
            $('#percentageYsteps').html(parseFloat(statusArr[4]).toFixed(2));
            $('#stepsY').html(statusArr[4] + ' steps');

            // Z bellows
            $('#percentageZsteps').html(parseFloat(statusArr[7]).toFixed(1));
            $('#stepsZ').html(statusArr[6]); //Steps
            $('#bellowsZ').css('height', parseFloat(10 + 0.9 * statusArr[7]).toFixed(1) + 'px');

            if (statusArr[6] != 7980 && $('#warningZ').attr('src') != 'Images/warning.png') {
                $('#warningZ').attr('src', 'Images/warning.png');
            }
            else if (statusArr[6] == 7980) {
                $('#warningZ').attr('src', "");
            }

            // X baratron
            var pressureX = parseFloat(statusArr[8]);
            $('#pressureX').html(pressureX.toFixed(3));

            // Y baratron
            var pressureY = parseFloat(statusArr[9]);
            $('#pressureY').html(pressureY.toFixed(3));

            // A baratron
            var pressureA = parseFloat(statusArr[10]);
            $('#pressureA').html(pressureA.toFixed(1));

            // Valve status
            var valveArray = statusArr[12];
            const positions = [
                "horizontal",   // V01
                "vertical",     // V02
                "horizontal",
                "horizontal",
                "vertical",
                "horizontal",
                "vertical",
                "vertical",
                "horizontal",
                "horizontal",
                "vertical",
                "horizontal",
                "vertical",
                "vertical",
                "vertical",
                "vertical",
                "horizontal",
                "horizontal",
                "horizontal",
                "horizontal",   // V20
                "horizontal",   // V21
                "horizontal",
                "vertical",
                "vertical",
                "vertical",
                "vertical",
                "horizontal",
                "horizontal",
                "horizontal",
                "horizontal",
                "horizontal",
                "horizontal"    // V32
            ];
            var i = 1;
            var n = '0';
            while (i <= 33) {
                if (i < 10) {
                    n = "0";
                }
                else {
                    n = "";
                }
                $('#V' + n + i.toString() + '_label').html(valveArray.charAt(i - 1));
                if (valveArray.charAt(i - 1) == '0') {
                    $('#V' + n + i.toString()).attr('src', 'Images/' + positions[i - 1] + '_closed.png');
                }
                else {
                    $('#V' + n + i.toString()).attr('src', 'Images/' + positions[i - 1] + '_open.png');
                }
                i = i + 1;
            }

            // Box humidity
            var roomRH = statusArr[13];
            $('#roomRH').html(roomRH);

            // Box temperature
            var housingT = statusArr[14];
            $('#housingT').html(housingT);

            // Fan speed
            var fanSpeed = statusArr[15];
            $('#fanSpeed').html(fanSpeed);

            // Cell pressure from the TILDAS
            var baratronTorr = parseFloat(statusArr[16]) * 1 + (0.406 + 0.223) / 1.33322;
            // var baratronTorr = parseFloat(statusArr[16]);
            $('#baratron').html(baratronTorr.toFixed(3));

            // CO2 mixing ratios from the TILDAS
            var mr1 = statusArr[17];
            $('#mr1').html(parseFloat(mr1).toFixed(1));
            var mr2 = statusArr[18];
            $('#mr2').html(parseFloat(mr2).toFixed(1));
            var mr3 = statusArr[19];
            $('#mr3').html(parseFloat(mr3).toFixed(1));
            var mr4 = statusArr[20];
            $('#mr4').html(parseFloat(mr4).toFixed(1));

            // Edwards vacuum gauge
            var edwards = statusArr[21];
            $('#edwards').html(parseFloat(edwards).toFixed(4));

            // Room humidity
            var roomHumidity = statusArr[22];
            $('#roomHumidity').html(roomHumidity);

            // Room temperature
            var roomTemperature = statusArr[23];
            $('#roomTemperature').html(roomTemperature);

            // Reset the command string
            cmd = "";

        },
        error: function (xhr, status, error) {
            console.error(error);
        }
    });
}