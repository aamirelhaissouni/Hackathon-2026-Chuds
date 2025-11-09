import time
from Pi5Neo import Pi5Neo
from mpu6050 import mpu6050

# --- CONFIGURATION ---
LED_COUNT = 12       # 12 LEDs in the ring
LED_BRIGHTNESS = 128 # 0-255, where 128 = 50% brightness (KEEP AT OR BELOW 128!)
GYRO_ADDRESS = 0x68  # Default I2C address for MPU-6050
SHAKE_THRESHOLD = 15 # !! TUNE THIS VALUE !!

def test_led():
    """Tests the NeoPixel LED ring."""
    print("--- TESTING NEOPIXEL RING ---")
    try:
        # Initialize the NeoPixel ring
        # Pi5Neo automatically uses SPI (no pin specification needed)
        strip = Pi5Neo('/dev/spidev0.0', LED_COUNT, LED_BRIGHTNESS)
        
        print("LEDs ON (RED) for 1 second...")
        strip.fill_strip(255, 0, 0)  # Red (R, G, B)
        strip.update_strip()
        time.sleep(1)
        
        print("LEDs OFF for 1 second...")
        strip.fill_strip(0, 0, 0)  # Off
        strip.update_strip()
        time.sleep(1)
        
        print("LEDs Flashing RED 3 times...")
        for j in range(3):
            # ON
            strip.fill_strip(255, 0, 0)  # Red
            strip.update_strip()
            time.sleep(0.2)
            
            # OFF
            strip.fill_strip(0, 0, 0)  # Off
            strip.update_strip()
            time.sleep(0.2)
        
        print("NeoPixel Test Complete.")
        
        # Turn off all LEDs
        strip.fill_strip(0, 0, 0)
        strip.update_strip()
        
    except Exception as e:
        print(f"NEOPIXEL TEST FAILED: {e}")
        print("Make sure SPI is enabled: sudo raspi-config -> Interface Options -> SPI")
        print("Is the NeoPixel ring wired correctly?")

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
            
            # Print all axes
            print(f"X: {ax:.2f}, Y: {ay:.2f}, Z: {az:.2f}")

            # Check for a "shake"
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
    print("NOTE: This script may require sudo to control NeoPixels!")
    print(f"Current brightness setting: {LED_BRIGHTNESS}/255 ({LED_BRIGHTNESS/255*100:.0f}%)")
    print("=" * 50)
    test_led()
    test_gyro()