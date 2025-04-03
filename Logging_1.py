import json
import logging
import can
import isotp
import os
import time
import RPi.GPIO as GPIO
import board
import busio
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont
from udsoncan.client import Client
from udsoncan.connections import PythonIsoTpConnection
import udsoncan.configs
from collections import deque
import threading

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

# Set up GPIO mode
GPIO.setmode(GPIO.BCM)

# Define button pins
BTN_FIRST = 12
BTN_SECOND = 16
BTN_ENTER = 20
BTN_THANKS = 21
buttons = [BTN_FIRST, BTN_SECOND, BTN_ENTER, BTN_THANKS]

# Set up buttons as input with pull-up resistors
for btn in buttons:
    GPIO.setup(btn, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Initialize I2C and OLED
i2c = busio.I2C(board.SCL, board.SDA)
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)

# Load font
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 9)

# Load configuration from JSON
with open('config.json') as config_file:
    config_data = json.load(config_file)
    logging.debug(f"Loaded ISO-TP Parameters: {config_data['isotp_params']}")

# Buffer for storing all CAN frames
can_buffer = deque(maxlen=1000)  # Adjust the buffer size as needed

# Set up CAN interface
def setup_can_interface(interface):
    if os.system(f'ip link show {interface} > /dev/null 2>&1') == 0:
        logging.info(f"{interface} is already active")
    else:
        os.system(f'sudo ip link set {interface} up type can bitrate 500000 dbitrate 1000000 restart-ms 1000 berr-reporting on fd on')

# CAN receiver function to capture all frames in the buffer
def receive_can_frames(bus):
    while True:
        msg = bus.recv(timeout=1)
        if msg:
            # Store all frames in the buffer without filtering
            logging.debug(f"Frame received: ID={hex(msg.arbitration_id)}, Data={msg.data.hex()}")
            can_buffer.append(msg)  # Add the received frame to the buffer

# Function to log CAN frames from the buffer
def log_can_frames():
    while True:
        if can_buffer:
            msg = can_buffer.popleft()  # Get the next frame from the buffer
            logging.info(f"Logged CAN Frame: ID={hex(msg.arbitration_id)}, Data={msg.data.hex()}")
        time.sleep(0.1)  # Adjust the interval as necessary

# Function to get ECU information (UDS)
def get_ecu_information():
    setup_can_interface(config_data["can_interface"])
    
    bus = can.interface.Bus(channel=config_data["can_interface"], bustype="socketcan", fd=True)
    bus.set_filters([{ "can_id": int(config_data["can_ids"]["rx_id"], 16), "can_mask": 0xFFF }])
    
    tp_addr = isotp.Address(
        isotp.AddressingMode.Normal_11bits,
        txid=int(config_data["can_ids"]["tx_id"], 16),
        rxid=int(config_data["can_ids"]["rx_id"], 16)
    )
    
    stack = isotp.CanStack(bus=bus, address=tp_addr, params=config_data["isotp_params"])
    logging.debug(f"Applied ISO-TP Parameters: {stack.params}")
    
    conn = PythonIsoTpConnection(stack)
    config = dict(udsoncan.configs.default_client_config)
    config["ignore_server_timing_requirements"] = config_data["uds_config"]["ignore_server_timing_requirements"]
    config["data_identifiers"] = {
        int(key, 16): udsoncan.AsciiCodec(value)
        for key, value in config_data["uds_config"]["data_identifiers"].items()
    }
    
    with Client(conn, request_timeout=2, config=config) as client:
        logging.info("UDS Client Started")
        try:
            client.tester_present()
            logging.info("Tester Present sent successfully")
        except Exception as e:
            logging.warning(f"Tester Present failed: {e}")
        
        change_session_with_retry(client, 0x01)
        change_session_with_retry(client, 0x03)
        
        for did in config["data_identifiers"]:
            try:
                response = client.read_data_by_identifier(did)
                if response.positive:
                    logging.info(f"ECU information (DID {hex(did)}): {response.service_data.values[did]}") 
                else:
                    logging.warning(f"Failed to read ECU information (DID {hex(did)})")
            except Exception as e:
                logging.error(f"Error reading ECU information (DID {hex(did)}): {e}")
        
        logging.info("UDS Client Closed")

def change_session_with_retry(client, session_type, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = client.change_session(session_type)
            if response.positive:
                logging.info(f"Switched to session {session_type} successfully")
                return
            else:
                logging.warning(f"Attempt {attempt + 1}: Failed to switch to session {session_type}")
        except Exception as e:
            logging.error(f"Attempt {attempt + 1}: Error in session {session_type} - {e}")
        time.sleep(0.5)

try:
    # Setup CAN interface
    setup_can_interface(config_data["can_interface"])

    # Initialize the CAN bus
    bus = can.interface.Bus(channel=config_data["can_interface"], bustype="socketcan", fd=True)

    # Start the CAN receiver thread (capture all frames in the buffer)
    threading.Thread(target=receive_can_frames, args=(bus,), daemon=True).start()

    # Start the CAN frame logger thread (log all frames from the buffer)
    threading.Thread(target=log_can_frames, daemon=True).start()

    while True:
        if GPIO.input(BTN_FIRST) == GPIO.LOW:
            time.sleep(0.2)
            get_ecu_information()
        if GPIO.input(BTN_THANKS) == GPIO.LOW:
            time.sleep(0.1)
            os.system('sudo poweroff')
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nExiting...")
finally:
    GPIO.cleanup()
