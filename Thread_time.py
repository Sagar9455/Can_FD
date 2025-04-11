import can
import time
import os
import isotp
import csv
import udsoncan
import threading
from udsoncan.client import Client
from udsoncan.connections import PythonIsoTpConnection
import logging

# ---------- CAN Interface Setup ----------
os.system('sudo ip link set can0 up type can bitrate 500000 dbitrate 1000000 restart-ms 1000 berr-reporting on fd on')
os.system('sudo ifconfig can0 up')

log_file = 'can_communication_log_threaded.asc'
log_lock = threading.Lock()
start_time = None  # Global reference for relative timestamps

# ---------- Load Test Cases ----------
test_cases = []
with open("test_cases_.txt", "r") as f:
    reader = csv.reader(f)
    next(reader)  # Skip header
    for row in reader:
        if not row[0].startswith("#"):
            test_cases.append(row)

# ---------- ISO-TP and UDS Configuration ----------
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

uds_config = dict(udsoncan.configs.default_client_config)
uds_config["ignore_server_timing_requirements"] = True
uds_config["data_identifiers"] = {
    0xF100: udsoncan.AsciiCodec(8),
    0xF101: udsoncan.AsciiCodec(8),
    0xF187: udsoncan.AsciiCodec(13),
    0xF1AA: udsoncan.AsciiCodec(13),
    0xF1B1: udsoncan.AsciiCodec(13),
    0xF193: udsoncan.AsciiCodec(13),
    0xF120: udsoncan.AsciiCodec(16),
    0xF18B: udsoncan.AsciiCodec(8),
    0xF102: udsoncan.AsciiCodec(0),
    0xF188: udsoncan.AsciiCodec(16),
    0xF18C: udsoncan.AsciiCodec(16),
    0xF197: udsoncan.AsciiCodec(16),
    0xF1A1: udsoncan.AsciiCodec(16)
}

# ---------- CAN and UDS Stack Setup ----------
bus = can.interface.Bus(channel="can0", bustype="socketcan", fd=True)
tp_addr = isotp.Address(isotp.AddressingMode.Normal_11bits, txid=0x7A0, rxid=0x7A8)
stack = isotp.CanStack(bus=bus, address=tp_addr, params=isotp_params)
conn = PythonIsoTpConnection(stack)

# ---------- Write ASC Log Header ----------
with open(log_file, 'w') as f:
    f.write(f'date: {time.strftime("%Y-%m-%d")}\n')
    f.write('base hex timestamps relative\n')
    f.write('comment: Logging CAN communication with UDS service\n')
    f.write('begin of logfile\n')

# ---------- Thread Functions ----------
def tx_thread_func():
    with open(log_file, 'a') as f, Client(conn, request_timeout=2, config=uds_config) as client:
        for case in test_cases:
            tc_id, step, service_id, subfunction, expected_response = case

            try:
                service_id = int(service_id, 16)
                subfunction = int(subfunction, 16)

                print(f"[Tx] Executing {tc_id}: {step}")
                if service_id == 0x10:
                    response = client.change_session(subfunction)
                elif service_id == 0x22:
                    response = client.read_data_by_identifier(subfunction)
                else:
                    continue

                relative_ts = time.time() - start_time
                with log_lock:
                    f.write('{:.4f} Tx 0 8 0x000007A0  {:02X} {:02X} 00 00 00 00 00 00\n'.format(
                        relative_ts, service_id, subfunction))
                    f.flush()
            except Exception as e:
                logging.error(f"Tx Error [{step}]: {e}")

def rx_thread_func():
    with open(log_file, 'a') as f:
        while True:
            message = bus.recv(timeout=1.0)
            if message:
                relative_ts = time.time() - start_time
                with log_lock:
                    f.write('{:.4f} Rx 0 8 {:#010x} {}\n'.format(
                        relative_ts, message.arbitration_id,
                        ' '.join(f'{x:02X}' for x in message.data) +
                        ' 00 00 00 00 00 00'[len(message.data)*3:]
                    ))
                    f.flush()

# ---------- Start Threads ----------
start_time = time.time()  # Set the global reference timestamp

tx_thread = threading.Thread(target=tx_thread_func, daemon=True)
rx_thread = threading.Thread(target=rx_thread_func, daemon=True)

try:
    rx_thread.start()
    tx_thread.start()

    tx_thread.join(timeout=15)
    time.sleep(2)  # Allow Rx thread a bit more time to finish

finally:
    with open(log_file, 'a') as f:
        f.write('end of logfile\n')
    os.system('sudo ifconfig can0 down')
