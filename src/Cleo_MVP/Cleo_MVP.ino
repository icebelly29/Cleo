#include <Wire.h>
#include <Adafruit_VL53L0X.h>
#include <Arduino_RouterBridge.h>
#include <Servo.h>

Adafruit_VL53L0X lox = Adafruit_VL53L0X();

// --- CUSTOM ADAFRUIT MOTOR SHIELD V1 DRIVER ---
#define MOTORLATCH 12
#define MOTORCLK 4
#define MOTORENABLE 7
#define MOTORDATA 8

#define MOTOR1_A 2
#define MOTOR1_B 3
#define MOTOR2_A 1
#define MOTOR2_B 4
#define MOTOR3_A 5
#define MOTOR3_B 7

#define MOTOR1_PWM 11
#define MOTOR2_PWM 3
#define MOTOR3_PWM 6

#define FORWARD 1
#define BACKWARD 2
#define RELEASE 3

uint8_t latch_state = 0;

void setupMotors() {
  pinMode(MOTORLATCH, OUTPUT);
  pinMode(MOTORENABLE, OUTPUT);
  pinMode(MOTORDATA, OUTPUT);
  pinMode(MOTORCLK, OUTPUT);
  
  latch_state = 0;
  latch_tx();
  digitalWrite(MOTORENABLE, LOW);
  
  pinMode(MOTOR1_PWM, OUTPUT);
  pinMode(MOTOR2_PWM, OUTPUT);
  pinMode(MOTOR3_PWM, OUTPUT);
}

void latch_tx() {
  digitalWrite(MOTORLATCH, LOW);
  shiftOut(MOTORDATA, MOTORCLK, MSBFIRST, latch_state);
  digitalWrite(MOTORLATCH, HIGH);
}

void runMotor(int motor, int command, int speed) {
  int a, b, pwm;
  if (motor == 1) { a = MOTOR1_A; b = MOTOR1_B; pwm = MOTOR1_PWM; }
  else if (motor == 2) { a = MOTOR2_A; b = MOTOR2_B; pwm = MOTOR2_PWM; }
  else if (motor == 3) { a = MOTOR3_A; b = MOTOR3_B; pwm = MOTOR3_PWM; }
  else return;

  // Invert direction for drive motors 1 and 2 to match wiring polarity
  if (motor == 1 || motor == 2) {
    if (command == FORWARD) command = BACKWARD;
    else if (command == BACKWARD) command = FORWARD;
  }

  if (command == FORWARD) {
    latch_state |= (1 << a);
    latch_state &= ~(1 << b);
  } else if (command == BACKWARD) {
    latch_state &= ~(1 << a);
    latch_state |= (1 << b);
  } else if (command == RELEASE) {
    latch_state &= ~(1 << a);
    latch_state &= ~(1 << b);
  }
  
  latch_tx();
  
  // FIX: On the Uno Q, analogWrite() conflicts with the Servo timer!
  // We use digitalWrite instead to run motors at full speed without breaking the servo.
  if (speed > 0) {
    digitalWrite(pwm, HIGH);
  } else {
    digitalWrite(pwm, LOW);
  }
}
// ----------------------------------------------

Servo panServo;
const int servoPin = 10;
const int obstacleThreshold = 250; // Millimeters

// Sweep variables
int servoPos = 90;
int servoDirection = 1;
unsigned long lastSweepTime = 0;

bool autonomousMode = true;
bool suctionEnabled = true;

// State Machine for Autonomous Mode
enum RobotState { 
  STATE_DRIVING, 
  STATE_REVERSING
};
RobotState currentState = STATE_DRIVING;
unsigned long stateStartTime = 0;
const unsigned long MIN_REVERSE_DURATION = 1200; // Milliseconds to reverse upon obstacle

// RPC Wrapper Functions
void rpcToggleMode() {
  autonomousMode = !autonomousMode;
  if (autonomousMode) {
    currentState = STATE_DRIVING;
    stateStartTime = millis();
    driveForward();
  } else {
    stopMotors();
  }
}

void rpcToggleSuction() {
  suctionEnabled = !suctionEnabled;
  if (suctionEnabled) runMotor(3, FORWARD, 255);
  else runMotor(3, RELEASE, 0);
}

void rpcForward() { autonomousMode = false; driveForward(); }
void rpcReverse() { autonomousMode = false; driveReverse(); }
void rpcLeft() { autonomousMode = false; turnLeft(); }
void rpcRight() { autonomousMode = false; turnRight(); }
void rpcForwardLeft() { autonomousMode = false; driveForwardLeft(); }
void rpcForwardRight() { autonomousMode = false; driveForwardRight(); }
void rpcReverseLeft() { autonomousMode = false; driveReverseLeft(); }
void rpcReverseRight() { autonomousMode = false; driveReverseRight(); }
void rpcStop() { autonomousMode = false; stopMotors(); }

void rpcTestShake() {
  autonomousMode = false;
  stopMotors();
  for (int i = 0; i < 4; i++) {
    panServo.write(45);
    delay(150);
    panServo.write(135);
    delay(150);
  }
  panServo.write(90);
}

void rpcTestArc() {
  autonomousMode = false;
  stopMotors();
  panServo.write(45);
  delay(400);
  panServo.write(135);
  delay(400);
  panServo.write(90);
}

void setup() {
  Serial.begin(115200);
  setupMotors();
  Bridge.begin();
  
  Bridge.provide("mode", rpcToggleMode);
  Bridge.provide("suction", rpcToggleSuction);
  Bridge.provide("forward", rpcForward);
  Bridge.provide("reverse", rpcReverse);
  Bridge.provide("left", rpcLeft);
  Bridge.provide("right", rpcRight);
  Bridge.provide("forward_left", rpcForwardLeft);
  Bridge.provide("forward_right", rpcForwardRight);
  Bridge.provide("reverse_left", rpcReverseLeft);
  Bridge.provide("reverse_right", rpcReverseRight);
  Bridge.provide("stop", rpcStop);
  Bridge.provide("test_shake", rpcTestShake);
  Bridge.provide("test_arc", rpcTestArc);

  if (!lox.begin()) {
    Serial.println("Error: VL53L0X sensor not found.");
  }
  panServo.attach(servoPin);
  panServo.write(90);

  if (suctionEnabled) runMotor(3, FORWARD, 255);
  if (autonomousMode) driveForward();
  else stopMotors();
}

void loop() {
  Bridge.update();

  if (autonomousMode) {
    runAutonomousLogic();
  } else {
    updateServo();
  }
}

void updateServo() {
  if (millis() - lastSweepTime > 50) {
    lastSweepTime = millis();
    servoPos += servoDirection * 5;
    if (servoPos >= 180) {
      servoPos = 180;
      servoDirection = -1;
    } else if (servoPos <= 0) {
      servoPos = 0;
      servoDirection = 1;
    }
    panServo.write(servoPos);
  }
}

void runAutonomousLogic() {
  unsigned long now = millis();

  // Continuously scan the area with the servo
  updateServo();

  // Read distance from Time-of-Flight sensor
  VL53L0X_RangingMeasurementData_t measurement;
  lox.rangingTest(&measurement, false);
  int distance = (measurement.RangeStatus != 4) ? measurement.RangeMilliMeter : 8190;

  switch (currentState) {
    case STATE_DRIVING:
      // Drive forward by default
      if (distance <= obstacleThreshold) {
        // Only drive back when met with an obstacle
        driveReverse();
        currentState = STATE_REVERSING;
        stateStartTime = now;
      } else {
        driveForward();
      }
      break;

    case STATE_REVERSING:
      // Drive back until the minimum duration passes AND the obstacle is clear
      if ((now - stateStartTime >= MIN_REVERSE_DURATION) && (distance > obstacleThreshold + 50)) {
        driveForward();
        currentState = STATE_DRIVING;
      } else {
        driveReverse();
      }
      break;

    default:
      currentState = STATE_DRIVING;
      driveForward();
      break;
  }
}

void driveForward() {
  runMotor(1, FORWARD, 255);
  runMotor(2, FORWARD, 255);
}
void driveReverse() {
  runMotor(1, BACKWARD, 255);
  runMotor(2, BACKWARD, 255);
}
void turnRight() {
  runMotor(1, FORWARD, 255);
  runMotor(2, BACKWARD, 255);
}
void turnLeft() {
  runMotor(1, BACKWARD, 255);
  runMotor(2, FORWARD, 255);
}
void driveForwardRight() {
  runMotor(1, FORWARD, 255);
  runMotor(2, RELEASE, 0);
}
void driveForwardLeft() {
  runMotor(1, RELEASE, 0);
  runMotor(2, FORWARD, 255);
}
void driveReverseRight() {
  runMotor(1, BACKWARD, 255);
  runMotor(2, RELEASE, 0);
}
void driveReverseLeft() {
  runMotor(1, RELEASE, 0);
  runMotor(2, BACKWARD, 255);
}
void stopMotors() {
  runMotor(1, RELEASE, 0);
  runMotor(2, RELEASE, 0);
}
