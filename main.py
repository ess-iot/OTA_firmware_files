import machine
import time
import ota
import update_firmware
from ota import OTAUpdater
from WIFI_CONFIG import SSID, PASSWORD

firmware_url = "https://raw.githubusercontent.com/ess-iot/OTA_firmware_files/"
ota_updater = OTAUpdater(SSID, PASSWORD, firmware_url, "main.py")
ota_updater.connect_wifi()
    
# Configure the LED pin (built-in LED is on GPIO 25)
led = machine.Pin('LED', machine.Pin.OUT)

# Toggle the LED
while True:
    led.toggle()  # Toggle the LED state
    time.sleep(0.6)  # Wait for 1 second
    if ota_updater.check_for_updates():
                ota_updater.download_and_install_update_if_available()
    
