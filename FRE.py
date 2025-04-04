import os
import time
import logging
import can
import isotp
import udsoncan
from udsoncan.client import Client
from udsoncan.connections import PythonIsoTpConnection

def get_canoe_timestamp():
    return time.strftime("%Y-%m-%d %H:%M:%S")

def generate_report(report_data):
    """Generates a dynamic UDS diagnostic report."""
    print("\n--- UDS Diagnostic Report ---")
    for entry in report_data:
        print(entry)

def get_ecu_information():
    """Retrieve and display ECU information dynamically from CAN Bus."""
    os.system('sudo ip link set can0 down')
    os.system('sudo ip link set can0 up type can bitrate 500000 dbitrate 1000000 restart-ms 1000 berr-reporting on fd on')
    os.system('sudo ifconfig can0 up')

    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

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

    tp_addr = isotp.Address(isotp.AddressingMode.Normal_11bits, txid=0x8A0, rxid=0x6A8)
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
                "request_status": "Pass" if response_status == "Pass" else "Fail",
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
