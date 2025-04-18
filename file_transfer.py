import os
import shutil
import time

SOURCE_DIR = '/home/pi/data/'
USB_MOUNT_BASE = '/media/pi/'

def get_usb_mount_point():
    """Returns the path to the mounted USB if found, else None."""
    for item in os.listdir(USB_MOUNT_BASE):
        mount_path = os.path.join(USB_MOUNT_BASE, item)
        if os.path.ismount(mount_path):
            return mount_path
    return None

def copy_files_to_usb():#API for calling at necessary point
    usb_mount_point = get_usb_mount_point()
    if not usb_mount_point:
        print("No USB drive detected. Please insert a USB.")
        return

    dest_dir = os.path.join(usb_mount_point, 'copied_data')
    os.makedirs(dest_dir, exist_ok=True)

    try:
        for filename in os.listdir(SOURCE_DIR):
            src_file = os.path.join(SOURCE_DIR, filename)
            dst_file = os.path.join(dest_dir, filename)
            if os.path.isfile(src_file):
                shutil.copy2(src_file, dst_file)
                print(f"Copied {filename} to USB.")
        print("All files copied successfully.")
    except Exception as e:
        print(f"Error copying files: {e}")
