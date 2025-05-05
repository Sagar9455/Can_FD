import re
import pandas as pd

input_path = '/mnt/data/KY_MKBD_Diagnostic_Rev01.cdd'
output_path = '/mnt/data/final_service_subfunctions.xlsx'

results = []

with open(input_path, 'r', encoding='utf-8') as f:
    current_service_id = None
    current_service_name = None
    temp_dtref = None
    inside_texttbl = False
    subfunction_id = None
    subfunction_name = None

    for line in f:
        # Detect main service
        if '>($' in line:
            match = re.search(r'\(\$(\w{2})\)\s*(.*?)<\/TUV>', line)
            if match:
                current_service_id = f"0x{match.group(1)}"
                current_service_name = match.group(2).strip()

        # Capture dtref for TEXTTBL lookup
        dtref_match = re.search(r"dtref='(_[A-Fa-f0-9]+)'", line)
        if dtref_match:
            temp_dtref = dtref_match.group(1)

        # Match subfunction ID from TEXTMAP
        map_match = re.search(r'<TEXTMAP s="(\w+)">', line)
        if map_match and len(map_match.group(1)) > 1:
            subfunction_id = f"0x{map_match.group(1)[1:]}"
        
        # Enter TEXTTBL section
        if temp_dtref and f"<TEXTTBL id='{temp_dtref}'" in line:
            inside_texttbl = True
            continue

        if inside_texttbl:
            # Extract subfunction name
            name_match = re.search(r"<TUV xml:lang='en-US'>(.*?)</TUV>", line)
            if name_match:
                subfunction_name = name_match.group(1).strip()
            
            # Check end of TEXTTBL block
            if '</TEXTTBL>' in line:
                if current_service_id and subfunction_id and subfunction_name:
                    results.append({
                        'Service ID': current_service_id,
                        'Service Name': current_service_name,
                        'Subfunction ID': subfunction_id,
                        'Subfunction Name': subfunction_name
                    })
                # Reset for next block
                inside_texttbl = False
                subfunction_id = None
                subfunction_name = None
                temp_dtref = None

# Save results
df = pd.DataFrame(results)
df.to_excel(output_path, index=False)

print(f"✅ Saved to: {output_path}")
