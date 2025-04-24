import pandas as pd

# File paths
excel_path = '/home/mobase/Can_FD/Sahithi/Diagnosticservice_CDD.xlsx'  # Input Excel file
txt_path = 'output_text_01.txt'        # Output text file

# Read the Excel file
df = pd.read_excel(excel_path)

# Select columns C-G (index 2 to 6)
df_subset = df.iloc[:, 2:7]  # Note: 7 is exclusive

# Convert rows to text lines
text_lines = df_subset.astype(str).apply(lambda row: ' | '.join(row), axis=1).tolist()

# Write to text file
with open(txt_path, 'w', encoding='utf-8') as f:
    for line in text_lines:
        f.write(line + '\n')

print(f"✅ Selected columns (C-G) saved to: {txt_path}")
