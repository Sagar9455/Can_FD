import re
import pandas as pd

cdd_file_path = "/home/mobase/Can_FD/Sahithi/KY_MKBD_Diagnostic_Rev01.cdd"
output_path = "combined_service_subservice_13.xlsx"

# Step 1: Extract service info
service_pattern = r'\(\$(\d{2})\)\s*(.*?)<\/TUV>'
results = []

# Step 2: Extract subservice info with nearby ServiceID (assumes previous ServiceID applies)
subservice_pattern = r"shstaticref='[^']*'\s+v='([^']*)'"

with open(cdd_file_path, 'r', encoding='utf-8') as file:
    for line in file:
        if '>($' in line:
            match = re.search(service_pattern, line)
            if match:
                ServiceID = match.group(1)
                Servicename = match.group(2)
                results.append({'Service_ID': ServiceID, 'Service_name': Servicename}) 
        # Extract subservice IDs
        sub_match = re.search(subservice_pattern, line)
        if sub_match :
            val = int(sub_match.group(1))
            hex_val = f"0x{val:02X}"  # Keep subservice ID in hexadecimal format
            SubserviceID = hex_val
            results.append({'Subservice_ID' : SubserviceID})  

# Step 3: Write to Excel
df = pd.DataFrame(results)
df.to_excel(output_path, index=False)

print(f"✅ Combined data written to '{output_path}' in a single sheet.")
