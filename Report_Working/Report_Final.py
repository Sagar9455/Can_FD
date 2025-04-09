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

#
test_cases = []

with open("test_cases.txt", "r") as f:
    reader = csv.reader(f)
    next(reader)  # Skip header
    for line_number, row in enumerate(reader, start=2):  # line 2 is first after header
        try:
            row = [col.strip() for col in row]

            # Skip empty, short or comment lines
            if not row or len(row) < 5:
                print(f"Skipping line {line_number}: Too short or empty - {row}")
                continue
            if row[0].startswith("#"):
                print(f"Skipping line {line_number}: Comment - {row}")
                continue

            test_cases.append(row)

        except Exception as e:
            print(f"Error reading line {line_number}: {row} -> {e}")

# Verify all test cases have 5 elements
for i, row in enumerate(test_cases):
    if len(row) != 5:
        print(f"Malformed test case at index {i}: {row}")
    else:
        pass  # You can add debug logging here if needed
grouped_cases = defaultdict(list)
for row in test_cases:
    grouped_cases[row[0]].append(row)

def generate_report(test_cases, filename="UDS_Report.html"):
    html_template = """<!DOCTYPE html>
<html>
<head>
    <title>UDS Diagnostic Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            text-align: center;
        }}
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
        .pass {{
            color: green;
            font-weight: bold;
        }}
        .fail {{
            color: red;
            font-weight: bold;
        }}
        .panel {{
            display: none;
            overflow: hidden;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            background: white;
            table-layout: fixed;
        }}
        th, td {{
            border: 1px solid #ccc;
            padding: 8px;
            text-align: center;
            vertical-align: top;
            overflow-wrap: break-word;
            word-wrap: break-word;
            white-space: normal;
            max-width: 200px;
        }}
        th {{
            background-color: #eee;
        }}
        .step-pass {{
            background-color: #c8e6c9;
        }}
        .step-fail {{
            background-color: #ffcdd2;
        }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
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

            const ctx = document.getElementById("summaryChart").getContext("2d");
            new Chart(ctx, {{
                type: 'pie',
                data: {{
                    labels: ['Passed', 'Failed'],
                    datasets: [{{
                        label: 'Test Case Results',
                        data: [{passed}, {failed}],
                        backgroundColor: ['#4CAF50', '#F44336'],
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    responsive: false,
                    plugins: {{
                        legend: {{
                            position: 'bottom'
                        }}
                    }}
                }}
            }});
        }});
    </script>
</head>
<body>
    <h1>UDS Diagnostic Report</h1>
    <div style="text-align:center; margin-bottom: 20px;">
        <p><strong>Total Test Cases:</strong> {total}</p>
        <p style="color:green;"><strong>Passed:</strong> {passed}</p>
        <p style="color:red;"><strong>Failed:</strong> {failed}</p>
    </div>
    <canvas id="summaryChart" width="300" height="300" style="display: block; margin: 0 auto 30px;"></canvas>
    {body}
</body>
</html>
"""

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

    total = len(test_cases)
    passed = sum(1 for tc in test_cases if tc["status"] == "Pass")
    failed = total - passed

    with open(filename, "w") as f:
        f.write(html_template.format(body=body, total=total, passed=passed, failed=failed))

    print(f"Report generated: {filename}")
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
        0xF100: udsoncan.AsciiCodec(4),
        0xF1DD: udsoncan.AsciiCodec(4),
        0xF187: udsoncan.AsciiCodec(9),
        0xF1AA: udsoncan.AsciiCodec(4),
        0xF1B1: udsoncan.AsciiCodec(4),
        0xF193: udsoncan.AsciiCodec(4),
        0xF120: udsoncan.AsciiCodec(16),
        0xF18B: udsoncan.AsciiCodec(4),
        0xF102: udsoncan.AsciiCodec(8),
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
    return f"{time.time() - start_time:.6f}"  # Seconds with nanoseconds

#
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
