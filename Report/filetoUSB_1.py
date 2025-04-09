import time
import os
import csv
import logging
import RPi.GPIO as GPIO
import board
import busio
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont
import can
import isotp
import udsoncan
from udsoncan.connections import PythonIsoTpConnection
from udsoncan.client import Client
import udsoncan.configs
from collections import defaultdict

# === Load Test Cases from CSV ===
test_cases = []
with open("test_cases.txt", "r") as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        if row and not row[0].startswith("#"):
            test_cases.append(row)

grouped_cases = defaultdict(list)
for row in test_cases:
    grouped_cases[row[0]].append(row)

# === Updated Report Formatter ===
def convert_report(report):
    grouped = defaultdict(list)
    for entry in report:
        grouped[entry['id']].append(entry)

    test_cases = []
    for tc_id, steps in grouped.items():
        status = "Pass"
        step_entries = []

        for i, step in enumerate(steps):
            if step["status"].lower() != "pass":
                status = "Fail"

            description = step["description"]
            if " - " in description:
                description = description.split(" - ", 1)[1]

            step_num = i + 1
            step_entries.append({
                "step": step_num,
                "description": description,
                "timestamp": step["timestamp"],
                "type": "Request Sent",
                "status": step["status"].capitalize(),
                "reason": step["failure_reason"],
                "rowspan": 2
            })

            step_entries.append({
                "timestamp": step["response_timestamp"],
                "type": "Response Received",
                "status": step["status"].capitalize(),
                "reason": step["failure_reason"]
            })

        test_cases.append({
            "name": tc_id,
            "status": status,
            "steps": step_entries
        })

    return test_cases

# === OLED Display Setup ===
i2c = busio.I2C(board.SCL, board.SDA)
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 9)

menu_combinations = {
    (BTN_FIRST, BTN_ENTER): "ECU Information",
    (BTN_SECOND, BTN_ENTER): "Testcase Execution",
    (BTN_FIRST, BTN_SECOND, BTN_ENTER): "ECU Flashing",
    (BTN_SECOND, BTN_FIRST, BTN_ENTER): "File Transfer\ncopying log files\nto USB device",
    (BTN_FIRST, BTN_FIRST, BTN_ENTER): "Reserved1\nfor future versions",
    (BTN_SECOND, BTN_SECOND, BTN_ENTER): "Reserved2\nfor future versions"
}
def display_text(text, y=10):
    oled.fill(0)
    image = Image.new("1", (oled.width, oled.height))
    draw = ImageDraw.Draw(image)
    draw.text((5, y), text, font=font, fill=255)
    oled.image(image)
    oled.show()
import shutil
import zipfile
import psutil  # You might need to install with: pip3 install psutil

def get_ecu_information():
    """Retrieve and display ECU information dynamically from CAN Bus."""
    os.system('sudo ip link set can0 down')
    os.system('sudo ip link set can0 up type can bitrate 500000 dbitrate 1000000 restart-ms 1000 berr-reporting on fd on')
    os.system('sudo ifconfig can0 up')

    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
    
    logging.getLogger('udsoncan').setLevel(logging.DEBUG)
    logging.getLogger('isotp').setLevel(logging.DEBUG)

    isotp_params = {
        'stmin': 32,
        'blocksize': 8,
        'wftmax': 0,
        'tx_padding': 0x00,
        'rx_flowcontrol_timeout': 1000,
        'rx_consecutive_frame_timeout': 1000,
        'max_frame_size': 4095,
        'can_fd': True,    
        'bitrate_switch': True
    }

    config = dict(udsoncan.configs.default_client_config)
    config["data_identifiers"] = {
        0xF101: udsoncan.AsciiCodec(4),
        0xF100: udsoncan.AsciiCodec(4),
        0xF1DD: udsoncan.AsciiCodec(4),
        0xF187: udsoncan.AsciiCodec(9),
        0xF1AA: udsoncan.AsciiCodec(13),
        0xF1B1: udsoncan.AsciiCodec(4),
        0xF193: udsoncan.AsciiCodec(4),
        0xF120: udsoncan.AsciiCodec(16),
        0xF18B: udsoncan.AsciiCodec(4),
        0xF102: udsoncan.AsciiCodec(8)
    }

    interface = "can0"
    bus = can.interface.Bus(channel=interface, bustype="socketcan", fd=True)
    bus.set_filters([{"can_id": 0x7A8, "can_mask": 0xFFF}])

    tp_addr = isotp.Address(isotp.AddressingMode.Normal_11bits, txid=0x7A0, rxid=0x7A8)
    stack = isotp.CanStack(bus=bus, address=tp_addr, params=isotp_params)
    conn = PythonIsoTpConnection(stack)

    report_data = []

    with Client(conn, request_timeout=2, config=config) as client:
        logging.info("UDS Client Started")

        def send_uds_request(action, uds_function, *args):
            """Helper function to send a UDS request and log response dynamically."""
           
            try:
                response = uds_function(*args)
                
                
            except Exception as e:
                logging.error(f"Error in {action}: {e}")
             

        # Tester Present (0x3E)
        send_uds_request("Tester Present (0x3E)", client.tester_present)

        # Default Session (0x10 0x01)
        send_uds_request("Default Session (0x10 0x01)", client.change_session, 0x01)

        # Extended Session (0x10 0x03)
        send_uds_request("Extended Session (0x10 0x03)", client.change_session, 0x03)

        # Read Data Identifiers (DIDs)
        for did in config["data_identifiers"]:
            send_uds_request(f"Read DID {hex(did)}", client.read_data_by_identifier, did)

              
       
        logging.info("UDS Client Closed")
        
def transfer_files_to_usb():
    log_folder = "/home/pi/diagnostic_logs"
    usb_root = "/media/pi"

    try:
        # Step 1: Check for USB mount
        devices = [d for d in os.listdir(usb_root) if os.path.ismount(os.path.join(usb_root, d))]
        if not devices:
            display_text("No USB Found")
            return

        usb_path = os.path.join(usb_root, devices[0])
        zip_name = f"DiagnosticBackup_{int(time.time())}.zip"
        zip_path = f"/tmp/{zip_name}"  # Create ZIP in /tmp

        # Step 2: Compress logs to ZIP
        display_text("Zipping files...")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(log_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, log_folder)
                    zipf.write(file_path, arcname)

        zip_size = os.path.getsize(zip_path)  # in bytes

        # Step 3: Check USB free space
        usage = psutil.disk_usage(usb_path)
        if usage.free < zip_size:
            display_text("Not enough space\non USB")
            os.remove(zip_path)
            return

        # Step 4: Copy ZIP to USB
        display_text("Copying to USB...")
        shutil.copy2(zip_path, usb_path)
        os.remove(zip_path)

        display_text("Transfer Complete!")

    except Exception as e:
        display_text(f"Error:\n{str(e)[:20]}")

def run_testcases():
    os.system('sudo ip link set can0 down')
    os.system('sudo ip link set can0 up type can bitrate 500000 dbitrate 1000000 restart-ms 1000 berr-reporting on fd on')
    os.system('sudo ifconfig can0 up')

    logging.basicConfig(level=logging.INFO)
    logging.getLogger('udsoncan').setLevel(logging.WARNING)
    logging.getLogger('isotp').setLevel(logging.WARNING)

    isotp_params = {
        'stmin': 32,
        'blocksize': 8,
        'tx_padding': 0x00,
        'can_fd': True,
        'bitrate_switch': True
    }

    config = dict(udsoncan.configs.default_client_config)
    config["data_identifiers"] = {
        0xF101: udsoncan.AsciiCodec(4),
        0xF187: udsoncan.AsciiCodec(9),
    }

    interface = "can0"
    bus = can.interface.Bus(channel=interface, bustype="socketcan", fd=True)
    bus.set_filters([{"can_id": 0x7A8, "can_mask": 0xFFF}])
    tp_addr = isotp.Address(isotp.AddressingMode.Normal_11bits, txid=0x7A0, rxid=0x7A8)
    stack = isotp.CanStack(bus=bus, address=tp_addr, params=isotp_params)
    conn = PythonIsoTpConnection(stack)

    report = []
    with Client(conn, request_timeout=2, config=config) as client:
        client.change_session(0x03)

        for tc_id, steps in grouped_cases.items():
            for step in steps:
                _, step_desc, service, subfunc, expected = step
                service_int = int(service, 16)
                subfunc_int = int(subfunc, 16)

                expected_bytes = [int(b, 16) for b in expected.strip().split()]
                status = "Fail"
                failure_reason = "-"
                timestamp = time.strftime('%H:%M:%S', time.localtime())
                response_timestamp = timestamp

                try:
                    response = None
                    if service_int == 0x10:
                        response = client.change_session(subfunc_int)
                    elif service_int == 0x11:
                        response = client.ecu_reset(subfunc_int)
                    elif service_int == 0x22:
                        response = client.read_data_by_identifier(subfunc_int)
                    else:
                        raise ValueError(f"Unsupported service: {service}")

                    response_timestamp = time.strftime('%H:%M:%S', time.localtime())

                    if not response.positive:
                        failure_reason = f"NRC: {hex(response.code)}"
                    else:
                        actual_bytes = list(response.original_payload)
                        if actual_bytes[:len(expected_bytes)] == expected_bytes:
                            status = "Pass"
                        else:
                            failure_reason = (
                                f"Expected: {' '.join(format(b, '02X') for b in expected_bytes)}, "
                                f"Got: {' '.join(format(b, '02X') for b in actual_bytes)}"
                            )

                except Exception as e:
                    response_timestamp = time.strftime('%H:%M:%S', time.localtime())
                    failure_reason = str(e)

                # OLED display update
                display_msg = f"{tc_id}\n{step_desc[:16]}\n{status}"
                display_text(display_msg)
                time.sleep(2)

                if status == "Fail":
                    display_text(f"FAILED\n{failure_reason[:20]}", y=0)
                    time.sleep(2)

                report.append({
                    "id": tc_id,
                    "timestamp": timestamp,
                    "response_timestamp": response_timestamp,
                    "description": step_desc,
                    "type": "Request Sent",
                    "status": status,
                    "failure_reason": failure_reason
                })

    filename = f"UDS_Report_{int(time.time())}.html"
    generate_report(convert_report(report), filename=filename)
    display_text("Report Done!\n" + filename[:16])
try:
    variable = 0
    selected_sequence = []

    while True:
        display_text("Select Option:\n1. ECU Info\n2. Testcase\n3. Flash\n4. File\n5. Reserved", y=0)

        if GPIO.input(BTN_FIRST) == GPIO.LOW:
            variable = (variable * 10) + 1
            selected_sequence.append(BTN_FIRST)
            display_text(str(variable))
            time.sleep(0.2)

        if GPIO.input(BTN_SECOND) == GPIO.LOW:
            variable = (variable * 10) + 2
            selected_sequence.append(BTN_SECOND)
            display_text(str(variable))
            time.sleep(0.2)

        if GPIO.input(BTN_ENTER) == GPIO.LOW:
            selected_sequence.append(BTN_ENTER)
            selected_option = menu_combinations.get(tuple(selected_sequence), "Invalid Input")
            display_text(selected_option)

            if selected_option == "ECU Information":
                time.sleep(1)
                display_text("Fetching ECU Information...")
                get_ecu_information()

            variable = 0
            selected_sequence.clear()
            time.sleep(1)
            
            if selected_option == "Testcase Execution":
                time.sleep(1)
                display_text("Running Tests...")
                run_testcases()

            variable = 0
            selected_sequence.clear()
            time.sleep(1)
            
            
             if selected_option == "File Transfer\ncopying log files\nto USB device":
                time.sleep(1)
                display_text("File Transfer...")
                transfer_files_to_usb()
               
            variable = 0
            selected_sequence.clear()
            time.sleep(1)

        if GPIO.input(BTN_THANKS) == GPIO.LOW:
            display_text("Shutting Down")
            time.sleep(1)
            os.system('sudo poweroff')

        time.sleep(0.1)

except KeyboardInterrupt:
    print("Exiting...")

finally:
    GPIO.cleanup()