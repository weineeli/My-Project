import os
import SimpleITK as sitk
import sitkUtils
import slicer
import vtk
import numpy as np
import json

file_number = '20'

# 定義四個中心線的路徑
centerline_paths = [
    fr"C:/Users/willy/Desktop/Done/{file_number}/Centerline_PV_Left_Superior.vtk",
    fr"C:/Users/willy/Desktop/Done/{file_number}/Centerline_PV_Left_Inferior.vtk",
    fr"C:/Users/willy/Desktop/Done/{file_number}/Centerline_PV_Right_Superior.vtk",
    fr"C:/Users/willy/Desktop/Done/{file_number}/Centerline_PV_Right_Inferior.vtk"
]

# 加載中心線節點
centerline_nodes = []
for path in centerline_paths:
    centerline_node = slicer.util.loadNodeFromFile(path, 'ModelFile')
    centerline_nodes.append(centerline_node)

def convert_to_triangle(model_node):
    # 使用 vtkTriangleFilter 將模型轉換為三角形
    triangle_filter = vtk.vtkTriangleFilter()
    triangle_filter.SetInputData(model_node.GetPolyData())
    triangle_filter.Update()
    return triangle_filter.GetOutput()

def remove_units(data_str):
    # 移除 "cm³" 單位和空格
    return data_str.replace(' cm³', '').strip()

def format_output(left_superior_info, left_inferior_info, right_superior_info, right_inferior_info):
    # 計算總脂肪體積和總體積
    total_fat_volume_5mm = left_superior_info[2] + left_inferior_info[2] + right_superior_info[2] + right_inferior_info[2]
    total_volume_5mm = float(remove_units(left_superior_info[0].split('/')[1])) + \
                       float(remove_units(left_inferior_info[0].split('/')[1])) + \
                       float(remove_units(right_superior_info[0].split('/')[1])) + \
                       float(remove_units(right_inferior_info[0].split('/')[1]))

    # 修正的 total_fat_volume_10mm，應從對應的10mm數據提取並轉換為數值類型
    fat_volume_10mm_ls = float(remove_units(left_superior_info[1].split('/')[0]))
    fat_volume_10mm_li = float(remove_units(left_inferior_info[1].split('/')[0]))
    fat_volume_10mm_rs = float(remove_units(right_superior_info[1].split('/')[0]))
    fat_volume_10mm_ri = float(remove_units(right_inferior_info[1].split('/')[0]))

    total_fat_volume_10mm = fat_volume_10mm_ls + fat_volume_10mm_li + fat_volume_10mm_rs + fat_volume_10mm_ri

    total_volume_10mm = float(remove_units(left_superior_info[1].split('/')[1])) + \
                        float(remove_units(left_inferior_info[1].split('/')[1])) + \
                        float(remove_units(right_superior_info[1].split('/')[1])) + \
                        float(remove_units(right_inferior_info[1].split('/')[1]))

    # 格式化輸出
    output_data = {
        "Extension 5mm": {
            "PV Left Superior": remove_units(left_superior_info[0]),
            "PV Left Inferior": remove_units(left_inferior_info[0]),
            "PV Right Superior": remove_units(right_superior_info[0]),
            "PV Right Inferior": remove_units(right_inferior_info[0]),
            "Total Fat Volume/Total Volume": f"{total_fat_volume_5mm:.2f}/{total_volume_5mm:.2f}"
        },
        "Extension 10mm": {
            "PV Left Superior": remove_units(left_superior_info[1]),
            "PV Left Inferior": remove_units(left_inferior_info[1]),
            "PV Right Superior": remove_units(right_superior_info[1]),
            "PV Right Inferior": remove_units(right_inferior_info[1]),
            "Total Fat Volume/Total Volume": f"{total_fat_volume_10mm:.2f}/{total_volume_10mm:.2f}"
        }
    }

    # 將結果保存到 JSON 文件
    json_path = fr"C:/Users/willy/Desktop/Done/{file_number}/output_data.json"
    with open(json_path, 'w', encoding='utf-8') as json_file:
        json.dump(output_data, json_file, ensure_ascii=False, indent=4)

    print(f"已將結果保存到: {json_path}")

# 合併信息
left_superior_info = (left_superior_info_1x[0], left_superior_info_2x[0], left_superior_info_1x[2])
left_inferior_info = (left_inferior_info_1x[0], left_inferior_info_2x[0], left_inferior_info_1x[2])
right_superior_info = (right_superior_info_1x[0], right_superior_info_2x[0], right_superior_info_1x[2])
right_inferior_info = (right_inferior_info_1x[0], right_inferior_info_2x[0], right_inferior_info_1x[2])

# 輸出結果並保存到 JSON
format_output(left_superior_info, left_inferior_info, right_superior_info, right_inferior_info)