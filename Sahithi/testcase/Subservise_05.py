import re
import pandas as pd

# Path to your .cdd file
cdd_file_path = "your_file.cdd"

# Regex to extract decimal subservice id from lines with shstaticref
pattern = r"shstaticref='[^']*'\s+v='([^']*)'"

subservice_ids_decimal = []

# Extract v values
with open(cdd_file_path, "r", encoding="utf-8") as file:
    for line in file:
        match = re.search(pattern, line)
        if match:
            subservice_ids_decimal.append(int(match.group(1)))  # convert to int directly

# Create hex values
subservice_ids_hex = [f"0x{val:02X}" for val in subservice_ids_decimal]

# Write both to Excel
df = pd.DataFrame({
    'subservice id (decimal)': subservice_ids_decimal,
    'subservice id (hex)': subservice_ids_hex
})

output_path = "subservice_ids_converted.xlsx"
df.to_excel(output_path, index=False)

print(f"Converted subservice IDs written to '{output_path}'")
