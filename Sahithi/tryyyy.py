import xml.etree.ElementTree as ET
import pandas as pd

# Input/Output paths
cdd_path = '/home/mobase/Can_FD/Sahithi/KY_MKBD_Diagnostic_Rev01.cdd'
output_excel = 'cdd_services_with_subservices.xlsx'

# Parse the CDD file
tree = ET.parse(cdd_path)
root = tree.getroot()

# Namespace handling
ns = {'ns': root.tag.split('}')[0].strip('{')}

rows = []

# Look for all diagnostic services
for diag_service in root.findall('.//ns:DIAG-SERVICE', ns):
    service_id_tag = diag_service.find('.//ns:ID', ns)
    service_desc_tag = diag_service.find('.//ns:LONG-NAME', ns)

    service_id = service_id_tag.text if service_id_tag is not None else ''
    service_desc = service_desc_tag.text if service_desc_tag is not None else ''

    # Look for subfunctions/subservices
    for sub in diag_service.findall('.//ns:SUBFUNCTIONS//ns:DIAG-SUBFUNCTION', ns):
        sub_id_tag = sub.find('.//ns:ID', ns)
        sub_desc_tag = sub.find('.//ns:LONG-NAME', ns)

        sub_id = sub_id_tag.text if sub_id_tag is not None else ''
        sub_desc = sub_desc_tag.text if sub_desc_tag is not None else ''

        rows.append({
            'Service ID': service_id,
            'Service Description': service_desc,
            'Sub service ID': sub_id,
            'Sub Service Description': sub_desc
        })

# Write to Excel
df = pd.DataFrame(rows)
df.to_excel(output_excel, index=False)

print(f"✅ Extracted service + sub-service info saved to: {output_excel}")
