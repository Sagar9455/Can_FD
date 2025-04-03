import os
import time
import logging
import RPi.GPIO as GPIO
import can
import isotp
import udsoncan
from udsoncan.client import Client
from udsoncan.connections import PythonIsoTpConnection
from udsoncan.services import DiagnosticSessionControl

# Setup GPIO button
BUTTON_PIN = 16
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Bring up CAN interface
os.system('sudo ip link set can0 up type can bitrate 500000 dbitrate 1000000 restart-ms 1000 berr-reporting on fd on')
os.system('sudo ifconfig can0 up')

# Logging setup
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

# Define ISO-TP parameters
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

# UDS Client Configuration
config = dict(udsoncan.configs.default_client_config)
config["ignore_server_timing_requirements"] = True
config["data_identifiers"] = {
    0xF100: udsoncan.AsciiCodec(8),
    0xF101: udsoncan.AsciiCodec(8),
    0xF190: udsoncan.AsciiCodec(16)
}

# Define CAN interface
interface = "can0"
bus = can.interface.Bus(channel=interface, bustype="socketcan", fd=True)
bus.set_filters([{ "can_id": 0x7A8, "can_mask": 0xFFF }])

# Define ISO-TP addressing
tp_addr = isotp.Address(isotp.AddressingMode.Normal_11bits, txid=0x7A0, rxid=0x7A8)
stack = isotp.CanStack(bus=bus, address=tp_addr, params=isotp_params)
conn = PythonIsoTpConnection(stack)

def generate_report(data):
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; }
            table { width: 80%; border-collapse: collapse; margin: 20px auto; }
            th, td { border: 1px solid black; padding: 10px; text-align: center; }
            th { background-color: #8a8a8a; color: black; font-weight: bold; }
            .pass { background-color: #c8e6c9; color: green; }
            .fail { background-color: #ffcdd2; color: red; }
            .section-title { background-color: #e0e0e0; }
        </style>
    </head>
    <body>
        <h2>UDS Diagnostic Report</h2>
        <table>
            <tr>
                <th>Timestamp</th>
                <th>Description</th>
                <th>Step</th>
                <th>Status</th>
            </tr>
    """
    
    for entry in data:
        html_content += f"""
            <tr class="section-title">
                <td rowspan="2">{entry["timestamp"]}</td>
                <td rowspan="2">{entry["action"]}</td>
                <td>Request Sent</td>
                <td class="{ 'pass' if entry['request_status'] == 'Pass' else 'fail' }">{entry['request_status']}</td>
            </tr>
            <tr>
                <td>Response Received</td>
                <td class="{ 'pass' if entry['response_status'] == 'Pass' else 'fail' }">{entry['response_status']}</td>
            </tr>
        """

    html_content += """
        </table>
    </body>
    </html>
    """
    with open("UDS_Report.html", "w") as file:
        file.write(html_content)
    print("Report generated: UDS_Report.html")

try:
    with Client(conn, request_timeout=2, config=config) as client:
        print("Waiting for button press...")
        while True:
            if GPIO.input(BUTTON_PIN) == GPIO.LOW:
                print("Button pressed! Sending UDS requests...")
                report_data = []

                steps = [
                    ("Default Session (0x10 0x01)", lambda: client.change_session(0x01)),
                    ("Extended Session (0x10 0x03)", lambda: client.change_session(0x03)),
                    ("Read DID (0xF190)", lambda: client.read_data_by_identifier(0xF190))
                ]

                for action, uds_function in steps:
                    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                    try:
                        response = uds_function()
                        request_status = "Pass"
                        response_status = "Pass" if response.positive else "Fail"
                    except Exception as e:
                        print(f"Error: {e}")
                        request_status = "Fail"
                        response_status = "Fail"
                    report_data.append({"timestamp": timestamp, "action": action, "request_status": request_status, "response_status": response_status})
                    time.sleep(0.5)

                generate_report(report_data)
                time.sleep(1)  # Prevent multiple detections
except KeyboardInterrupt:
    print("Exiting...")
finally:
    GPIO.cleanup()
