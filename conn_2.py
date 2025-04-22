import requests

# Replace this with the actual IP address of your PC (Windows machine running Flask)
PC_IP = "192.168.10.220"  
PORT = 5000

url = f"http://{PC_IP}:{PORT}/trigger"

try:
    response = requests.post(url)
    if response.status_code == 200:
        data = response.json()
        print("✅ Response from PC/CANoe:", data["canoe_response"])
    else:
        print("❌ Failed with status code:", response.status_code)
except Exception as e:
    print("❌ Error during request:", str(e))
