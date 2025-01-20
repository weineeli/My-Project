import vtk
import json
import os

# 定義變數來替換路徑中的數字和方向
file_number = '70'
sides = ['Right_Superior', 'Left_Superior', 'Right_Inferior', 'Left_Inferior']

# 依次處理每個側邊名稱
for side in sides:
    # 設定JSON文件的路徑，使用變數來構建路徑
    json_file_path = fr'C:\Users\willy\Desktop\Done\{file_number}\Centerline_PV_{side}.mrk.json'

    # 讀取JSON文件
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # 創建VTK的PolyData來儲存點和曲線
    points = vtk.vtkPoints()
    lines = vtk.vtkCellArray()

    # 初始化點的索引
    point_index = 0

    # 迭代每個markup並轉換為VTK格式
    for markup in data['markups']:
        curve_type = markup['type']
        if curve_type == "Curve":
            control_points = markup['controlPoints']
            previous_point_id = None

            for point in control_points:
                position = point['position']
                point_id = points.InsertNextPoint(position)

                if previous_point_id is not None:
                    line = vtk.vtkLine()
                    line.GetPointIds().SetId(0, previous_point_id)
                    line.GetPointIds().SetId(1, point_id)
                    lines.InsertNextCell(line)

                previous_point_id = point_id

    # 創建PolyData並設置點和曲線
    poly_data = vtk.vtkPolyData()
    poly_data.SetPoints(points)
    poly_data.SetLines(lines)

    # 創建VTK檔案的寫入器，使用變數來構建路徑
    vtk_file_path = os.path.join(rf'C:\Users\willy\Desktop\Done\{file_number}', f'Centerline_PV_{side}.vtk')
    writer = vtk.vtkPolyDataWriter()
    writer.SetFileName(vtk_file_path)
    writer.SetInputData(poly_data)
    writer.Write()

    print(f"VTK檔案已儲存至 {vtk_file_path}")
