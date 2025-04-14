from drivers.can_logger import CANLogger

can_logger = CANLogger()
can_bus = can_logger.setup()
uds = UDSClient(config, bus=can_bus, logger=can_logger)

from drivers.can_logger import CANLogger
from drivers.uds_client import UDSClient

# Initialize CAN Logger
can_logger = CANLogger(channel="can0", interface="socketcan", can_fd=True)

# Pass it to your UDSClient
uds = UDSClient(config, logger=can_logger)

import can
import os
import isotp
import time
import logging
from udsoncan.client import Client
from udsoncan.connections import PythonIsoTpConnection
from udsoncan.configs import default_client_config
from drivers.Parse_handler import load_testcases
from udsoncan import AsciiCodec
from drivers.report_generator import generate_report, convert_report


class UDSClient:
    def __init__(self, config, bus=None, logger=None):
        can_cfg = config["uds"]["can"]
        isotp_cfg = config["uds"]["isotp"]
        timing_cfg = config["uds"]["timing"]

        self.uds_config = config["uds"]
        print("UDS Config loaded:", self.uds_config)

        self.tx_id = int(can_cfg["tx_id"], 16)
        self.rx_id = int(can_cfg["rx_id"], 16)
        is_extended = can_cfg.get("is_extended", False)

        if is_extended:
            addr_mode = isotp.AddressingMode.Normal_29bits
        else:
            addr_mode = isotp.AddressingMode.Normal_11bits

        address = isotp.Address(
            addr_mode,
            txid=self.tx_id,
            rxid=self.rx_id
        )

        self.external_bus = bus
        self.logger = logger

        self.bus = bus or can.interface.Bus(
            channel=can_cfg["channel"],
            bustype=can_cfg["interface"],
            fd=can_cfg.get("can_fd", True),
            can_filters=[{"can_id": self.rx_id, "can_mask": 0x7FF, "extended": False}]
        )

        self.stack = isotp.CanStack(
            bus=self.bus,
            address=address,
            params=isotp_cfg
        )

        self.conn = PythonIsoTpConnection(self.stack)

        self.client_config = default_client_config.copy()
        self.client_config["p2_timeout"] = timing_cfg["p2_client"] / 1000.0
        self.client_config["p2_star_timeout"] = timing_cfg["p2_extended_client"] / 1000.0
        self.client_config["s3_client_timeout"] = timing_cfg["s3_client"] / 1000.0

        self.info_dids = self.uds_config["ecu_information_dids"]
        self.decode_dids = self.uds_config["decoding_dids"]

        # Register AsciiCodec for all decoding
        self.client_config["data_identifiers"] = {
            int(did_str, 16): AsciiCodec(length)
            for did_str, length in self.decode_dids.items()
        }

    def start_logging(self, filename):
        if self.logger:
            log_path = os.path.join("logs", filename)
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            self.logger.start(log_path)

    def stop_logging(self):
        if self.logger:
            self.logger.stop()

    def get_ecu_information(self, oled):
        
        # Start CAN logging with timestamped filename
        timestamp = time.strftime("%Y%m%d_%H%M")
        log_path = os.path.join("output", "asc_logs", f"ECU_INFO_{timestamp}.asc")
        self.logger.start(log_path)

        session_default = int(self.uds_config["default_session"], 16)
        session_extended = int(self.uds_config["extended_session"], 16)

        with Client(self.conn, request_timeout=2, config=self.client_config) as client:
            client.change_session(session_default)
            time.sleep(0.2)
            client.change_session(session_extended)
            time.sleep(0.2)

            for did_hex, info in self.info_dids.items():
                label = info["label"]
                did = int(did_hex, 16)
                try:
                    response = client.read_data_by_identifier(did)
                    if response.positive:
                        value = response.service_data.values[did]
                        oled.display_text(f"{label}:\n{value}")
                        print(f"[ECU Info] {label} ({did_hex}) = {value}")
                    else:
                        oled.display_text(f"{label}: NRC {hex(response.code)}")
                except Exception as e:
                    oled.display_text(f"{label}: {str(e)[:16]}")
                time.sleep(2)

        self.stop_logging()

    def run_testcase(self, oled):
         # Start CAN logging with timestamped filename
         timestamp = time.strftime("%Y%m%d_%H%M")
         log_path = os.path.join("output", "asc_logs", f"TESTCASE_{timestamp}.asc")
         self.logger.start(log_path)

        grouped_cases = load_testcases()
        report = []

        with Client(self.conn, request_timeout=2, config=self.client_config) as client:
            for tc_id, steps in grouped_cases.items():
                logging.info(f"Running Test Case: {tc_id}")
                for step in steps:
                    _, step_desc, service, subfunc, expected = step
                    try:
                        service_int = int(service, 16)
                        subfunc_int = int(subfunc, 16)
                        expected_bytes = [int(b, 16) for b in expected.strip().split()]
                        logging.info(f"{tc_id} - {step_desc}: SID={service}, Sub={subfunc}, Expected={expected_bytes}")

                        response = None
                        if service_int == 0x10:
                            response = client.change_session(subfunc_int)
                        elif service_int == 0x11:
                            response = client.ecu_reset(subfunc_int)
                        elif service_int == 0x22:
                            response = client.read_data_by_identifier(subfunc_int)
                        else:
                            raise ValueError(f"Unsupported service: {service}")

                        status = "Fail"
                        failure_reason = "-"
                        if response.positive:
                            actual = list(response.original_payload)
                            if actual[:len(expected_bytes)] == expected_bytes:
                                status = "Pass"
                                logging.info(f"{tc_id} {step_desc} -> PASS")
                            else:
                                failure_reason = f"Expected {expected_bytes}, got {actual}"
                                logging.warning(f"{tc_id} {step_desc} -> FAIL - {failure_reason}")
                        else:
                            failure_reason = f"NRC: {hex(response.code)}"
                            logging.warning(f"{tc_id} {step_desc} -> FAIL - {failure_reason}")

                    except Exception as e:
                        status = "Fail"
                        failure_reason = str(e)
                        logging.error(f"{tc_id} {step_desc} -> EXCEPTION - {failure_reason}")

                    oled.display_text(f"{tc_id}\n{step_desc[:20]}\n{status}")
                    time.sleep(2)
                    if status == "Fail":
                        oled.display_text(f"FAIL\n{failure_reason[:20]}")
                        time.sleep(2)

                    report.append({
                        "id": tc_id,
                        "timestamp": time.strftime('%H:%M:%S'),
                        "response_timestamp": time.strftime('%H:%M:%S'),
                        "description": step_desc,
                        "type": "Request Sent",
                        "status": status,
                        "failure_reason": failure_reason
                    })

        project_root = os.path.abspath(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        report_dir = os.path.join(project_root, 'output', 'html_reports')
        os.makedirs(report_dir, exist_ok=True)

        report_filename = f"UDS_Report_{int(time.time())}.html"
        report_path = os.path.join(report_dir, report_filename)

        html_report = convert_report(report)
        generate_report(html_report, filename=report_path)

        oled.display_text("Report Done!\n" + report_filename[:16])

        logging.info(f"Test report saved: {report_filename}")
        self.stop_logging()
