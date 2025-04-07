import time
import RPi.GPIO as GPIO
import board
import busio
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont
import udsoncan
from udsoncan.connections import PythonIsoTpConnection
from udsoncan.client import Client
import udsoncan.configs
import isotp
import can
import logging
import os


def generate_report(data):
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>UDS Diagnostic Report</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .container { text-align: center; }
            h1 { text-align: center; margin-bottom: 20px; font-weight: bold; }
            table { width: 100%; border-collapse: collapse; background: white; }
            th, td { border: 1px solid black; padding: 10px; text-align: center; }
            th { background-color: #b0b0b0; color: black; font-weight: bold; }
            .pass { background-color: #c8e6c9; color: green; }
            .fail { background-color: #ffcdd2; color: red; }
            .section-title { background-color: #f0f0f0; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>UDS Diagnostic Report</h1>
            <table>
                <tr>
                    <th>S.No</th>
                    <th>Description</th>
                    <th>Timestamp</th>
                    <th>Step</th>
                    <th>Status</th>
                    <th>Failure Reason</th>
                </tr>
    """
    
    for idx, entry in enumerate(data, start=1):
        html_content += f"""
            <tr class="section-title">
                <td rowspan="2">{idx}</td>
                <td rowspan="2">{entry["action"]}</td>
                <td>{entry["timestamp"]}</td>
                <td>Request Sent</td>
                <td class="{'pass' if entry['request_status'] == 'Pass' else 'fail'}">{entry['request_status']}</td>
                <td>{entry['failure_reason'] if entry['request_status'] == 'Fail' else '-'}</td>
            </tr>
            <tr>
                <td>{entry["response_timestamp"] if entry['response_status'] == 'Pass' else '---'}</td>
                <td>Response Received</td>
                <td class="{'pass' if entry['response_status'] == 'Pass' else 'fail'}">{entry['response_status']}</td>
                <td>-</td>
            </tr>
        """

    html_content += """
            </table>
        </div>
    </body>
    </html>
    """
    
    with open("RTY.html", "w") as file:
        file.write(html_content)
    print("Report generated: UDS_Report.html")
    
    
    
start_time = time.time()

def get_canoe_timestamp():
    return f"{time.time() - start_time:.6f}"  # Seconds with nanoseconds

# Set up GPIO mode
GPIO.setmode(GPIO.BCM)

# Define button pins
BTN_FIRST = 12  # First button in combination
BTN_SECOND = 16  # Second button in combination
BTN_ENTER = 20  # Confirm selection
BTN_THANKS = 21  # System is shutting down
buttons = [BTN_FIRST, BTN_SECOND, BTN_ENTER, BTN_THANKS]

# Set up buttons as input with pull-up resistors
for btn in buttons:
    GPIO.setup(btn, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Initialize I2C and OLED
i2c = busio.I2C(board.SCL, board.SDA)
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)

time.sleep(0.5)  # Added delay for OLED stability

# Load font
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 9)

# Menu options mapped to button sequences
menu_combinations = {
    (BTN_FIRST, BTN_ENTER): "ECU Information",
    (BTN_SECOND, BTN_ENTER): "Testcase Execution",
    (BTN_FIRST, BTN_SECOND, BTN_ENTER): "ECU Flashing",
    (BTN_SECOND, BTN_FIRST, BTN_ENTER): "File Transfer\ncopying log files\nto USB device",
    (BTN_FIRST, BTN_FIRST, BTN_ENTER): "Reserved1\nfor future versions",
    (BTN_SECOND, BTN_SECOND, BTN_ENTER): "Reserved2\nfor future versions"
}
selected_sequence = []
selected_option = None
last_displayed_text = ""

# Function to display text on OLED
def display_text(text, y=10):
    """Function to display text on OLED"""
    global last_displayed_text
    if text != last_displayed_text:
        oled.fill(0)  # Clear screen
        oled.show()
        
        image = Image.new("1", (oled.width, oled.height))
        draw = ImageDraw.Draw(image)
        
        # Draw text on OLED
        draw.text((5, y), text, font=font, fill=255)
        
        # Display image on OLED
        oled.image(image)
        oled.show()
        last_displayed_text = text
       

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
            timestamp = get_canoe_timestamp()
            try:
                response = uds_function(*args)
                request_status = "Pass"
                if response.positive:
                    response_status = "Pass"
                    failure_reason = "-"
                else:
                    response_status = "Fail"
                    failure_reason = f"NRC: {hex(response.code)}"
            except Exception as e:
                logging.error(f"Error in {action}: {e}")
                response_status = "Fail"
                failure_reason = str(e)

            response_timestamp = get_canoe_timestamp()
            report_data.append({
                "timestamp": timestamp,
                "response_timestamp": response_timestamp,
                "action": action,
                "request_status": "Pass",
                "response_status": response_status,
                "failure_reason": failure_reason
            })

        # Tester Present (0x3E)
        send_uds_request("Tester Present (0x3E)", client.tester_present)

        # Default Session (0x10 0x01)
        send_uds_request("Default Session (0x10 0x01)", client.change_session, 0x01)

        # Extended Session (0x10 0x03)
        send_uds_request("Extended Session (0x10 0x03)", client.change_session, 0x03)

        # Read Data Identifiers (DIDs)
        for did in config["data_identifiers"]:
            send_uds_request(f"Read DID {hex(did)}", client.read_data_by_identifier, did)

        # Generate Report
        generate_report(report_data)

         
        display_text("Report Generated")
        logging.info("UDS Client Closed")
        

variable=0
varFinal=0
display_text("            Welcome\n                   to\n           Diagnostic")

time.sleep(1.5)
try:
    while True:
        oled.fill(0)  # Clear screen
        oled.show()
        display_text("Select a option:\n1. ECU Information\n2. Testcase Execution\n3. ECU Flashing\n4. File Transfer into USB device\n5. Reserved",y=0)
        
        while True:
                        
            if GPIO.input(BTN_FIRST) == GPIO.LOW:
                variable=(variable*10)+1
                selected_sequence.append(BTN_FIRST)
                b = str(variable)
                display_text(b)
                #time.sleep(0.2)
        
            if GPIO.input(BTN_SECOND) == GPIO.LOW:
                variable=(variable*10)+2
                selected_sequence.append(BTN_SECOND)
                a = str(variable)
                display_text(a)
                #time.sleep(0.2)      
        
            if GPIO.input(BTN_ENTER) == GPIO.LOW:
                varFinal=variable
                variable=0
                selected_sequence.append(BTN_ENTER)
                    
                selected_option = menu_combinations.get(tuple(selected_sequence), "Invalid Input")
                display_text(f"{selected_option}")
        
                if selected_option == "ECU Information":
                    time.sleep(0.5)
                    display_text("Fetching\nECU Information...")
                    get_ecu_information()
                    display_text("Completed")
               
                if selected_option == "Exit":
                    os.system("exit")
                selected_sequence.clear()  # Reset sequence after confirmation
                #time.sleep(0.1)
        
            if GPIO.input(BTN_THANKS) == GPIO.LOW:
                display_text("Shutting Down")
                time.sleep(0.1)
                os.system('sudo poweroff')
        
            time.sleep(0.1)

except KeyboardInterrupt:
    print("\nExiting...")

finally:
    GPIO.cleanup()
