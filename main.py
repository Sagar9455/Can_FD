import json
import csv
import time
import threading
import can
from udsoncan.client import Client
from udsoncan.connections import PythonIsoTpConnection
import isotp

# Load config
with open('config.json') as f:
    config = json.load(f)

data_identifiers = {int(k, 16): v for k, v in config["data_identifiers"].items()}
stmin_config = {k.upper(): v for k, v in config["stmin_config"].items()}

latest_stmin_info = {"did": None, "stmin": None}

# Setup CAN and ISOTP
can_bus = can.interface.Bus(channel='can0', bustype='socketcan')

tp_addr = isotp.Address(isotp.AddressingMode.Normal_11bits, txid=0x7E0, rxid=0x7E8)
tp_layer = isotp.CanStack(bus=can_bus, address=tp_addr)
conn = PythonIsoTpConnection(tp_layer)

# Monitor Flow Control frames
def interpret_stmin(byte_val):
    if byte_val <= 0x7F:
        return byte_val
    elif 0xF1 <= byte_val <= 0xF9:
        return (byte_val - 0xF0) * 0.1
    else:
        return 0

def monitor_stmin():
    monitor_bus = can.interface.Bus(channel='can0', bustype='socketcan')
    while True:
        msg = monitor_bus.recv()
        if msg and len(msg.data) >= 3:
            if msg.data[0] == 0x30:  # Flow Control
                stmin_val = interpret_stmin(msg.data[2])
                latest_stmin_info["stmin"] = stmin_val
                print(f"[Monitor] FC frame from 0x{msg.arbitration_id:X}: STmin={stmin_val} ms (0x{msg.data[2]:02X})")

# Start monitor thread
threading.Thread(target=monitor_stmin, daemon=True).start()

# Diagnostic session
def perform_diagnostics():
    results = []
    with Client(conn, request_timeout=2) as client:
        client.config["data_identifiers"] = {
            did: lambda x: x.decode("ascii") for did in data_identifiers
        }

        # Enter extended diagnostic session (optional)
        try:
            client.change_session(0x03)
        except Exception as e:
            print(f"[!] Failed to enter extended session: {e}")

        for did_hex, expected_stmin in stmin_config.items():
            did = int(did_hex, 16)
            latest_stmin_info["did"] = did_hex
            latest_stmin_info["stmin"] = None

            print(f"\n[Request] Reading DID 0x{did_hex}")
            try:
                response = client.read_data_by_identifier(did)
                time.sleep(1.0)  # Wait for FC if any
                actual_stmin = latest_stmin_info["stmin"]

                result = {
                    "DID": did_hex,
                    "Value": response.service_data.values.get(did),
                    "Expected_STmin": expected_stmin,
                    "Actual_STmin": actual_stmin,
                    "Status": "PASS" if actual_stmin == expected_stmin else "FAIL"
                }

            except Exception as e:
                result = {
                    "DID": did_hex,
                    "Value": None,
                    "Expected_STmin": expected_stmin,
                    "Actual_STmin": None,
                    "Status": f"ERROR: {str(e)}"
                }

            results.append(result)
            print(result)

    return results

# Write to CSV
def write_report(results):
    with open("stmin_report.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["DID", "Value", "Expected_STmin", "Actual_STmin", "Status"])
        writer.writeheader()
        writer.writerows(results)
    print("\n✅ Report written to stmin_report.csv")

# Main execution
if __name__ == "__main__":
    results = perform_diagnostics()
    write_report(results)
