import sys
import os
import time
import logging
import RPi.GPIO as GPIO

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from drivers import oled_display, button_input, config_loader, uds_client
from drivers.report_generator import ReportGenerator


print(sys.path)

# Load config
config = config_loader.load_config("config.json")

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler("uds_debug.log"), logging.StreamHandler()]
)

# Bring up CAN interface 
if config.get("can_interface", {}).get("bringup_on_startup", False):
    bitrate = config["can_interface"].get("bitrate", 500000)
    dbitrate = config["can_interface"].get("dbitrate", 1000000)
    restart_ms = config["can_interface"].get("restart_ms", 1000)
    os.system(f"sudo ip link set can0 down")
    os.system(f"sudo ip link set can0 up type can bitrate {bitrate} dbitrate {dbitrate} restart-ms {restart_ms} berr-reporting on fd on")
    os.system("sudo ifconfig can0 up")
    logging.info("CAN interface can0 brought up")



# Setup
oled = oled_display.OLEDDisplay(config["display"])
btn_map = config["gpio"]["buttons"]
BTN_FIRST = btn_map["first"]
BTN_SECOND = btn_map["second"]
BTN_ENTER = btn_map["enter"]
BTN_THANKS = btn_map["thanks"]

buttons = button_input.ButtonInput(list(btn_map.values()))
uds = uds_client.UDSClient(config)


menu_combinations = config["menu_combinations"]
def show_text(text):
    oled.clear()
    oled.display_text(text)


# Welcome screen (centered)
oled.display_centered_text("Welcome\nto\nDiagnostics")
time.sleep(2)

# Prompt screen (centered)
oled.display_centered_text("Select Option:")
time.sleep(1)
# Main loop
while True:
    show_text("- Read ECU Info\n- Run Test cases\n- ECU Updater\n- Transfer Files")

    selected_sequence = []
    variable = 0
    varFinal=0

    # Combo input mode
    while True:
        if GPIO.input(BTN_FIRST) == GPIO.LOW:
            selected_sequence.append(BTN_FIRST)
            variable = (variable * 10) + 1
            show_text(str(variable))
            time.sleep(0.3)

        if GPIO.input(BTN_SECOND) == GPIO.LOW:
            selected_sequence.append(BTN_SECOND)
            variable = (variable * 10) + 2
            show_text(str(variable))
            time.sleep(0.3)

        if GPIO.input(BTN_ENTER) == GPIO.LOW :
            varFinal=variable
            variable=0
            selected_sequence.append(BTN_ENTER)
            key = str(tuple(selected_sequence))
            print(f"Captured sequence: {selected_sequence}")
            print(f"key string used : {str(tuple(selected_sequence))}")
            selected_option = menu_combinations.get(key, "Invalid Input")
            show_text(f"{selected_option}")
            
            time.sleep(0.5)

            if selected_option == "ECU Information":
                show_text("Fetching ECU Info...")
                uds.get_ecu_information(oled)
                show_text("Done")
                time.sleep(2)

            elif selected_option == "Testcase Execution":
                show_text("Running Testcases...")
                time.sleep(2)
                uds.run_testcase(oled)
                show_text("Done")
                time.sleep(2)
                
            elif selected_option == "Reserved1\nfor future versions":
                show_text("Reserved1\nfor future versions")
                time.sleep(2)
                show_text("Done")
                time.sleep(2)
         
            elif selected_option == "Reserved2\nfor future versions":
                show_text("Reserved2\nfor future versions")
                time.sleep(2)
                show_text("Done")
                time.sleep(2)
                
            elif selected_option.startswith("File Transfer"):
                show_text("Transferring logs...")
                time.sleep(2)
                #transfer_files_to_usb()
                #show_text("Done")
                #time.sleep(2)

            elif selected_option == "Exit":
                show_text("Exiting...")
                time.sleep(1)
                os.system("exit")

            break  # exit sequence input loop

        if GPIO.input(BTN_THANKS) == GPIO.LOW:
            show_text("Shutting Down")
            time.sleep(2)
            GPIO.cleanup()
            os.system("sudo poweroff")

        time.sleep(0.1)
