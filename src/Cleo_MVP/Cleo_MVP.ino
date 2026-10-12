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
  STATE_STOPPING, 
  STATE_TURNING, 
  STATE_INVESTIGATIVE_ARC,
  STATE_FRUSTRATED_SHAKE,
  STATE_STUCK_SHUTDOWN
};
RobotState currentState = STATE_DRIVING;
unsigned long stateStartTime = 0;
int animationStep = 0;

// Anomaly Detection (TinyML) Data
const int HISTORY_SIZE = 20;
int distanceHistory[HISTORY_SIZE];
int historyIndex = 0;
bool historyFull = false;
unsigned long lastHistoryUpdate = 0;
unsigned long lastStuckTime = 0;
const unsigned long STUCK_COOLDOWN = 15000;

void clearHistory() {
  historyFull = false;
  historyIndex = 0;
}

void addDistanceToHistory(int distance) {
  if (millis() - lastHistoryUpdate > 500) {
    distanceHistory[historyIndex] = distance;
    historyIndex++;
    if (historyIndex >= HISTORY_SIZE) {
      historyIndex = 0;
      historyFull = true;
    }
    lastHistoryUpdate = millis();
  }
}

bool isRobotStuck() {
  if (!historyFull) return false;
  // Cooldown: do not trigger if a stuck event occurred recently
  if (millis() - lastStuckTime < STUCK_COOLDOWN) return false;
  
  int minDist = 9999;
  int maxDist = 0;
  for (int i=0; i<HISTORY_SIZE; i++) {
    if (distanceHistory[i] < minDist) minDist = distanceHistory[i];
    if (distanceHistory[i] > maxDist) maxDist = distanceHistory[i];
  }
  
  // Anomaly: If variance over 10 seconds is less than 50mm, the robot is stuck
  return (maxDist - minDist < 50);
}


// RPC Wrapper Functions
void rpcToggleMode() {
  autonomousMode = !autonomousMode;
  if (autonomousMode) {
    clearHistory();
    lastStuckTime = millis();
    currentState = STATE_DRIVING;
    stateStartTime = millis();
    animationStep = 0;
    driveForward();
  } else {
    currentState = STATE_DRIVING;
    animationStep = 0;
    stopMotors();
  }
}

void rpcToggleSuction() {
  suctionEnabled = !suctionEnabled;
  if (suctionEnabled) runMotor(3, FORWARD, 255);
  else runMotor(3, RELEASE, 0);
}

void rpcForward() { if (!autonomousMode) driveForward(); }
void rpcReverse() { if (!autonomousMode) driveReverse(); }
void rpcLeft() { if (!autonomousMode) turnLeft(); }
void rpcRight() { if (!autonomousMode) turnRight(); }
void rpcStop() { if (!autonomousMode) stopMotors(); }

void rpcTestShake() {
  stopMotors();
  autonomousMode = true;
  currentState = STATE_FRUSTRATED_SHAKE;
  stateStartTime = millis();
}

void rpcTestArc() {
  stopMotors();
  autonomousMode = true;
  currentState = STATE_INVESTIGATIVE_ARC;
  stateStartTime = millis();
  animationStep = 0;
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

  // Read distance
  VL53L0X_RangingMeasurementData_t measurement;
  lox.rangingTest(&measurement, false);
  int distance = (measurement.RangeStatus != 4) ? measurement.RangeMilliMeter : 8190;

  switch (currentState) {
    case STATE_DRIVING:
      updateServo();
      addDistanceToHistory(distance);

      // AI Anomaly Detection: Are we stuck?
      if (isRobotStuck()) {
        stopMotors();
        lastStuckTime = now;
        currentState = STATE_FRUSTRATED_SHAKE;
        stateStartTime = now;
        break;
      }

      // Standard Obstacle Avoidance
      if (distance <= obstacleThreshold) {
        stopMotors();
        currentState = STATE_STOPPING;
        stateStartTime = now;
      }
      break;

    case STATE_STOPPING:
      if (now - stateStartTime >= 100) {
        currentState = STATE_INVESTIGATIVE_ARC;
        stateStartTime = now;
        animationStep = 0;
      }
      break;

    case STATE_INVESTIGATIVE_ARC:
      // Organic Personality: Cautiously backup and look around
      if (animationStep == 0) {
        runMotor(1, BACKWARD, 255);
        runMotor(2, BACKWARD, 255);
        panServo.write(45);
        animationStep = 1;
      } else if (animationStep == 1 && now - stateStartTime >= 400) {
        panServo.write(135);
        animationStep = 2;
      } else if (animationStep == 2 && now - stateStartTime >= 800) {
        panServo.write(90);
        if (servoPos < 90) turnLeft();
        else turnRight();
        currentState = STATE_TURNING;
        stateStartTime = now;
      }
      break;

    case STATE_TURNING:
      if (now - stateStartTime >= 500) {
        panServo.write(90);
        servoPos = 90;
        clearHistory(); // Reset anomaly history
        driveForward();
        currentState = STATE_DRIVING;
      }
      break;

    case STATE_FRUSTRATED_SHAKE:
      // Organic Personality: Rapid wiggle to show frustration
      if (now - stateStartTime < 1500) {
        // Servo-only shake: BO motors stay off
        stopMotors();
        int shakeCycle = ((now - stateStartTime) / 150) % 2;
        if (shakeCycle == 0) {
          panServo.write(45);
        } else {
          panServo.write(135);
        }
      } else if (now - stateStartTime < 2500) {
        // Phase 2: Reverse for 1 second to clear the obstacle
        panServo.write(90);
        driveReverse();
      } else {
        // Phase 3: Turn and resume
        servoPos = 90;
        turnRight();
        currentState = STATE_TURNING;
        stateStartTime = now;
        clearHistory();
      }
      break;

    case STATE_STUCK_SHUTDOWN:
      // Fallback: sweep servo and wait for user rescue via Web UI
      updateServo();
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
void stopMotors() {
  runMotor(1, RELEASE, 0);
  runMotor(2, RELEASE, 0);
}
