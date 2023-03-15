// This JavaScript file...
// is the main program loop

var cmd = "";
var timeExecuted = 0;   // Time when cmd has been sent to Arduino
var line = 0;
var moving = "no";
var waiting = "no";     // Wait for the delay to goto next command
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
            // IMPORTANT: if you add/remove elements below, you have to update the lenght filter in the writeLogfile.php!
            // Unix -> Mac timestamp, TILDAS uses Mac timestamp
            logData.push([parseInt(currentTime + 2082844800 + 3600), parseFloat($('#housingT').html()), parseFloat($('#housingTargetT').val()), parseFloat($('#roomRH').html()), $('#percentageXsteps').html(), $('#percentageYsteps').html(), $('#percentageZsteps').html(), $('#pressureX').html(), $('#pressureY').html(), $('#pressureA').html(), $('#edwards').html().trim(), parseFloat($('#fanSpeed').html()), parseFloat($('#roomTemperature').html()), parseFloat($('#roomHumidity').html())]);

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

        // This command waits until A target pressure is reached, than closes valves
        else if (commandsArray[line][0] == "A" && commandsArray[line][1] == "X" && executed == "yes" && moving == "no" && waiting == "no") {
            // Do this before every command in method
            if ($("#command" + (line + 2)).length) { $("#command" + (line + 2))[0].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' }); }
            $("#command" + line).prepend("&#9758; ");
            cmd = "AX" + parameterArray[line];

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
            if (parseFloat($("#cellTargetPressure").html()) > 0) {
                var pTarget = parseFloat($("#cellTargetPressure").html());
            }
            else {
                var pTarget = parseFloat(parameterArray[line]); // Normally about 40 Torr
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
            // Case 1
            // console.log( new Date().getTime() / 1000, "Case 1: Bellows are currently moving, nothing changed." );
        }
        else if (moving == "yes" && executed == "no" && waiting == "no" && $('#moveStatus').html() == "-") {
            // Case 2
            timeExecuted = new Date().getTime() / 1000;
            moving = "no";
            executed = "yes";
            waiting = "yes";
            $("#command" + line).append(" &#10003;");
        }
        else if (moving == "no" && executed == "yes" && waiting == "yes" && $('#moveStatus').html() == "-" && new Date().getTime() / 1000 - timeExecuted < timeArray[line]) {
            // Case 3
            // Now move the progress bar
            var pbpc = (new Date().getTime() / 1000 - timeExecuted) * 307 / timeArray[line];
            $('#progressBar').css("width", pbpc + "px");
            $("#progress").html(parseInt(pbpc / 3.07) + "%");
        }
        else {
            // Case 4
            // console.log( new Date().getTime() / 1000, "Case 4: Jumps to next sample." );
            waiting = "no";
            // Goto next line in method
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
                // Move to the next sample (by index)
                sample++;
                // Check if this element exists
                if ($('#sample' + sample).length) {
                    // OK, next sample exists, read out sample name & method file name now
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