import xml.etree.ElementTree as ET
import pandas as pd

# File paths
cdd_path = 'c0d9bceb-9bd0-43ff-8707-4e3a12232357.cdd'
output_excel = 'cdd_services_with_subservices.xlsx'

# Parse CDD XML
tree = ET.parse(cdd_path)
root = tree.getroot()

# Get XML namespace dynamically
ns = {'ns': root.tag.split('}')[0].strip('{')}

data = []

# Search for DIAG-SERVICE
for service in root.findall('.//ns:DIAG-SERVICE', ns):
    service_id = service.findtext('ns:ID', default='', namespaces=ns)
    service_name = service.findtext('ns:LONG-NAME', default='', namespaces=ns)

    # Search subfunctions if they exist
    subfunctions = service.findall('.//ns:SUBFUNCTION', ns)
    if subfunctions:
        for sub in subfunctions:
            sub_id = sub.findtext('ns:ID', default='', namespaces=ns)
            sub_name = sub.findtext('ns:LONG-NAME', default='', namespaces=ns)
            data.append({
                'Service ID-2': f"0x{service_id}",
                'Service Description-3': service_name,
                'Sub service ID-4': f"0x{sub_id}",
                'Sub Service Description-5': sub_name
            })
    else:
        # If no subfunction, just add the main service
        data.append({
            'Service ID-2': f"0x{service_id}",
            'Service Description-3': service_name,
            'Sub service ID-4': '',
            'Sub Service Description-5': ''
        })

# Write to Excel
df = pd.DataFrame(data)
df.to_excel(output_excel, index=False)

print(f"✅ Saved to: {output_excel}")
