import re
import pandas as pd

cdd_file_path = "/home/mobase/Can_FD/Sahithi/KY_MKBD_Diagnostic_Rev01.cdd"
output_path = "combined_service_subservice_04.xlsx"

# Step 1: Extract service info
service_pattern = r'\(\$(\d{2})\)\s*(.*?)<\/TUV>'
services = []

with open(cdd_file_path, 'r', encoding='utf-8') as file:
    for line in file:
        if '>($' in line:
            match = re.search(service_pattern, line)
            if match:
               # services.append({
                    #'ServiceID': int(match.group(1), 16),  # Convert hex string to int
                   # 'Service_name': match.group(2).strip()
                ServiceID = match.group(1)
                Service_name = match.group(2)
                services.append({'ServiceID': ServiceID, 'Service_name': Service_name})

               # })
                

# Step 2: Extract subservice info with nearby ServiceID (assumes previous ServiceID applies)
subservice_pattern = r"shstaticref='[^']*'\s+v='([^']*)'"
combined_data = []
current_service = None

with open(cdd_file_path, 'r', encoding='utf-8') as file:
    for line in file:
        # Update current service context if available
        service_match = re.search(service_pattern, line)
        if service_match:
            current_service = {
                'ServiceID': int(service_match.group(1), 16),
                'Service_name': service_match.group(2).strip()
            }

        # Extract subservice IDs
        sub_match = re.search(subservice_pattern, line)
        if sub_match and current_service:
            val = int(sub_match.group(1))
            hex_val = f"0x{val:02X}"
            combined_data.append({
                'ServiceID': current_service['ServiceID'],
                'Service_name': current_service['Service_name'],
                'Subservice ID': hex_val
            })

# Step 3: Write to Excel
df = pd.DataFrame(combined_data)
df.to_excel(output_path, index=False)

print(f"✅ Combined data written to '{output_path}' in a single sheet.")
