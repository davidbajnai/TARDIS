// This is the JS script for...
// ...the awesome station clock

function pad(num, size)
{
    num = num.toString();
    while (num.length < size) num = "0" + num;
    return num;
}

function getTime()
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