import pandas as pd

# File paths
excel_path = 'MKBD_DiagnosticserviceList.xlsx'  # Input Excel file
txt_path = 'MKBD_output_text.txt'        # Output text file

# Read the Excel file
df = pd.read_excel(excel_path)

# Select columns C-G (index 2 to 6)
#df_subset = df.iloc[:, 2:7] # Note: 7 is exclusive
#or
df_subset = df.iloc[:, [0,5, 2, 4 ,6]] # column a and c-g

#filtered_df = df_subset[(df_subset.iloc[:, 1] == 10) & (df_subset.iloc[:, 3] == 1)] #or
#filtered_df = df_subset[(df_subset.iloc[:, 1].astype(str) == "10") & (df_subset.iloc[:, 3].astype(str) == "01")]
filtered_df = df_subset[(df_subset.iloc[:, 1].astype(str) == "10") & (df_subset.iloc[:, 3].astype(str) == "01")]

# Convert rows to text lines
#text_lines = filtered_df.astype(str).apply(lambda row: ' | '.join(row), axis=1).tolist()



# Convert rows to text lines
text_lines = df_subset.astype(str).apply(lambda row: ' , '.join(row), axis=1).tolist()

# Write to text file
with open(txt_path, 'w', encoding='utf-8') as f:
    for line in text_lines:
        f.write(line + '\n')

print(f"✅ Selected columns (C-G) saved to: {txt_path}")
