import os
import threading
import can
import time
import logging


class CANLogger:
    def __init__(self, channel='can0', interface='socketcan', can_fd=True):
        self.channel = channel
        self.interface = interface
        self.can_fd = can_fd
        self.running = False
        self.thread = None
        self.bus = None
        self.log_path = None
        self.file = None

    def _log_loop(self):
        while self.running:
            try:
                msg = self.bus.recv(1)
                if msg:
                    timestamp = f"{msg.timestamp:.6f}"
                    can_id = f"{msg.arbitration_id:03X}"
                    dlc = f"{msg.dlc}"
                    data = ' '.join(f"{byte:02X}" for byte in msg.data)
                    line = f"{timestamp} {can_id} Rx d {dlc} {data}\n"
                    self.file.write(line)
                    self.file.flush()
            except Exception as e:
                logging.error(f"CAN log error: {e}")
                continue

    def start(self, log_path):
        if self.running:
            self.stop()

        self.log_path = log_path
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        self.file = open(self.log_path, 'w')

        try:
            self.bus = can.interface.Bus(channel=self.channel, bustype=self.interface, fd=self.can_fd)
            self.running = True
            self.thread = threading.Thread(target=self._log_loop, daemon=True)
            self.thread.start()
            logging.info(f"CAN logging started: {self.log_path}")
        except Exception as e:
            logging.error(f"Failed to start CAN logger: {e}")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        if self.file:
            self.file.close()
            logging.info(f"CAN logging stopped: {self.log_path}")
        self.thread = None
        self.file = None
        self.bus = None
