import can
import isotp
import time
import logging
from udsoncan.client import Client
from udsoncan.connections import PythonIsoTpConnection

from report_generator import generate_report
from utils import get_canoe_timestamp  # Make sure you have this utility for timestamps
from oled_display import display_text  # If display is used

class UDSClient:
    def __init__(self, config):
        tx_id = int(config['tx_id'], 16)
        rx_id = int(config['rx_id'], 16)
        channel = config['channel']
        iface = config['interface']

        self.data_identifiers = config.get('data_identifiers', [])

        self.bus = can.interface.Bus(channel=channel, bustype=iface)
        self.stack = isotp.CanStack(bus=self.bus, address=isotp.Address(isotp.AddressingMode.Normal_11bits, txid=tx_id, rxid=rx_id))
        self.conn = PythonIsoTpConnection(self.stack)

    def get_ecu_information(self):
        report_data = []

        with Client(self.conn, request_timeout=2) as client:
            logging.info("UDS Client Started")

            # 1. Tester Present (0x3E)
            try:
                client.tester_present()
                logging.info("Tester Present sent successfully")
            except Exception as e:
                logging.warning(f"Tester Present failed: {e}")

            # 2. Default Session (0x10 0x01)
            report_data.append(self._send_session_control(client, 0x01, "Default Session (0x10 0x01)"))
            time.sleep(0.5)

            # 3. Extended Session (0x10 0x03)
            report_data.append(self._send_session_control(client, 0x03, "Extended Session (0x10 0x03)"))
            time.sleep(0.5)

            # 4. ReadDataByIdentifier
            for did in self.data_identifiers:
                report_data.append(self._read_did(client, did))
                time.sleep(0.3)

            # 5. Report Generation
            generate_report(report_data)
            display_text("Report Generated")
            logging.info("UDS Client Completed")

    def _send_session_control(self, client, session_id, label):
        try:
            timestamp = get_canoe_timestamp()
            response = client.change_session(session_id)

            if response.positive:
                logging.info(f"{label} success")
                request_status = "Pass"
                response_status = "Pass"
                failure_reason = "-"
            else:
                request_status = "Fail"
                response_status = "Fail"
                failure_reason = f"NRC: {response.code_name} (0x{response.code:02X})"

        except Exception as e:
            logging.error(f"{label} failed: {e}")
            timestamp = get_canoe_timestamp()
            request_status = "Fail"
            response_status = "Fail"
            failure_reason = str(e)

        return {
            "timestamp": timestamp,
            "response_timestamp": get_canoe_timestamp(),
            "action": label,
            "request_status": request_status,
            "response_status": response_status,
            "failure_reason": failure_reason
        }

    def _read_did(self, client, did):
        label = f"Read DID 0x{did:04X}"
        timestamp = get_canoe_timestamp()

        try:
            logging.info(f"Reading {label}...")
            response = client.read_data_by_identifier(did)

            if response.positive:
                request_status = "Pass"
                response_status = "Pass"
                failure_reason = "-"
                logging.info(f"{label} success, value: {response.service_data}")
            else:
                request_status = "Fail"
                response_status = "Fail"
                failure_reason = f"NRC: {response.code_name} (0x{response.code:02X})"
                logging.warning(f"{label} failed - {failure_reason}")

        except Exception as e:
            logging.error(f"{label} exception: {e}")
            request_status = "Fail"
            response_status = "Fail"
            failure_reason = str(e)

        return {
            "timestamp": timestamp,
            "response_timestamp": get_canoe_timestamp(),
            "action": label,
            "request_status": request_status,
            "response_status": response_status,
            "failure_reason": failure_reason
        }


def generate_reports(report_data):
    return generate_report(report_data)
