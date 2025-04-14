import can
import time
import os
import isotp
import unittest
import csv
import isotp
import udsoncan
from udsoncan.client import Client
from udsoncan.connections import PythonIsoTpConnection
import udsoncan.configs
import logging

"""Retrieve and display ECU information."""
os.system('sudo ip link set can0 up type can bitrate 500000 dbitrate 1000000 restart-ms 1000 berr-reporting on fd on')  # Set bitrate to 500kbps
os.system('sudo ifconfig can0 up')

# Define the log file path
log_file = 'zcan_communication_log_@31.asc'
# Define ASC log file
bus = can.interface.Bus(channel="can0", bustype="socketcan", fd=True)
asc_logger = can.ASCWriter(log_file)
notifier = can.Notifier(bus,[asc_logger])#logs TX and Rx
                        
def create_uds_session_request():
    with Client(conn, request_timeout=2, config=config) as client:
        logging.info("UDS Client Started")
        
        for case in test_cases:
            tc_id, step, service_id, subfunction, expected_response = case

            service_id = int(service_id, 16)
            subfunction = int(subfunction, 16)
            expected_response = int(expected_response, 16)
            
            print(f"Executing {tc_id}: {step}")
       
            if service_id == 0x10:  # Diagnostic Session Control
                try:
                    response = client.change_session(subfunction)
                    
                    ''' f.write('{:.4f} Tx 0 8 0x000007A0  {} {} 00 00 00 00 00 00 00 00\n'.format(
                             time.time(), hex(service_id), hex(subfunction)))# Log sent message'''
                         
                    print(f"Sent Tx: {step}")   
                except Exception as e:
                    logging.error(f"Error in Extended Session: {e}")
            elif service_id == 0x22:  # Read Data By Identifier
                     try:
                        response = client.read_data_by_identifier(subfunction)
                        '''f.write('{:.4f} Tx 0 8 0x000007A0  {} {} 00 00 00 00 00 00 00 00\n'.format(
                             time.time(), service_id, subfunction))# Log sent message
                        '''    
                     except Exception as e:
                           logging.error(f"Error in RDBI : {e}")  
                                
                     print(f"Sent Tx: {step}") 
        
test_cases = []
with open("test_cases_.txt", "r") as f:
    reader = csv.reader(f)
    next(reader)  # Skip header
    for row in reader:
        if not row[0].startswith("#"):  # Ignore comments
            test_cases.append(row) 
                   
with open(log_file, 'w') as f:
    # Write the header to the ASC file
    f.write('date: {}\n'.format(time.strftime('%Y-%m-%d')))
    f.write('base hex timestamps absolute')
    f.write('comment: Logging CAN communication with UDS service\n')
    f.write('begin of logfile\n')

    # Define ISO-TP parameters for CAN FD with 11-bit identifiers
    isotp_params = {
        'stmin': 32,
        'blocksize': 8,
        'wftmax': 0,
        'tx_padding': 0x00,
        'rx_flowcontrol_timeout': 1000,
        'rx_consecutive_frame_timeout': 1000,
        'max_frame_size': 4095,
        'can_fd': True,    
        'bitrate_switch': True# Enable CAN FD mode
    }
    
    # UDS Client Configuration
    config = dict(udsoncan.configs.default_client_config)
    config["ignore_server_timing_requirements"] = True
    config["data_identifiers"] = {
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
    
    # Define CAN interface
    interface = "can0"
    # Create CAN bus interface
    bus = can.interface.Bus(channel=interface, bustype="socketcan", fd=True)
   
    # Define ISO-TP addressing for 11-bit CAN IDs
    tp_addr = isotp.Address(isotp.AddressingMode.Normal_11bits, txid=0x7A0, rxid=0x7A8)
    
    # Create ISO-TP stack
    stack = isotp.CanStack(bus=bus, address=tp_addr, params=isotp_params) 
    # Create UDS connection
    conn = PythonIsoTpConnection(stack)
    
   #-------logging-------# 
    # Create the UDS Read DTC request (Tx)
    create_uds_session_request()
    while True:
        message = bus.recv(timeout=2.0)  # Timeout after 1 second if no response is received

        if message:
            message_type = 'Rx' if message.is_rx else 'Tx'
            # Log the Rx message
            '''f.write('{:.4f} {} 0 8 {:#010x} {} 00 00 00 00 00 00 00 00\n'.format(
                time.time(), message_type, message.arbitration_id, ' '.join([f'{x:02X}' for x in message.data])
            ))'''
            #print(f"Received Rx: {message}")
        else:
            print("No response received from ECU.")
    
    # Write the footer to the ASC file
    f.write('end of logfile\n')




    
 
        


