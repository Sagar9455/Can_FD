import re
import pandas as pd

input_path = '/home/mobase/Can_FD/Sahithi/KY_MKBD_Diagnostic_Rev01.cdd'
output_path = 'output_results_final.xlsx'

# Step 1: Build shstaticref -> subservice ID (v) list mapping
subservice_map = {}
with open(input_path, 'r', encoding='utf-8') as file:
    for line in file:
        match = re.search(r"shstaticref='([^']+)'\s+v='([^']+)'", line)
        if match:
            ref = match.group(1)
            value = match.group(2)
            subservice_map.setdefault(ref, []).append(value)

# Step 2: Parse service ID + name, and associate subservices using last seen shstaticref
results = []
current_ref = None

with open(input_path, 'r', encoding='utf-8') as file:
    for line in file:
        # If a line contains a shstaticref, store it
        ref_match = re.search(r"shstaticref='([^']+)'", line)
        if ref_match:
            current_ref = ref_match.group(1)

        # If line contains a service definition
        if '>($' in line:
            match = re.search(r'\(\$(\w{2})\)\s+(.*?)<\/TUV>', line)
            if match:
                service_id = match.group(1)
                service_name = match.group(2)

                # Map subservice(s) if shstaticref exists and is mapped
                if current_ref and current_ref in subservice_map:
                    for sub_id in subservice_map[current_ref]:
                        results.append({
                            'ServiceID': service_id,
                            'Service_name': service_name,
                            'SubserviceID': sub_id
                        })
                else:
                    results.append({
                        'ServiceID': service_id,
                        'Service_name': service_name,
                        'SubserviceID': ''
                    })

                # Reset current_ref after use
                current_ref = None

# Step 3: Save to Excel
df = pd.DataFrame(results)
df.to_excel(output_path, index=False)

print(f"✅ Extracted {len(results)} rows. Data saved to: {output_path}")
