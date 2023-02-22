#include <AccelStepper.h>
#include "Adafruit_Si7021.h"

// #include <SparkFun_MCP9600.h>
// MCP9600 thermocouple;

bool enableHeater = false;
// uint8_t loopCnt = 0;
Adafruit_Si7021 sensor = Adafruit_Si7021();

long XstartPos = 0;
long YstartPos = 0;
long ZstartPos = 0;
long steps = 0;

char command;
String string;
String stat = "S";
String statusMessage = "";
float Xpercentage = 0.00;
float Ypercentage = 0.00;
float Zpercentage = 0.00;
float Xpressure = 0.00;
float Ypressure = 0.00;
float Apressure = 0.0;
float XpressureArray[200];
float YpressureArray[200];
float ApressureArray[200];
float XpercentageArray[200];
float YpercentageArray[200];
float boxTempArray[200];
int fsSetPoint = 0;
float boxTemp = 0.000;
float boxTemp2 = 0.000;
long now = 0;
long lastTime = 0;
long timeChange = 0;
float Terror = 0.000;
float errSum = 0.000;
float dErr = 0.000;
float lastErr = 0.000;
int cycl = 0;

// variables for the PID
int PID_Status = 1;
float housingSetT = 32.000;
int kp = 395;
float ki = 0.33;
float kd = 0.033;

float targetPercent = 0.000;

long Xsteps = 0;
long Ysteps = 0;
long Zsteps = 0;
long XstepsIni = 0;
long YstepsIni = 0;
long ZstepsIni = 0;
// int bellowsCalibratedX = 0;

long startMillis = 0;

AccelStepper Xaxis(1, 3, 2); // pin 3 = step, pin 2 = direction
AccelStepper Yaxis(1, 5, 4); // pin 5 = step, pin 4 = direction
AccelStepper Zaxis(1, 15, 14); // pin 15 = step, pin 14 = direction

// Pins 22-53 are used for the valve control

// Reset pin is set to +5V (HIGH)
const byte XYZsleepPin = 16;

// For the microstep setting of the DRV8825 driver module
const byte MO0Pin = 9;
const byte MO1Pin = 10;
const byte MO2Pin = 11;

float relDiff = 0; // Relative pressure difference in %

// 0-100 (x) are 62438 steps, at 1/8 microsteps

void setup()
{
  Serial.begin(115200);
  // Wait for serial port to open
  while (!Serial) {
    delay(10);
  }

  // Wire.begin();
  // Wire.setClock(100000);
  // thermocouple.begin(0x66);
  
  sensor.begin();
  // This is all for the t and h sensor
  // Serial.println("Si7021 test!");
  // if (!sensor.begin()) {
  //   Serial.println("Did not find Si7021 sensor!");
  //   while (true);
  // }
  // Serial.print("Found model ");
  // switch (sensor.getModel()) {
  //   case SI_Engineering_Samples:
  //     Serial.print("SI engineering samples"); break;
  //   case SI_7013:
  //     Serial.print("Si7013"); break;
  //   case SI_7020:
  //     Serial.print("Si7020"); break;
  //   case SI_7021:
  //     Serial.print("Si7021"); break;
  //   case SI_UNKNOWN:
  //   default:
  //     Serial.print("Unknown");
  // }
  // Serial.print(" Rev(");
  // Serial.print(sensor.getRevision());
  // Serial.print(")");
  // Serial.print(" Serial #"); Serial.print(sensor.sernum_a, HEX); Serial.println(sensor.sernum_b, HEX);
  // End of setup for the t and h sensor

  // Configure the output pins and set them to low, for valves (via relay boards)
  int pinNr = 22;
  while ( pinNr <= 53 )
  {
    pinMode(pinNr, OUTPUT);
    digitalWrite(pinNr, HIGH);
    pinNr = pinNr + 1;
  }

  digitalWrite(21 + 17, HIGH); // Ventil #17 (turbo pump) schlie�en
  digitalWrite(21 + 27, HIGH); // Ventil #27 (fore vacuum pump) schlie�en
  digitalWrite(21 + 16, HIGH);

  pinMode(A0, INPUT); // Potentiometer X
  pinMode(A1, INPUT); // Potentiometer Y
  pinMode(A2, INPUT); // Bellows pressure X (0-10 Torr)
  pinMode(A3, INPUT); // Bellows pressure Y (0-10 Torr)
  pinMode(A4, INPUT); // Baratron (A, 0-1000 mbar)

  pinMode(6, OUTPUT); // Power supply analog in (I)
  pinMode(8, OUTPUT); // Power supply analog in (U)
  analogWrite(6, 45); // Set the maximum voltage to little less than 12 V (maximum is 60 V)
  analogWrite(8, 0); // Set the maximum current to about 2 A (maximum is 8 A) valid range 4-40 (10-100%)


  // pinMode(XYZenablePin, OUTPUT);
  // digitalWrite(XYZenablePin, LOW);

  pinMode(XYZsleepPin, OUTPUT);
  digitalWrite(XYZsleepPin, LOW); // Drivers for X and Y sleeping

  // This is the pinout for motors X, Y, and Z (microstepping)
  pinMode(MO0Pin, OUTPUT);
  pinMode(MO1Pin, OUTPUT);
  pinMode(MO2Pin, OUTPUT);

  // Set the microstepping 1/32: 1 1 1, 1/8: 1 1 0, motors X, Y, and Z
  digitalWrite(MO0Pin, HIGH);
  digitalWrite(MO1Pin, HIGH);
  digitalWrite(MO2Pin, LOW);

  // From the potentiometer of the two bellows
  // Do an averaging here
  int i = 0;
  while ( i < 200 )
  {
    Xpercentage = Xpercentage + -100.00 / 800.00 * analogRead(A0) + 100 + 10000 / 800;
    Ypercentage = Ypercentage + -100.00 / 800.00 * analogRead(A1) + 100 + 10000 / 800;
    i = i + 1;
  }
  Xpercentage = Xpercentage / 200.00;
  Ypercentage = Ypercentage / 200.00;

  // Set the current steps
  // For 1/32 microsteps: max range = 245000 steps, for 1/8 these are 62438
  Xsteps = Xpercentage * 62438.00 / 100;
  Ysteps = Ypercentage * 62438.00 / 100;
  Zsteps = 15960 / 2; // Start position is at 50 percent
  Xaxis.setCurrentPosition(Xsteps);
  Yaxis.setCurrentPosition(Ysteps);
  Zaxis.setCurrentPosition(Zsteps);

  XstartPos = Xsteps;
  YstartPos = Ysteps;
  ZstartPos = Zsteps;
  steps = 0;

  Xaxis.setMaxSpeed(50 * 32);
  Xaxis.setAcceleration(20 * 32);

  Yaxis.setMaxSpeed(50 * 32);
  Yaxis.setAcceleration(20 * 32);

  Zaxis.setMaxSpeed(50 * 16);
  Zaxis.setAcceleration(20 * 16);

  delay(100);

  Xpressure = analogRead(A2) * 5.00 * 1.333 / 1024.00;
  Ypressure = analogRead(A3) * 5.00 * 1.333 / 1024.00;
  Apressure = analogRead(A4) * 500.00 / 1024.00;

  delay(100);
}

void wait(int seconds, String message)
{
  startMillis = millis();
  while ( millis() < startMillis + seconds * 1000 )
  {
    sendStatus( message );
    delay(10);
  }
}

void controlT()
{
  now = millis();
  timeChange = now - lastTime;
  
  // Compute all the working error variables after cycle 60
  Terror = boxTemp - housingSetT;
  
  if( cycl > 60 ) {
    errSum += (Terror * timeChange/1000);
    dErr = (Terror + lastErr) / timeChange*1000;
    // Remember some variables for next time
    lastErr = Terror;
    lastTime = now;
  }
  cycl = cycl + 1;
  // Compute PID Output
  
  fsSetPoint = kp * Terror + ki * errSum + kd * dErr;

  if( fsSetPoint > 100 )
  {
    fsSetPoint = 100;
  }
  else if( fsSetPoint < 9)
  {
    fsSetPoint = 9;
  }
  if( PID_Status != 1)
  {
    fsSetPoint = 0;
  }
  
  analogWrite(8, fsSetPoint * 40 / 100 );
}

void runXP(float percentage, String string)
{
  digitalWrite(XYZsleepPin, HIGH);
  delay(100);
  stat = "W";
  if (percentage > 100)
  {
    percentage = 100;
  }
  if (percentage < 0)
  {
    percentage = 0;
  }
  XstartPos = Xaxis.currentPosition();
  long steps = ( percentage * 62438.00 / 100 ) - Xsteps;
  // Check if bellows opens or compresses
  // If it opens, then open a bit more and then move back
  // If it closes, simply close
  sendStatus("MX");
  Xaxis.move(steps);
  while ( Xaxis.currentPosition() != XstartPos + steps )
  {
    Xaxis.run();
  }
  Xsteps = Xsteps + steps;
  digitalWrite(XYZsleepPin, LOW); // Back in sleeping mode
  stat = "S";
}

void runYP(float percentage, String string)
{
  digitalWrite(XYZsleepPin, HIGH);
  delay(100);
  stat = "W";
  if (percentage > 100)
  {
    percentage = 100;
  }
  else if (percentage < 0)
  {
    percentage = 0;
  }
  YstartPos = Yaxis.currentPosition();
  long steps = percentage * 62438.00 / 100 - Ysteps;
  sendStatus("MY");
  Yaxis.move(steps);
  long i = 0;
  while ( Yaxis.currentPosition() != YstartPos + steps )
  {
    Yaxis.run();
  }
  Ysteps = Ysteps + steps;
  digitalWrite(XYZsleepPin, LOW);
  stat = "S";
}

void runZP(float percentage, String string)
{
  digitalWrite(XYZsleepPin, HIGH);
  delay(100);
  stat = "W";
  if (percentage > 100)
  {
    percentage = 100;
  }
  else if (percentage < 0)
  {
    percentage = 0;
  }

  ZstartPos = Zaxis.currentPosition();
  long steps = percentage * 15960 / 100 - Zsteps;
  sendStatus("MZ");
  Zaxis.move(steps);
  long i = 0;
  while ( Zaxis.currentPosition() != ZstartPos + steps )
  {
    Zaxis.run();
  }
  Zsteps = Zsteps + steps;
  digitalWrite(XYZsleepPin, LOW);
  stat = "S";
  
}

void startingPosition()
{
  switchValve( "V01C" );
  switchValve( "V02C" );
  switchValve( "V03C" );
  switchValve( "V04C" );
  switchValve( "V05O" );
  switchValve( "V06C" );
  switchValve( "V07O" );
  switchValve( "V08C" );
  switchValve( "V09C" );
  switchValve( "V10C" );
  switchValve( "V11O" );
  switchValve( "V12C" );
  switchValve( "V13O" );
  switchValve( "V14C" );
  switchValve( "V15C" );
  switchValve( "V16O" );
  switchValve( "V17O" );
  switchValve( "V18C" );
  switchValve( "V19O" );
  switchValve( "V20C" );
  switchValve( "V22C" );
  switchValve( "V27C" );

  delay(50);
}

void expandX(int number)
{
  if ( number == 1 ) // 1.5% reduction
  {
    switchValve( "V06C" );
    switchValve( "V07O" );
    wait(20, "EX");
    switchValve( "V07C" );
    switchValve( "V06O" );
    wait(5, "EX");
  }
  else if ( number == 2 ) // 14% reduction
  {
    switchValve( "V11C" );
    switchValve( "V16C" );
    switchValve( "V07O" );
    wait(10, "EX");
    switchValve( "V07C" );
    switchValve( "V16O" );
    switchValve( "V11O" );
    wait(20, "EX");
  }
  else if ( number == 3 ) // 32% reduction
  {
    switchValve( "V16C" );
    switchValve( "V06O" ); // this line is redundant
    switchValve( "V05O" );
    switchValve( "V07O" );
    wait(15, "EX");
    switchValve( "V07C" );
    switchValve( "V05C" );
    switchValve( "V16O" );
    wait(20, "EX");
  }
}

void expandY(int number)
{
  if ( number == 1 ) // 5.3% reduction
  {
    switchValve( "V12C" );
    switchValve( "V13O" );
    wait(20,"EY");
    switchValve( "V13C" );
    switchValve( "V12O" );
    wait(5,"EY");
  }
  else if ( number == 2 ) // 37% reduction
  {
    switchValve( "V05C" );
    switchValve( "V16C" );
    switchValve( "V13O" );
    wait(10,"EY");
    switchValve( "V13C" );
    switchValve( "V16O" );
    switchValve( "V05O" );
    wait(20,"EY");
  }
  else if ( number == 3 ) // 61% reduction
  {
    switchValve( "V16C" );
    switchValve( "V11O" );
    switchValve( "V13O" );
    wait(15,"EY");
    switchValve( "V13C" );
    switchValve( "V11C" );
    switchValve( "V16O" );
    wait(20,"EY");
  }
}

void refillSample( float tPress )
{
  // Get the pressure in bellows Y
  int expN = 0;
  sendStatus("RS" + String(expN));
  while ( Ypressure < tPress && expN < 10 )
  {
    switchValve("V22O" );
    wait(20,"RS" + String(expN));
    switchValve( "V22C" );
    switchValve( "V10O" );
    wait(20,"RS" + String(expN));
    switchValve( "V10C" );
    wait(20,"RS" + String(expN));
    expN = expN + 1;
  }
}

void runAX(float pressureTarget)
{
  for (;;)
  {
    sendStatus("AX");
    delay(10);

    if (Apressure >= pressureTarget)
    {
      switchValve( "V15C" );
      switchValve( "V21C" );
      break;
    }

  }  
}

void setPressureX(float targetPressure)
{
  float V0 = 41.008; // This is a instrument constant for bellows X
  for ( int a = 0; a < 15; a++ )
  {
    // Get current pressure
    int m = 100; // Integration cycles
    for (int j = 0; j < m; j++)
    {
      sendStatus("PX");
      delay(10);
    }
    delay(100);
    // Now see what to do
    if ( abs(Xpressure - targetPressure) <= 0.001 )
    {
      // Serial.println( "Target pressure reached." );
      break;
    }
    else if ( (Xaxis.currentPosition() * 100.0000 / 62438.00 != 100  && Xaxis.currentPosition() * 100.0000 / 62438.00 > 0) || ( (Xpressure - targetPressure) < -0.001 && Xaxis.currentPosition() * 100.0000 / 62438.00 == 100) )
    {
      // p = k / (V + V0)
      // Now calculate the k value for the current filling
      float k = Xpressure * ( Xaxis.currentPosition() * 100.0000 / 62438.00 + V0 );
      // Serial.print("k: ");
      // Serial.println( k );
      // Now calculate the target V (% bellows)
      targetPercent = k / targetPressure - V0;
      // Serial.print("Target percent: ");
      // Serial.println( targetPercent );
      // targetPercent = Xaxis.currentPosition() * 100.0000 / 62438.00 + (targetPressure - Xpressure) / -0.0038;
      // Send the command to the bellows
      runXP( targetPercent, "MX" );
      sendStatus("PX");
      delay(100);
    }
    else if ( Xaxis.currentPosition() * 100.0000 / 62438.00 == 100 && Xaxis.currentPosition() * 100.0000 / 62438.00 > 0 )
    {
      // Now decide which route should be evacuated
      if ( (Xpressure - targetPressure) / Xpressure * 100 > 60 )
      {
        // Expand by ~65%
        sendStatus("PX");
        expandX( 3 );
      }
      else if ( (Xpressure - targetPressure) / Xpressure * 100 <= 60 && (Xpressure - targetPressure) / Xpressure * 100 > 35 )
      {
        // Expand by ~40%
        sendStatus("PX");
        expandX( 2 );
      }
      else if ( (Xpressure - targetPressure) / Xpressure * 100 <= 35 )
      {
        // Expand by ~5.4%
        sendStatus("PX");
        expandX( 1 );
      }
    }
    else if ( Xaxis.currentPosition() * 100.0000 / 62438.00 == 0 )
    {
      // Too little gas, refill reference gas
      break;
    }
    else
    {
      break;
    }
  }
}

void setPressureY(float targetPressure)
{
  float V0 = 42.337; // This is a instrument constant for bellows Y
  for ( int a = 0; a < 15; a++ )
  {
    // Get current pressure
    int m = 100; // Integration cycles
    for (int j = 0; j < m; j++)
    {
      sendStatus("PY");
      delay(10);
    }
    delay(100);
    // Now decide what to do
    if ( abs(Ypressure - targetPressure) <= 0.001 )
    {
      // Serial.println( "Target pressure reached." );
      break;
    }
    else if ( Yaxis.currentPosition() * 100.0000 / 62438.00 != 100 || ( Yaxis.currentPosition() * 100.0000 / 62438.00 == 100 && (Ypressure - targetPressure) < -0.001 ) )
    {
      // Compress bellows
      // p = k / (V + V0)
      // Now calculate the k value for the current filling
      float k = Ypressure * ( Yaxis.currentPosition() * 100.0000 / 62438.00 + V0 );
      // Serial.print("k: ");
      // Serial.println( k );
      // Now calculate the target V (% bellows)
      targetPercent = k / targetPressure - V0;
      // Send the command to the bellows
      runYP( targetPercent, "MY" );
      sendStatus("PY");
      delay(100);
    }
    else if ( Yaxis.currentPosition() * 100.0000 / 62438.00 == 100 )
    {
      // Expand gas
      // Now decide which route should be evacuated
      if ( (Ypressure - targetPressure) / Ypressure * 100 > 60 )
      {
        // Expand by ~61%
        sendStatus("PY");
        expandY( 3 );
        delay(100);
      }
      else if ( (Ypressure - targetPressure) / Ypressure * 100 <= 60 && (Ypressure - targetPressure) / Ypressure * 100 > 33 )
      {
        // Expand by ~37% steps
        sendStatus("PY");
        expandY( 2 );
        delay(100);
      }
      else if ( (Ypressure - targetPressure) / Ypressure * 100 <= 33 )
      {
        // Expand by ~5.3% steps
        sendStatus("PY");
        expandY( 1 );
        delay(100);
      }
    }
    else if ( Yaxis.currentPosition() * 100.0000 / 62438.00 == 0 )
    {
      // Too little gas
      break;
    }
  }
}

void setN2Pressure(float targetPressure)
{
  if ( targetPressure > 10 )
  {
    for ( int a = 0; a < 10; a++ )
    {
      // Get current pressure
      int m = 100; // Integration cycles
      for (int j = 0; j < m; j++)
      {
        sendStatus("SN");
        delay(10);
      }
      delay(100);
      // Now decide what to do
      if ( abs(Apressure - targetPressure) <= 0.1 )
      {
        // Serial.println( "Target pressure reached." );
        break;
      }
      else
      {
        // Compress/open bellows
        targetPercent = Zaxis.currentPosition() * 100.0000 / 15960.00 + (Apressure - targetPressure) / 0.1044;
        // Send the command to the bellows
        runZP( targetPercent, "MZ" );
        delay(100);
      }
    }
  }
  else
  {
    delay(100);
  }
}

void switchValve( String param )
{
  // param is a string like V03C or V12O
  // Extract an integer out of the valve number
  int v = param.substring(1, 3).toInt();
  if ( param.substring(3, 4) == "O" )
  {
    // Check the case for valve 17 (turbo) and 27 (fore vacuum)
    if ( v == 17 )
    {
      digitalWrite(21 + 27, HIGH);
      delay(2000);
    }
    else if ( v == 27 )
    {
      digitalWrite(21 + 17, HIGH);
      delay(250);
    }
    digitalWrite(21 + v, LOW); // Open valve
  }
  else if ( param.substring(3, 4) == "C" )
  {
    digitalWrite(21 + v, HIGH); // Close valve
  }
  sendStatus("SV");
  delay(50);
}


void sendStatus( String param )
{
  // Get all the current settings
  Xpressure = analogRead(A2) * 5.00 * 1.333224 / 1024.00;
  Ypressure = analogRead(A3) * 5.00 * 1.333224 / 1024.00;
  Apressure = analogRead(A4) * 500.00 / 1024;
  Xpercentage = -100.00 / 800 * analogRead(A0) + 100 + 10000 / 800;
  Ypercentage = -100.00 / 800 * analogRead(A1) + 100 + 10000 / 800;

  boxTemp = sensor.readTemperature();
  // boxTemp2 = thermocouple.getThermocoupleTemp();

  
  int n = 50; // Integration cycles
  for (int i = 0; i < n; i++) {
    // Move elements up in the array
    XpressureArray[i] = XpressureArray[i + 1];
    YpressureArray[i] = YpressureArray[i + 1];
    ApressureArray[i] = ApressureArray[i + 1];
    XpercentageArray[i] = XpercentageArray[i + 1];
    YpercentageArray[i] = YpercentageArray[i + 1];
    boxTempArray[i] = boxTempArray[i + 1];
  }
  XpressureArray[n - 1] = Xpressure;
  YpressureArray[n - 1] = Ypressure;
  ApressureArray[n - 1] = Apressure;
  XpercentageArray[n - 1] = Xpercentage;
  YpercentageArray[n - 1] = Ypercentage;
  boxTempArray[n - 1] = boxTemp;

  Xpressure = 0;
  Ypressure = 0;
  Apressure = 0;
  Xpercentage = 0;
  Ypercentage = 0;
  boxTemp = 0;

  for (int i = 0; i < n; i++) {
    // Add all elements of the array
    Xpressure = Xpressure + XpressureArray[i];
    Ypressure = Ypressure + YpressureArray[i];
    Apressure = Apressure + ApressureArray[i];
    Xpercentage = Xpercentage + XpercentageArray[i];
    Ypercentage = Ypercentage + YpercentageArray[i];
    boxTemp = boxTemp + boxTempArray[i];
  }

  // The baratrons and pressure sensors are calibrated and zeroed here
  // Preferably adjust the reference bellow
  Xpressure = (Xpressure / n - 0.325) / 0.933007 / 1.09901 / 1.003107; // Reference gas bellow
  Ypressure = (Ypressure / n - 0.297); // Sample bellow
  Apressure = Apressure / n - 4.4; // A pressure

  Xpercentage = Xpercentage / n;
  Ypercentage = Ypercentage / n;
  boxTemp = boxTemp / n;

  // Print out the current settings
  Serial.print( param );
  Serial.print( "," );
  Serial.print( Xaxis.currentPosition() * 100.0000 / 62438.00, 2 );
  Serial.print( "," );
  Serial.print( Xpercentage, 1 );
  Serial.print(",");
  Serial.print( Yaxis.currentPosition()  * 100.0000 / 62438.00, 2 );
  Serial.print( "," );
  Serial.print( Ypercentage, 1 );
  Serial.print( "," );
  Serial.print( Zaxis.currentPosition() );
  Serial.print(",");
  Serial.print( Zaxis.currentPosition() * 100 / 15960.00 );
  Serial.print(",");
  Serial.print( Xpressure, 3 );
  Serial.print( "," );
  Serial.print( Ypressure, 3 );
  Serial.print( "," );
  Serial.print( Apressure, 1 );
  Serial.print( "," );
  Serial.print(stat);
  Serial.print( "," );
  int pinNr = 22;
  while (pinNr <= 53)
  {
    if ( digitalRead(pinNr) == LOW )
    {
      Serial.print("1");
    }
    else
    {
      Serial.print("0");
    }
    pinNr = pinNr + 1;
  }
  Serial.print(",");
  Serial.print(boxTemp2, 3); // this is the place of the box humidity
  Serial.print(",");
  Serial.print(boxTemp, 3);
  Serial.print(",");
  Serial.print(fsSetPoint-9);
  
  Serial.println("");
}

//void bellowsCalibrationY()
//{
//  for (int i = 0; i < 11; i++) {
//    runYP( 100 - i * 10, "CY" );
//    delay(500);
//    x[i] = 100 - i * 10;
//    y[i] = -100.00 / 800.00 * analogRead(A1) + 100 + 10000 / 800; // Xpercentage, Y is on A1
//  }
//  for (int i = 0; i < 11; i++)
//  {
//    Serial.print(x[i]);
//    Serial.print(",");
//    Serial.println(y[i]);
//  }
//  // Now do the regression
//  int ret = fitCurve(order, sizeof(x) / sizeof(double), y, x, sizeof(coeffs) / sizeof(double), coeffs);
//  if (ret == 0) { //Returned value is 0 if no error
//    uint8_t c = 'a';
//    Serial.println("Coefficients for Y bellows are:");
//    for (int i = 0; i < sizeof(coeffs) / sizeof(double); i++) {
//      // snprintf(buf, 100, "%c=",c++);
//      // Serial.print(buf);
//      Serial.print(coeffs[i]);
//      Serial.println("");
//    }
//  }
//  Serial.println( coeffs[1] );
//  Serial.println( Yaxis.currentPosition() );
//  runYP( coeffs[1], "CY" ); // z.B. -0.21
//  Serial.println( Yaxis.currentPosition() );
//  // int tmp = Xaxis.currentPosition() + coeffs[1] * 62438 / 100;
//  Yaxis.setCurrentPosition( 0 );
//  Serial.println( Yaxis.currentPosition() );
//
//  delay(10000);
//  runYP(50, "CY");
//}




// Here comes the main program loop ----------------------

void loop()
{
  // Monitor the serial port
  while ( Serial.available() ) {
    delay(10);
    command = Serial.read();
    string += command;
  }

  controlT();

  // Set the stepper motor positions
  if ( string.substring(0, 2) == "XP" )
  {
    runXP( string.substring(2, 9).toFloat(), "MX" );
    string = "";
    command = "";
    sendStatus("-");
  }
  else if ( string.substring(0, 2) == "XS" )
  {
    // Sets the pressure in bellows X to the given pressure XS1.702
    setPressureX( string.substring(2, 9).toFloat() );
    string = "";
    command = "";
    sendStatus("-");
  }
  else if ( string.substring(0, 2) == "FS" )
  {
    // Sets the housing temperature
    housingSetT = string.substring(2, 9).toFloat();
    string = "";
    command = "";
    sendStatus("-");
  }
    else if ( string.substring(0, 2) == "KL" )
  {
    // Resets the valves to starting position
    startingPosition();
    string = "";
    command = "";
    sendStatus("-");
  }
  else if ( string.substring(0, 2) == "TC" )
  {
    // Sets the housing temperature
    PID_Status = string.substring(2, 9).toInt();
    string = "";
    command = "";
    sendStatus("-");
  }
  else if ( string.substring(0, 2) == "YP" )
  {
    runYP( string.substring(2, 9).toFloat(), "MY" );
    string = "";
    command = "";
    sendStatus("-");
  }

  else if ( string.substring(0, 2) == "AX" )
  {
    runAX(string.substring(2, 9).toFloat());
    string = "";
    command = "";
    sendStatus("-");
  }

  else if ( string.substring(0, 2) == "YS" )
  {
    // Sets the pressure in bellows Y to the given pressure YS1.702
    setPressureY( string.substring(2, 9).toFloat() );
    string = "";
    command = "";
    sendStatus("-");
  }
  else if ( string.substring(0, 2) == "ZP" )
  {
    runZP( string.substring(2, 9).toFloat(), "MZ" );
    string = "";
    command = "";
    sendStatus("-");
  }
  else if ( string.substring(0, 2) == "SN" )
  {
    setN2Pressure( string.substring(2, 9).toFloat() );
    string = "";
    command = "";
    sendStatus("-");
  }
  else if ( string.substring(0, 2) == "RS" )
  {
    refillSample( string.substring(2, 9).toFloat() );
    string = "";
    command = "";
    sendStatus("-");
  }
  // Get the current status & sleep (set motor currents to zero)
  else if ( string.substring(0, 1) == "S" )
  {
    digitalWrite(XYZsleepPin, LOW);
    string = "";
    command = "";
    stat = "S";
    sendStatus("-");
  }
  // Get current status & wake up
  else if ( string.substring(0, 1) == "W" )
  {
    digitalWrite(XYZsleepPin, HIGH);
    string = "";
    command = "";
    stat = "W";
    sendStatus("-");
  }
  // Set the valve positions 'V02C'
  else if ( string.substring(0, 1) == "V" )
  {
    // Extract an integer out of the valve number
    int v = string.substring(1, 3).toInt();
    if ( string.substring(3, 4) == "O" )
    {
      if ( v == 17 )
      {
        digitalWrite(21 + 27, HIGH); // Close valve 27
        delay(250);
      }
      else if ( v == 27 )
      {
        digitalWrite(21 + 17, HIGH); // Close valve 17
        delay(250);
      }
      if ( v == 19 )
      {
        digitalWrite(21 + 20, HIGH); // Close valve 20
        delay(250);
      }
      else if ( v == 20 )
      {
        digitalWrite(21 + 19, HIGH); // Close valve 19
        delay(250);
      }
      digitalWrite(21 + v, LOW); // Open valve
    }
    else if ( string.substring(3, 4) == "C" )
    {
      digitalWrite(21 + v, HIGH); // Close valve
    }
    string = "";
    command = "";
    sendStatus("-");
  }
  // Just send the status
  else if ( string.substring(0, 1) == "?" )
  {
    sendStatus("-");
    string = "";
    command = "";
  }

  // Print out the current settings
  sendStatus("-"); // Disabled for programming
  delay(20);
}
