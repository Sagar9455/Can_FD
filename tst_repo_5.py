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
    next(reader)  # Skip header
    for row in reader:
        if row and not row[0].startswith("#"):
            test_cases.append(row)

# Group test cases by TestCase ID
grouped_cases = defaultdict(list)
for row in test_cases:
    grouped_cases[row[0]].append(row)

# === Report Formatting Helper ===
def convert_report(report):
    grouped = defaultdict(list)
    for entry in report:
        grouped[entry['id']].append(entry)

    test_cases = []
    for tc_id, steps in grouped.items():
        status = "Pass"
        step_entries = []

        for i, step in enumerate(steps):
            if step["status"].upper() != "PASS":
                status = "Fail"
            step_entries.append({
                "step": i + 1,
                "description": step["description"],
                "timestamp": step["timestamp"],
                "type": step["type"],
                "status": step["status"].capitalize(),
                "reason": step["failure_reason"],
                "rowspan": 1
            })

        test_cases.append({
            "name": tc_id,
            "status": status,
            "steps": step_entries
        })

    return test_cases

# === HTML Report Generator ===
def generate_report(test_cases, filename="UDS_Report.html"):
    html_template = """<!DOCTYPE html>
<html>
<head>
    <title>UDS Diagnostic Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        h1 {{ text-align: center; }}
        button.accordion {{
            background-color: #ddd;
            color: black;
            cursor: pointer;
            padding: 10px;
            width: 100%;
            border: none;
            text-align: left;
            outline: none;
            font-size: 16px;
            border-radius: 5px;
            margin-bottom: 5px;
        }}
        .pass {{ color: green; font-weight: bold; }}
        .fail {{ color: red; font-weight: bold; }}
        .panel {{
            display: none;
            overflow: hidden;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            background: white;
        }}
        th, td {{
            border: 1px solid #ccc;
            padding: 8px;
            text-align: center;
        }}
        th {{ background-color: #eee; }}
        .step-pass {{ background-color: #c8e6c9; }}
        .step-fail {{ background-color: #ffcdd2; }}
    </style>
    <script>
        document.addEventListener("DOMContentLoaded", () => {{
            const acc = document.getElementsByClassName("accordion");
            for (let i = 0; i < acc.length; i++) {{
                acc[i].addEventListener("click", function () {{
                    this.classList.toggle("active");
                    const panel = this.nextElementSibling;
                    panel.style.display = (panel.style.display === "block") ? "none" : "block";
                }});
            }}
        }});
    </script>
</head>
<body>
    <h1>UDS Diagnostic Report</h1>
    {body}
</body>
</html>"""

    body = ""
    for test_case in test_cases:
        result_class = "pass" if test_case["status"] == "Pass" else "fail"
        body += f'<button class="accordion">▶ {test_case["name"]} - <span class="{result_class}">{test_case["status"]}</span></button>\n'
        body += '<div class="panel"><table><tr><th>Step</th><th>Description</th><th>Timestamp</th><th>Type</th><th>Status</th><th>Failure Reason</th></tr>\n'
        for step in test_case["steps"]:
            row_class = "step-pass" if step["status"] == "Pass" else "step-fail"
            rowspan = f'rowspan="{step["rowspan"]}"' if "rowspan" in step else ""
            body += f'<tr class="{row_class}">'
            if "step" in step:
                body += f'<td {rowspan}>{step["step"]}</td>'
                body += f'<td {rowspan}>{step["description"]}</td>'
            body += f'<td>{step["timestamp"]}</td><td>{step["type"]}</td>'
            body += f'<td class="{step["status"].lower()}">{step["status"]}</td><td>{step["reason"]}</td></tr>\n'
        body += '</table></div>\n'

    with open(filename, "w") as f:
        f.write(html_template.format(body=body))

    print(f"Report generated: {filename}")

# === GPIO Setup ===
BTN_FIRST = 12
BTN_SECOND = 16
BTN_ENTER = 20
BTN_THANKS = 21
buttons = [BTN_FIRST, BTN_SECOND, BTN_ENTER, BTN_THANKS]

GPIO.setmode(GPIO.BCM)
for btn in buttons:
    GPIO.setup(btn, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# === OLED Setup ===
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

menu_combinations = {
    (BTN_FIRST, BTN_ENTER): "ECU Information",
    (BTN_SECOND, BTN_ENTER): "Testcase Execution",
    (BTN_FIRST, BTN_SECOND, BTN_ENTER): "ECU Flashing",
    (BTN_SECOND, BTN_FIRST, BTN_ENTER): "File Transfer\ncopying log files\nto USB device",
    (BTN_FIRST, BTN_FIRST, BTN_ENTER): "Reserved1\nfor future versions",
    (BTN_SECOND, BTN_SECOND, BTN_ENTER): "Reserved2\nfor future versions"
}

start_time = time.time()

def get_canoe_timestamp():
    return time.strftime('%H:%M:%S', time.localtime())

# === Main UDS Test Executor ===
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

                status = "Fail"
                failure_reason = "-"
                timestamp = get_canoe_timestamp()

                try:
                    if service_int == 0x10:
                        response = client.change_session(subfunc_int)
                    elif service_int == 0x11:
                        response = client.ecu_reset(subfunc_int)
                    elif service_int == 0x22:
                        response = client.read_data_by_identifier(subfunc_int)
                    else:
                        raise ValueError(f"Unsupported service: {service}")

                    if response.code == 0:
                        status = "Pass"
                    else:
                        failure_reason = f"NRC: {hex(response.code)}"

                except Exception as e:
                    failure_reason = str(e)

                report.append({
                    "id": tc_id,
                    "timestamp": timestamp,
                    "description": step_desc,
                    "type": "Request Sent",
                    "status": status,
                    "failure_reason": failure_reason
                })

    filename = f"UDS_Report_{int(time.time())}.html"
    generate_report(convert_report(report), filename=filename)
    display_text("Report Done!\n" + filename[:16])

# === Main Menu Loop ===
display_text("   Welcome\nto Diagnostic")
time.sleep(1.5)

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
                display_text("Running Tests...")
                get_ecu_information()

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
