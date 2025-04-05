from uds import UdsClient
from uds.transport import isotp_can
import can
from datetime import datetime

def get_canoe_timestamp():
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

def generate_report(report_data):
    html = """<!DOCTYPE html>
<html>
<head>
    <title>UDS Diagnostic Report</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 40px; }
        h1 { color: #333; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #ccc; padding: 10px; text-align: left; }
        th { background-color: #e0e0e0; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .fail { color: red; font-weight: bold; }
        .pass { color: green; font-weight: bold; }
    </style>
</head>
<body>
    <h1>UDS Diagnostic Report</h1>
    <table>
        <tr>
            <th>Timestamp</th>
            <th>Response Timestamp</th>
            <th>Action</th>
            <th>Request Status</th>
            <th>Response Status</th>
            <th>Failure Reason</th>
            <th>Raw Response</th>
        </tr>"""

    for entry in report_data:
        html += f"""
        <tr>
            <td>{entry['timestamp']}</td>
            <td>{entry['response_timestamp']}</td>
            <td>{entry['action']}</td>
            <td class="{entry['request_status'].lower()}">{entry['request_status']}</td>
            <td class="{entry['response_status'].lower()}">{entry['response_status']}</td>
            <td>{entry['failure_reason']}</td>
            <td>{entry['raw_response']}</td>
        </tr>"""

    html += """
    </table>
</body>
</html>"""

    with open("RT.html", "w") as f:
        f.write(html)
    print("Report generated: RT.html")

def run_uds_diagnostics():
    bus = can.interface.Bus(channel='can0', bustype='socketcan')
    tp_addr = isotp_can.Address(isotp_can.AddressingMode.Extended, txid=0x18DAF110, rxid=0x18DA10F1)
    tp_layer = isotp_can.TransportLayer(bus=bus, address=tp_addr)

    client = UdsClient(tp_layer)
    report_data = []

    with client:
        steps = [
            ("Default Session", lambda: client.change_session(0x01)),
            ("Extended Session", lambda: client.change_session(0x03)),
            ("Read DID (0xF100)", lambda: client.read_data_by_identifier(0xF100)),
            ("Read DID (0xF101)", lambda: client.read_data_by_identifier(0xF101)),
            ("Read DID (0xF1DD)", lambda: client.read_data_by_identifier(0xF1DD)),
            ("Read DID (0xF113)", lambda: client.read_data_by_identifier(0xF113)),
            ("Read DID (0xF187)", lambda: client.read_data_by_identifier(0xF187)),
        ]

        for action, func in steps:
            timestamp = get_canoe_timestamp()
            request_status = "Fail"
            response_status = "Fail"
            failure_reason = "No response"
            raw_response = "-"

            try:
                print(f"{action}...")
                response = func()
                if response.positive:
                    request_status = "Pass"
                    response_status = "Pass"
                    failure_reason = "-"
                    raw_response = str(response.service_data)
                    print(f"Response Data: {raw_response}")
                else:
                    failure_reason = f"NRC 0x{response.code:02X}: {response.code_name}"
            except Exception as e:
                failure_reason = f"Exception: {str(e)}"

            response_timestamp = get_canoe_timestamp()
            report_data.append({
                "timestamp": timestamp,
                "response_timestamp": response_timestamp,
                "action": action,
                "request_status": request_status,
                "response_status": response_status,
                "failure_reason": failure_reason,
                "raw_response": raw_response
            })

    generate_report(report_data)

if __name__ == "__main__":
    run_uds_diagnostics()
