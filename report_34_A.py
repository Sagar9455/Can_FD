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
    
    with open("RT.html", "w") as file:
        file.write(html_content)
    print("Report generated: UDS_Report.html")




def get_canoe_timestamp():
    return f"{time.time() - start_time:.9f}"  # Seconds with nanoseconds


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

# Define CAN interface
interface = "can0"
bus = can.interface.Bus(channel=interface, bustype="socketcan", fd=True)
bus.set_filters([{ "can_id": 0x7A8, "can_mask": 0xFFF }])

# Define ISO-TP addressing
tp_addr = isotp.Address(isotp.AddressingMode.Normal_11bits, txid=0x7A0, rxid=0x7A8)
stack = isotp.CanStack(bus=bus, address=tp_addr, params=isotp_params)
conn = PythonIsoTpConnection(stack)



try:
    with Client(conn, request_timeout=2, config=config) as client:
        print("Waiting for button press...")
        while True:
            if GPIO.input(BUTTON_PIN) == GPIO.LOW:
                print("Button pressed! Sending UDS requests...")
                report_data = []
                
                # Capture start time for CANoe-like timestamp
               
                try:
                    print("Switching to Default Session...")
                    start_time = time.time()
                    timestamp = get_canoe_timestamp()
                    
                    
                    response = client.change_session(0x01)  # 0x01: Default Session
                    if response.positive:
                         print("Default Session Activated.")
                         request_status = "Pass"
                         response_status = "Pass"
                         failure_reason = "-"
                    else:
                        request_status = "Fail"
                        response_status = "Fail"    
                except Exception as e:
                    print(f"Failed to switch to Default Session: {e}")
                    
                    response_status = "Fail"
                    failure_reason = str(e)
                response_timestamp = get_canoe_timestamp()
                report_data.append({
                        "timestamp": timestamp,
                        "response_timestamp": response_timestamp,
                        "action": "Default Session (0x10 0x01)",
                        "request_status": request_status,
                        "response_status": response_status,
                        "failure_reason": failure_reason
                    })
                time.sleep(0.5)

                # Step 2: Extended Session Control (0x10 0x03)
                timestamp = get_canoe_timestamp()
                try:
                    print("Switching to Extended Session...")
                    
                    response = client.change_session(0x03)  
                    if response.positive:
                         
                         request_status = "Pass"
                         response_status = "Pass"
                         failure_reason = "-"
                    else:
                        request_status = "Fail" 
                        response_status = "Fail"      
                except Exception as e:
                    print(f"Failed to switch to Extended Session: {e}")
                    
                    response_status = "Fail"
                    failure_reason = str(e)
                response_timestamp = get_canoe_timestamp()  
                report_data.append({
                        "timestamp": timestamp,
                        "response_timestamp": response_timestamp,
                        "action": "Default Session (0x10 0x01)",
                        "request_status": request_status,
                        "response_status": response_status,
                        "failure_reason": failure_reason
                    })
                time.sleep(0.5)

                # Step 3: Read DID (0xF100)
                timestamp = get_canoe_timestamp()
                try:
                    print("Reading DID 0xF100...")
                    response = client.read_data_by_identifier(0xF100)
                    request_status = "Pass"
                    if response.positive:
                        response_status = "Pass"
                        
                        
                        print(f"Response Data: {response.service_data}")
                    
                except Exception as e:
                    print(f"Error: {e}")
                    failure_reason = str(e)
                response_timestamp = get_canoe_timestamp()
                report_data.append({
                        "timestamp": timestamp,
                        "response_timestamp": response_timestamp,
                        "action": "Read DID (0xF100)",
                        "request_status": request_status,
                        "response_status": response_status,
                        "failure_reason": failure_reason
                    })
                
                # Step 3: Read DID (0xF101)
                timestamp = get_canoe_timestamp()
                try:
                    print("Reading DID 0xF101...")
                    response = client.read_data_by_identifier(0xF101)
                    request_status = "Pass"
                    if response.positive:
                        response_status = "Pass"
                        
                        
                        print(f"Response Data: {response.service_data}")
                    
                except Exception as e:
                    print(f"Error: {e}")
                    failure_reason = str(e)
                response_timestamp = get_canoe_timestamp()
                report_data.append({
                        "timestamp": timestamp,
                        "response_timestamp": response_timestamp,
                        "action": "Read DID (0xF101)",
                        "request_status": request_status,
                        "response_status": response_status,
                        "failure_reason": failure_reason
                    })
                
                
                # Step 3: Read DID (0xF1DD)
                timestamp = get_canoe_timestamp()
                try:
                    print("Reading DID 0xF1DD...")
                    response = client.read_data_by_identifier(0xF1DD)
                    request_status = "Pass"
                    if response.positive:
                        response_status = "Pass"
                        
                        
                        print(f"Response Data: {response.service_data}")
                    
                except Exception as e:
                    print(f"Error: {e}")
                    failure_reason = str(e)
                response_timestamp = get_canoe_timestamp()
                report_data.append({
                        "timestamp": timestamp,
                        "response_timestamp": response_timestamp,
                        "action": "Read DID (0xF1DD)",
                        "request_status": request_status,
                        "response_status": response_status,
                        "failure_reason": failure_reason
                    })
                   
                
                # Step 3: Read DID (0xF187)
                timestamp = get_canoe_timestamp()
                try:
                    print("Reading DID 0xF187...")
                    response = client.read_data_by_identifier(0xF187)
                    request_status = "Pass"
                    if response.positive:
                        response_status = "Pass"
                        
                        
                        print(f"Response Data: {response.service_data}")
                    
                except Exception as e:
                    print(f"Error: {e}")
                    failure_reason = str(e)
                response_timestamp = get_canoe_timestamp()
                report_data.append({
                        "timestamp": timestamp,
                        "response_timestamp": response_timestamp,
                        "action": "Read DID (0xF187)",
                        "request_status": request_status,
                        "response_status": response_status,
                        "failure_reason": failure_reason
                    })
                 
                # Step 3: Read DID (0xF1AA) 
                timestamp = get_canoe_timestamp()
                try: 
                    print("Reading DID 0xF1AA...") 
                    response = client.read_data_by_identifier(0xF1AA) 
                    request_status = "Pass" 
                    if response.positive: 
                        response_status = "Pass" 
                         
                           
                        print(f"Response Data: {response.service_data}")   
                       
                except Exception as e:   
                    print(f"Error: {e}")   
                    failure_reason = str(e)   
                response_timestamp = get_canoe_timestamp()   
                report_data.append({   
                        "timestamp": timestamp,   
                        "response_timestamp": response_timestamp,   
                        "action": "Read DID (0xF1AA)",   
                        "request_status": request_status,   
                        "response_status": response_status,   
                        "failure_reason": failure_reason   
                    })   
                                     
                
                
                # Step 3: Read DID (0xF1B1) 
                timestamp = get_canoe_timestamp() 
                try: 
                    print("Reading DID 0xF1B1...") 
                    response = client.read_data_by_identifier(0xF1B1) 
                    request_status = "Pass" 
                    if response.positive: 
                        response_status = "Pass" 
                         
                           
                        print(f"Response Data: {response.service_data}")   
                       
                except Exception as e:   
                    print(f"Error: {e}")   
                    failure_reason = str(e)   
                response_timestamp = get_canoe_timestamp()   
                report_data.append({   
                        "timestamp": timestamp,   
                        "response_timestamp": response_timestamp,   
                        "action": "Read DID (0xF1B1)",   
                        "request_status": request_status,   
                        "response_status": response_status,   
                        "failure_reason": failure_reason   
                    })
                
                
                # Step 3: Read DID (0xF193) 
                timestamp = get_canoe_timestamp()
                try: 
                    print("Reading DID 0xF193...") 
                    response = client.read_data_by_identifier(0xF193) 
                    request_status = "Pass" 
                    if response.positive: 
                        response_status = "Pass" 
                         
                           
                        print(f"Response Data: {response.service_data}") 
                       
                except Exception as e:   
                    print(f"Error: {e}")   
                    failure_reason = str(e)   
                response_timestamp = get_canoe_timestamp()  
                report_data.append({   
                        "timestamp": timestamp,   
                        "response_timestamp": response_timestamp,   
                        "action": "Read DID (0xF193)",   
                        "request_status": request_status,   
                        "response_status": response_status,   
                        "failure_reason": failure_reason   
                    })
                
                # Step 3: Read DID (0xF120) 
                timestamp = get_canoe_timestamp()
                try: 
                    print("Reading DID 0xF120...") 
                    response = client.read_data_by_identifier(0xF120) 
                    request_status = "Pass" 
                    if response.positive: 
                        response_status = "Pass" 
                         
                           
                        print(f"Response Data: {response.service_data}") 
                       
                except Exception as e:   
                    print(f"Error: {e}")   
                    failure_reason = str(e)   
                response_timestamp = get_canoe_timestamp()  
                report_data.append({   
                        "timestamp": timestamp,   
                        "response_timestamp": response_timestamp,   
                        "action": "Read DID (0xF120)",   
                        "request_status": request_status,   
                        "response_status": response_status,   
                        "failure_reason": failure_reason   
                    })
                
                # Step 3: Read DID (0xF18B) 
                timestamp = get_canoe_timestamp()
                try: 
                    print("Reading DID 0xF18B...") 
                    response = client.read_data_by_identifier(0xF18B) 
                    request_status = "Pass" 
                    if response.positive: 
                        response_status = "Pass" 
                         
                           
                        print(f"Response Data: {response.service_data}") 
                       
                except Exception as e:   
                    print(f"Error: {e}")   
                    failure_reason = str(e)   
                response_timestamp = get_canoe_timestamp()
                report_data.append({   
                        "timestamp": timestamp,   
                        "response_timestamp": response_timestamp,   
                        "action": "Read DID (0xF18B)",   
                        "request_status": request_status,   
                        "response_status": response_status,   
                        "failure_reason": failure_reason   
                    })
                
                # Step 3: Read DID (0xF102) 
                timestamp = get_canoe_timestamp()
                try: 
                    print("Reading DID 0xF102...") 
                    response = client.read_data_by_identifier(0xF102) 
                    request_status = "Pass" 
                    if response.positive: 
                        response_status = "Pass" 
                         
                           
                        print(f"Response Data: {response.service_data}") 
                       
                except Exception as e:   
                    print(f"Error: {e}")   
                    failure_reason = str(e)   
                response_timestamp = get_canoe_timestamp()
                report_data.append({   
                        "timestamp": timestamp,   
                        "response_timestamp": response_timestamp,   
                        "action": "Read DID (0xF102)",   
                        "request_status": request_status,   
                        "response_status": response_status,   
                        "failure_reason": failure_reason   
                    })
                
                
                
                generate_report(report_data)
                time.sleep(1)  # Prevent multiple detections
except KeyboardInterrupt:
    print("Exiting...")
finally:
    GPIO.cleanup()
