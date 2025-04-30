import re
import pandas as pd

input_path = '/home/mobase/Can_FD/Sahithi/BDC_ver0.12_ver9.0.cdd'
output_path = 'output_results_03.xlsx'

results = []

with open(input_path, 'r', encoding='utf-8') as file:
    for line in file:
        # Optional: quick filter
        if '>($' in line:
            match = re.search(r'\(\$(\d{2})\)\s*(.*?)<\/TUV>', line)
            if match:
                ServiceID = match.group(1)
                Service_name = match.group(2)
                results.append({'ServiceID': ServiceID, 'Service_name': Service_name})

df = pd.DataFrame(results)
df.to_excel(output_path, index=False)

print(f"✅ Extracted data saved to: {output_path}")
