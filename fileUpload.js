// This JavaScript file...
// declares the functions that are used to upload the method and sequence CSV files

var commandsArray = [];
var parameterArray = [];
var timeArray = [];
var colArr = [];

$('body').on('change', '#uploadMethod', function () {
    var data = new FormData();
    data.append('file', this.files[0]);
    $.ajax({
        url: 'uploadMethod.php',
        data: data,
        type: 'POST',
        processData: false,
        contentType: false,
        success: function (result) {
            console.log("Method uploaded successfully.");
        }
    });
});

function loadMethod(methodFileName) {

    var xM = methodFileName;

    $.ajax({
        url: 'uploadMethod.php',
        data: { methodFileName: xM },
        type: 'POST',
        success: function (result) {

            console.log("Method loaded successfully.");

            $('#method').empty();
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
                $("#method").append("<div id='command" + i + "' class='command' style='background-color: white;position:relative;top:" + (vertical + i * 1) + "px;left:0px;'>" + i + ": " + commandsArray[i] + " &rarr; " + parameterArray[i] + " &rarr; wait " + timeArray[i] + " s</div>");
            }
            vertical = vertical + 0;
        }
    });
};

$('body').on('change', '#uploadSequence', function() {

    var data = new FormData();
    data.append('file', this.files[0]);

    $.ajax({
        url: 'uploadSequence.php',
        data: data,
        type: 'POST',
        processData: false,
        contentType: false,
        success: function(result) {

            console.log( "Sequence sucessfully uploaded.");
            
            // Delete all elements in div sequence
            $('#sequence').empty();
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
                    $('#sampleName').val(sampleNameArr[i]);
                }
                $("#sequence").append("<div id='sample" + i + "' class='command' style='background-color: white;position:relative;top:" + (vertical + i * 1) + "px;left:0px;'>" + i + "," + sampleNameArr[i] + "," + methodFileArr[i] + "</div>");
            }
            vertical = vertical + 0;
        }
    });
});