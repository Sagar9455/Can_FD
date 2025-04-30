import pandas as pd

# File paths
excel_path = 'output_results.xlsx'
txt_path = 'output_text.txt'

# Read the Excel file
df = pd.read_excel(excel_path)

# Select columns C-G (index 2 to 6)
df_subset = df.iloc[:, 2:7]  # Columns C to G

# Function to insert '-' after the first column
def format_row(row):
    row = row.astype(str).tolist()
    return f"{row[0]} - {' , '.join(row[1:])}"

# Format the header
header = df_subset.columns.astype(str).tolist()
header_line = f"{header[0]} - {' , '.join(header[1:])}"

# Format data rows
data_lines = df_subset.apply(format_row, axis=1).tolist()

# Combine header and data
all_lines = [header_line] + data_lines

# Write to .txt file
with open(txt_path, 'w', encoding='utf-8') as f:
    f.write('#')
    for line in all_lines:
        f.write(line + '\n')

print(f"✅ Columns C-G with '-' after the first column saved to: {txt_path}")
