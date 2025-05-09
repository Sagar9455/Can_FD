import re
import pandas as pd

# File paths
cdd_file_path = "/home/mobase/Can_FD/Sahithi/KY_MKBD_Diagnostic_Rev01.cdd"
output_path = "combined_service_subservice.xlsx"

# Step 1: Extract main services (correct ServiceID + Service_name)
services = []
with open(cdd_file_path, 'r', encoding='utf-8') as file:
    for line in file:
        if '>($' in line:
            match = re.search(r'\(\$(\d{2})\)\s*(.*?)<\/TUV>', line)
            if match:
                service_id = int(match.group(1), 16)
                service_name = match.group(2)
                services.append({'ServiceID': service_id, 'Service_name': service_name})

services_df = pd.DataFrame(services)

# Step 2: Extract subservice values from lines with shstaticref and v
pattern = r"shstaticref='[^']*'\s+v='([^']*)'"
subservices = []

with open(cdd_file_path, "r", encoding="utf-8") as file:
    for line in file:
        match = re.search(pattern, line)
        if match:
            val = int(match.group(1))
            sub_hex = f"0x{val:02X}"
            subservices.append(sub_hex)

# Step 3: Append subservice IDs to correct services (repeat rows if needed)
# For demo, assume all subservices belong to just one or a few known ServiceIDs like 0x19 (e.g., ReadDTCInformation)
# Replace or enhance this logic based on actual shstaticref mapping, if needed

# Example: Assign all subservices to ServiceID 25 for now (adjust this logic to match your mapping)
target_service_id = 25  # This is likely wrong; refine based on actual mapping if available
matched_service = services_df[services_df['ServiceID'] == target_service_id]

# Repeat matched row for each subservice
final_rows = []
for sub_id in subservices:
    for _, row in matched_service.iterrows():
        final_rows.append({
            'ServiceID': row['ServiceID'],
            'Service_name': row['Service_name'],
            'Subservice ID': sub_id
        })

final_df = pd.DataFrame(final_rows)

# Step 4: Save to Excel
final_df.to_excel(output_path, index=False)
print(f"✅ Combined data saved to: {output_path}")
