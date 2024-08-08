#include <AccelStepper.h>
#include "Adafruit_SHTC3.h"
#include <ArduinoJson.h>

// This is the temperature sensor
Adafruit_SHTC3 shtc3 = Adafruit_SHTC3();

long XstartPos = 0;
long YstartPos = 0;
long ZstartPos = 0;
long steps = 0;
char command;
String string;
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
int fanSpeed = 0;
float boxTemp = 0.000;
float SPT = 32.5; // Set the housing temperature here
float boxHum = 0.00;
unsigned long now = 0;
unsigned long lastTime = 0;
unsigned long timeChange = 0;
float Terror = 0.000;
float errSum = 0.000;
float dErr = 0.000;
float lastErr = 0.000;
unsigned long cycl = 0;
float targetPercent = 0.000;
long Xsteps = 0;
long Ysteps = 0;
long Zsteps = 0;
unsigned long startMillis = 0;
const byte relayPins[] = {18, 19};
String valveStatus;
String relayStatus;

StaticJsonDocument<350> doc; // Define a JSON document
String jsonString;

AccelStepper Xaxis(AccelStepper::DRIVER, 3, 2); // mode, step, direction
const byte Xenable = 4;
AccelStepper Yaxis(AccelStepper::DRIVER, 6, 5);
const byte Yenable = 7;
AccelStepper Zaxis(AccelStepper::DRIVER, 9, 8);
const byte Zenable = 10;

const byte CurrentPin = 11;
const byte VoltagePin = 12;

void setup()
{
  Serial.begin(115200);

  // Wait for serial port to open
  while (!Serial) {
    delay(10);
  }

  // Start temperature sensor
  shtc3.begin();

  delay(4000);

  // DIGITAL PINS

  // Pinout for valve control
  for (int pinNr = 22; pinNr <= 53; pinNr++) {
    pinMode(pinNr, OUTPUT);
    delay(10);
  }

  // Pinout for relay control
  // relayPins[] = {18, 19}, as defined above
  pinMode(relayPins[0], OUTPUT);
  digitalWrite(relayPins[0], HIGH); // Relay off
  pinMode(relayPins[1], OUTPUT);
  digitalWrite(relayPins[1], HIGH); // Relay off

  // Motor enable pins
  pinMode(Xenable, OUTPUT);
  pinMode(Yenable, OUTPUT);
  pinMode(Zenable, OUTPUT);
  digitalWrite(Xenable, HIGH); // Disable motor
  digitalWrite(Yenable, HIGH); // Disable motor
  digitalWrite(Zenable, HIGH); // Disable motor

  delay(100);

  // Fan control
  pinMode(CurrentPin, OUTPUT); // Power supply analog in (I)
  pinMode(VoltagePin, OUTPUT); // Power supply analog in (U)
  analogWrite(CurrentPin, 0);  // Set the current - this is changed by the PID controller
  analogWrite(VoltagePin, 45); // Set the maximum voltage (255 = 5V analog out = 60V)

  delay(100);

  // ANALOG PINS

  // Potentiometers
  pinMode(A0, INPUT); // Poti X
  pinMode(A1, INPUT); // Poti Y

  // Baratron pressure gauges
  pinMode(A2, INPUT); // Baratron X (0-10 Torr)
  pinMode(A3, INPUT); // Baratron Y (0-10 Torr)
  pinMode(A4, INPUT); // Baratron A (0-1000 mbar)

  // CALIBRATE STEPPER MOTORS

  // Calculate X and Y bellow percentages based on the potentiometer
  byte i = 0;
  while (i < 200)
  // Integrate 200 values for better accuracy
  {
    Xpercentage += -0.12453 * analogRead(A0) + 104.83600;
    Ypercentage += -0.12438 * analogRead(A1) + 112.72790;
    i++;
  }
  Xpercentage /= 200.00;
  Ypercentage /= 200.00;

  // Set the position of the motors
  // For X and Y bellows, 0-100% are 62438 steps, at 1/8 microsteps
  Xsteps = Xpercentage * 62438.00 / 100;
  Ysteps = Ypercentage * 62438.00 / 100;
  // For Z bellow, we use 1/8 microsteps but at half the range
  Zsteps = 15960 / 2; // Start position is at 50%
  Xaxis.setCurrentPosition(Xsteps);
  Yaxis.setCurrentPosition(Ysteps);
  Zaxis.setCurrentPosition(Zsteps);

  XstartPos = Xsteps;
  YstartPos = Ysteps;
  ZstartPos = Zsteps;

  // Set the maximum speed and acceleration
  Xaxis.setMaxSpeed(50 * 32);
  Xaxis.setAcceleration(20 * 32);

  Yaxis.setMaxSpeed(50 * 32);
  Yaxis.setAcceleration(20 * 32);

  Zaxis.setMaxSpeed(50 * 16);
  Zaxis.setAcceleration(20 * 16);

  delay(1000);
}

void wait(int seconds, String message)
{
  startMillis = millis();
  while (millis() < startMillis + seconds * 1000)
  {
    sendStatus(message);
    delay(100);
  }
}

// Controlls the housing temperature
void controlT()
{
  now = millis();
  timeChange = now - lastTime;

  // Compute all the working error variables after cycle 60
  Terror = boxTemp - SPT;

  if (cycl > 60)
  {
    errSum += (Terror * timeChange / 1000);
    dErr = (Terror + lastErr) / timeChange * 1000;
    // Remember some variables for next time
    lastErr = Terror;
    lastTime = now;
  }
  cycl = cycl + 1;

  // Compute PID Output
  // The structure of the PID control string: fanSpeed = kp * Terror + ki * errSum + kd * dErr;
  fanSpeed = 390 * Terror + 0.30 * errSum + 0.030 * dErr;

  if (fanSpeed > 100)
  {
    fanSpeed = 100;
  }
  else if (fanSpeed < 0)
  {
    fanSpeed = 0;
  }

  // Set the current of the adjustable power supply
  // Each of the two fans can take max 1.86A, and they are connected in parallel
  // 255 = 5V analog out = 8A
  analogWrite(CurrentPin, fanSpeed / 100 * 40);
}

void runXP(float percentage)
{
  digitalWrite(Xenable, LOW); // Wake up the motor
  delay(100);
  if (percentage > 100)
  {
    percentage = 100;
  }
  if (percentage < 0)
  {
    percentage = 0;
  }
  XstartPos = Xaxis.currentPosition();
  long steps = (percentage * 62438.00 / 100) - Xsteps;
  sendStatus("MX");
  Xaxis.move(steps);
  while (Xaxis.currentPosition() != XstartPos + steps)
  {
    Xaxis.run();
  }
  Xsteps = Xsteps + steps;
  digitalWrite(Xenable, HIGH); // Disable motor
}

void runYP(float percentage)
{
  digitalWrite(Yenable, LOW); // Wake up the motor
  delay(100);
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
  while (Yaxis.currentPosition() != YstartPos + steps)
  {
    Yaxis.run();
  }
  Ysteps = Ysteps + steps;
  digitalWrite(Yenable, HIGH); // Disable motor
}

void runZP(float percentage)
{
  digitalWrite(Zenable, LOW); // Wake up the motor
  delay(100);
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
  while (Zaxis.currentPosition() != ZstartPos + steps)
  {
    Zaxis.run();
  }
  Zsteps = Zsteps + steps;
  digitalWrite(Zenable, HIGH); // Disable motor
}

void startingPosition()
{
  switchValve("V01C");
  switchValve("V02C");
  switchValve("V03C");
  switchValve("V04C");
  switchValve("V05O");
  switchValve("V06C");
  switchValve("V07O");
  switchValve("V08C");
  switchValve("V09C");
  switchValve("V10C");
  switchValve("V11O");
  switchValve("V12C");
  switchValve("V13O");
  switchValve("V14C");
  switchValve("V15C");
  switchValve("V16O");
  switchValve("V17O");
  switchValve("V18C");
  switchValve("V19O");
  switchValve("V20C");
  switchValve("V21C");
  switchValve("V22C");
  switchValve("V27C");
  switchValve("V28C");
  switchValve("V29C");
  switchValve("V30C");
  switchValve("V31C");
  switchValve("V32C");
  delay(50);
}

void expandX(int number)
{
  if (number == 1) // 1.5% reduction
  {
    switchValve("V06C");
    switchValve("V07O");
    wait(20, "EX");
    switchValve("V07C");
    switchValve("V06O");
    wait(5, "EX");
  }
  else if (number == 2) // 14% reduction
  {
    switchValve("V11C");
    switchValve("V16C");
    switchValve("V07O");
    wait(10, "EX");
    switchValve("V07C");
    switchValve("V16O");
    switchValve("V11O");
    wait(20, "EX");
  }
  else if (number == 3) // 32% reduction
  {
    switchValve("V16C");
    switchValve("V05O");
    switchValve("V07O");
    wait(15, "EX");
    switchValve("V07C");
    switchValve("V05C");
    switchValve("V16O");
    wait(20, "EX");
  }
}

void expandY(int number)
{
  if (number == 1) // 5.3% reduction
  {
    switchValve("V12C");
    switchValve("V13O");
    wait(20, "EY");
    switchValve("V13C");
    switchValve("V12O");
    wait(5, "EY");
  }
  else if (number == 2) // 37% reduction
  {
    switchValve("V05C");
    switchValve("V16C");
    switchValve("V13O");
    wait(10, "EY");
    switchValve("V13C");
    switchValve("V16O");
    switchValve("V05O");
    wait(20, "EY");
  }
  else if (number == 3) // 61% reduction
  {
    switchValve("V16C");
    switchValve("V11O");
    switchValve("V13O");
    wait(15, "EY");
    switchValve("V13C");
    switchValve("V11C");
    switchValve("V16O");
    wait(20, "EY");
  }
}

void refillSample(float tPress)
{
  byte expN = 0;
  sendStatus("RS");
  while (Ypressure < tPress && expN < 10)
  {
    switchValve("V22O");
    wait(20, "RS");
    switchValve("V22C");
    switchValve("V10O");
    wait(20, "RS");
    switchValve("V10C");
    wait(5, "RS");
    expN = expN + 1;
  }
}

void runIA(float pressureTarget)
{

  sendStatus("IA");
  switchValve("V21O");
  delay(10);

  unsigned long startTime = millis();

  while (Apressure <= pressureTarget && millis() - startTime <= 120000)
  {
    sendStatus("IA");
    delay(10);
  }

  switchValve("V15C");
  switchValve("V21C");
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
      break;
    }
    else if ( (Xaxis.currentPosition() * 100.0000 / 62438.00 != 100  && Xaxis.currentPosition() * 100.0000 / 62438.00 > 0) || ( (Xpressure - targetPressure) < -0.001 && Xaxis.currentPosition() * 100.0000 / 62438.00 == 100) )
    {
      // p = k / (V + V0)
      // Now calculate the k value for the current filling
      float k = Xpressure * ( Xaxis.currentPosition() * 100.0000 / 62438.00 + V0 );
      // Now calculate the target V (% bellows)
      targetPercent = k / targetPressure - V0;
      // Send the command to the bellows
      runXP(targetPercent);
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
      break;
    }
    else if ( Yaxis.currentPosition() * 100.0000 / 62438.00 != 100 || ( Yaxis.currentPosition() * 100.0000 / 62438.00 == 100 && (Ypressure - targetPressure) < -0.001 ) )
    {
      // Compress bellows
      // p = k / (V + V0)
      // Now calculate the k value for the current filling
      float k = Ypressure * ( Yaxis.currentPosition() * 100.0000 / 62438.00 + V0 );
      // Now calculate the target V (% bellows)
      targetPercent = k / targetPressure - V0;
      // Send the command to the bellows
      runYP(targetPercent);
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
      else if ((Ypressure - targetPressure) / Ypressure * 100 <= 33)
      {
        // Expand by ~5.3% steps
        sendStatus("PY");
        expandY(1);
        delay(100);
      }
    }
    else if (Yaxis.currentPosition() * 100.0000 / 62438.00 == 0)
    {
      // Too little gas
      break;
    }
  }
}

void setN2Pressure(float targetPressure)
{
  if (targetPressure > 10)
  {
    for (int a = 0; a < 10; a++)
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
      if (abs(Apressure - targetPressure) <= 0.1)
      {
        break;
      }
      else
      {
        // Compress/open bellows
        targetPercent = Zaxis.currentPosition() * 100.0000 / 15960.00 + (Apressure - targetPressure) / 0.1044;
        // Send the command to the bellows
        runZP(targetPercent);
        delay(100);
      }
    }
  }
  else
  {
    delay(100);
  }
}

void switchValve(String param)
{
  // param is a string like V03C or V12O
  int v = param.substring(1, 3).toInt(); // Get the valve number
  if (param.substring(3, 4) == "O")
  {
    // Check the case for valve 17 (turbo) and 27 (fore vacuum)
    if (v == 17)
    {
      digitalWrite(21 + 27, LOW); // Close valve 27
      delay(250);
    }
    else if (v == 27)
    {
      digitalWrite(21 + 17, LOW); // Close valve 17
      delay(250);
    }
    if (v == 19)
    {
      digitalWrite(21 + 20, LOW); // Close valve 20
      delay(250);
    }
    else if (v == 20)
    {
      digitalWrite(21 + 19, LOW); // Close valve 19
      delay(250);
    }
    digitalWrite(21 + v, HIGH); // Open valve
  }
  else if (param.substring(3, 4) == "C")
  {
    digitalWrite(21 + v, LOW); // Close valve
  }
  delay(50);
}

void switchRelay(String param)
{
  // param is a string like U01C or U02O
  int v = param.substring(1, 3).toInt();
  if (param.substring(3, 4) == "O")
  {
    digitalWrite(relayPins[v-1], LOW); // Open relay
  }
  else if (param.substring(3, 4) == "C")
  {
    digitalWrite(relayPins[v-1], HIGH); // Close relay
  }
  delay(50);
}

void sendStatus( String param )
{

  // Control the housing temperature
  sensors_event_t humidity, temp;
  shtc3.getEvent(&humidity, &temp);
  boxTemp = temp.temperature;
  boxHum = humidity.relative_humidity;
  controlT();

  // Get all the current settings
  Xpressure = analogRead(A2) * 5.00 * 1.333224 / 1024.00; // 0-10 Torr Baratron
  Ypressure = analogRead(A3) * 5.00 * 1.333224 / 1024.00; // 0-10 Torr Baratron
  Apressure = analogRead(A4) * 500.00 / 1024;             // 0-1000 mbar Baratron
  Xpercentage = -0.12453 * analogRead(A0) + 104.83600;
  Ypercentage = -0.12438 * analogRead(A1) + 112.72790;

  // Integrate temperatures and pressures
  int n = 50; // Integration cycles
  for (int i = 0; i < n; i++)
  {
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

  for (int i = 0; i < n; i++)
  {
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
  // Divide Xpressure by pCO2Sam/pCO2Ref
  // If divided <1, then the reference pCO2 decreases
  Xpressure = (Xpressure / n - 0.300) / 0.970942 * 0.952011 / 1.001206 / 1.001642 / 0.99888 / 0.997630; // Reference gas bellow
  Ypressure = (Ypressure / n - 0.265);  // Gauge Y, sample bellow
  Apressure = Apressure / n - 5.0;      // Gauge A

  Xpercentage = Xpercentage / n;
  Ypercentage = Ypercentage / n;
  boxTemp = boxTemp / n;

  // Get valve states
  valveStatus = "";
  for (byte pinNr = 22; pinNr <= 53; pinNr++) {
    valveStatus += digitalRead(pinNr) == LOW ? "0" : "1";
  }
  // Get relay states
  relayStatus = "";
  for (byte relayPinNr = 0; relayPinNr <= 1; relayPinNr++) {
    relayStatus += digitalRead(relayPins[relayPinNr]) == LOW ? "1" : "0";
  }

  // Clear the JSON string
  doc.clear();

  // Create a JSON string with keys
  doc["moveStatus"] = param;
  doc["X_position"] = String(Xaxis.currentPosition() * 100.0000 / 62438.00, 2);
  doc["X_percentage"] = String(Xpercentage,1);
  doc["Y_position"] = String(Yaxis.currentPosition() * 100.0000 / 62438.00, 2);
  doc["Y_percentage"] = String(Ypercentage,1);
  doc["Z_position"] = String(Zaxis.currentPosition());
  doc["Z_percentage"] = String(Zaxis.currentPosition() * 100 / 15960.00, 2);
  doc["X_pressure"] = String(Xpressure, 3);
  doc["Y_pressure"] = String(Ypressure, 3);
  doc["A_pressure"] = String(Apressure, 1);
  doc["valves"] = valveStatus;
  doc["relays"] = relayStatus;
  doc["boxHumidity"] = String(boxHum, 2);
  doc["boxTemperature"] = String(boxTemp, 2);
  doc["boxSetpoint"] = String(SPT,2);
  doc["fanSpeed"] = String(fanSpeed);

  // Serialize the JSON document
  doc.shrinkToFit();
  String jsonString = doc.as<String>();
  Serial.println(jsonString);
  Serial.flush();
}


// Here comes the main program loop ----------------------------------------------------------------

void loop()
{
  // Monitor the serial port
  while (Serial.available())
  {
    delay(10);
    command = Serial.read();
    string += command;
  }

  // Perform a function based on on the command sent by the index.html

  if (string.substring(0, 1) == "V")
  {
    // Set the valve positions
    switchValve(string);
    string = "";
    command = ' ';
    sendStatus("-");
  }

  else if (string.substring(0, 2) == "XP")
  {
    // Set the stepper motor positions
    runXP(string.substring(2, 9).toFloat());
    string = "";
    command = ' ';
    sendStatus("-");
  }

  else if (string.substring(0, 2) == "XS")
  {
    // Set the pressure in bellows X to the given pressure
    setPressureX(string.substring(2, 9).toFloat());
    string = "";
    command = ' ';
    sendStatus("-");
  }

  else if (string.substring(0, 2) == "KL")
  {
    // Resets the valves to starting position
    startingPosition();
    string = "";
    command = ' ';
    sendStatus("-");
  }

  else if (string.substring(0, 2) == "YP")
  {
    // Move bellow Y (sample side)
    runYP(string.substring(2, 9).toFloat());
    string = "";
    command = ' ';
    sendStatus("-");
  }

  else if (string.substring(0, 2) == "IA")
  {
    // Wait until gauge A reaches the required pressure - for air refill
    runIA(string.substring(2, 9).toFloat());
    string = "";
    command = ' ';
    sendStatus("-");
  }

  else if (string.substring(0, 2) == "YS")
  {
    // Set pressure in bellow Y (sample side)
    setPressureY(string.substring(2, 9).toFloat());
    string = "";
    command = ' ';
    sendStatus("-");
  }

  else if (string.substring(0, 2) == "ZP")
  {
    // Move bellow Z
    runZP(string.substring(2, 9).toFloat());
    string = "";
    command = ' ';
    sendStatus("-");
  }

  else if (string.substring(0, 2) == "SN")
  {
    // Set N2 pressure by moving the Z bellow
    setN2Pressure(string.substring(2, 9).toFloat());
    string = "";
    command = ' ';
    sendStatus("-");
  }

  else if (string.substring(0, 2) == "RS")
  {
    // Refill sample from manifold
    // To work, this function needs a starting position, and
    // that the sample gas is aleady in the manifold and not the autofinger
    refillSample(string.substring(2, 9).toFloat());
    string = "";
    command = ' ';
    sendStatus("-");
  }

  else if (string.substring(0, 1) == "U")
  {
    // Switch the relays
    switchRelay(string);
    string = "";
    command = ' ';
    sendStatus("-");
  }

  // Print out the current settings
  sendStatus("-");

  delay(20);

}