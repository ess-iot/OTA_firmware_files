import network
import urequests
import machine
import time
import ota_update
# Main Function
def main():
    # Check for OTA updates
    ota_update.ota_update()

    # Run main application (LED blinking)
    print("hello main.py\n")
    print("NEW main\n")

main()
