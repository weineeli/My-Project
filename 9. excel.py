import os
import json
import pandas as pd

# Set variable for the folder number
folder_number = "277"

# Load data from JSON file
json_path = fr"C:\Users\willy\Desktop\Done\{folder_number}\output_data.json"
with open(json_path, 'r') as json_file:
    output_data = json.load(json_file)

# Extract data from JSON
headers = ["PV Left Superior", "PV Left Inferior", "PV Right Superior", "PV Right Inferior", "脂肪體積/模型總體積"]
data = [
    [output_data["Extension 5mm"]["PV Left Superior"],
     output_data["Extension 5mm"]["PV Left Inferior"],
     output_data["Extension 5mm"]["PV Right Superior"],
     output_data["Extension 5mm"]["PV Right Inferior"],
     output_data["Extension 5mm"]["Total Fat Volume/Total Volume"]],
    [output_data["Extension 10mm"]["PV Left Superior"],
     output_data["Extension 10mm"]["PV Left Inferior"],
     output_data["Extension 10mm"]["PV Right Superior"],
     output_data["Extension 10mm"]["PV Right Inferior"],
     output_data["Extension 10mm"]["Total Fat Volume/Total Volume"]]
]

# Create DataFrame
df = pd.DataFrame(data, columns=headers)
df.insert(0, 'Extension', ['往外延伸 5mm', '往外延伸 10mm'])

# Save the DataFrame to an Excel file
output_path = fr"C:\Users\willy\Desktop\Done\{folder_number}\output_data.xlsx"
df.to_excel(output_path, index=False)

print(f"Excel file saved to {output_path}")
