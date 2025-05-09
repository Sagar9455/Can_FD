import re
import pandas as pd

cdd_file_path = "/home/mobase/Can_FD/Sahithi/KY_MKBD_Diagnostic_Rev01.cdd"
output_path = "combined_service_subservice_14.xlsx"

# Regex patterns
service_pattern = r'\(\$(\d{2})\)\s*(.*?)<\/TUV>'
subservice_pattern = r"shstaticref='[^']*'\s+v='([^']*)'"

results = []
current_service_id = None
current_service_name = None

with open(cdd_file_path, 'r', encoding='utf-8') as file:
    for line in file:
        # Match service
        service_match = re.search(service_pattern, line)
        if service_match:
            current_service_id = service_match.group(1)
            current_service_name = service_match.group(2)
            results.append({
                'Service_ID': current_service_id,
                'Service_name': current_service_name,
                'Subservice_ID': None
            })

        # Match subservice
        subservice_match = re.search(subservice_pattern, line)
        if subservice_match and current_service_id:
            val = int(subservice_match.group(1))
            hex_val = f"0x{val:02X}"
            results.append({
                'Service_ID': current_service_id,
                'Service_name': current_service_name,
                'Subservice_ID': hex_val
            })

# Create DataFrame and write to Excel
df = pd.DataFrame(results)
df.to_excel(output_path, index=False)

print(f"✅ Combined data written to '{output_path}' in a single sheet.")
