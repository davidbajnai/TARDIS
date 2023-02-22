<!DOCTYPE html>
<html>
	<head>
		<meta name="viewport" content="width=device-width, initial-scale=1.0">
		<link rel = "stylesheet" type = "text/css" href = "stylesheet.css">
		<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
		<script>
			var cmd = "";

			function wait(sec){
   				var start = new Date().getTime();
   				var end = start;
   				while( end < start + sec * 1000 )
				{
     				end = new Date().getTime();
  				}
			}

			function toggleValve(valve,status) {
				// cmd = "Noch mehr von PHP";
				if( status == '0' || status == 'O' )
 				{
					cmd = valve + 'O';
				}
				else if( status == '1' || status == 'C' )
 				{
					cmd = valve + 'C';
				}
				else
 				{
					cmd = '';
					alert('Invalid command, could not determine the current status of the valve.');
				}
			}

			function createFolder() {
				// Create a folder for the data
				$.ajax({
						type: "POST",
						url: 'createFolder.php',
						async: false,
						data: {
							sampleName: $('#sampleName').val()
							},
						success: function(response){
							console.log(response);
							$('#folderName').html( response );
							}
						});
			}

			function writeLogfile( logData,folderName ) {
				// Write logdata
				$.ajax({
						type: "POST",
						url: 'writeLogfile.php',
						data: {
							sampleName: $('#sampleName').val(),
							logData: logData,
							folderName: folderName
							},
						success: function( response ){
							console.log( response );
							// $('#folderName').html(response);
							}
						});
			}

			function copyFiles() {
				console.log( "Copy files." );
				// Copy all files with a date younger than date
				$.ajax({
						type: "POST",
						url: 'copyFiles.php',
						async: false,
						data: {
							date: $('#timeMeasurementStarted').html(),
							folderName: $('#folderName').html()
							},
						success: function(response){
							console.log(response);
							}
						});
			}

			function evaluateData() {
				console.log( "Run Python program." )
				$.ajax({
  					type: "POST",
  					url: "evaluateData.php",
					async: true,
  					data: {
						  sampleName: $('#folderName').html(),
						  userName: $('#userName').val(),
						  polynomial: $('#polynomial').val()
						}
				}).done(function( result ) {
   					// Do something
					console.log( result );
					console.log( "Data gotten from evaluateData.php" );
				});
			}
			
			function startWritingData() {
				cmd = 'TWD1';
				console.log( cmd );
			}
			
			function stopWritingData() {
				cmd = 'TWD0';
				console.log( cmd );
			}

			function setHousingTCmd(settemp) {
				var temp = parseFloat( $(settemp).val() ).toFixed(3);
				cmd = 'FS' + temp;
				console.log( cmd );
			}
			function setPIDStatus(status) {
				cmd = 'TC' + status;
				console.log( cmd );
			}
			function startingPosition() {
				cmd = 'KL';
				console.log( cmd );
			}

			function moveBellows( bellow ) {
				$('#moveStatus').html('M' + bellow);
				var percentage = parseFloat( $('#setPercentage' + bellow).val() ).toFixed(1);
				if( percentage < 0 )
				{
					percentage = 0.0;
					$('#setPercentage' + bellow).val( "0.0" );
				}
				if( percentage > 100 )
				{
					percentage = 100.0;
					$('#setPercentage' + bellow).val( "100.0" );
				}
				cmd = bellow + 'P' + percentage;
				console.log( cmd );
			}

			function getStatus( cmd )
			{
				$.ajax({
					type: "POST",
					url: 'getStatus.php',
					data: {cmd: cmd},
					async: false,
					success: function( response ){
						// The following status string received
						// console.log(response);
						// Now split the status string
						const statusArr = response.split(",");
						//         0           1    2    3     4     5   6  7    8   9  10  11            12                   13     14     15     16         17          18          19     20
						// 2022-02-18 21:50:20,-,34921,55.94,51636,82.65,0,0.00,2.5,0.6,2.1,S,00000000000000000000000000000000,25.124,23.389,50,66.243,51.6351e+04,44.8385e+04,47.1265e+04,97.5315e+03
						$('#moveStatus').html( statusArr[1] );
						// alert( statusArr[1] );
						if( statusArr[1] == "MX" && $('#motorX').attr('src') == 'images/standing_motor.gif' )
						{
							$('#motorX').attr('src','images/rotating_motor.gif');
						}
						else if( statusArr[1] == "MY" && $('#motorY').attr('src') == 'images/standing_motor.gif' )
						{
							$('#motorY').attr('src','images/rotating_motor.gif');
						}
						else if( statusArr[1] == "MZ" && $('#motorZ').attr('src') == 'images/standing_motor.gif' )
						{
							$('#motorZ').attr('src','images/rotating_motor.gif');
						}
						else if( statusArr[1] == "-" && ( $('#motorX').attr('src') == 'images/rotating_motor.gif' || $('#motorY').attr('src') == 'images/rotating_motor.gif' || $('#motorZ').attr('src') == 'images/rotating_motor.gif' ) )
						{
							$('#motorX').attr('src','images/standing_motor.gif');
							$('#motorY').attr('src','images/standing_motor.gif');
							$('#motorZ').attr('src','images/standing_motor.gif');
						}
						var percentageX = statusArr[3];
						// X bellows
						$('#bellowsX').css('height', parseInt( 10 + 0.9 * percentageX ) + 'px');
						$('#percentageX').html( parseFloat(percentageX).toFixed(1) );
						$('#percentageX').css("color","gray");
						$('#percentageXsteps').html( parseFloat(statusArr[2]).toFixed(2) );
						$('#stepsX').html( statusArr[2] + ' steps' );
						// Y bellows
						var percentageY = statusArr[5];
						$('#bellowsY').css('height', ( 10 + 0.9 * percentageY ) + 'px');
						$('#percentageY').html( parseFloat(percentageY).toFixed(1) );
						$('#percentageY').css("color","gray");
						$('#percentageYsteps').html( parseFloat(statusArr[4]).toFixed(2) );
						$('#stepsY').html( statusArr[4] + ' steps' );
						// Z bellows
						$('#percentageZsteps').html( parseFloat(statusArr[7]).toFixed(1) );
						$('#stepsZ').html( statusArr[6] + ' steps' );
						$('#bellowsZ').css('height',parseFloat( 10 + 0.9 * statusArr[7] ).toFixed(1) + 'px');
						// X baratron
						var pressureX = parseFloat(statusArr[8]);
						$('#pressureX').html( pressureX.toFixed(3) );
						// Y baratron
						var pressureY = parseFloat(statusArr[9]);
						$('#pressureY').html( pressureY.toFixed(3) );
						// A baratron
						var pressureA = parseFloat(statusArr[10]);
						$('#pressureA').html( pressureA.toFixed(1) );
						// Valves
						var valveArray = statusArr[12];
						const positions = [
							"horizontal",
							"vertical",
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
							"horizontal",
							"horizontal",
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
							"horizontal"
						];
						// Valve status
						var i = 1;
						var n = '0';
						while(i < 32)
						{
							if( i < 10 )
							{
								n = "0";
							}
							else
							{
								n = "";
							}
							$('#V' + n + i.toString() + '_label').html( valveArray.charAt(i - 1) );
							if(valveArray.charAt(i - 1) == '0')
							{
								$('#V' + n + i.toString()).attr('src','images/' + positions[i-1] + '_closed.png');
							}
							else
							{
								$('#V' + n + i.toString()).attr('src','images/' + positions[i-1] + '_open.png');
							}
							i = i + 1;
						}

						// Room humidity
						var roomH = statusArr[24];
						$('#roomH').html( roomH );
						// Room temperature
						var roomT = statusArr[23];
						$('#roomT').html( roomT );
						// Room pressure
						var roomP = statusArr[25];
						$('#roomP').html( roomP );

						// Box humidity
						var roomRH = statusArr[13];
						$('#roomRH').html( roomRH );
						// Box temperature
						var housingT = statusArr[14];
						$('#housingT').html( housingT );
						var fanSpeed = statusArr[15];
						$('#setFanSpeed').val(fanSpeed);
						var baratronMbar = statusArr[16] * 1.33322 + 0.406 + 0.223;
						var baratronTorr = statusArr[16] * 1 + (0.406+0.223)/1.33322;
						$('#baratron').html( baratronTorr.toFixed(3) );
						// Absorption lines and CO2 concentrations from spectrometer
						var mr1 = statusArr[17];
						$('#mr1').html( '<sup>12</sup>C<sup>16</sup>O<sup>17</sup>O: ' + Math.round( Number(mr1)/1000 ) + ' ppmv' );
						var mr2 = statusArr[18];
						$('#mr2').html( '<sup>12</sup>C<sup>16</sup>O<sup>18</sup>O: ' + Math.round( Number(mr2)/1000 ) + ' ppmv' );
						var mr3 = statusArr[19];
						$('#mr3').html( '<sup>12</sup>C<sup>16</sup>O<sup>16</sup>O: ' + Math.round( Number(mr3)/1000 ) + ' ppmv' );
						var mr4 = statusArr[20];
						$('#mr4').html( 'free path CO<sub>2</sub>: ' + Math.round( Number(mr4)/1000 ) + ' ppmv' );
						var edwards = statusArr[22];
						$('#edwards').html( edwards );
						var CellTemperature =  statusArr[21]-273.15;
						$('#CellTemperature').html( CellTemperature.toFixed(3) );
						var d17O = ((mr1/mr3) / 1.08 - 1) * 1000;
						var d18O = ((mr2/mr3) / 1.06 - 1) * 1000;
						$('#d18O').html( 'δ<sup>18</sup>O: ' + d18O.toFixed(1) + "‰");
						var D17O = d17O - 0.528 * d18O;
						$('#D17O').html( "Δ<sup>'17</sup>O: " + D17O.toFixed(3) + "‰");	
						// Reset the command string
						cmd = "";
					},
					error: function(xhr, status, error){
						console.error(xhr);
					}
				});
			}

			getStatus();


			// Stuff related to the clock

			// setInterval(setDate, 1000);

			// setDate(); // Put this later into the loop

			
		</script>

		<script>
			var seconds = 0;
			var minutes = 0;
			var hour = 0;
			var hourAngle = 0;
			const radiusHour = 31;
			const radiusMinutes = 42;
			const radiusSeconds = 42;
			function pad(num, size)
			{
			num = num.toString();
			while (num.length < size) num = "0" + num;
			return num;
			}
			function getTime()
			{
				var date = new Date;
				seconds = date.getSeconds();
				minutes = date.getMinutes();
				hour = date.getHours();
				minutesAngle = (minutes / 60 * 2 * Math.PI) - 0.5 * Math.PI;
				secondsAngle = (seconds / 60 * 2 * Math.PI) - 0.5 * Math.PI;
				hourAngle = ( hour / 12 * 2 * Math.PI + 1/12 * minutes / 60 * 2 * Math.PI ) - 0.5 * Math.PI;
				$('#digital').html( hour + ":" + pad(minutes,2) + ":" + pad(seconds,2) + "<br> Göttingen Hbf" );
				// Write on canvas
				var c = document.getElementById("myCanvas");
				var ctx = c.getContext("2d");
				ctx.clearRect(0, 0, c.width, c.height);
				ctx.lineCap = 'round';
				ctx.strokeStyle = 'black';
				// Draw circle
				ctx.beginPath();
				ctx.lineWidth = 2.8;
				ctx.arc(50, 50, 48, 0, 2 * Math.PI);
				ctx.stroke();

				// Draw tickmarks
				ctx.beginPath();
				for (let i = 0; i < 60; i++)
				{ 
					ticksAngle = i * 2 * Math.PI / 60;
					ctx.moveTo( 50 + 43 * Math.cos( ticksAngle ), 50 + 43 * Math.sin( ticksAngle ) );
					ctx.lineTo( 50 + 48 * Math.cos( ticksAngle ), 50 + 48 * Math.sin( ticksAngle ) );
				}
				ctx.lineWidth = 2.2;
				ctx.strokeStyle = '#061350';
				ctx.stroke();

				ctx.beginPath();
				for (let i = 0; i < 12; i++)
				{ 
					ticksAngle = i * 2 * Math.PI / 12;
					ctx.moveTo( 50 + 38 * Math.cos( ticksAngle ), 50 + 38 * Math.sin( ticksAngle ) );
					ctx.lineTo( 50 + 48 * Math.cos( ticksAngle ), 50 + 48 * Math.sin( ticksAngle ) );
				}
				ctx.lineWidth = 3;
				ctx.strokeStyle = '#061350';
				ctx.stroke();

				// Write hour
				ctx.strokeStyle = '#061350';
				ctx.beginPath();
				ctx.moveTo(50, 50); // Center
				ctx.lineTo( 50 + radiusHour * Math.cos( hourAngle ), 50 + radiusHour * Math.sin( hourAngle ) );
				ctx.lineWidth = 6;
				ctx.stroke();
				// Write minutes
				ctx.strokeStyle = '#061350';
				ctx.beginPath();
				ctx.moveTo(50, 50); // Center
				ctx.lineTo( 50 + radiusMinutes * Math.cos( minutesAngle ), 50 + radiusMinutes * Math.sin( minutesAngle ) );
				ctx.lineWidth = 5;
				ctx.stroke();

				// Write seconds
				
				ctx.beginPath();
				ctx.moveTo(50, 50); // Center
				ctx.strokeStyle = '#EC0016';
				ctx.lineTo( 50 + 23 * Math.cos( secondsAngle ), 50 + 23 * Math.sin( secondsAngle ) );
				ctx.lineWidth = 2;
				ctx.stroke();
				
				ctx.moveTo(50 + 33 * Math.cos( secondsAngle ), 50 + 33 * Math.sin( secondsAngle ));
				ctx.strokeStyle = '#EC0016';
				ctx.lineTo( 50 + radiusSeconds * Math.cos( secondsAngle ), 50 + radiusSeconds * Math.sin( secondsAngle ) );
				ctx.lineWidth = 2;
				ctx.stroke();
				
				ctx.beginPath();
				ctx.arc(50 + radiusSeconds / 1.5 * Math.cos( secondsAngle ), 50 + radiusSeconds / 1.5 * Math.sin( secondsAngle ), 5, 0, 2 * Math.PI);
				ctx.fillStyle = "#f0ecec00";
				ctx.fill();
				ctx.stroke();

				ctx.beginPath();
				ctx.strokeStyle = '#061350';
				ctx.fillStyle = "#061350";
				ctx.moveTo(50, 50); // Center
				ctx.arc(50, 50, 4, 0, 2 * Math.PI);
				ctx.fill();
				ctx.stroke();
			}
		</script>
	</head>
	<body>
		<!-- <h1>IR laser spectrometer</h1> -->
		<!-- <a href="http://192.168.1.242:8081">Show webcam</a> -->
<!--
		<span id="statusString" style="border:1px solid black;padding:3px;">undefined</span>
		2022-02-18 21:50:20,-,34921,55.94,51636,82.65,0,0.00,2.5,0.6,S,00000000000000000000000000000000,25.124,23.389,66.243,51.6351e+04,44.8385e+04,47.1265e+04,97.5315e+03
-->
		<div id="wrap" style="position:relative;border:1px solid black;width:2010px;height:840px;">
			<img src="images/schaltbild.png" style="position:absolute;top:5px;left:5px;" />
			<div id="sequence" style="overflow: scroll;padding-left:2px;padding-right:2px;position:absolute;top:110px;left:1370px;width:300px;height:160px;border:1px solid gray;"></div>
			<div id="method" style="overflow: scroll;padding-left:2px;padding-right:2px;position:absolute;top:273px;left:1370px;width:300px;height:300px;border:1px solid gray;"></div>
			<button onclick="startWritingData();" style="position:absolute;top:36px;left:585px;width:60px;height:30px;background-color:#BCBBB2;border-radius:3px; border: 1px solid black;">WD on</button>
			<button onclick="stopWritingData();" style="position:absolute;top:66px;left:585px;width:60px;height:30px;background-color:#BCBBB2;border-radius:3px; border: 1px solid black;">WD off</button>
			<span id="moveStatus" style="position:absolute;top:265px;left:1700px;width:140px;padding:3px;border:1px solid black;background-color:white;">-</span>
			<span id="cycleJS" style="position:absolute;top:35px;left:150px;height:30px;width:130px; border:4px solid #061350; font-family:monospace; color: #ffffff; background-color: #1455C0;padding-left:8px;padding-top:5px;">NaN</span>
			<div id="baratron" style="position:absolute;top:35px;left:660px;width:60px;padding:3px;border:1px solid black;background-color:white;">CellP </div>
				<p style="position:absolute;top:15px;left:730px;font-size:18px;color:white;">Torr (cell)</p>
			<div id="CellTemperature" style="position:absolute;top:75px;left:660px;width:60px;padding:3px;border:1px solid black;background-color:white;">CellT</div>
				<p style="position:absolute;top:55px;left:730px;font-size:18px;color:white;">°C (cell)</p>

			<div style="position:absolute;top:131px;left:725px;">
				<span style="position:relative;top:-35px;left:77px;">V01</span>
				<img id="V01" src="images/horizontal_closed.png" onclick="var status=$('#V01_label').html();toggleValve('V01',status);" style="width:50px;"/>
				<span id="V01_label" style="display:none;">undefined</span>
			</div>
			<div style="position:absolute;top:178px;left:685px;">
				<span style="position:relative;top:2px;left:77px;">V02</span>
				<img id="V02" src="images/vertical_closed.png" onclick="var status=$('#V02_label').html();toggleValve('V02',status);" style="width:50px;"/>
				<span id="V02_label" style="display:none;">undefined</span>
			</div>
			<div style="position:absolute;top:410px;left:480px;">
				<span style="position:relative;top:-35px;left:77px;">V03</span>
				<img id="V03" src="images/vertical_closed.png" onclick="var status=$('#V03_label').html();toggleValve('V03',status);" style="width:50px;"/>
				<span id="V03_label" style="display:none;">undefined</span>
			</div>
			<div style="position:absolute;top:410px;left:240px;">
				<span style="position:relative;top:-35px;left:77px;">V04</span>
				<img id="V04" src="images/vertical_closed.png" onclick="var status=$('#V04_label').html();toggleValve('V04',status);" style="width:50px;"/>
				<span id="V04_label" style="display:none;">undefined</span>
			</div>
			<div style="position:absolute;top:340px;left:410px;">
				<span style="position:relative;top:-35px;left:77px;">V05</span>
				<img id="V05" src="images/vertical_closed.png" onclick="var status=$('#V05_label').html();toggleValve('V05',status);" style="width:50px;"/>
				<span id="V05_label" style="display:none;">undefined</span>
			</div>
			<div style="position:absolute;top:410px;left:345px;">
				<span style="position:relative;top:-35px;left:77px;">V06</span>
				<img id="V06" src="images/vertical_closed.png" onclick="var status=$('#V06_label').html();toggleValve('V06',status);" style="width:50px;"/>
				<span id="V06_label" style="display:none;">undefined</span>
			</div>
			<div style="position:absolute;top:475px;left:410px;">
				<span style="position:relative;top:-35px;left:77px;">V07</span>
				<img id="V07" src="images/vertical_closed.png" onclick="var status=$('#V07_label').html();toggleValve('V07',status);" style="width:50px;"/>
				<span id="V07_label" style="display:none;">undefined</span>
			</div>
			<div style="position:absolute;top:475px;left:190px;">
				<span style="position:relative;top:-35px;left:77px;">V08</span>
				<img id="V08" src="images/vertical_closed.png" onclick="var status=$('#V08_label').html();toggleValve('V08',status);" style="width:50px;"/>
				<span id="V08_label" style="display:none;">undefined</span>
			</div>
			<div style="position:absolute;top:410px;left:905px;">
				<span style="position:relative;top:-35px;left:77px;">V09</span>
				<img id="V09" src="images/vertical_closed.png" onclick="var status=$('#V09_label').html();toggleValve('V09',status);" style="width:50px;"/>
				<span id="V09_label" style="display:none;">undefined</span>
			</div>
			<div style="position:absolute;top:410px;left:1150px;">
				<span style="position:relative;top:-35px;left:77px;">V10</span>
				<img id="V10" src="images/vertical_closed.png" onclick="var status=$('#V10_label').html();toggleValve('V10',status);" style="width:50px;"/>
				<span id="V10_label" style="display:none;">undefined</span>
			</div>
			<div style="position:absolute;top:345px;left:972px;">
				<span style="position:relative;top:-35px;left:77px;">V11</span>
				<img id="V11" src="images/vertical_closed.png" onclick="var status=$('#V11_label').html();toggleValve('V11',status);" style="width:50px;"/>
				<span id="V11_label" style="display:none;">undefined</span>
			</div>
			<div style="position:absolute;top:410px;left:1040px;">
				<span style="position:relative;top:-35px;left:77px;">V12</span>
				<img id="V12" src="images/vertical_closed.png" onclick="var status=$('#V12_label').html();toggleValve('V12',status);" style="width:50px;"/>
				<span id="V12_label" style="display:none;">undefined</span>
			</div>
			<div style="position:absolute;top:470px;left:972px;">
				<span style="position:relative;top:-35px;left:77px;">V13</span>
				<img id="V13" src="images/vertical_closed.png" onclick="var status=$('#V13_label').html();toggleValve('V13',status);" style="width:50px;"/>
				<span id="V13_label" style="display:none;">undefined</span>
			</div>
			<div style="position:absolute;top:472px;left:1190px;">
				<span style="position:relative;top:-35px;left:77px;">V14</span>
				<img id="V14" src="images/vertical_closed.png" onclick="var status=$('#V14_label').html();toggleValve('V14',status);" style="width:50px;"/>
				<span id="V14_label" style="display:none;">undefined</span>
			</div>
			<div style="position:absolute;top:710px;left:686px;">
				<span style="position:relative;top:-35px;left:77px;">V15</span>
				<img id="V15" src="images/vertical_closed.png" onclick="var status=$('#V15_label').html();toggleValve('V15',status);" style="width:50px;"/>
				<span id="V15_label" style="display:none;">undefined</span>
			</div>
			<div style="position:absolute;top:595px;left:686px;">
				<span style="position:relative;top:-35px;left:77px;">V16</span>
				<img id="V16" src="images/vertical_closed.png" onclick="var status=$('#V16_label').html();toggleValve('V16',status);" style="width:50px;"/>
				<span id="V16_label" style="display:none;">undefined</span>
			</div>
			<div style="position:absolute;top:131px;left:843px;">
				<span style="position:relative;top:-35px;left:77px;">V17</span>
				<img id="V17" src="images/vertical_closed.png" onclick="var status=$('#V17_label').html();toggleValve('V17',status);" style="width:50px;"/>
				<span id="V17_label" style="display:none;">undefined</span>
			</div>
			<div style="position:absolute;top:410px;left:145px;">
				<span style="position:relative;top:-35px;left:77px;">V18</span>
				<img id="V18" src="images/vertical_closed.png" onclick="var status=$('#V18_label').html();toggleValve('V18',status);" style="width:50px;"/>
				<span id="V18_label" style="display:none;">undefined</span>
			</div>
			<div style="position:absolute;top:231px;left:620px;">
				<span style="position:relative;top:-35px;left:77px;">V19</span>
				<img id="V19" src="images/vertical_closed.png" onclick="var status=$('#V19_label').html();toggleValve('V19',status);" style="width:50px;"/>
				<span id="V19_label" style="display:none;">undefined</span>
			</div>
			<div style="position:absolute;top:231px;left:540px;">
			    <span style="position:relative;top:-35px;left:77px;">V20</span>
				<img id="V20" src="images/vertical_closed.png" onclick="var status=$('#V20_label').html();toggleValve('V20',status);" style="width:50px;"/>
				<span id="V20_label" style="display:none;">undefined</span>
			</div>
			<!-- <div style="position:absolute;top:26px;left:600px;">
			    <span style="position:relative;top:-35px;left:77px;">V21</span>
				<img id="V21" src="images/vertical_closed.png" onclick="var status=$('#V21_label').html();toggleValve('V21',status);" style="width:50px;"/>
				<span id="V21_label" style="display:none;">undefined</span>
			</div> -->
			<div style="position:absolute;top:410px;left:1230px;">
			    <span style="position:relative;top:-35px;left:77px;">V22</span>
				<img id="V22" src="images/vertical_closed.png" onclick="var status=$('#V22_label').html();toggleValve('V22',status);" style="width:50px;"/>
				<span id="V22_label" style="display:none;">undefined</span>
			</div>

			<div style="position:absolute;top:612px;left:1318px;">
			    <span style="position:relative;top:-35px;left:77px;">V23</span>
				<img id="V23" src="images/vertical_closed.png" onclick="var status=$('#V23_label').html();toggleValve('V23',status);" style="width:50px;"/>
				<span id="V23_label" style="display:none;">undefined</span>
			</div>
			<div style="position:absolute;top:612px;left:1408px;">
			    <span style="position:relative;top:-35px;left:77px;">V24</span>
				<img id="V24" src="images/vertical_closed.png" onclick="var status=$('#V24_label').html();toggleValve('V24',status);" style="width:50px;"/>
				<span id="V24_label" style="display:none;">undefined</span>
			</div>
			<div style="position:absolute;top:612px;left:1498px;">
			    <span style="position:relative;top:-35px;left:77px;">V25</span>
				<img id="V25" src="images/vertical_closed.png" onclick="var status=$('#V25_label').html();toggleValve('V25',status);" style="width:50px;"/>
				<span id="V25_label" style="display:none;">undefined</span>
			</div>
			<div style="position:absolute;top:612px;left:1588px;">
			    <span style="position:relative;top:-35px;left:77px;">V26</span>
				<img id="V26" src="images/vertical_closed.png" onclick="var status=$('#V26_label').html();toggleValve('V26',status);" style="width:50px;"/>
				<span id="V26_label" style="display:none;">undefined</span>
			</div>
			<div style="position:absolute;top:212px;left:843px;">
			    <span style="position:relative;top:-35px;left:77px;">V27</span>
				<img id="V27" src="images/vertical_closed.png" onclick="var status=$('#V27_label').html();toggleValve('V27',status);" style="width:50px;"/>
				<span id="V27_label" style="display:none;">undefined</span>
			</div>

			<img id="bellowsX" src="images/bellows.png" style="width:100px;height:60px;position:absolute;top:510px;left:295px;" />
			<img id="bellowsY" src="images/bellows.png" style="width:100px;height:60px;position:absolute;top:510px;left:1100px;" />
			<img id="bellowsZ" src="images/bellows.png" style="width:100px;height:60px;position:absolute;top:320px;left:688px;" />
			
			<span id="pressureX" style="position:absolute;top:350px;left:319px;background-color:white;border:1px solid black;width:50px;padding:3px;">NaN</span>
				<p style="position:absolute;top:308px;left:319px;font-size:18px;">X (mbar)</p>
			<span id="pressureY" style="position:absolute;top:350px;left:1128px;background-color:white;border:1px solid black;width:50px;padding:3px;">NaN</span>
				<p style="position:absolute;top:308px;left:1128px;font-size:18px;">Y (mbar)</p>
			<div id='pressureA' style="position:absolute;top:555px;left:612px;background-color:white;border:1px solid black;width:70px;padding:3px;"><em>NaN</em></div>
				<p style="position:absolute;top:513px;left:612px;font-size:18px;">A (torr)</p>

			<img id="motorX" src="images/standing_motor.gif" style="width:25px;position:absolute;top:625px;left:380px;" />
			<span id="percentageX" style="position:absolute;top:300px;left:1700px;background-color:white;border:1px solid black;width:50px;padding:3px;">NaN</span>
			<span id="percentageXsteps" style="position:absolute;top:625px;left:315px;background-color:white;border:1px solid black;width:50px;padding:3px;">NaN</span>
			<input type="text" id="setPercentageX" placeholder="100.0" style="position:absolute;top:655px;left:315px;background-color:white;border:1px solid black;width:50px;padding:3px;" />
			<button onclick="moveBellows('X');" style="position:absolute;top:655px;left:365px;background-color:#BCBBB2;border:1px solid black;width:50px;padding:3px;">Set X</button>

			<img id="motorY" src="images/standing_motor.gif" style="width:25px;position:absolute;top:625px;left:1184px;" />
			<span id="percentageY" style="position:absolute;top:330px;left:1700px;background-color:white;border:1px solid black;width:50px;padding:3px;">NaN</span>
			<span id="percentageYsteps" style="position:absolute;top:625px;left:1120px;background-color:white;border:1px solid black;width:50px;padding:3px;">NaN</span>
			<input type="text" id="setPercentageY" placeholder="100.0" style="position:absolute;top:655px;left:1120px;background-color:white;border:1px solid black;width:50px;padding:3px;" />
			<button onclick="moveBellows('Y');" style="position:absolute;top:655px;left:1169px;background-color:#BCBBB2;border:1px solid black;width:50px;padding:3px;">Set Y</button>
			
			<img id="motorZ" src="images/standing_motor.gif" style="width:25px;position:absolute;top:450px;left:755px;" />
			<span id="percentageZsteps" style="position:absolute;top:450px;left:690px;background-color:white;border:1px solid black;width:50px;padding:3px;">NaN</span>
			<span id="stepsZ" style="position:absolute;top:360px;left:1700px;background-color:white;border:1px solid black;width:94px;padding:3px;">NaN</span>
			<input type="text" id="setPercentageZ" placeholder="50.0" style="position:absolute;top:480px;left:690px;background-color:white;border:1px solid black;width:50px;padding:3px;" />
			<button onclick="moveBellows('Z');" style="position:absolute;top:480px;left:740px;background-color:#BCBBB2;border:1px solid black;width:50px;padding:3px;">Set Z</button>
			
			<span id="mr1" style="position:absolute;top:100px;left:1100px;background-color:white;border:1px solid black;width:180px;padding:3px;">mr1</span>
			<span id="mr2" style="position:absolute;top:130px;left:1100px;background-color:white;border:1px solid black;width:180px;padding:3px;">mr2</span>
			<span id="mr3" style="position:absolute;top:160px;left:1100px;background-color:white;border:1px solid black;width:180px;padding:3px;">mr3</span>
			<span id="mr4" style="position:absolute;top:190px;left:1100px;background-color:white;border:1px solid black;width:180px;padding:3px;">mr4</span>
			<span id="d18O" style="position:absolute;top:220px;left:1100px;background-color:white;border:1px solid black;width:180px;padding:3px;">d18O</span>
			<span id="D17O" style="position:absolute;top:250px;left:1100px;background-color:white;border:1px solid black;width:180px;padding:3px;">D17O</span>
			<span id="edwards" style="position:absolute;top:350px;left:858px;background-color:white;border:1px solid black;width:70px;padding:3px;">edwards</span>
				<p style="position:absolute;top:308px;left:858px;font-size:18px;">Edwards (mbar)</p>
			<!-- <canvas id="isotopeRatios" style="position:absolute;top:850px;left:50px;background-color:white;border:1px solid black;padding:3px;" width="600" height="200" ></canvas> -->
			<!-- <span id="ymaxLabel" style="position:absolute;top:850px;left:5px;background-color:white;border:1px solid black;padding:3px;">50 mbar</span> -->
			<!-- <span id="yminLabel" style="position:absolute;top:1050px;left:5px;background-color:white;border:1px solid black;padding:3px;">0 mbar</span> -->
			<div style="position:absolute;top:20px;left:1370px;">
				Sequence: <input type="file" id="uploadSequence">
			</div>
			<div style="position:absolute;top:40px;left:1370px;">
				Method: <input type="file" id="uploadMethod">
			</div>
			<div style="position:absolute;top:60px;left:1370px;">
				User: 
				<select name='userName' id='userName'>	
					<option value='David Bajnai'>Bajnai, David</option>
					<option value='Thierry Wasselin'>Wasselin, Thierry</option>
					<option value='Dennis Kohl'>Kohl, Dennis</option>
					<option value='Tommaso Di Rocco'>Di Rocco, Tommaso</option>
					<option value='Andreas Pack'>Pack, Andreas</option>
					<option value='Oliver Jaeger'>Jäger, Oliver</option>
					<option value='Dingsu Feng'>Feng, Dingsu</option>
					<option value='Fabian Zahnow'>Zahnow, Fabian</option>
					<option value='Praktikum'>Praktikum</option>
				</select>
			</div>
			<div style="position:absolute;top:80px;left:1370px;">
				Polynomial: <input type="number" id="polynomial" value="100">. degree
			</div>
			<div></div>
			<input id='housingTargetT' value=31.500 type="number" style="position:absolute;top:163px;left:30px;width: 60px;border:1px solid black;padding:2px;"/>
			<button onclick="setHousingTCmd(housingTargetT);" style="position:absolute;top:163px;left:80px;height:21px;width:40px;padding:0px;background-color:#BCBBB2;border-radius:3px; border: 1px solid black;">Set T</button>
			<button onclick="setPIDStatus(1);" style="position:absolute;top:163px;left:130px;width:50px;height:21px;padding:0px;background-color:#BCBBB2;border-radius:3px; border: 1px solid black;">Fan on</button>
			<button onclick="setPIDStatus(2);" style="position:absolute;top:163px;left:185px;width:50px;height:21px;padding:0px;background-color:#BCBBB2;border-radius:3px; border: 1px solid black;">Fan off</button>
			<input id='setFanSpeed' value=15 type="number" style="position:absolute;top:190px;left:30px;;background-color:white;border:1px solid black;width:60px;padding:2px;"/>
			<p style="position:absolute;top:170px;left:100px;font-size:18px;">fan speed</p>

			<div id='housingT' style="position:absolute;top:225px;left:30px;background-color:white;border:1px solid black;width:60px;padding:2px;">undefined</div>
			<p style="position:absolute;top:205px;left:100px;font-size:18px;">°C (box)</p>
			<div id='roomRH' style="position:absolute;top:252px;left:30px;background-color:white;border:1px solid black;width:60px;padding:2px;">undefined</div>
			<p style="position:absolute;top:235px;left:100px;font-size:18px;">%rH (box)</p>

			<div id='roomT' style="position:absolute;top:287px;left:30px;background-color:white;border:1px solid black;width:60px;padding:2px;">undefined</div>
			<p style="position:absolute;top:267px;left:100px;font-size:18px;">°C (room)</p>
			<div id='roomH' style="position:absolute;top:314px;left:30px;background-color:white;border:1px solid black;width:60px;padding:2px;">undefined</div>
			<p style="position:absolute;top:294px;left:100px;font-size:18px;">%rH (room)</p>
			<div id='roomP' style="position:absolute;top:341px;left:30px;background-color:white;border:1px solid black;width:60px;padding:2px;">undefined</div>
			<p style="position:absolute;top:321px;left:100px;font-size:18px;">mbar (room)</p>

			<div id='progressBar' style='position:absolute;top:20px;left:1700px;border:1px #5CD85A;width:0px;height:20px;background-color:#5CD85A;'></div>
			<div id='progress' style='position:absolute;top:20px;left:1700px;border:1px solid black;padding-left:5px;width:280px;height:20px;'>progress</div>
			<div id='methodStatus' style='position:absolute;top:50px;left:1700px;'>methodStatus</div>
			
			<button type='button' style='font-family:open-sans; font-size:24px;position:absolute;top:25px;left:1100px;height:60px; width:188px;border-radius:3px; background-color:#63A615;color:#ffffff;border:1px solid black;cursor:pointer;' onclick='createFolder();$("#methodStatus").html("Method running");var timeMeasurementStarted = parseInt( new Date().getTime() / 1000 );$("#timeMeasurementStarted").html( timeMeasurementStarted );$("#sample0").prepend("&#9758; ");'>Start method</button>
			<div style="position:absolute;top:80px;left:1700px;">
				<input type="text" id="sampleName" placeholder="Sample name">
			</div>
			<div id="timeMeasurementStarted" style="position:absolute;top:128px;left:1700px;width:200px;"><em>Time started</em></div>
			<div id="folderName" style="position:absolute;top:145px;left:1700px;width:200px;"><em>Folder name</em></div>
			<div id="cellTargetPressure" style="position:absolute;top:163px;left:1700px;width:200px;"><em>Cell target p</em></div>
			<div id="nitrogenTargetPressure" style="position:absolute;top:181px;left:1700px;width:200px;"><em>N2 target p</em></div>
			<div id="refgasTargetPressure" style="position:absolute;top:199px;left:1700px;width:200px;"><em>Refgas target p</em></div>
			<div id="samgasTargetPressure" style="position:absolute;top:218px;left:1700px;width:200px;"><em>Sample target p</em></div>
			<div id="cycle" style="position:absolute;top:45px;left:255px;width:200px;font-family:monospace;color:#ffffff;font-size:26px">9¾</div>

			<div style="position:absolute;top:85px;left:150px;height:30px;width:130px;border:4px solid #061350;font-family:monospace;color: #ffffff;background-color: #1455C0;padding-left:8px;padding-top:5px;" id="digital">Time</div>			
			
			<button onclick="startingPosition();" style="position:absolute;top:770px;left:30px;width:180px;height:30px;background-color:#BCBBB2;border-radius:3px; border: 1px solid black;">Starting Position</button>

			<canvas style="position:absolute;top:30px;left:30px;" id="myCanvas" width="100" height="100" style="border:1px solid black;"></canvas>

		</div>

		<!-- Ajax JavaScript File Upload Logic -->
		<script>
			var commandsArray = []; // Global variable
			var parameterArray = [];
			var timeArray = [];
			var colArr = [];

			$('body').on('change', '#uploadMethod', function() {
				var data = new FormData(); // Das ist unser Daten-Objekt ...
				data.append('file', this.files[0]); // ... an das wir unsere Datei anhängen
				$.ajax({
					url: 'uploadMethod.php', 	// Wohin soll die Datei geschickt werden?
					data: data,          		// Das ist unser Datenobjekt.
					type: 'POST',         		// HTTP-Methode, hier: POST
					processData: false,
					contentType: false,
					// und wenn alles erfolgreich verlaufen ist, schreibe eine Meldung
					// in das Response-Div
					success: function(result) {
						// One could do something here
					}
				});
			});

			function loadMethod( methodFileName ) {
				// alert(methodFileName);
				var xM = methodFileName;
				// var data = new FormData(); // das ist unser Daten-Objekt ...
				// data.append('file', this.files[0]); // ... an die wir unsere Datei anhängen
				$.ajax({
					url: 'loadMethod.php', // Wohin soll die Datei geschickt werden?
					data: {
						methodFileName: xM
						}, // Das ist unser Datenobjekt.
					type: 'POST',         // HTTP-Methode, hier: POST
					// processData: false,
					// contentType: false,
					// und wenn alles erfolgreich verlaufen ist, schreibe eine Meldung
					// in das Response-Div
					success: function( result ) {
						// Delete all elements in div sequence
						console.log( "loadMethod-Funktion",result );
						$('#method').empty();
						colArr = result.split("|");
						commandsArray = [];
						commandsArray = colArr[0].split(","); // This is a 1D array here
						console.log("commandsArray",commandsArray);
						parameterArray = colArr[1].split(","); // For valves: 0 = close, 1 = open, for bellows position in %
						console.log("parameterArray",parameterArray);
						timeArray = colArr[2].split(",");
						console.log("timeArray",timeArray);
						// Create list with commands on frontpanel
						var vertical = 0;
						for (let i = 0; i < commandsArray.length; i++) {
							$( "#method" ).append( "<div id='command" + i + "' class='command' style='background-color: white;position:relative;top:" + (vertical + i * 1) + "px;left:0px;'>" + i + ": " + commandsArray[i] + " &rarr; " + parameterArray[i] + " &rarr; wait " + timeArray[i] + " s</div>" );  
						}
						vertical = vertical + 0;
					}
				});
			};

			$('body').on('change', '#uploadSequence', function() {
				var data = new FormData(); // das ist unser Daten-Objekt ...
				data.append('file', this.files[0]); // ... an die wir unsere Datei anhängen
				$.ajax({
					url: 'uploadSequence.php', // Wohin soll die Datei geschickt werden?
					data: data,          // Das ist unser Datenobjekt.
					type: 'POST',         // HTTP-Methode, hier: POST
					processData: false,
					contentType: false,
					// und wenn alles erfolgreich verlaufen ist, schreibe eine Meldung
					// in das Response-Div
					success: function(result) {
						// Delete all elements in div sequence
						$('#sequence').empty();
						var colSeqArr = result.split("|");
						let sampleNameArr = colSeqArr[0].split(",");
						console.log( "Sample array", sampleNameArr );
						let methodFileArr = colSeqArr[1].split(",");
						console.log( "Methods file name array", methodFileArr );
						// Create list with commands on frontpanel
						var vertical = 0;
						for (let i = 0; i < sampleNameArr.length; i++) {
							if( i == 0 )
							{
								// Loading the method of the first sample
								console.log( "First method file:", methodFileArr[i] );
								loadMethod( methodFileArr[i] );
								$('#sampleName').val( sampleNameArr[i] );
							}
							$( "#sequence" ).append( "<div id='sample" + i + "' class='command' style='background-color: white;position:relative;top:" + (vertical + i * 1) + "px;left:0px;'>" + i + "," + sampleNameArr[i] + "," + methodFileArr[i] + "</div>" );  
						}
						vertical = vertical + 0;
					}
				});
			});
		</script>
		<script>
			// Method script
			var startTime = 0;
			var timeExecuted = 0; // Time when cmd has been sent to Arduino
			var line = 0;
			var moving = "no";
			var waiting = "no"; // Wait for the delay to goto next command
			var executed = "yes";
			var cycleJS = 0;
			var firstSample = "";
			var currentTimeOld = 0;
			var logData = [];
			var sample = 0;
			var diff = 0;
			var cycle = 0;

			// Interval function (equivalent to main loop of a program)
			setInterval(function()
				{	
					// console.log("Interval loop running");
					// Check every 30 sec the Temperature
					// Update all readings and, in case, send a command cmd
					getStatus( cmd );
					console.log('Current cmd',cmd);
					cmd = "";
					getTime(); // Sets the clock
					// Execute the individual commands from the method
					if( $("#methodStatus").text() == "Method running"  )
					{
						var currentTime = parseInt( new Date().getTime() / 1000 );
						// Write data to logfile
						if( currentTime % 5 == 0 && currentTime != currentTimeOld && $("#sampleName").val() != "" )
						{

							// IMPORTANT: if you add/remove elements below, you have to update the lenght filter in the writeLogfile.php!
							// Unix -> Mac timestamp, TILDAS uses Mac timestamp
							logData.push( [parseInt(currentTime + 2082844800),parseFloat( $('#housingT').html() ),parseFloat( $('#housingTargetT').val() ),parseFloat( $('#roomRH').html() ),$('#percentageXsteps').html(),$('#percentageYsteps').html(),$('#percentageZsteps').html(),$('#pressureX').html(),$('#pressureY').html(),$('#pressureA').html(),$('#edwards').html().trim(),$('#setFanSpeed').val(),parseFloat( $('#roomT').html()),parseFloat( $('#roomH').html()),parseFloat( $('#roomP').html())] );
							
							if( currentTime % 30 == 0 )
							{
								// Write data to logfile every ~ 2 min
								console.log("Writing to logfile now.");
								writeLogfile( logData,$('#folderName').html() );
								// Reset logfile array
								logData = [];
							}
							currentTimeOld = currentTime;
						}
						// Valve commands V03 1
						if( commandsArray[line][0] == "V" && executed == "yes" && moving == "no" && waiting == "no" )
						{
							// Do this before every command in method
							if( $("#command" + (line+2)).length ){ $("#command" + (line+2))[0].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' }); }
							$("#command" + line).prepend("&#9758; ");
							// Valve that needs to be switched
							if( parameterArray[line] == 0 )
							{
								toggleValve(commandsArray[line],"1");
							}	
							else
							{
								toggleValve(commandsArray[line],"0");
							}
							// Do this after every command
							timeExecuted = new Date().getTime() / 1000;
							moving = "no";
							executed = "yes";
							waiting = "yes";
							$("#command" + line).append(" &#10003;");
							console.log('Command',commandsArray[line],timeExecuted,'started and finished.');
						}
						// Set housing temperature
						else if( commandsArray[line][0] == "F" && commandsArray[line][1] == "S" && executed == "yes" && moving == "no" && waiting == "no" )
						{
							// Do this before every command in method
							if( $("#command" + (line+2)).length ){ $("#command" + (line+2))[0].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' }); }
							$("#command" + line).prepend("&#9758; ");
							cmd = "FS" + parameterArray[line];
							// Do this after every command
							timeExecuted = new Date().getTime() / 1000;
							moving = "no";
							executed = "yes";
							waiting = "yes";
							$("#command" + line).append(" &#10003;");
							console.log('Command',commandsArray[line],timeExecuted,'started and finished.');
						}

						// Set fan ON /OFF
						else if( commandsArray[line][0] == "T" && commandsArray[line][1] == "C" && executed == "yes" && moving == "no" && waiting == "no" )
						{
							// Do this before every command in method
							if( $("#command" + (line+2)).length ){ $("#command" + (line+2))[0].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' }); }
							$("#command" + line).prepend("&#9758; ");
							cmd = "TC" + parameterArray[line];
							// Do this after every command
							timeExecuted = new Date().getTime() / 1000;
							moving = "no";
							executed = "yes";
							waiting = "yes";
							$("#command" + line).append(" &#10003;");
							console.log('Command',commandsArray[line],timeExecuted,'started and finished.');
						}

						// Reset valves to starting position
						else if( commandsArray[line][0] == "K" && commandsArray[line][1] == "L" && executed == "yes" && moving == "no" && waiting == "no" )
						{
							// Do this before every command in method
							if( $("#command" + (line+2)).length ){ $("#command" + (line+2))[0].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' }); }
							$("#command" + line).prepend("&#9758; ");
							cmd = "KL" + parameterArray[line];
							// Do this after every command
							timeExecuted = new Date().getTime() / 1000;
							moving = "no";
							executed = "yes";
							waiting = "yes";
							$("#command" + line).append(" &#10003;");
							console.log('Command',commandsArray[line],timeExecuted,'started and finished.');
						}

						// Write cell pressure for the first sample on frontpanel "WC <no parameter>"
						else if( commandsArray[line][0] == "W" && commandsArray[line][1] == "C" && executed == "yes" && moving == "no" && waiting == "no" )
						{
							// Do this before every command in method
							if( $("#command" + (line+2)).length ){ $("#command" + (line+2))[0].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' }); }
							$("#command" + line).prepend("&#9758; ");
							$("#cellTargetPressure").html( $("#baratron").html() );
							// Do this after every command
							timeExecuted = new Date().getTime() / 1000;
							moving = "no";
							executed = "yes";
							waiting = "yes";
							$("#command" + line).append(" &#10003;");
							console.log('Command',commandsArray[line],timeExecuted,'started and finished.');
						}

						// Write nitrogen pressure for the first sample on the frontpanel "WA <no parameter>"
						else if( commandsArray[line][0] == "W" && commandsArray[line][1] == "A" && executed == "yes" && moving == "no" && waiting == "no" )
						{
							// Do this before every command in method
							if( $("#command" + (line+2)).length ){ $("#command" + (line+2))[0].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' }); }
							$("#command" + line).prepend("&#9758; ");
							$("#nitrogenTargetPressure").html( (parseFloat( $("#pressureA").html() ) + 0.5).toFixed(1) );
							// Do this after every command
							timeExecuted = new Date().getTime() / 1000;
							moving = "no";
							executed = "yes";
							waiting = "yes";
							$("#command" + line).append(" &#10003;");
							console.log('Command',commandsArray[line],timeExecuted,'started and finished.');
						}
						// Write reference gas target pressure for the first sample on the frontpanel "WR <no parameter>"
						else if( commandsArray[line][0] == "W" && commandsArray[line][1] == "R" && executed == "yes" && moving == "no" && waiting == "no" )
						{
							// Do this before every command in method
							if( $("#command" + (line+2)).length ){ $("#command" + (line+2))[0].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' }); }
							$( "#command" + line).prepend("&#9758; " );
							// Keep the target pressure (ref) for all samples in sequence
							if( $( "#refgasTargetPressure" ).html() == "<em>Refgas target p</em>" )
							{
								$( "#refgasTargetPressure" ).html( "1.700" );
							}
							else
							{
								$( "#refgasTargetPressure" ).html( (parseFloat($( "#refgasTargetPressure" ).html()) * 1.0026).toFixed(3) );
							}
							// Do this after every command
							timeExecuted = new Date().getTime() / 1000;
							moving = "no";
							executed = "yes";
							waiting = "yes";
							$("#command" + line).append(" &#10003;");
							console.log('Command',commandsArray[line],timeExecuted,'started and finished.');
						}
						// Write sample gas target pressure for the first sample on the frontpanel "WS <no parameter>"
						else if( commandsArray[line][0] == "W" && commandsArray[line][1] == "S" && executed == "yes" && moving == "no" && waiting == "no" )
						{
							// Do this before every command in method
							if( $("#command" + (line+2)).length ){ $("#command" + (line+2))[0].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' }); }
							$( "#command" + line).prepend("&#9758; " );
							// Keep the target pressure (sam) for all samples in sequence
							if( $( "#samgasTargetPressure" ).html() == "<em>Sample target p</em>" )
							{
								$( "#samgasTargetPressure" ).html( "1.700" );
							}
							else
							{
								$( "#samgasTargetPressure" ).html( (parseFloat($( "#samgasTargetPressure" ).html()) * 1.0026).toFixed(3) );
							}
							// Do this after every command
							timeExecuted = new Date().getTime() / 1000;
							moving = "no";
							executed = "yes";
							waiting = "yes";
							$("#command" + line).append(" &#10003;");
							console.log('Command',commandsArray[line],timeExecuted,'started and finished.');
						}
						// Execute command at laser spectrometer: Start writing data to disk "TWD 0"
						else if( commandsArray[line][0] == "T" && commandsArray[line][1] == "W" && commandsArray[line][2] == "D" && executed == "yes" && moving == "no" && waiting == "no" )
						{
							// Do this before every command in method
							if( $("#command" + (line+2)).length ){ $("#command" + (line+2))[0].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' }); }
							$("#command" + line).prepend("&#9758; ");
							// Do something here
							// Execute command at laser spectrometer: Stop writing data to disk
							if( parameterArray[line] == 0 )
							{
								// Do something here
								stopWritingData();						
							}
							else if( parameterArray[line] == 1 )
							{
								// Do something here
								startWritingData();
								$('#cycle').html( cycle );
								cycle++;						
							}
							// Do this after every command
							// Do this after every command
							timeExecuted = new Date().getTime() / 1000;
							moving = "no";
							executed = "yes";
							waiting = "yes";
							$("#command" + line).append(" &#10003;");
							console.log('Command',commandsArray[line],timeExecuted,'started and finished.');
						}
						// Move bellows (X,Y,Z) "BY 53" with the percentage as parameter BX 34.5
						else if( commandsArray[line][0] == "B" && moving == "no" && executed == "yes" && waiting == "no" )
						{
							// Do this before every command in method
							if( $("#command" + (line+2)).length ){ $("#command" + (line+2))[0].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' }); }
							$("#command" + line).prepend("&#9758; ");
							// Move bellows
							if( parameterArray[line].substr(0,1) == "+" || parameterArray[line].substr(0,1) == "-" )
							{
								// Move increment
								// Get current bellows position
								let currentPercent = parseFloat( $("#percentage" + commandsArray[line][1] + "steps").text() );
								// Calculate the new bellows position
								let newPercent = currentPercent + parseFloat( parameterArray[line] );
								$( "#setPercentage" + commandsArray[line][1] ).val( newPercent.toFixed(1) );
							}
							else
							{
								// Move absolute
								$( "#setPercentage" + commandsArray[line][1] ).val( parameterArray[line] );
							}
							moveBellows( commandsArray[line][1] );
							console.log( "Just started to move bellows, move status:", $('#moveStatus').html() );
		
							// After each command
							$("#progressBar").css( "width","0px" );
							$("#progress").html("0%");
							timeExecuted = new Date().getTime() / 1000; // Start time of command
							moving = "yes";
							executed = "no";
							waiting = "no";

							console.log('Command',commandsArray[line],timeExecuted,'started.');
						}
						// Set bellows to pressure target (X,Y) "PX 1.723"
						else if( commandsArray[line][0] == "P" && executed == "yes" && moving == "no" && waiting == "no" )
						{
							// Do this before every command in method
							if( $("#command" + (line+2)).length ){ $("#command" + (line+2))[0].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' }); }
							$("#command" + line).prepend("&#9758; ");
							if( commandsArray[line][1] == "X" )
							{
								if( $( "#refgasTargetPressure" ).html() == "<em>Refgas target p</em>" )
								{
									var pTarget = parseFloat( parameterArray[line] );
								}
								else
								{
									var pTarget = parseFloat( $( "#refgasTargetPressure" ).html() ).toFixed(3);
								}
							}
							else if( commandsArray[line][1] == "Y" )
							{
								if( $( "#samgasTargetPressure" ).html() == "<em>Sample target p</em>" )
								{
									var pTarget = parseFloat( parameterArray[line] );
								}
								else
								{
									var pTarget = parseFloat( $( "#samgasTargetPressure" ).html() ).toFixed(3);
								}
							}
							console.log("The target pressure is: ", pTarget.toFixed(3), "mbar");
							// alert( pTarget.toFixed(3) );							
							getStatus( commandsArray[line][1] + "S" + pTarget.toFixed(3) );
							$('#moveStatus').html( 'M' + commandsArray[line][1] );
							// Resetting the progress bar						
							$("#progressBar").css( "width","0px" );
							$("#progress").html("0%");
							// Do this after every command
							timeExecuted = new Date().getTime() / 1000;
							moving = "yes";
							executed = "no";
							waiting = "no";
						}
						// Set bellows to pressure target (X,Y) "PX 1.723"
						else if( commandsArray[line][0] == "S" && commandsArray[line][1] == "N" && executed == "yes" && moving == "no" && waiting == "no" )
						{
							// Do this before every command in method
							if( $("#command" + (line+2)).length ){ $("#command" + (line+2))[0].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' }); }
							$("#command" + line).prepend("&#9758; ");
	
							if( $( "#nitrogenTargetPressure" ).html() == "<em>N2 target p</em>" )
							{
								var pTarget = 0;
							}
							else
							{
								var pTarget = parseFloat( $( "#nitrogenTargetPressure" ).html() );
							}
							console.log("The target N2 pressure (A) is: ", pTarget, " Torr");
							// alert( pTarget.toFixed(3) );							
							getStatus( "SN" + pTarget.toFixed(1) );
							$('#moveStatus').html( 'SN' );
							// Resetting the progress bar						
							$("#progressBar").css( "width","0px" );
							$("#progress").html("0%");
							// Do this after every command
							timeExecuted = new Date().getTime() / 1000;
							moving = "yes";
							executed = "no";
							waiting = "no";
						}
						// Refill sample gas
						else if( commandsArray[line][0] == "R" && commandsArray[line][1] == "S" && executed == "yes" && moving == "no" && waiting == "no" )
						{
							// Do this before every command in method
							if( $("#command" + (line+2)).length ){ $("#command" + (line+2))[0].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' }); }
							$("#command" + line).prepend("&#9758; ");

							getStatus( "RS" + parseFloat( parameterArray[line] ).toFixed(3) );
							$('#moveStatus').html( 'RS' );
							console.log('Hello David, its all right');

							// Resetting the progress bar						
							$("#progressBar").css( "width","0px" );
							$("#progress").html("0%");
							// Do this after every command
							timeExecuted = new Date().getTime() / 1000;
							moving = "yes";
							executed = "no";
							waiting = "no";
						}
						// Mixes and inserts gas into bellows X
						else if( commandsArray[line][0] == "X" && commandsArray[line][1] == "I" && executed == "yes" && moving == "no" && waiting == "no" )
						{
							// Do this before every command in method
							if( $("#command" + (line+2)).length ){ $("#command" + (line+2))[0].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' }); }
							$("#command" + line).prepend("&#9758; ");	
							getStatus( "XI" );
							// Resetting the progress bar						
							$("#progressBar").css( "width","0px" );
							$("#progress").html("0%");
							// Do this after every command
							timeExecuted = new Date().getTime() / 1000;
							moving = "yes";
							executed = "no";
							waiting = "no";
						}
						// Set bellows Z to cell pressure target (40.000 Torr) "QZ 40.1"
						else if( commandsArray[line][0] == "Q" && executed == "yes" && moving == "no" && waiting == "no" )
						{
							// Do this before every command in method
							if( $("#command" + (line+2)).length ){ $("#command" + (line+2))[0].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' }); }
							$("#command" + line).prepend("&#9758; ");

							// Measure the current pressure (in Torr) in the cell
							let p = parseFloat( $("#baratron").text() );
							console.log("Current pressure in the cell is: ", p.toFixed(3), "Torr");
							// Check if any pressure is given in the cellTargetPressure window
							if( parseFloat( $("#cellTargetPressure").html() ) > 0 )
							{
								var pTarget = parseFloat( $("#cellTargetPressure").html() );
							}
							else
							{
								var pTarget = parseFloat( parameterArray[line] ); // Normally about 40 Torr
							}
							console.log("Target pressure is: ", pTarget.toFixed(3), "Torr");
							let percent = parseFloat( $("#percentageZsteps").text() );
							console.log("Current percentage (Z) is: ", percent.toFixed(1), "%");
							var percentTarget = percent + ( pTarget - p ) / -0.007030;
							percentTarget = parseFloat( percentTarget ).toFixed(1);
							console.log("Target percentage is: ", percentTarget, "%");
							// Move bellows
							$( "#setPercentageZ" ).val( percentTarget );
							console.log( "Sends the move Z bellows command." );
							moveBellows( "Z" );
							// Resetting the progress bar						
							$("#progressBar").css( "width","0px" );
							$("#progress").html("0%");
							// Do this after every command
							timeExecuted = new Date().getTime() / 1000; // In this case only comes after the movement has finished
							moving = "yes";
							executed = "no";
							waiting = "no";
							console.log( "moving:",moving,"executed:",executed,"waiting:",waiting )
						}
						// Set bellows Z to nitrogen pressure target "AZ 178.2"
						else if( commandsArray[line][0] == "A" && executed == "yes" && moving == "no" && waiting == "no" )
						{
							// Do this before every command in method
							if( $("#command" + (line+2)).length ){ $("#command" + (line+2))[0].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' }); }
							$("#command" + line).prepend("&#9758; ");
							// Measure the current nitrogen pressure (in Torr)
							let p = parseFloat( $("#pressureA").text() );
							console.log("Current nitrogen pressure is: ", p.toFixed(1), "Torr");
							// Check if any pressure is given in the nitrogenTargetPressure window
							if( parseFloat( $("#cellTargetPressure").html() ) > 0 )
							{
								var pTarget = parseFloat( $("#nitrogenTargetPressure").html() );
							}
							else
							{
								var pTarget = parseFloat( parameterArray[line] ); // Normally about 40 Torr
							}
							console.log("Target pressure is: ", pTarget.toFixed(3), "Torr");
							let percent = parseFloat( $("#percentageZsteps").text() );
							console.log("Current percentage (Z) is: ", percent.toFixed(1), "%");
							var percentTarget = percent + ( pTarget - p ) / -0.1118;
							percentTarget = parseFloat( percentTarget ).toFixed(1);
							console.log("Target percentage is: ", percentTarget, "%");
							// Move bellows
							$( "#setPercentageZ" ).val( percentTarget );
							console.log( "Sends the move Z bellows command." );
							moveBellows( "Z" );	
							// Resetting the progress bar						
							$("#progressBar").css( "width","0px" );
							$("#progress").html("0%");
							// Do this after every command
							// timeExecuted = new Date().getTime() / 1000; In this case only comes after the movement has finished
							moving = "yes";
							executed = "no";
							waiting = "no";
							console.log( "moving:",moving,"executed:",executed,"waiting:",waiting )
						}

						// Check if bellows target position has been reached
						if( moving == "yes" && executed == "no" && waiting == "no" && ( $('#moveStatus').html() != "-" || new Date().getTime() / 1000.00 - timeExecuted < 1 ) )
						{
							// Case 1
							// console.log( new Date().getTime() / 1000, "Case 1: Bellows are currently moving, nothing changed." );
						}
						else if( moving == "yes" && executed == "no" && waiting == "no" && $('#moveStatus').html() == "-" )
						{
							// Case 2
							// console.log( new Date().getTime() / 1000, "Case 2: Bellows reached target position." );
							timeExecuted = new Date().getTime() / 1000;
							moving = "no";
							executed = "yes";
							waiting = "yes";
							$("#command" + line).append(" &#10003;");
						}
						else if( moving == "no" && executed == "yes"  && waiting == "yes" && $('#moveStatus').html() == "-" && new Date().getTime() / 1000 - timeExecuted < timeArray[line] )
						{
							// Case 3
							// console.log( new Date().getTime() / 1000, "Case 3: Progress bar is moving." );
							// Now move the progress bar
							var pbpc = ( new Date().getTime() / 1000 - timeExecuted ) * 285 / timeArray[line];
							$('#progressBar').css("width",pbpc+"px");
							$("#progress").html( parseInt(pbpc / 2.85) + "%" );
							// console.log("Progress bar increasing.");
						}
						else
						{
							// Case 4
							// console.log( new Date().getTime() / 1000, "Case 4: Jumps to next sample." );
							waiting = "no";
							// Goto next line in method
							line++;
							console.log("Now goto next line",line);
							if( line == commandsArray.length )
							{
								console.log("End of method.");
								$('#progressBar').css("width","0px");
								$("#methodStatus").html('Sample finished.');
								$("#sample" + sample).append(" &#10003;");
								$("#sample" + sample)[0].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' });
								cycle = 0;
								// Copy files from TILDAS to raspberry folder
								copyFiles();
								// Execute Python script
								evaluateData();
								// Move to the next sample (by index)
								sample++;
								// Check if this element exists
								if( $('#sample' + sample ).length )
								{
									// OK, next sample exists, read out sample name & method file name now
									$("#sample" + sample).prepend("&#9758; ");
									let sampleName = $( '#sample' + sample ).html().split(",")[1];
									let methodFileName = $( '#sample' + sample ).html().split(",")[2];
									$('#sampleName').val( sampleName );
									loadMethod( methodFileName );
									line = 0;
									createFolder();
									$("#methodStatus").html('Method running');
								}
								else
								{
									// No next sample, sequence finished
									console.log("No more sample to be run.");
									sample = 0;
									line = 0;
									cycle = 0;
									$( "#refgasTargetPressure" ).html( "<em>Refgas target p</em>" );
									// // Get data in database
									// wait(30);
									// let tmp = $('#folderName').html().split('/');
									// tmp = tmp[1];
									// window.open('http://192.168.1.242/evaluateData.php?sampleName=' + tmp + '&polynomial=2','_blank');
								}
							}
						}
					}

					$('#cycleJS').text('ICE ' + cycleJS );
					cycleJS++;
				}
			,50);
			
		</script>

		<h2>Instructions</h2>

		<p> Start the communication script: /usr/bin/python3 /var/www/html/serialComm.py</p>
		<p>For startup: Make sure that "RS" is active at TILDAS and that mode is in "Stream Data", otherwise Python does not get data. Then ensure that the arduino is running.</p>

		The general structure of a command line in the method files is "command,parameter,wait". The method files are CSV files with a separation by comma. You can edit them in Excel (check is the exported cvs file has separation of columns by a comma). A parameter is used for most commands, but is ignored for some (there one may set it to 0, but it always has to be present)
		<ul>
			<li>Sequences and methods should always start from the situation pictured below. You can reset the valves to this situation by pressing the <b>Starting Position</b> button.<br /><img src="images/startMethod.png" width="600px"/></lt>
			<li>V03,0,15: Close valve 3 and wait 15 s</li>
			<li>V13,1,12: Open valve 13 and wait 12 s</li>
			<li>WC,0,5: Write current cell presure (Baratron at absorption cell) on front panel for later use (cell presure adjustment) and wait 5 s</li>
			<li>WA,0,7: Write current N<sub>2</sub> pressure (Baratron gauge A) on front panel for later use (N<sub>2</sub> presure adjustment) and wait 7 s</li>
			<li>WR,0,12: Write current reference CO<sub>2</sub> pressure (Baratron bellows X) on front panel for later use (CO<sub>2</sub> presure adjustment) and wait 12 s, this value is kept for the entire measurement</li>
			<li>WS,0,6: Write current sample CO<sub>2</sub> pressure (Baratron bellows Y) on front panel for later use (CO<sub>2</sub> presure adjustment) and wait 6 s, this value is kept for the entire measurement</li>
			<li>TWD,1,10: Starts writing the data from the TILDAS in hard disk and waits 10 s</li>
			<li>TWD,0,10: Stops writing the data from the TILDAS in hard disk</li>
			<li>BX,45.3,12: Move bellows X to 45.3% and wait 12 s. If the parameter has a sign, the bellows are moved by an increment relative to the current position.</li>
			<li>BX,-7.2,12: Move bellows X by -7.2% (percent points) reative to the current position and wait 12 s.</li>
			<li>BY,25.3,12: Move bellows Y to 25.3% and wait 12 s. If the parameter has a sign, the bellows are moved by an increment relative to the current position.</li>
			<li>BY,+4.5,12: Move bellows Y by 4.5% (percent points) reative to the current position and wait 12 s.</li>
			<li>BZ,25.3,12: Move bellows Z to 25.3% and wait 12 s. If the parameter has a sign, the bellows are moved by an increment relative to the current position.</li>
			<li>PX,1.653,10: Move bellows X or expand the gas so that the pressure is 1.653 mbar in bellows X and then wait 10 s. If the bellows are compressed to &lt; 11%, reference gas is refilled. The starting situation should be:<br /><img src="images/startPX.png" width="600px" /></li>
			<li>PY,1.653,10: Move bellows Y so that the pressure is 1.653 mbar in bellows Y and then wait 10 s. Possibly, you need to set to a different pressure in Y to get the same CO<sub>2</sub> mixing ratio because the pressure gauges are not 100% identical. The starting situation should be:<br /><img src="images/startPY.png" width="600px" /></li>
			<li>QC,39.387,10: Set the cell pressure by moving bellows Z to the pressure written by command WC on the frontpanel. The parameter 39.387 is only used in case that there is no value given on the frontpanel. Only a small range can be adjusted.</li>
			<li>SN,277.13,10: Set the N<sub>2</sub> pressure (Baratron gauge A) by moving bellows Z to the pressure written by command WA on the frontpanel. The parameter 277.13 is only used in case that there is no value given on the frontpanel. Only a small range can be adjusted.</li>
		</ul>
	</body>
</html>

