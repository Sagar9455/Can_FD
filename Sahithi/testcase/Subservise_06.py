import re
import pandas as pd

# Path to your .cdd file
cdd_file_path = "/home/mobase/Can_FD/Sahithi/KY_MKBD_Diagnostic_Rev01.cdd"

# Regex to extract v values from lines containing shstaticref
pattern = r"shstaticref='[^']*'\s+v='([^']*)'"

# Extract v values and convert to int
subservice_ids = []
with open(cdd_file_path, "r", encoding="utf-8") as file:
    for line in file:
        match = re.search(pattern, line)
        if match:
            decimal_val = int(match.group(1))
            hex_val = f"0x{decimal_val:02X}"
            subservice_ids.append(hex_val)

# Create a DataFrame with empty 1st and 2nd columns, hex values in 3rd
df = pd.DataFrame({
    '': [''] * len(subservice_ids),
    ' ': [''] * len(subservice_ids),
    'subservice id': subservice_ids
})

# Write to Excel
output_path = "subservice_ids_hex_only.xlsx"
df.to_excel(output_path, index=False)

print(f"Hex subservice IDs written to third column in '{output_path}'")
