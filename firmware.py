import network
import urequests
import machine
import time
import os

# Wi-Fi Credentials
SSID = "JioFiberESS"
PASSWORD = "Top50$$$"

# OTA Settings
VERSION_URL = "https://github.com/ess-iot/OTA_firmware_files/blob/main/version.json"
FIRMWARE_PATH = "/firmware.py"
CURRENT_VERSION = "1.0"

# GPIO Pin for LED
led = machine.Pin('LED', machine.Pin.OUT)

# Wi-Fi Connection
def connect_to_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    print("Connecting to Wi-Fi...")
    
    timeout = 10
    while not wlan.isconnected() and timeout > 0:
        time.sleep(1)
        timeout -= 1

    if wlan.isconnected():
        print("Connected to Wi-Fi:", wlan.ifconfig())
        return True
    else:
        print("Failed to connect to Wi-Fi")
        return False

# Check for Updates
def check_for_update():
    print("Checking for updates...")
    try:
        response = urequests.get(VERSION_URL)
        data = response.json()
        response.close()

        latest_version = data.get("version")
        firmware_url = data.get("firmware_url")
        
        if latest_version and firmware_url:
            print(f"Current version: {CURRENT_VERSION}, Latest version: {latest_version}")
            if latest_version > CURRENT_VERSION:
                print("Update available!")
                return firmware_url
            else:
                print("Firmware is up to date.")
        else:
            print("Invalid version data.")
    except Exception as e:
        print("Error checking for updates:", e)
    return None

# Download Firmware
def download_firmware(firmware_url):
    print("Downloading firmware...")
    try:
        response = urequests.get(firmware_url)
        with open(FIRMWARE_PATH, "w") as f:
            f.write(response.text)
        response.close()
        print("Firmware downloaded successfully.")
        return True
    except Exception as e:
        print("Error downloading firmware:", e)
        return False

# Apply Firmware
def apply_firmware():
    print("Applying firmware update...")
    try:
        with open(FIRMWARE_PATH, "r") as f:
            exec(f.read())
        print("Firmware applied successfully.")
    except Exception as e:
        print("Error applying firmware:", e)

# LED Blinking Function
def blink_led():
    while True:
        led.value(1)
        time.sleep(1)
        led.value(0)
        time.sleep(0)

# OTA Update Logic
def ota_update():
    if connect_to_wifi():
        firmware_url = check_for_update()
        if firmware_url and download_firmware(firmware_url):
            apply_firmware()
        else:
            print("OTA update failed. Running current firmware.")

# Main Function
def main():
    # Check for OTA updates
    ota_update()

    # Run main application (LED blinking)
    blink_led()

if __name__ == "__main__":
    main()

