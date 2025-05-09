import re
import pandas as pd

# File paths
cdd_file_path = "/home/mobase/Can_FD/Sahithi/KY_MKBD_Diagnostic_Rev01.cdd"
output_path = "subserviceeee_01.xlsx"

# ---------- Part 1: Extract ServiceID and Service_name ----------
service_results = []

with open(cdd_file_path , 'r', encoding='utf-8') as file:
    for line in file:
        if '>($' in line:
            match = re.search(r'\(\$(\d{2})\)\s*(.*?)<\/TUV>', line)
            if match:
                service_results.append({
                    'ServiceID': match.group(1),
                    'Service_name': match.group(2)
                })

df_services = pd.DataFrame(service_results)

# ---------- Part 2: Extract subservice IDs ----------
subservice_pattern = r"shstaticref='[^']*'\s+v='([^']*)'"
subservice_ids = []

with open(cdd_file_path, "r", encoding="utf-8") as file:
    for line in file:
        match = re.search(subservice_pattern, line)
        if match:
            decimal_val = int(match.group(1))
            hex_val = f"0x{decimal_val:02X}"
            subservice_ids.append(hex_val)

df_subservices = pd.DataFrame({
    '': [''] * len(subservice_ids),
    ' ': [''] * len(subservice_ids),
    'subservice id': subservice_ids
})

# ---------- Write both DataFrames to different sheets ----------
with pd.ExcelWriter(output_path) as writer:
    df_services.to_excel(writer, sheet_name='Service Info', index=False)
    df_subservices.to_excel(writer, sheet_name='Subservices', index=False)

print(f"✅ Both service and subservice data saved to '{output_path}' in two sheets.")
