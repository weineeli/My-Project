import os
import json

# 替換的數字和側邊名稱
replacement_number = "70"  
side_names = ["Right_Superior", "Left_Superior", "Right_Inferior", "Left_Inferior"]

# 依次處理每個側邊名稱
for replacement_side in side_names:
    # 設定資料夾路徑
    folder_path = rf'C:\Users\willy\Desktop\Done\{replacement_number}\Centerline_PV_{replacement_side}'
    
    # 初始化一個字典來儲存合併的內容
    merged_content = {
        "@schema": "https://raw.githubusercontent.com/slicer/slicer/master/Modules/Loadable/Markups/Resources/Schema/markups-schema-v1.0.3.json#",
        "markups": []
    }
    
    # 遍歷資料夾中的所有 .mrk.json 文件
    for filename in os.listdir(folder_path):
        if filename.endswith(".mrk.json"):
            file_path = os.path.join(folder_path, filename)
            
            # 讀取 .mrk.json 文件
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
                # 將所有的 markups 合併到 merged_content 中
                merged_content["markups"].extend(data.get("markups", []))

    # 將合併後的內容儲存到一個新的 .mrk.json 文件中
    output_path = os.path.join(rf'C:\Users\willy\Desktop\Done\{replacement_number}', f'Centerline_PV_{replacement_side}.mrk.json')
    with open(output_path, 'w', encoding='utf-8') as outfile:
        json.dump(merged_content, outfile, indent=4)

    print(f"{replacement_side} 的合併完成並儲存至 {output_path}")
