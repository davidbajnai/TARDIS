#include <AccelStepper.h>
#include "Adafruit_SHTC3.h"
#include <ArduinoJson.h>
#include <RunningMedian.h>

// Initialize the variables --------------------------------------------------------------------

Adafruit_SHTC3 shtc3 = Adafruit_SHTC3(); // Temperature sensor
long XstartPos = 0;
long YstartPos = 0;
long ZstartPos = 0;
long steps = 0;
char command;
String string;
float X_percentage = 0.0f;
float Y_percentage = 0.0f;
float Zpercentage = 0.0f;
float X_pressure = 0.0f;
float Y_pressure = 0.0f;
float Z_pressure = 0.0f;
float D_pressure = 0.0f;
const byte n = 50; // Integration cycles (4 seconds at 12.4 Hz)
RunningMedian X_pressure_Array = RunningMedian(n);
RunningMedian Y_pressure_Array = RunningMedian(n);
RunningMedian Z_pressure_Array = RunningMedian(n);
RunningMedian X_percentage_Array = RunningMedian(n);
RunningMedian Y_percentage_Array = RunningMedian(n);
RunningMedian boxTemperature_Array = RunningMedian(n);
RunningMedian boxHumidity_Array = RunningMedian(n);
RunningMedian D_pressureArray = RunningMedian(n);
float fanSpeed = 0.0f;
float boxTemperature = 0.0f;
const float boxSetpoint = 32.5f; // Set the housing temperature here
float boxHumidity = 0.0f;
unsigned long lastTime = 0;
unsigned long startTime = 0;
float errSum = 0.0f;
float lastErr = 0.0f;
float targetPercent = 0.0f;
long Xsteps = 0;
long Ysteps = 0;
long Zsteps = 0;
unsigned long startMillis = 0;
String valveStatus;
String relayStatus;
StaticJsonDocument<350> doc;
String jsonString;
float arduinoSpeed;


// Define the pinout ---------------------------------------------------------------------------

// Stepper motor control
AccelStepper Xaxis(AccelStepper::DRIVER, 3, 2); // mode, step, direction
const byte Xenable = 4;
AccelStepper Yaxis(AccelStepper::DRIVER, 6, 5);
const byte Yenable = 7;
AccelStepper Zaxis(AccelStepper::DRIVER, 9, 8);
const byte Zenable = 10;

// Pins for the relays
const byte relayPins[] = {18, 19};

// Temperature control
const byte CurrentPin = 11;
const byte VoltagePin = 12;

// Baratron pressure gauges
const byte pinBaratronX = A2;
const byte pinBaratronY = A3;
const byte pinBaratronZ = A7;

// DeltaPlus pressure gauge
const byte pinDeltaPlus = A6;

// Potentiometers
const byte pinPotiX = A0;
const byte pinPotiY = A1;

// Functions for reading out the sensors -------------------------------------------------------

// Do the calibration and zero-ing here!

float readBaratronX() // Reference bellow, 0-10 Torr, 10V Baratron
{
  constexpr float conversion = 5.0f / 1023.0f;
  return (analogRead(pinBaratronX) * conversion) - 0.2294f;
}

float readBaratronY() // Sample bellow, 0-10 Torr, 10V Baratron
{
  constexpr float conversion = 5.0f / 1023.0f;
  return (analogRead(pinBaratronY) * conversion) - 0.203f;
}

float readBaratronZ() // Pressure adjust bellow, 0-500 mBar, 5V Baratron
{
  constexpr float conversion = 500.0f / 1023.0f;
  return (analogRead(pinBaratronZ) * conversion) * 0.750062f - 0.15f;
}

// Function to read the DeltaPlus pressure gauge
float readDeltaPlus()
{
  return analogRead(pinDeltaPlus) * 0.44f - 0.f;
}


// Functions for the potentiometers
float percentageX_fromPoti()
{
  return -0.12453f * analogRead(pinPotiX) + 104.83600f;
}

float percentageY_fromPoti()
{
  return -0.12438f * analogRead(pinPotiY) + 112.72790f;
}

// Functions for the stepper motors
float percentageX_fromSteps()
{
  constexpr float multiplier = 100.0f / 62438.0f;
  return Xaxis.currentPosition() * multiplier;
}

float percentageY_fromSteps()
{
  constexpr float multiplier = 100.0f / 62438.0f;
  return Yaxis.currentPosition() * multiplier;
}

float percentageZ_fromSteps()
{
  constexpr float multiplier = 100.0f / 15960.0f;
  return Zaxis.currentPosition() * multiplier;
}


// Setup ---------------------------------------------------------------------------------------
void setup()
{
  Serial.begin(115200);

  // Wait for serial port to open
  while (!Serial)
  {
    delay(10);
  }

  // Start temperature sensor
  shtc3.begin();

  delay(4000);

  // DIGITAL PINS

  // Pinout for valve control
  for (int pinNr = 22; pinNr <= 53; pinNr++)
  {
    pinMode(pinNr, OUTPUT);
    delay(10);
  }

  // Pinout for relay control
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
  // Set the current to 0
  // This is changed by the PID controller in controlT()
  analogWrite(CurrentPin, 0);
  // Set the maximum voltage
  // 255 on PWM pin = 5V analog out = 60V
  // 30 on PWM pin = 0.583V analog out = 7V
  analogWrite(VoltagePin, 30); // Set the maximum voltage

  delay(100);

  // ANALOG PINS

  // Potentiometers
  pinMode(pinPotiX, INPUT); // Poti X
  pinMode(pinPotiY, INPUT); // Poti Y

  // Baratron pressure gauges
  pinMode(pinBaratronX, INPUT); // Baratron X (0-10 Torr)
  pinMode(pinBaratronY, INPUT); // Baratron Y (0-10 Torr)
  pinMode(pinBaratronZ, INPUT); // Baratron Z (0-1000 mbar)

  // DeltaPlus pressure gauge
  pinMode(pinDeltaPlus, INPUT); // DeltaPlus pressure gauge

  // CALIBRATE STEPPER MOTORS

  // Calculate X and Y bellow percentages based on the potentiometer
  byte i = 0;
  while (i < 200)
  // Integrate 200 values for better accuracy
  {
    X_percentage += percentageX_fromPoti();
    Y_percentage += percentageY_fromPoti();
    i++;
  }
  X_percentage /= 200.00;
  Y_percentage /= 200.00;

  // Set the position of the motors
  // For X and Y bellows, 0-100% are 62438 steps, at 1/8 microsteps
  Xsteps = X_percentage * 62438.00 / 100;
  Ysteps = Y_percentage * 62438.00 / 100;
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

  startTime = millis();

  delay(1000);
}

// Some functions for the program ---------------------------------------------------------------
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
  unsigned long now = millis();

  if (now - startTime < 3000)
    return;

  unsigned long dt = now - lastTime;
  float error = boxTemperature - boxSetpoint;

  const float Kp = 370.0f;
  const float Ki = 0.34f;
  const float Kd = 0.055f;

  // Convert to seconds only when needed
  errSum += error * (dt / 1000.0f);
  float dErr = (error - lastErr) / (dt / 1000.0f);

  fanSpeed = Kp * error + Ki * errSum + Kd * dErr;

  if (fanSpeed > 100 || boxTemperature > (boxSetpoint + 0.5f))
    fanSpeed = 100;
  else if (fanSpeed < 0)
    fanSpeed = 0;

  // Update state
  lastErr = error;
  lastTime = now;

  // Set the current of the adjustable power supply
  // 255 on PWM pin = 5V analog out = 8A
  // 64 on PWM pin = 1.25V analog out = 2A (max current)
  // when the fanSpeed is 100, the PWM pin should be 64
  const float scaling = 0.64f;
  analogWrite(CurrentPin, fanSpeed * scaling);
}

void moveBellowX(float percentage)
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
  long steps = (percentage * 62438.0f / 100) - Xsteps;
  sendStatus("MX");
  Xaxis.move(steps);
  while (Xaxis.currentPosition() != XstartPos + steps)
  {
    Xaxis.run();
  }
  Xsteps = Xsteps + steps;
  digitalWrite(Xenable, HIGH); // Disable motor
}

void moveBellowY(float percentage)
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
  long steps = percentage * 62438.0f / 100 - Ysteps;
  sendStatus("MY");
  Yaxis.move(steps);
  while (Yaxis.currentPosition() != YstartPos + steps)
  {
    Yaxis.run();
  }
  Ysteps = Ysteps + steps;
  digitalWrite(Yenable, HIGH); // Disable motor
}

void moveBellowZ(float percentage)
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
  switchValve("V05O"); // Open
  switchValve("V06C");
  switchValve("V07O"); // Open
  switchValve("V08C");
  switchValve("V09C");
  switchValve("V10C");
  switchValve("V11O"); // Open
  switchValve("V12C");
  switchValve("V13O"); // Open
  switchValve("V14C");
  switchValve("V15C");
  switchValve("V16C");
  switchValve("V17O"); // Open
  switchValve("V18C");
  switchValve("V19O"); // Open
  switchValve("V20C");
  switchValve("V21O"); // Open
  switchValve("V22C");
  switchValve("V27C");
  switchValve("V28O"); // Open
  switchValve("V29C");
  switchValve("V30C");
  switchValve("V31C");
  switchValve("V32C");
  delay(50);
}

void expandX(int number)
{
  if (number == 1) // 6% reduction
  {
    switchValve("V13C");
    switchValve("V06C");
    switchValve("V07O");
    wait(20, "EX");
    switchValve("V07C");
    switchValve("V06O");
    wait(5, "EX");
    switchValve("V13O");
  }
  else if (number == 2) // 35% reduction
  {
    switchValve("V11C");
    switchValve("V28C");
    switchValve("V07O");
    wait(10, "EX");
    switchValve("V07C");
    switchValve("V28O");
    wait(20, "EX");
    switchValve("V11O");
  }
  else if (number == 3) // 60% reduction
  {
    switchValve("V28C");
    switchValve("V19C");
    switchValve("V05O");
    switchValve("V07O");
    wait(15, "EX");
    switchValve("V07C");
    switchValve("V05C");
    switchValve("V28O");
    wait(20, "EX");
    switchValve("V19C");
  }
}

void expandY(int number)
{
  if (number == 1) // 6% reduction
  {
    switchValve("V07C");
    switchValve("V12C");
    switchValve("V13O");
    wait(20, "EY");
    switchValve("V13C");
    switchValve("V12O");
    wait(5, "EY");
    switchValve("V07O");
  }
  else if (number == 2) // 35% reduction
  {
    switchValve("V05C");
    switchValve("V28C");
    switchValve("V13O");
    wait(10, "EY");
    switchValve("V13C");
    switchValve("V28O");
    wait(20, "EY");
    switchValve("V05O");
  }
  else if (number == 3) // 65% reduction
  {
    switchValve("V28C");
    switchValve("V19C");
    switchValve("V11O");
    switchValve("V13O");
    wait(15, "EY");
    switchValve("V13C");
    switchValve("V11C");
    switchValve("V28O");
    wait(20, "EY");
    switchValve("V19O");
  }
}

void refillSampleFromManifold(float targetPressure)
{
  byte attempt = 0;
  while (Y_pressure < targetPressure && attempt++ < 10)
  {
    switchValve("V22O");
    wait(15, "RS");
    switchValve("V22C");
    switchValve("V10O");
    wait(15, "RS");
    switchValve("V10C");
  }
}

// Function to wait for a sample to be ready from the KIEL
void waitForKiel()
{
  sendStatus("WK");
  delay(10);

  unsigned long startTime = millis();
  const unsigned long maxWait = 9000000; // 2.5 hours

  while (D_pressure <= 15 && millis() - startTime <= maxWait)
  {
    sendStatus("WK");
    delay(10);
  }

}

void setPressureX(float targetPressure)
{
  const float V0 = 41.008f; // This is a instrument constant for bellows X
  for (byte a = 0; a < 10; a++)
  {
    // Wait a little and get pressure
    const byte m = 100;
    for (byte j = 0; j < m; j++)
    {
      sendStatus("PX");
      delay(10);
    }
    delay(100);
    // Decide what to do
    if (abs(X_pressure - targetPressure) <= 0.001 || percentageX_fromSteps() <= 1)
    {
      break;
    }
    else if (percentageX_fromSteps() != 100 || ((X_pressure - targetPressure) < -0.001 && percentageX_fromSteps() == 100))
    {
      // Adjust the bellow; p = k / (V + V0)
      float k = X_pressure * (percentageX_fromSteps() + V0);
      targetPercent = k / targetPressure - V0;
      
      // Send the command to the bellows
      moveBellowX(targetPercent);
      sendStatus("PX");
      delay(100);
    }
    else if (percentageX_fromSteps() == 100)
    {
      // Expand gas. This is only relevant when refilling the bellows
      // Now decide which route should be evacuated
      if ((X_pressure - targetPressure) / X_pressure * 100 > 60)
      {
        sendStatus("PX");
        expandX(3);
      }
      else if ((X_pressure - targetPressure) / X_pressure * 100 <= 60 && (X_pressure - targetPressure) / X_pressure * 100 > 35)
      {
        sendStatus("PX");
        expandX(2);
      }
      else if ((X_pressure - targetPressure) / X_pressure * 100 <= 35)
      {
        sendStatus("PX");
        expandX(1);
      }
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
  for (byte a = 0; a < 10; a++)
  {
    // Wait a little and get pressure
    const byte m = 100;
    for (byte j = 0; j < m; j++)
    {
      sendStatus("PY");
      delay(10);
    }
    delay(100);

    // Now decide what to do
    if (abs(Y_pressure - targetPressure) <= 0.001 || percentageY_fromSteps() <= 1)
    {
      break;
    }
    else if (percentageY_fromSteps() != 100 || (percentageY_fromSteps() == 100 && (Y_pressure - targetPressure) < -0.001))
    {
      // Adjust the bellow; p = k / (V + V0)
      float k = Y_pressure * (percentageY_fromSteps() + V0);
      targetPercent = k / targetPressure - V0;

      // Send the command to the bellows
      moveBellowY(targetPercent);
      sendStatus("PY");
      delay(100);
    }
    else if (percentageY_fromSteps() == 100)
    {
      // Expand gas. This is only relevant when refilling the bellows
      // Now decide which route should be evacuated
      if ((Y_pressure - targetPressure) / Y_pressure * 100 > 60)
      {
        sendStatus("PY");
        expandY(3);
        delay(100);
      }
      else if ((Y_pressure - targetPressure) / Y_pressure * 100 <= 60 && (Y_pressure - targetPressure) / Y_pressure * 100 > 35)
      {
        sendStatus("PY");
        expandY(2);
        delay(100);
      }
      else if ((Y_pressure - targetPressure) / Y_pressure * 100 <= 35)
      {
        sendStatus("PY");
        expandY(1);
        delay(100);
      }
    }
    else
    {
      break;
    }
  }
}

void setCollisionGasPressure(float targetPressure)
{
  if (targetPressure > 10)
  {
    for (byte a = 0; a < 5; a++)
    {
      // Get current pressure
      const byte m = 100; // Integration cycles
      for (byte j = 0; j < m; j++)
      {
        sendStatus("SN");
        delay(10);
      }
      delay(100);
      // Now decide what to do
      if (abs(Z_pressure - targetPressure) <= 0.1)
      {
        break;
      }
      else
      {
        // Compress/open bellows
        targetPercent = percentageZ_fromSteps() + (Z_pressure - targetPressure) / 0.08f;
        // Send the command to the bellows
        moveBellowZ(targetPercent);
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
    digitalWrite(relayPins[v - 1], LOW); // Open relay
  }
  else if (param.substring(3, 4) == "C")
  {
    digitalWrite(relayPins[v - 1], HIGH); // Close relay
  }
  delay(50);
}

void sendStatus(String param)
{

  // Get sensor readings
  sensors_event_t humidity, temp;
  shtc3.getEvent(&humidity, &temp);

  // Add the sensor and pressure readings to arrays
  X_pressure_Array.add(readBaratronX());
  Y_pressure_Array.add(readBaratronY());
  Z_pressure_Array.add(readBaratronZ());
  X_percentage_Array.add(percentageX_fromPoti());
  Y_percentage_Array.add(percentageY_fromPoti());
  boxTemperature_Array.add(temp.temperature);
  boxHumidity_Array.add(humidity.relative_humidity);
  D_pressureArray.add(readDeltaPlus());

  // Get the averages
  X_pressure = X_pressure_Array.getAverage();
  Y_pressure = Y_pressure_Array.getAverage();
  Z_pressure = Z_pressure_Array.getAverage();
  X_percentage = X_percentage_Array.getAverage();
  Y_percentage = Y_percentage_Array.getAverage();
  boxTemperature = boxTemperature_Array.getAverage();
  boxHumidity = boxHumidity_Array.getAverage();
  D_pressure = D_pressureArray.getAverage();

  // Control the fan speed
  controlT();

  // Get valve states
  valveStatus = "";
  for (byte pinNr = 22; pinNr <= 53; pinNr++)
  {
    valveStatus += digitalRead(pinNr) == LOW ? "0" : "1";
  }
  // Get relay states
  relayStatus = "";
  for (byte relayPinNr = 0; relayPinNr <= 1; relayPinNr++)
  {
    relayStatus += digitalRead(relayPins[relayPinNr]) == LOW ? "1" : "0";
  }

  // Clear the JSON string
  doc.clear();

  // Create a JSON string with keys
  doc["moveStatus"] = param;
  doc["X_position"] = String(percentageX_fromSteps(), 2);
  doc["X_percentage"] = String(X_percentage, 1);
  doc["Y_position"] = String(percentageY_fromSteps(), 2);
  doc["Y_percentage"] = String(Y_percentage, 1);
  doc["Z_position"] = String(Zaxis.currentPosition());
  doc["Z_percentage"] = String(percentageZ_fromSteps(), 2);
  doc["X_pressure"] = String(X_pressure, 3);
  doc["Y_pressure"] = String(Y_pressure, 3);
  doc["Z_pressure"] = String(Z_pressure, 1);
  doc["valveArray"] = valveStatus;
  doc["relayArray"] = relayStatus;
  doc["boxHumidity"] = String(boxHumidity, 2);
  doc["boxTemperature"] = String(boxTemperature, 4);
  doc["boxSetpoint"] = String(boxSetpoint, 2);
  doc["fanSpeed"] = String(fanSpeed, 2);
  doc["D_pressure"] = String(D_pressure, 1);
  doc["arduinoSpeed"] = String(arduinoSpeed, 0);

  // Serialize the JSON document
  doc.shrinkToFit();
  String jsonString = doc.as<String>();
  Serial.println(jsonString);
  Serial.flush();
}

// Here comes the main program loop ----------------------------------------------------------------

void loop()
{

  // Measure the speed of the Arduino
  static unsigned long prevMicros = 0;
  unsigned long nowMicros = micros();
  unsigned long loopDuration = nowMicros - prevMicros;
  prevMicros = nowMicros;
  if (loopDuration > 0) {
    arduinoSpeed = 1000000.0 / loopDuration; // Hz = 1 / seconds, micros to seconds
  }

  // Monitor the serial port
  while (Serial.available())
  {
    delay(10);
    command = Serial.read();
    string += command;
  }

  // Perform a function based on on the command sent by the index.html

  if (string.startsWith("V"))
  {
    // Set the valve positions
    switchValve(string);
    string = "";
    command = ' ';
    sendStatus("-");
  }

  else if (string.startsWith("U"))
  {
    // Switch the relays
    switchRelay(string);
    string = "";
    command = ' ';
    sendStatus("-");
  }

  else if (string.startsWith("PY"))
  {
    // Set pressure in bellow Y (sample side)
    setPressureY(string.substring(2).toFloat());
    string = "";
    command = ' ';
    sendStatus("-");
  }

  else if (string.startsWith("PX"))
  {
    // Set the pressure in bellow X (reference side)
    setPressureX(string.substring(2).toFloat());
    string = "";
    command = ' ';
    sendStatus("-");
  }

  else if (string.startsWith("BX"))
  {
    // Move bellow X (reference side)
    moveBellowX(string.substring(2).toFloat());
    string = "";
    command = ' ';
    sendStatus("-");
  }

  else if (string.startsWith("BY"))
  {
    // Move bellow Y (sample side)
    moveBellowY(string.substring(2).toFloat());
    string = "";
    command = ' ';
    sendStatus("-");
  }

  else if (string.startsWith("BZ"))
  {
    // Move bellow Z
    moveBellowZ(string.substring(2).toFloat());
    string = "";
    command = ' ';
    sendStatus("-");
  }

  else if (string.startsWith("KL"))
  {
    // Resets the valves to starting position
    startingPosition();
    string = "";
    command = ' ';
    sendStatus("-");
  }

  else if (string.startsWith("WK"))
  {
    // Wait until gauge D reaches a pressure threshold
    waitForKiel();
    string = "";
    command = ' ';
    sendStatus("-");
  }

  else if (string.startsWith("SN"))
  {
    // Set N2 pressure by moving the Z bellow
    setCollisionGasPressure(string.substring(2).toFloat());
    string = "";
    command = ' ';
    sendStatus("-");
  }

  else if (string.startsWith("RS"))
  {
    // Refill sample from manifold
    // To work, this function needs a starting position, and
    // that the sample gas is aleady in the manifold and not the autofinger
    refillSampleFromManifold(string.substring(2).toFloat());
    string = "";
    command = ' ';
    sendStatus("-");
  }

  // Print out the current settings
  sendStatus("-");

  delay(20);
}