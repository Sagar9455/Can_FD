import os
import shutil
import time
import logging
from datetime import datetime

class USBTransfer:
    def __init__(self, oled):
        self.oled = oled
        self.outputs_folder = "//home/mobase/Test2/Demo/Module_Inte/output"
        self.usb_root = "/media"
        logging.info("USBTransfer initialized")

    def show_progress_animation(self, base_msg, duration=3, interval=0.5):
        steps = int(duration / interval)
        for i in range(steps):
            dots = '.' * ((i % 3) + 1)
            self.oled.display_centered_text(f"{base_msg}{dots}")
            time.sleep(interval)

    def get_usb_mount_path(self):
        logging.info(f"Looking for USB under: {self.usb_root}")
        try:
            for user in os.listdir(self.usb_root):
                user_path = os.path.join(self.usb_root, user)
                if os.path.isdir(user_path):
                    for device in os.listdir(user_path):
                        mount_path = os.path.join(user_path, device)
                        if os.path.ismount(mount_path):
                            logging.info(f"USB mount found at: {mount_path}")
                            return mount_path
        except Exception as e:
            logging.error(f"Error while scanning USB: {e}")
        return None

    def transfer_files_to_usb(self):
        try:
            self.oled.display_centered_text("Looking for USB...")
            logging.info("Starting transfer...")
            time.sleep(1)

            usb_path = self.get_usb_mount_path()
            if not usb_path:
                self.oled.display_centered_text("No USB found!")
                logging.warning("No USB device mounted")
                time.sleep(2)
                return

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_folder = os.path.join(usb_path, f"UDS_Backup_{timestamp}")
            os.makedirs(backup_folder, exist_ok=True)
            logging.info(f"Backup folder created on USB: {backup_folder}")

            self.oled.display_centered_text("USB Found.\nCopying Data...")
            self.show_progress_animation("Transferring", duration=3)

            destination = os.path.join(backup_folder, "Outputs")
            shutil.copytree(self.outputs_folder, destination)

            file_count = sum(len(files) for _, _, files in os.walk(destination))
            self.oled.display_centered_text(f"Transfer Done\n{file_count} files")
            logging.info(f"Transfer complete. Files copied: {file_count}")
            time.sleep(2)

        except Exception as e:
            self.oled.display_centered_text(f"Error:\n{str(e)[:20]}")
            logging.error(f"Error during USB transfer: {e}")
            time.sleep(3)
