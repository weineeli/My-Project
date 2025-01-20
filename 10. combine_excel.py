import os
import json
import pandas as pd

# List to store all data
all_data = []

# Function to process data from a folder and append to all_data
def process_folder(folder_number):
    folder_path = fr"C:\Users\willy\Desktop\Done\{folder_number}"
    json_path = os.path.join(folder_path, "output_data.json")

    # Check if the JSON file exists in the folder
    if not os.path.exists(json_path):
        print(f"Folder {folder_number}: JSON file not found, skipping...")
        return

    # Load data from JSON file
    with open(json_path, 'r') as json_file:
        output_data = json.load(json_file)

    # Define the expected keys
    extensions = ["Extension 5mm", "Extension 10mm"]

    # Extract data for both extensions if they exist
    for extension in extensions:
        if extension in output_data:
            row = [
                output_data[extension].get("PV Left Superior", "N/A"),
                output_data[extension].get("PV Left Inferior", "N/A"),
                output_data[extension].get("PV Right Superior", "N/A"),
                output_data[extension].get("PV Right Inferior", "N/A"),
                output_data[extension].get("Total Fat Volume/Total Volume", "N/A")
            ]
            extension_label = extension.replace("Extension", "往外延伸")
            row.insert(0, extension_label)
            row.insert(0, folder_number)
            all_data.append(row)
        else:
            print(f"Folder {folder_number}: '{extension}' not found, skipping...")

# Iterate through folders 2-20, skipping non-existing ones
for folder_number in range(2, 71):
    process_folder(str(folder_number))

# Create the final DataFrame with all collected data
if all_data:
    headers = ["Folder Number", "Extension", "PV Left Superior", "PV Left Inferior", "PV Right Superior", "PV Right Inferior", "脂肪體積/模型總體積"]
    final_df = pd.DataFrame(all_data, columns=headers)

    # Save the final DataFrame to a single Excel file on the Desktop
    output_path = r"C:\Users\willy\Desktop\output_data.xlsx"
    final_df.to_excel(output_path, index=False)

    print(f"Consolidated Excel file saved to {output_path}")
else:
    print("No valid data found to consolidate.")
