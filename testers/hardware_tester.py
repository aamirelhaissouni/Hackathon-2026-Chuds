import time
from gpiozero import LED
# This is the assumed library. If yours is different, change this import.
from mpu6050 import mpu6050

# --- CONFIGURATION ---
LED_PIN = 17         # The GPIO pin (BCM numbering) the LED is connected to.
GYRO_ADDRESS = 0x68  # Default I2C address for MPU-6050.
SHAKE_THRESHOLD = 15 # !! TUNE THIS VALUE !!

def test_led():
    """Tests the LED ring."""
    print("--- TESTING LED ---")
    try:
        led = LED(LED_PIN)
        
        print("LED ON for 1 second...")
        led.on()
        time.sleep(1)
        
        print("LED OFF for 1 second...")
        led.off()
        time.sleep(1)
        
        print("LED Flashing 3 times...")
        led.blink(on_time=0.2, off_time=0.2, n=3)
        time.sleep(2) # Wait for blink to finish
        
        print("LED Test Complete.")
        led.off()
        
    except Exception as e:
        print(f"LED TEST FAILED: {e}")
        print("Is the LED wired to pin {LED_PIN}?")

def test_gyro():
    """Tests the Gyroscope sensor."""
    print("\n--- TESTING GYRO ---")
    print(f"Looking for sensor at address {hex(GYRO_ADDRESS)}...")
    print("Press Ctrl+C to stop.")
    
    try:
        sensor = mpu6050(GYRO_ADDRESS)
        print("Gyroscope connected!")
    except Exception as e:
        print(f"GYRO TEST FAILED: {e}")
        print("Is the sensor wired up? Is the I2C address correct?")
        return

    print("Reading data... Try shaking the sensor.")
    while True:
        try:
            # Get acceleration data
            accel_data = sensor.get_accel_data()
            
            ax = accel_data['x']
            ay = accel_data['y']
            az = accel_data['z']
            
            # Print the Z-axis (usually the "up/down" slam)
            # You can also use 'x' or 'y' depending on orientation
            print(f"X: {ax:.2f}, Y: {ay:.2f}, Z: {az:.2f}")

            # Check for a "shake"
            # We use abs() because a slam can be a positive or negative spike
            if abs(az) > SHAKE_THRESHOLD or abs(ax) > SHAKE_THRESHOLD or abs(ay) > SHAKE_THRESHOLD:
                print(f"!!! SHAKE DETECTED !!! (Value: {max(abs(ax), abs(ay), abs(az)):.2f})")
                
            time.sleep(0.1) # Check 10 times per second
            
        except KeyboardInterrupt:
            print("\nStopping gyro test.")
            break
        except Exception as e:
            print(f"Error reading sensor: {e}")
            time.sleep(1)

# --- This makes the script runnable ---
if __name__ == "__main__":
    test_led()
    test_gyro()