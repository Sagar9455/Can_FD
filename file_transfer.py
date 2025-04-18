'''
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
'''
import os
import shutil
import subprocess

SOURCE_DIR = '/home/pi/data/'

def get_usb_mount_point():
    """Scans for USB mount points."""
    try:
        mounts = subprocess.check_output(['lsblk', '-o', 'MOUNTPOINT,LABEL'], text=True)
        for line in mounts.splitlines():
            if '/media/' in line or '/mnt/' in line:
                parts = line.strip().split()
                if parts and os.path.ismount(parts[0]):
                    return parts[0]
    except Exception as e:
        print(f"Error detecting USB: {e}")
    return None

def copy_files_to_usb():
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
        print("✅ All files copied successfully.")
    except Exception as e:
        print(f"Error copying files: {e}")
