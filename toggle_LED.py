import machine
import time

# Configure the LED pin (built-in LED is on GPIO 25)
#led = machine.Pin(25, machine.Pin.OUT)  # Change 25 to your GPIO pin if using an external LED
led = machine.Pin('LED', machine.Pin.OUT)

# Toggle the LED
while True:
    led.toggle()  # Toggle the LED state
    time.sleep(1)  # Wait for 1 second
