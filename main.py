import time
import struct
from machine import Pin, UART, Timer
from umodbus.serial import Serial as ModbusRTUMaster
import ujson
import math
import utime
import gc
from ota import OTAUpdater
from WIFI_CONFIG import SSID, PASSWORD

#Set machine frequency
machine.freq(96_000_000)

# Define the pins for Modbus communication
rtu_pins = (Pin(16), Pin(17))

# Initialize Modbus RTU Master
host = ModbusRTUMaster(baudrate=9600, data_bits=8, stop_bits=1, parity=None, pins=rtu_pins, ctrl_pin=None, uart_id=0)

# Initialize UART1 with TX on GPIO 8 and RX on GPIO 9 for GPS
uart = UART(1, baudrate=115200, tx=Pin(8), rx=Pin(9), timeout=1000)

def log_message(message):
    timestamp = time.localtime()  # Get current time
    formatted_time = "{:04}-{:02}-{:02} {:02}:{:02}:{:02}".format(timestamp[0], timestamp[1], timestamp[2], timestamp[3], timestamp[4], timestamp[5])
    log_entry = f"{formatted_time} - {message}\n\n"
    print(log_entry)
    return
    
# GPS initialization commands
gps_init_commands = [
    'AT+QGPS=1',  # Turn on GNSS engine
    'AT+QGPSCFG="nmeasrc",1'  # Configure NMEA source
]

# Function to send AT commands to UART and get response
def send_at_command(command, wait_time=1):
    uart.write(command + '\r\n')
    time.sleep(wait_time)
    response = b""
    while uart.any():
        response += uart.read(100)
    return response.decode('utf-8').strip()

# Initialize GPS module
def initialize_gps():
    print("Initializing GPS module...")
    response = send_at_command('AT+QGPS?')
    if "+QGPS: 1" in response:  
        print("GPS module already initialized.")
        return True
    elif "+CME ERROR: 504" in response:  
        print("GPS module already initialized but no data received.")
        for _ in range(3): 
            coordinates = get_gps_coordinates()
            if coordinates:
                return True
            time.sleep(10) 
        print("Failed to fetch GPS data after retries.")
        return False
    elif "+CME ERROR: 505" in response: 
        print("Starting GPS module...")
        response = send_at_command('AT+QGPS=1')
        if "OK" in response:
            print("GPS module started successfully.")
        else:
            print("Failed to start GPS module.")
            return False
    
    for command in gps_init_commands:
        response = send_at_command(command)
        print(f"Command: {command}, Response: {response}")
        if "ERROR" in response:
            return False
        elif "OK" not in response:
            return False
    
    print("GPS module initialized successfully.")
    return True

# Function to read a block of input registers
def read_input_registers(address, start_address, num_regs, retries=3):
    for _ in range(retries):
        try:
            # Build Modbus RTU request for reading input registers
            response = host.read_input_registers(address, start_address, num_regs, False)
            return response
        except Exception as e:
            print(f"Error reading registers at address {start_address}: {e}")
            time.sleep(0.5)  
    return None

# Function to convert two consecutive registers to float
def registers_to_float(registers, index):
    # Combine two registers to get the 32-bit integer value
    combined_value = (registers[index + 1] << 16) | registers[index]
    # Interpret as float
    float_value = struct.unpack('f', struct.pack('I', combined_value))[0]
    
    return float_value

# Define register addresses and number of registers to read in one batch
start_address = 0
num_registers = 64

# Function to read voltage, current, and power values from energy meter
def read_energy_values(address):
    registers = read_input_registers(address, start_address, num_registers)
  
    if registers:        
        v1 = registers_to_float(registers, 0)
        v2 = registers_to_float(registers, 2)
        v3 = registers_to_float(registers, 4)
        c1 = registers_to_float(registers, 6)
        c2 = registers_to_float(registers, 8)
        c3 = registers_to_float(registers, 10)
        kW1 = registers_to_float(registers, 24)
        kW2 = registers_to_float(registers, 26)
        kW3 = registers_to_float(registers, 28)
        kVA1 = registers_to_float(registers, 30)
        kVA2 = registers_to_float(registers, 32)
        kVA3 = registers_to_float(registers, 34)
        kVAr1 = registers_to_float(registers, 36)
        kVAr2 = registers_to_float(registers, 38)
        kVAr3 = registers_to_float(registers, 40)
        Total_kW = registers_to_float(registers, 42)
        Total_kVA = registers_to_float(registers, 44)
        Total_kVAr = registers_to_float(registers, 46)
        PF1 = registers_to_float(registers, 48)
        PF2 = registers_to_float(registers, 50)
        PF3 = registers_to_float(registers, 52)
        Fr = registers_to_float(registers, 56)
        Total_kWh = registers_to_float(registers, 58)
        Total_kVAh = registers_to_float(registers, 60)
        Total_kVArh = registers_to_float(registers, 62)
        
        return {
            "v1": v1,
            "v2": v2,
            "v3": v3,
            "c1": c1,
            "c2": c2,
            "c3": c3,
            "kW1": kW1,
            "kW2": kW2,
            "kW3": kW3,
            "kVA1": kVA1,
            "kVA2": kVA2,
            "kVA3": kVA3,
            "kVAr1": kVAr1,
            "kVAr2": kVAr2,
            "kVAr3": kVAr3,
            "Total_kW": Total_kW,
            "Total_kVA": Total_kVA,
            "Total_kVAr": Total_kVAr,
            "PF1": PF1,
            "PF2": PF2,
            "PF3": PF3,
            "Fr": Fr,
            "Total_kWh": Total_kWh,
            "Total_kVAh": Total_kVAh,
            "Total_kVArh": Total_kVArh,
            "deviceSerialNumber":"123321",
            "accessKey":"U2FsdGVkX1/I5IyZo17tD1lgBpVohU6VH09zb2bwU+u6ivVkXgOYTrO2ka8wQeNk4HS3nwCfjF60ohf7Ry6caIyBLx9nnIkehGJOoZQ7x3GpWhQy7CfyjF5ZAMRzyUcEs27OdSDXwxB1orNXPXRSRa4eSVjFTjdeo5ZAcOJ3YTM=",
            "secretKey":"38738c2c-03f7-4a4c-8730-e4679417dbda"   
        }
    else:
        return {
            "Energy meter values": "None"
        }

# Function to read GPS coordinates
def get_gps_coordinates():
    for retry in range(3):  
        print(f"Retry {retry + 1} to fetch GPS data...")
        response = send_at_command('AT+QGPSGNMEA="GGA"')
        if "$GPGGA" in response or "$GNGGA" in response:
            gpgga_data = parse_gpgga(response)
            if gpgga_data:
                latitude, longitude = gpgga_data['latitude'], gpgga_data['longitude']
                print(f"GPS data found - Latitude: {latitude}, Longitude: {longitude}")
                return latitude, longitude
        elif "+CME ERROR: 504" in response: 
            print("GPS already initialized but no data received. Retrying...")
            continue  
        elif "+CME ERROR: 505" in response:  
            print("GPS not started, attempting to start...")
            if initialize_gps():
                continue 
        time.sleep(10) 
    
    print("Failed to fetch GPS data after retries. Publishing energy data with GPS data set to null.")
    return None, None


# Function to parse GPS data from NMEA sentence
def parse_gpgga(sentence):
    parts = sentence.split(',')
    if len(parts) >= 15 and parts[2] and parts[4]:
        return {
            'latitude': convert_to_decimal_degrees(parts[2], parts[3]),
            'longitude': convert_to_decimal_degrees(parts[4], parts[5])
        }
    return None

# Function to convert NMEA format to decimal degrees
def convert_to_decimal_degrees(value, direction):
    if len(value) < 4:
        return None
    # Degrees are the first 2 or 3 characters
    degrees = int(value[:2]) if len(value) == 9 else int(value[:3])
    # Minutes are the rest (including the decimal point)
    minutes = float(value[2:]) if len(value) == 9 else float(value[3:])
    # Convert to decimal degrees
    decimal = degrees + minutes / 60
    # South and West are negative
    if direction in ['S', 'W']:
        decimal *= -1
    return decimal

# MQTT AT commands
def publish_mqtt_data(data):
    json_data = ujson.dumps(data)
    data_length = len(json_data)
      

    at_commands = [
        'AT',
        'AT+QMTCFG="recv/mode",0,0,1',
        'AT+QMTOPEN=0,"140.238.167.220",8880',
        'AT+QMTOPEN?',
        'AT+QMTCONN=0,"client07","essitco","lav38sin"',
        f'AT+QMTPUBEX=0,0,0,0,"energy_values",{data_length}',
        json_data,
        'AT+QMTDISC=0'
    ]
    # Send MQTT commands
    for command in at_commands:
        response = send_at_command(command)
        print(f"Command: {command}, Response: {response}")

# Function to calculate Haversine distance
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# Main function to read and publish energy and GPS data
def read_and_publish_energy_gps_data(address):
    current_freq = machine.freq()
    firmware_url = "https://raw.githubusercontent.com/ess-iot/OTA_firmware_files/"
    ota_updater = OTAUpdater(SSID, PASSWORD, firmware_url, "main.py")
    ota_updater.connect_wifi()
    print(f"Current frequency: {current_freq} Hz\n\n")
    initialize_gps()
    last_lon,last_lat = None, None
    Threshold = 50
    last_publish_time = time.time()  
    settime = 30

    while True: 
        try:
            coordinates = get_gps_coordinates()
            data = {}
            if coordinates[0] and coordinates[1]: 
                lat, lon = coordinates[0], coordinates[1]
                if last_lat and last_lon:
                    distance = haversine(last_lat, last_lon, lat, lon)
                    log_message(f"Distance: {distance:.4f} meters")
                    
                    if distance >= Threshold:
                        data = read_energy_values(address)
                        data.update({"latitude": coordinates[0],"longitude": coordinates[1]})
                        log_message(f"Movement detected: {distance:.2f} meters")
                        publish_mqtt_data(data)
                        log_message(f"Energy and GPS data published: {data}")
                        last_lat, last_lon = lat, lon
                        gc.collect()
                else:
                    last_lat, last_lon = lat, lon
                        
            if time.time() - last_publish_time >= settime:
                data = read_energy_values(address)
                data.update({"latitude": coordinates[0],"longitude": coordinates[1]})
                log_message(f"TIME EXCEED")
                publish_mqtt_data(data)
                log_message(f"Energy and GPS data published: {data}")
                last_publish_time = time.time()
                gc.collect()
                
            if ota_updater.check_for_updates():
                ota_updater.download_and_install_update_if_available()
            else
                print("No updates available.")
                    
        except Exception as e:
            print("Error:", e)
        
address = 1  # Address of the Modbus RTU device
read_and_publish_energy_gps_data(address)


