import os

# Path of the folder containing the PDFs
folder_path = r"C:\Users\ilias\Documents\Existant\Datasheets"

# Output text file
output_file = "pdf_names.txt"

# Get all PDF filenames
pdf_files = [
    file for file in os.listdir(folder_path)
    if file.lower().endswith(".pdf")
]

# Write names to txt file
with open(output_file, "w", encoding="utf-8") as f:
    for pdf in pdf_files:
        f.write(pdf + "\n")

print(f"{len(pdf_files)} PDF names exported to {output_file}")