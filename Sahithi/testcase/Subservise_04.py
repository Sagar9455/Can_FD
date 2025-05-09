import re
import pandas as pd

# Path to your .cdd file
cdd_file_path = "your_file.cdd"

# Regular expression to match lines containing shstaticref and extract v
pattern = r"shstaticref='[^']*'\s+v='([^']*)'"

# Store all matched subservice IDs
subservice_ids = []

# Read file and apply regex
with open(cdd_file_path, "r", encoding="utf-8") as file:
    for line in file:
        match = re.search(pattern, line)
        if match:
            subservice_ids.append(match.group(1))

# Write to Excel
df = pd.DataFrame({'subservice id': subservice_ids})
output_path = "subservice_ids.xlsx"
df.to_excel(output_path, index=False)

print(f"Extracted {len(subservice_ids)} subservice IDs written to '{output_path}'")
