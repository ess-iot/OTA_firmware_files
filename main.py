import machine
import time
import ota
import update_firmware

# Configure the LED pin (built-in LED is on GPIO 25)
led = machine.Pin('LED', machine.Pin.OUT)

# Toggle the LED
while True:
    led.toggle()  # Toggle the LED state
    time.sleep(0.6)  # Wait for 1 second
    
