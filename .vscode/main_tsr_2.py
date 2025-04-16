UDS Config loaded: {'can': {'channel': 'can0', 'interface': 'socketcan', 'bitrate': 500000, 'dbitrate': 1000000, 'tx_id': '0x7A0', 'rx_id': '0x7A8', 'is_extended': False, 'can_fd': True}, 'isotp': {'stmin': 10, 'blocksize': 8, 'wftmax': 0, 'tx_padding': 0, 'rx_flowcontrol_timeout': 1000, 'rx_consecutive_frame_timeout': 1000, 'max_frame_size': 4095, 'can_fd': True, 'bitrate_switch': True}, 'timing': {'s3_client': 3000, 's3_server': 5000, 'p2_client': 1000, 'p2_extended_client': 5000, 'p2_server': 100, 'p2_extended_server': 5000}, 'ecu_information_dids': {'0xF100': {'label': 'VIN', 'length': 4}, '0xF101': {'label': 'SoftwareVersion', 'length': 4}, '0xF187': {'label': 'VIN2', 'length': 9}, '0xF1AA': {'label': 'Part Number', 'length': 4}}, 'decoding_dids': {'0xF100': 4, '0xF101': 4, '0xF187': 9, '0xF1AA': 4, '0xF1B1': 4, '0xF193': 4, '0xF1DD': 4, '0xF120': 16, '0xF18B': 4, '0xF102': 8}, 'tester_present': '0x3E', 'default_session': '0x01', 'extended_session': '0x03'}
Captured sequence: [16, 20]
key string used: (16, 20)
ERROR:UdsClient:[InvalidResponseException] : ReadDataByIdentifier service execution returned an invalid response. Response given by server is incomplete.
ERROR:root:TC_003 3 - Part Number -> EXCEPTION - ReadDataByIdentifier service execution returned an invalid response. Response given by server is incomplete.
WARNING:root:TC_004 3 - SMK Software Version Number -> FAIL - Expected [98, 241, 170, 50, 46, 51, 51], got [98, 241, 170, 50, 46, 52, 51]
ERROR:UdsClient:[TimeoutException] : Did not receive response in time. P2 timeout time has expired (timeout=0.050 sec)
ERROR:root:TC_007 3 - S/W Version -> EXCEPTION - Did not receive response in time. P2 timeout time has expired (timeout=0.050 sec)
ERROR:UdsClient:[TimeoutException] : Did not receive response in time. P2 timeout time has expired (timeout=0.050 sec)
ERROR:root:TC_008 3 - BDC Platform Software Version Number -> EXCEPTION - Did not receive response in time. P2 timeout time has expired (timeout=0.050 sec)
ERROR:UdsClient:[UnicodeDecodeError] : 'ascii' codec can't decode byte 0x80 in position 0: ordinal not in range(128)
ERROR:root:TC_010 3 - EOL -> EXCEPTION - 'ascii' codec can't decode byte 0x80 in position 0: ordinal not in range(128)
Full path:/home/mobase/Inte_Project/output/can_logs/can_log_20250416_135400.asc
File name:can_log_20250416_135400.asc
Report generated: /home/mobase/Inte_Project/output/html_reports/UDS_Report_1744791915.html
[CANLogger] Log file saved to: /home/mobase/Inte_Project/output/can_logs/can_log_20250416_135400.asc
