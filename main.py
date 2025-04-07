from modules import button_input, oled_display, uds_client, config_loader
import logging
import time

# Load configuration
config = config_loader.load_config("config.json")
oled = oled_display.OLED()

logging.info("Waiting for button press to start diagnostics...")

# Load configuration
config = ConfigLoader()
menu_combinations = config.get('menu_combinations')
oled_config = config.get('display')
can_config = config.get('can')
uds_config = config.get('uds')
isotp_config = uds_config.get('isotp')
report_filename = config.get('report.filename')

# Initialize components
oled = OLEDDisplay(oled_config)
buttons = ButtonInput(config.get('gpio.button_pins'))
uds = UDSClient(can_config)
report = ReportGenerator(report_filename)

def load_testcases(file_path):
    testcases = []
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            testcase = {
                "id": row["TestCaseID"],
                "description": row["Step"],
                "service_id": int(row["ServiceID"], 16),
                "sub_id": int(row["SubFunction/ID"], 16),
                "expected_response": int(row["ExpectedResponse"], 16)
            }
            testcases.append(testcase)
    return testcases

def display_text(text, y=0):
    oled.clear()
    oled.display_text(text, y)

# Display welcome screen
display_text("            Welcome\n                   to\n           Diagnostic")
time.sleep(2)

variable = 0
varFinal = 0
selected_sequence = []
selected_option = None

# GPIO pin numbers
BTN_FIRST = config.get('gpio.button_pins')[0]
BTN_SECOND = config.get('gpio.button_pins')[1]
BTN_ENTER = config.get('gpio.button_pins')[2]
BTN_THANKS = config.get('gpio.button_pins')[3]

while True:
        oled.clear()
        display_text("Select a option:\n1. ECU Information\n2. Testcase Execution\n3. ECU Flashing\n4. File Transfer into USB device\n5. Reserved", y=0)

        while True:
            if GPIO.input(BTN_FIRST) == GPIO.LOW:
                variable = (variable * 10) + 1
                selected_sequence.append(BTN_FIRST)
                display_text(str(variable))

            if GPIO.input(BTN_SECOND) == GPIO.LOW:
                variable = (variable * 10) + 2
                selected_sequence.append(BTN_SECOND)
                display_text(str(variable))

            if GPIO.input(BTN_ENTER) == GPIO.LOW:
                varFinal = variable
                variable = 0
                selected_sequence.append(BTN_ENTER)

                selected_option = menu_combinations.get(tuple(selected_sequence), "Invalid Input")
                display_text(f"{selected_option}")

                if selected_option == "ECU Information":
                    time.sleep(0.5)
                    display_text("Fetching\nECU Information...")
                    uds.get_ecu_information()
                    display_text("Completed")

                elif selected_option == "Testcase Execution":
                    time.sleep(0.5)
                    display_text("Executing\nUDS Testcases...")
                    runner = UDSTestRunner(
                        can_config=can_config,
                        uds_config=uds_config,
                        isotp_config=isotp_config,
                        testcase_file="uds_testcases.txt"
                    )
                    results = runner.run_all()
                    generate_report(results)
                    display_text("Report\nGenerated")

                elif selected_option == "Exit":
                    os.system("exit")

                selected_sequence.clear()

            if GPIO.input(BTN_THANKS) == GPIO.LOW:
                display_text("Shutting Down")
                time.sleep(0.1)
                os.system('sudo poweroff')

            time.sleep(0.1)

        logging.info(f"Diagnostic completed. Report saved at: {report_path}")
        time.sleep(2)
        oled.clear_display()
