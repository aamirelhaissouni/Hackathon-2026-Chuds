"""
Hardware module for Raspberry Pi 5 + Arduino Uno communication
Handles: Gyroscope detection (via Arduino)
Compatible with existing main.py interface
"""

import time
import serial
import threading

# --- CONFIGURATION ---
ARDUINO_PORT = '/dev/ttyACM0'  # or '/dev/ttyUSB0' - check with: ls /dev/tty*
BAUD_RATE = 9600

# --- Global Variables ---
_arduino_serial = None
_shake_detected = False
_serial_lock = threading.Lock()
_serial_running = False
_serial_thread = None

def _serial_reader_thread():
    """Background thread that reads from Arduino serial port"""
    global _shake_detected, _serial_running, _arduino_serial
    
    print("[Serial Thread] Started")
    
    while _serial_running:
        try:
            if _arduino_serial and _arduino_serial.in_waiting > 0:
                line = _arduino_serial.readline().decode('utf-8').strip()
                
                with _serial_lock:
                    if line == "SHAKE":
                        _shake_detected = True
                        print("[Serial] SHAKE detected!")
                    elif line == "ARDUINO_READY":
                        print("[Serial] Arduino is ready")
                        
        except Exception as e:
            print(f"[Serial Thread] Error: {e}")
            time.sleep(0.1)
    
    print("[Serial Thread] Stopped")


def setup_gyro():
    """
    Initialize serial connection to Arduino.
    Returns the serial object (for compatibility with main.py's check_for_shake(gyro) calls)
    """
    global _arduino_serial, _serial_running, _serial_thread
    
    try:
        _arduino_serial = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)  # Wait for Arduino to reset
        print(f"[Arduino] Connected on {ARDUINO_PORT}")
        
        # Start the serial reader thread
        _serial_running = True
        _serial_thread = threading.Thread(target=_serial_reader_thread, daemon=True)
        _serial_thread.start()
        
        return _arduino_serial
        
    except Exception as e:
        print(f"[Arduino] ERROR: Could not connect - {e}")
        print(f"[Arduino] Make sure Arduino is connected. Try: ls /dev/tty*")
        return None


def check_for_shake(gyro_obj):
    """
    Check if a shake was detected by Arduino.
    Args:
        gyro_obj: The serial object (for compatibility with main.py)
    Returns:
        True if shake detected, False otherwise.
    Automatically resets the flag after reading.
    """
    global _shake_detected
    
    with _serial_lock:
        if _shake_detected:
            _shake_detected = False  # Reset the flag
            return True
    return False


# --- Test Function ---
if __name__ == "__main__":
    print("=== Testing Hardware Module ===")
    
    # Test Arduino connection
    print("\n2. Testing Arduino connection...")
    gyro = setup_gyro()
    
    if gyro:
        print("\n3. Monitoring gyroscope for 10 seconds...")
        print("   Try shaking the device!")
        
        start_time = time.time()
        shake_count = 0
        while time.time() - start_time < 10:
            if check_for_shake(gyro):
                shake_count += 1
                print(f"   >>> SHAKE DETECTED! (Count: {shake_count}) <<<")
            
            time.sleep(0.1)
        
        print(f"\n   Total shakes detected: {shake_count}")
    
    print("\n=== Test Complete ===")
