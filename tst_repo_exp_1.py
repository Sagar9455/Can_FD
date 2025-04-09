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

def display_text(text, y=10):
    oled.fill(0)
    image = Image.new("1", (oled.width, oled.height))
    draw = ImageDraw.Draw(image)
    draw.text((5, y), text, font=font, fill=255)
    oled.image(image)
    oled.show()

def get_ecu_information():
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
