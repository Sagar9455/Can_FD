import re
import pandas as pd

input_path = '/home/mobase/Can_FD/Sahithi/KY_MKBD_Diagnostic_Rev01.cdd'
output_path = 'Zoutput_results_05.xlsx'

# Step 1: Parse all shstaticref -> v mappings (can be many per ref)
subservice_map = {}
with open(input_path, 'r', encoding='utf-8') as file:
    for line in file:
        match = re.search(r"shstaticref='([^']+)'\s+v='([^']+)'", line)
        if match:
            ref = match.group(1)
            value = match.group(2)
            subservice_map.setdefault(ref, []).append(value)

# Step 2: Parse all service definitions
results = []
current_ref = None

with open(input_path, 'r', encoding='utf-8') as file:
    for line in file:
        # Store shstaticref temporarily if it appears (may precede service entry)
        ref_match = re.search(r"shstaticref='([^']+)'", line)
        if ref_match:
            current_ref = ref_match.group(1)

        # Match service ID and name
        match = re.search(r'\(\$(\w{2})\)\s*(.*?)<\/TUV>', line)
        if match:
            service_id = match.group(1)
            service_name = match.group(2)

            # If shstaticref was previously stored, map all its subservice v-values
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

            # Reset after processing one service
            current_ref = None

# Step 3: Export results
df = pd.DataFrame(results)
df.to_excel(output_path, index=False)

print(f"✅ Extracted {len(results)} services with subservices. Data saved to: {output_path}")
