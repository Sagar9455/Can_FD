import re
import pandas as pd

input_path = '/home/mobase/Can_FD/Sahithi/KY_MKBD_Diagnostic_Rev01.cdd'
output_path = 'output_results_05.xlsx'

# Step 1: Extract all shstaticref -> v mappings into a dictionary
subservice_map = {}
with open(input_path, 'r', encoding='utf-8') as file:
    for line in file:
        match = re.search(r"shstaticref='([^']+)'\s+v='([^']+)'", line)
        if match:
            ref = match.group(1)
            value = match.group(2)
            subservice_map.setdefault(ref, []).append(value)

# Step 2: Extract service definitions and associate subservices using latest shstaticref above it
results = []
current_ref = None

with open(input_path, 'r', encoding='utf-8') as file:
    for line in file:
        # Capture shstaticref if present (to be applied to the next service line)
        ref_match = re.search(r"shstaticref='([^']+)'", line)
        if ref_match:
            current_ref = ref_match.group(1)

        # Match service definition lines like: >($27) SecurityAccess - Send key</TUV>
        if '>($' in line:
            match = re.search(r'\(\$(\w{2})\)\s*(.*?)<\/TUV>', line)
            if match:
                service_id = match.group(1)
                service_name = match.group(2)

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

                current_ref = None  # Reset after service block is processed

# Step 3: Export to Excel
df = pd.DataFrame(results)
df.to_excel(output_path, index=False)
print(f"✅ Extracted {len(results)} services with subservices. Data saved to: {output_path}")
