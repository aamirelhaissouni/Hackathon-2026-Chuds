/*
 * Arduino Uno Sensor Hub for Rage-O-Meter
 * Handles: MPU6050 Gyroscope, MAX4466 Microphone, Piezo Speaker
 * Communicates with Raspberry Pi 5 via Serial (USB)
 */

#include <Wire.h>

// --- PIN CONFIGURATION ---
const int MIC_PIN = A0;           // MAX4466 analog output
const int SPEAKER_PIN = 9;        // Piezo speaker (PWM)

// --- MPU6050 CONFIGURATION ---
const int MPU_ADDR = 0x68;        // I2C address
int16_t accelX, accelY, accelZ;

// --- THRESHOLDS ---
const float SHAKE_THRESHOLD = 20000.0;  // Tune this for gyro sensitivity
const int YELL_THRESHOLD = 600;         // Tune this for mic sensitivity (0-1023)
const int SAMPLE_WINDOW = 50;           // Microphone sampling window (ms)

// --- TIMING ---
unsigned long lastSensorCheck = 0;
const unsigned long SENSOR_INTERVAL = 100; // Check sensors every 100ms

void setup() {
  Serial.begin(9600);
  
  // Initialize I2C for MPU6050
  Wire.begin();
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B);  // PWR_MGMT_1 register
  Wire.write(0);     // Wake up MPU6050
  Wire.endTransmission(true);
  
  pinMode(SPEAKER_PIN, OUTPUT);
  
  Serial.println("ARDUINO_READY");
}

void loop() {
  unsigned long currentTime = millis();
  
  // --- Check sensors at regular intervals ---
  if (currentTime - lastSensorCheck >= SENSOR_INTERVAL) {
    lastSensorCheck = currentTime;
    
    // --- Read Gyroscope ---
    bool isShaking = checkGyro();
    
    // --- Read Microphone ---
    bool isYelling = checkMicrophone();
    
    // --- Send Data to Raspberry Pi ---
    if (isShaking) {
      Serial.println("SHAKE");
    }
    if (isYelling) {
      Serial.println("YELL");
    }
  }
  
  // --- Listen for Commands from Raspberry Pi ---
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command == "BEEP") {
      playBeep();
    } else if (command.startsWith("TONE:")) {
      // Format: TONE:frequency:duration
      int freq = command.substring(5, command.indexOf(':', 5)).toInt();
      int duration = command.substring(command.indexOf(':', 5) + 1).toInt();
      playTone(freq, duration);
    }
  }
}

// --- Check for shake using MPU6050 ---
bool checkGyro() {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B);  // Starting register for accel data
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, 6, true);
  
  accelX = Wire.read() << 8 | Wire.read();
  accelY = Wire.read() << 8 | Wire.read();
  accelZ = Wire.read() << 8 | Wire.read();
  
  // Calculate magnitude
  float magnitude = sqrt(sq(accelX) + sq(accelY) + sq(accelZ));
  
  return (magnitude > SHAKE_THRESHOLD);
}

// --- Check for yelling using MAX4466 ---
bool checkMicrophone() {
  unsigned long startMillis = millis();
  int peakToPeak = 0;
  int signalMax = 0;
  int signalMin = 1024;
  
  // Collect samples over the sample window
  while (millis() - startMillis < SAMPLE_WINDOW) {
    int sample = analogRead(MIC_PIN);
    
    if (sample > signalMax) {
      signalMax = sample;
    }
    if (sample < signalMin) {
      signalMin = sample;
    }
  }
  
  peakToPeak = signalMax - signalMin;
  
  return (peakToPeak > YELL_THRESHOLD);
}

// --- Play a simple beep ---
void playBeep() {
  tone(SPEAKER_PIN, 1000, 200);  // 1kHz for 200ms
}

// --- Play a specific tone ---
void playTone(int frequency, int duration) {
  tone(SPEAKER_PIN, frequency, duration);
}