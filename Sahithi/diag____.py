import re
import pandas as pd

# File paths
input_path = 'your_file.cdd'         # Replace with your actual .cdd file path
output_path = 'output_results.xlsx'  # Output Excel file

# List to collect results
results = []

# Read and process the .cdd file
with open(input_path, 'r', encoding='utf-8') as file:
    for line in file:
        # Look for pattern like ($10) DescriptionText
        match = re.search(r'\(\$(\d{2})\)\s*([^\s<]+)', line)
        if match:
            code = match.group(1)
            description = match.group(2)
            results.append({'Code': code, 'Description': description})

# Convert to DataFrame and save to Excel
df = pd.DataFrame(results)
df.to_excel(output_path, index=False)

print(f"✅ Extracted data saved to: {output_path}")
